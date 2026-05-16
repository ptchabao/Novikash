from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from app.core.database import get_session
from app.core.rbac import get_permissions, has_permission
from app.core.admin_audit import log_action, get_recent
from app.api.auth import get_staff_user, require_permission
from app.models.models import (
    User, Wallet, Transaction, PaymentMethod, SystemConfig,
    Loan, NoviPlusProfile, Notification,
)
from app.schemas.schemas import (
    AdminUserRead, UserUpdate, AdminTransactionRead, PaymentMethodRead,
    PaymentMethodBase, KYCUpdate, StaffMeRead, ManualWalletAdjustment,
    AdminDashboardStats, LoanAdminRead, NoviPlusAdminRead, NoviPlusVerifyRequest,
    LoanStatusUpdate, AdminAuditEntry,
)

router = APIRouter()


def _user_to_admin_read(user: User) -> AdminUserRead:
    return AdminUserRead(
        id=user.id,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_verified=user.is_verified,
        is_kyc_verified=user.is_kyc_verified,
        identity_type=user.identity_type,
        identity_number=user.identity_number,
        identity_document_url=user.identity_document_url,
        created_at=user.created_at,
        wallet=user.wallet,
    )


@router.get("/me", response_model=StaffMeRead)
def staff_me(staff: User = Depends(get_staff_user)):
    return StaffMeRead(
        id=staff.id,
        phone=staff.phone,
        email=staff.email,
        role=staff.role,
        permissions=sorted(get_permissions(staff.role)),
    )


@router.get("/dashboard", response_model=AdminDashboardStats)
def dashboard_stats(
    staff: User = Depends(require_permission("dashboard.view")),
    session: Session = Depends(get_session),
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = session.exec(select(func.count(User.id))).one()
    verified_users = session.exec(
        select(func.count(User.id)).where(User.is_verified == True)
    ).one()
    pending_kyc = session.exec(
        select(func.count(User.id)).where(
            User.identity_number.isnot(None),
            User.is_kyc_verified == False,
        )
    ).one()

    wallets = session.exec(select(Wallet)).all()
    total_available = sum(w.balance_available for w in wallets)
    total_locked = sum(w.balance_locked for w in wallets)

    active_loans = session.exec(
        select(func.count(Loan.id)).where(Loan.status == "ACTIVE")
    ).one()
    pending_loans = session.exec(
        select(func.count(Loan.id)).where(Loan.status == "PENDING")
    ).one()
    pending_novi = session.exec(
        select(func.count(NoviPlusProfile.id)).where(NoviPlusProfile.status == "PENDING_BANK")
    ).one()

    txs_today = session.exec(
        select(Transaction).where(Transaction.created_at >= today_start)
    ).all()

    deposits_today = sum(t.amount for t in txs_today if t.type == "DEPOSIT" and t.status == "SUCCESS")
    withdrawals_today = sum(t.amount for t in txs_today if t.type == "WITHDRAW" and t.status == "SUCCESS")
    manual_credits = sum(
        t.amount for t in txs_today
        if t.type == "ADMIN_CREDIT" and t.status == "SUCCESS"
    )

    return AdminDashboardStats(
        total_users=total_users or 0,
        verified_users=verified_users or 0,
        pending_kyc=pending_kyc or 0,
        total_wallet_balance=round(total_available, 2),
        total_locked_balance=round(total_locked, 2),
        active_loans=active_loans or 0,
        pending_loans=pending_loans or 0,
        pending_novi_plus=pending_novi or 0,
        transactions_today=len(txs_today),
        deposits_today=round(deposits_today, 2),
        withdrawals_today=round(withdrawals_today, 2),
        manual_credits_today=round(manual_credits, 2),
    )


# --- Users ---

@router.get("/users", response_model=List[AdminUserRead])
def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    staff: User = Depends(require_permission("users.read")),
    session: Session = Depends(get_session),
):
    query = select(User)
    if search:
        query = query.where(User.phone.contains(search))
    if role:
        query = query.where(User.role == role)
    query = query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    users = session.exec(query).all()
    return [_user_to_admin_read(u) for u in users]


@router.get("/users/{user_id}", response_model=AdminUserRead)
def get_user(
    user_id: int,
    staff: User = Depends(require_permission("users.read")),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return _user_to_admin_read(user)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    staff: User = Depends(require_permission("users.write")),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if data.role:
        if not has_permission(staff.role, "users.roles"):
            raise HTTPException(status_code=403, detail="Seul un SuperAdmin peut modifier les rôles")
        if staff.role != "SUPERADMIN" and data.role in ("ADMIN", "SUPERADMIN"):
            raise HTTPException(status_code=403, detail="Promotion admin réservée au SuperAdmin")
        user.role = data.role

    if data.is_verified is not None:
        user.is_verified = data.is_verified
    if data.email is not None:
        user.email = data.email

    session.add(user)
    session.commit()
    session.refresh(user)
    log_action(staff.id, staff.phone, "user.update", str(user_id), data.model_dump(exclude_none=True))
    return _user_to_admin_read(user)


# --- Wallet adjustments ---

@router.post("/users/{user_id}/wallet/credit")
def manual_credit(
    user_id: int,
    data: ManualWalletAdjustment,
    staff: User = Depends(require_permission("wallets.credit")),
    session: Session = Depends(get_session),
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")

    user = session.get(User, user_id)
    if not user or not user.wallet:
        raise HTTPException(status_code=404, detail="Utilisateur ou wallet introuvable")

    wallet = user.wallet
    wallet.balance_available += data.amount

    ref = data.reference or f"ADM-CR-{uuid.uuid4().hex[:12].upper()}"
    transaction = Transaction(
        type="ADMIN_CREDIT",
        amount=data.amount,
        status="SUCCESS",
        reference=ref,
        receiver_wallet_id=wallet.id,
        processed_at=datetime.utcnow(),
    )
    session.add(wallet)
    session.add(transaction)
    session.add(Notification(
        user_id=user.id,
        type="ADMIN_CREDIT",
        message=f"Crédit manuel de {data.amount:.0f} XOF. Motif : {data.reason}",
    ))
    session.commit()

    log_action(staff.id, staff.phone, "wallet.credit", user.phone, {
        "amount": data.amount, "reason": data.reason, "reference": ref,
    })
    return {
        "message": "Crédit effectué",
        "new_balance": wallet.balance_available,
        "reference": ref,
    }


@router.post("/users/{user_id}/wallet/debit")
def manual_debit(
    user_id: int,
    data: ManualWalletAdjustment,
    staff: User = Depends(require_permission("wallets.debit")),
    session: Session = Depends(get_session),
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Montant invalide")

    user = session.get(User, user_id)
    if not user or not user.wallet:
        raise HTTPException(status_code=404, detail="Utilisateur ou wallet introuvable")

    wallet = user.wallet
    if wallet.balance_available < data.amount:
        raise HTTPException(status_code=400, detail="Solde insuffisant")

    wallet.balance_available -= data.amount
    ref = data.reference or f"ADM-DB-{uuid.uuid4().hex[:12].upper()}"
    transaction = Transaction(
        type="ADMIN_DEBIT",
        amount=data.amount,
        status="SUCCESS",
        reference=ref,
        sender_wallet_id=wallet.id,
        processed_at=datetime.utcnow(),
    )
    session.add(wallet)
    session.add(transaction)
    session.add(Notification(
        user_id=user.id,
        type="ADMIN_DEBIT",
        message=f"Débit manuel de {data.amount:.0f} XOF. Motif : {data.reason}",
    ))
    session.commit()

    log_action(staff.id, staff.phone, "wallet.debit", user.phone, {
        "amount": data.amount, "reason": data.reason, "reference": ref,
    })
    return {
        "message": "Débit effectué",
        "new_balance": wallet.balance_available,
        "reference": ref,
    }


# --- Transactions ---

@router.get("/transactions", response_model=List[AdminTransactionRead])
def list_transactions(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    staff: User = Depends(require_permission("transactions.read")),
    session: Session = Depends(get_session),
):
    query = select(Transaction).order_by(Transaction.created_at.desc())
    if type:
        query = query.where(Transaction.type == type)
    if status:
        query = query.where(Transaction.status == status)
    query = query.offset(offset).limit(limit)
    transactions = session.exec(query).all()

    wallet_users: dict[int, str] = {}
    for w in session.exec(select(Wallet)).all():
        u = session.get(User, w.user_id)
        if u:
            wallet_users[w.id] = u.phone

    result = []
    for t in transactions:
        result.append(AdminTransactionRead(
            id=t.id,
            amount=t.amount,
            currency=t.currency,
            exchange_rate=t.exchange_rate,
            type=t.type,
            status=t.status,
            reference=t.reference,
            created_at=t.created_at,
            processed_at=t.processed_at,
            sender_wallet_id=t.sender_wallet_id,
            receiver_wallet_id=t.receiver_wallet_id,
            sender_phone=wallet_users.get(t.sender_wallet_id) if t.sender_wallet_id else None,
            receiver_phone=wallet_users.get(t.receiver_wallet_id) if t.receiver_wallet_id else None,
        ))
    return result


# --- Loans ---

@router.get("/loans", response_model=List[LoanAdminRead])
def list_loans(
    status: Optional[str] = Query(None),
    loan_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    staff: User = Depends(require_permission("loans.read")),
    session: Session = Depends(get_session),
):
    query = select(Loan).order_by(Loan.created_at.desc())
    if status:
        query = query.where(Loan.status == status)
    if loan_type:
        query = query.where(Loan.loan_type == loan_type)
    loans = session.exec(query.limit(limit)).all()

    result = []
    for loan in loans:
        borrower = session.get(User, loan.borrower_id)
        result.append(LoanAdminRead(
            id=loan.id,
            borrower_id=loan.borrower_id,
            loan_type=loan.loan_type,
            amount=loan.amount,
            interest_rate=loan.interest_rate,
            total_amount=loan.total_amount,
            status=loan.status,
            due_date=loan.due_date,
            created_at=loan.created_at,
            borrower_phone=borrower.phone if borrower else None,
        ))
    return result


@router.patch("/loans/{loan_id}/status")
def update_loan_status(
    loan_id: int,
    data: LoanStatusUpdate,
    staff: User = Depends(require_permission("loans.manage")),
    session: Session = Depends(get_session),
):
    loan = session.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Prêt introuvable")
    allowed = {"ACTIVE", "REPAID", "REJECTED", "DEFAULTED", "PENDING"}
    if data.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Autorisés : {allowed}")
    loan.status = data.status
    session.add(loan)
    session.commit()
    log_action(staff.id, staff.phone, "loan.status", str(loan_id), {"status": data.status})
    return {"message": "Statut mis à jour", "status": loan.status}


@router.get("/loans/novi-plus/pending", response_model=List[NoviPlusAdminRead])
def list_pending_novi_plus(
    staff: User = Depends(require_permission("loans.novi_verify")),
    session: Session = Depends(get_session),
):
    profiles = session.exec(
        select(NoviPlusProfile).where(
            NoviPlusProfile.status.in_(["PENDING_BANK", "DRAFT"])
        )
    ).all()
    result = []
    for p in profiles:
        user = session.get(User, p.user_id)
        result.append(NoviPlusAdminRead(
            id=p.id,
            user_id=p.user_id,
            user_phone=user.phone if user else None,
            first_name=p.first_name,
            last_name=p.last_name,
            employer=p.employer,
            contract_type=p.contract_type,
            contract_end_date=p.contract_end_date,
            partner_bank=p.partner_bank,
            account_number=p.account_number,
            declared_salary=p.declared_salary,
            verified_salary=p.verified_salary,
            status=p.status,
            rejection_reason=p.rejection_reason,
            submitted_at=p.submitted_at,
            activated_at=p.activated_at,
        ))
    return result


@router.patch("/loans/novi-plus/{profile_id}/verify")
def verify_novi_plus(
    profile_id: int,
    data: NoviPlusVerifyRequest,
    staff: User = Depends(require_permission("loans.novi_verify")),
    session: Session = Depends(get_session),
):
    profile = session.get(NoviPlusProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil NOVI+ introuvable")

    if data.approve:
        profile.status = "ACTIVE"
        profile.verified_salary = data.verified_salary or profile.declared_salary
        profile.activated_at = datetime.utcnow()
        profile.rejection_reason = None
        msg = "✅ Votre compte NOVI+ est activé."
    else:
        profile.status = "REJECTED"
        profile.rejection_reason = data.rejection_reason or "Validation bancaire refusée"
        msg = f"NOVI+ refusé : {profile.rejection_reason}"

    session.add(profile)
    session.add(Notification(user_id=profile.user_id, type="NOVI_PLUS_STATUS", message=msg))
    session.commit()
    log_action(staff.id, staff.phone, "novi_plus.verify", str(profile_id), data.model_dump())
    return {"message": "Profil NOVI+ mis à jour", "status": profile.status}


# --- KYC ---

@router.get("/kyc/pending", response_model=List[AdminUserRead])
def list_pending_kyc(
    staff: User = Depends(require_permission("kyc.read")),
    session: Session = Depends(get_session),
):
    users = session.exec(
        select(User).where(User.identity_number != None, User.is_kyc_verified == False)
    ).all()
    return [_user_to_admin_read(u) for u in users]


@router.patch("/kyc/{user_id}/verify", response_model=AdminUserRead)
def verify_user_kyc(
    user_id: int,
    data: KYCUpdate,
    staff: User = Depends(require_permission("kyc.verify")),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_kyc_verified = data.is_kyc_verified
    session.add(user)
    session.commit()
    session.refresh(user)
    log_action(staff.id, staff.phone, "kyc.verify", str(user_id), {"verified": data.is_kyc_verified})
    return _user_to_admin_read(user)


# --- Payment methods ---

@router.get("/payment-methods", response_model=List[PaymentMethodRead])
def list_payment_methods(
    staff: User = Depends(require_permission("payment_methods.manage")),
    session: Session = Depends(get_session),
):
    return session.exec(select(PaymentMethod)).all()


@router.post("/payment-methods", response_model=PaymentMethodRead)
def create_payment_method(
    data: PaymentMethodBase,
    staff: User = Depends(require_permission("payment_methods.manage")),
    session: Session = Depends(get_session),
):
    method = PaymentMethod(**data.model_dump())
    session.add(method)
    session.commit()
    session.refresh(method)
    return method


@router.patch("/payment-methods/{method_id}", response_model=PaymentMethodRead)
def update_payment_method(
    method_id: int,
    data: PaymentMethodBase,
    staff: User = Depends(require_permission("payment_methods.manage")),
    session: Session = Depends(get_session),
):
    method = session.get(PaymentMethod, method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Méthode introuvable")
    for key, value in data.model_dump().items():
        setattr(method, key, value)
    session.add(method)
    session.commit()
    session.refresh(method)
    return method


# --- System config (SuperAdmin) ---

@router.post("/config")
def set_system_config(
    key: str,
    value: str,
    description: Optional[str] = None,
    staff: User = Depends(require_permission("config.manage")),
    session: Session = Depends(get_session),
):
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if config:
        config.value = value
        config.description = description
        config.updated_at = datetime.utcnow()
    else:
        config = SystemConfig(key=key, value=value, description=description)
    session.add(config)
    session.commit()
    log_action(staff.id, staff.phone, "config.set", key, {"value": value})
    return {"status": "ok", "key": key, "value": value}


@router.get("/audit", response_model=List[AdminAuditEntry])
def audit_log(
    limit: int = Query(50, le=200),
    staff: User = Depends(require_permission("dashboard.view")),
):
    return [AdminAuditEntry(**e) for e in get_recent(limit)]
