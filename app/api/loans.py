from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid

from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.models import (
    User, Wallet, Loan, LoanGuarantee, Transaction, Notification,
    NoviPlusProfile, UserLoanProfile,
)
from app.schemas.schemas import (
    LoanRequest, LoanRead, GuaranteeResponse, NoviPlusActivateRequest,
    NoviPlusProfileRead, LoanEligibilityRead, LoanOverviewRead,
    LoanSimulationRead, PendingGuaranteeRead,
)

router = APIRouter()

WEEKLY_INTEREST_RATE = 0.01
MAX_LOAN_WEEKS = 4
ALOBA_MIN_WALLET = 2000.0
ALOBA_GLOBAL_CAP = 100000.0
ALOBA_DEFAULT_MULTIPLIER = 5.0
ALOBA_REDUCED_MULTIPLIER = 3.0
NOVI_SALARY_RATIO = 0.20
CDD_MIN_MONTHS = 3
BANK_VALIDATION_SECONDS = int(os.getenv("NOVI_BANK_VALIDATION_SECONDS", "5"))


def _get_or_create_loan_profile(session: Session, user: User) -> UserLoanProfile:
    profile = session.exec(
        select(UserLoanProfile).where(UserLoanProfile.user_id == user.id)
    ).first()
    if not profile:
        profile = UserLoanProfile(user_id=user.id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def _active_loan(session: Session, user_id: int) -> Optional[Loan]:
    return session.exec(
        select(Loan).where(
            Loan.borrower_id == user_id,
            Loan.status.in_(["PENDING", "ACTIVE"]),
        )
    ).first()


def _months_remaining(end_date: datetime) -> float:
    delta = end_date - datetime.utcnow()
    return delta.days / 30.44


def _simulate_repayment(amount: float, weeks: int = MAX_LOAN_WEEKS) -> LoanSimulationRead:
    interest = amount * WEEKLY_INTEREST_RATE * weeks
    due = datetime.utcnow() + timedelta(weeks=weeks)
    return LoanSimulationRead(
        amount=amount,
        weeks=weeks,
        interest_rate_per_week=WEEKLY_INTEREST_RATE,
        interest_amount=round(interest, 2),
        total_to_repay=round(amount + interest, 2),
        due_date=due,
    )


def _aloba_eligibility(session: Session, user: User, wallet: Wallet) -> LoanEligibilityRead:
    profile = _get_or_create_loan_profile(session, user)
    now = datetime.utcnow()
    if profile.suspended_until and profile.suspended_until > now:
        return LoanEligibilityRead(
            can_request=False,
            reason="Votre compte a enregistré plusieurs retards de remboursement. L'accès au prêt est temporairement suspendu pendant 3 mois.",
            wallet_balance=wallet.balance_available,
            multiplier=profile.aloba_multiplier,
            is_suspended=True,
            suspended_until=profile.suspended_until,
        )
    if wallet.balance_available < ALOBA_MIN_WALLET:
        return LoanEligibilityRead(
            can_request=False,
            reason=f"Un solde minimum de {ALOBA_MIN_WALLET:.0f} FCFA est requis sur votre wallet.",
            wallet_balance=wallet.balance_available,
            multiplier=profile.aloba_multiplier,
        )
    raw_max = wallet.balance_available * profile.aloba_multiplier
    max_amount = min(raw_max, ALOBA_GLOBAL_CAP)
    active = _active_loan(session, user.id)
    if active:
        return LoanEligibilityRead(
            can_request=False,
            reason="Vous avez déjà un prêt actif en cours. Le remboursement complet est nécessaire avant toute nouvelle demande.",
            max_amount=max_amount,
            wallet_balance=wallet.balance_available,
            multiplier=profile.aloba_multiplier,
        )
    return LoanEligibilityRead(
        can_request=True,
        max_amount=round(max_amount, 2),
        wallet_balance=wallet.balance_available,
        multiplier=profile.aloba_multiplier,
    )


def _novi_eligibility(session: Session, user: User) -> LoanEligibilityRead:
    profile = session.exec(
        select(NoviPlusProfile).where(NoviPlusProfile.user_id == user.id)
    ).first()
    active = _active_loan(session, user.id)
    if active:
        return LoanEligibilityRead(
            can_request=False,
            reason="Vous avez déjà un prêt actif en cours. Le remboursement complet est nécessaire avant toute nouvelle demande.",
        )
    if not profile or profile.status != "ACTIVE":
        status_msg = {
            "PENDING_BANK": "Validation bancaire en cours (24h max).",
            "REJECTED": profile.rejection_reason if profile else "Profil NOVI+ non activé.",
            None: "Activez NOVI+ pour accéder au prêt instantané.",
        }.get(profile.status if profile else None, "Activez NOVI+ pour accéder au prêt instantané.")
        return LoanEligibilityRead(can_request=False, reason=status_msg)
    salary = profile.verified_salary or profile.declared_salary
    max_amount = round(salary * NOVI_SALARY_RATIO, 2)
    return LoanEligibilityRead(
        can_request=True,
        max_amount=max_amount,
        wallet_balance=user.wallet.balance_available if user.wallet else 0,
    )


def _maybe_complete_bank_validation(session: Session, profile: NoviPlusProfile) -> NoviPlusProfile:
    if profile.status != "PENDING_BANK" or not profile.submitted_at:
        return profile
    elapsed = (datetime.utcnow() - profile.submitted_at).total_seconds()
    if elapsed >= BANK_VALIDATION_SECONDS:
        profile.status = "ACTIVE"
        profile.verified_salary = profile.declared_salary
        profile.activated_at = datetime.utcnow()
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.get("/overview", response_model=LoanOverviewRead)
def get_loans_overview(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    wallet = current_user.wallet
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet not found")

    loan_profile = _get_or_create_loan_profile(session, current_user)
    novi_profile = session.exec(
        select(NoviPlusProfile).where(NoviPlusProfile.user_id == current_user.id)
    ).first()
    if novi_profile:
        novi_profile = _maybe_complete_bank_validation(session, novi_profile)

    active = _active_loan(session, current_user.id)
    all_loans = session.exec(
        select(Loan).where(Loan.borrower_id == current_user.id).order_by(Loan.created_at.desc())
    ).all()

    pending_guarantees = session.exec(
        select(LoanGuarantee).where(
            LoanGuarantee.guarantor_id == current_user.id,
            LoanGuarantee.status == "PENDING",
        )
    ).all()

    novi_read = NoviPlusProfileRead.model_validate(novi_profile) if novi_profile else None

    return LoanOverviewRead(
        active_loan=LoanRead.model_validate(active) if active else None,
        loans=[LoanRead.model_validate(l) for l in all_loans],
        has_active_loan=active is not None,
        novi_plus=novi_read,
        novi_plus_eligibility=_novi_eligibility(session, current_user),
        aloba_eligibility=_aloba_eligibility(session, current_user, wallet),
        pending_guarantee_count=len(pending_guarantees),
        terms_accepted=loan_profile.terms_accepted_at is not None,
    )


@router.post("/novi-plus/activate", response_model=NoviPlusProfileRead)
def activate_novi_plus(
    data: NoviPlusActivateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if data.contract_type == "CDD":
        if not data.contract_end_date:
            raise HTTPException(status_code=400, detail="Date de fin de contrat requise pour un CDD")
        remaining = _months_remaining(data.contract_end_date)
        if remaining < CDD_MIN_MONTHS:
            raise HTTPException(
                status_code=400,
                detail="Votre contrat actuel arrive à échéance dans moins de 3 mois. NOVI+ nécessite une domiciliation active avec une durée minimale restante de 3 mois.",
            )

    existing = session.exec(
        select(NoviPlusProfile).where(NoviPlusProfile.user_id == current_user.id)
    ).first()

    status = "PENDING_BANK" if data.bank_consent else "DRAFT"
    submitted_at = datetime.utcnow() if data.bank_consent else None

    if existing:
        for field, value in data.model_dump(exclude={"bank_consent"}).items():
            setattr(existing, field, value)
        existing.bank_consent = data.bank_consent
        existing.status = status
        existing.submitted_at = submitted_at
        existing.rejection_reason = None
        profile = existing
    else:
        profile = NoviPlusProfile(
            user_id=current_user.id,
            **data.model_dump(exclude={"bank_consent"}),
            bank_consent=data.bank_consent,
            status=status,
            submitted_at=submitted_at,
        )
        session.add(profile)

    session.commit()
    session.refresh(profile)

    if data.bank_consent:
        profile = _maybe_complete_bank_validation(session, profile)
        notification = Notification(
            user_id=current_user.id,
            type="NOVI_PLUS_STATUS",
            message="✅ Votre compte NOVI+ est activé." if profile.status == "ACTIVE"
            else "Nous vérifions actuellement vos informations avec votre banque partenaire.",
        )
        session.add(notification)
        session.commit()

    return profile


@router.get("/simulate", response_model=LoanSimulationRead)
def simulate_loan(
    amount: float,
    weeks: int = MAX_LOAN_WEEKS,
    current_user: User = Depends(get_current_user),
):
    if weeks < 1 or weeks > MAX_LOAN_WEEKS:
        raise HTTPException(status_code=400, detail=f"Durée entre 1 et {MAX_LOAN_WEEKS} semaines")
    return _simulate_repayment(amount, weeks)


@router.post("/terms/accept")
def accept_loan_terms(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    profile = _get_or_create_loan_profile(session, current_user)
    profile.terms_accepted_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    return {"message": "Conditions acceptées"}


@router.post("/request", response_model=LoanRead)
def request_loan(
    data: LoanRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not data.terms_accepted:
        raise HTTPException(status_code=400, detail="Vous devez accepter les conditions d'utilisation")

    loan_profile = _get_or_create_loan_profile(session, current_user)
    if not loan_profile.terms_accepted_at:
        loan_profile.terms_accepted_at = datetime.utcnow()
        session.add(loan_profile)

    wallet = current_user.wallet
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet not found")

    if _active_loan(session, current_user.id):
        raise HTTPException(
            status_code=400,
            detail="Vous avez déjà un prêt actif en cours. Le remboursement complet est nécessaire avant toute nouvelle demande.",
        )

    simulation = _simulate_repayment(data.amount, MAX_LOAN_WEEKS)
    due_date = simulation.due_date
    total_to_repay = simulation.total_to_repay

    if data.loan_type == "NOVI+":
        elig = _novi_eligibility(session, current_user)
        if not elig.can_request:
            raise HTTPException(status_code=400, detail=elig.reason)
        if data.amount > elig.max_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Montant maximum éligible : {elig.max_amount:.0f} FCFA",
            )
        if not current_user.is_kyc_verified:
            raise HTTPException(status_code=403, detail="Vérification d'identité requise pour NOVI+")
        guarantors_required = 0
    elif data.loan_type == "ALOBA":
        elig = _aloba_eligibility(session, current_user, wallet)
        if not elig.can_request:
            raise HTTPException(status_code=400, detail=elig.reason)
        if data.amount > elig.max_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Montant maximum éligible : {elig.max_amount:.0f} FCFA",
            )
        if not data.guarantors:
            raise HTTPException(status_code=400, detail="Au moins une caution est requise pour ALOBA")
        guarantors_required = len(data.guarantors)
        amount_to_cover = max(0.0, data.amount - wallet.balance_available)
        if amount_to_cover > 0 and len(data.guarantors) == 0:
            raise HTTPException(status_code=400, detail="Des cautions sont nécessaires pour couvrir le montant")
    else:
        raise HTTPException(status_code=400, detail="Type de prêt invalide")

    new_loan = Loan(
        borrower_id=current_user.id,
        loan_type=data.loan_type,
        amount=data.amount,
        interest_rate=WEEKLY_INTEREST_RATE,
        total_amount=total_to_repay,
        status="PENDING",
        due_date=due_date,
    )
    session.add(new_loan)
    session.commit()
    session.refresh(new_loan)

    if data.loan_type == "NOVI+":
        wallet.balance_available += data.amount
        new_loan.status = "ACTIVE"
        transaction = Transaction(
            type="LOAN_DISBURSEMENT",
            amount=data.amount,
            status="SUCCESS",
            reference=f"LOAN-DISB-{uuid.uuid4()}",
            receiver_wallet_id=wallet.id,
        )
        session.add(wallet)
        session.add(new_loan)
        session.add(transaction)
        session.add(Notification(
            user_id=current_user.id,
            type="LOAN_DISBURSED",
            message=f"Votre prêt NOVI+ de {data.amount:.0f} FCFA a été versé sur votre wallet.",
        ))
        session.commit()
        session.refresh(new_loan)
        return new_loan

    amount_to_cover = max(0.0, data.amount - wallet.balance_available)
    amount_per_guarantor = amount_to_cover / len(data.guarantors) if data.guarantors else 0

    for phone in data.guarantors:
        guarantor = session.exec(select(User).where(User.phone == phone)).first()
        if not guarantor:
            raise HTTPException(
                status_code=404,
                detail=f"Caution introuvable ({phone}). Message : « Vous avez été désigné comme caution sur ALOBA. Téléchargez l'application pour confirmer votre participation. »",
            )
        if guarantor.id == current_user.id:
            raise HTTPException(status_code=400, detail="Vous ne pouvez pas être votre propre caution")
        if guarantor.wallet.balance_available < amount_per_guarantor:
            raise HTTPException(
                status_code=400,
                detail=f"La caution {phone} n'a pas les fonds suffisants ({amount_per_guarantor:.0f} FCFA requis)",
            )

        guarantee = LoanGuarantee(
            loan_id=new_loan.id,
            guarantor_id=guarantor.id,
            amount_locked=round(amount_per_guarantor, 2),
            status="PENDING",
        )
        session.add(guarantee)
        session.add(Notification(
            user_id=guarantor.id,
            type="LOAN_GUARANTEE_REQUEST",
            message=f"{current_user.phone} vous a désigné comme caution ALOBA pour {data.amount:.0f} FCFA. Montant à garantir : {amount_per_guarantor:.0f} FCFA.",
        ))

    session.commit()
    session.refresh(new_loan)
    return new_loan


@router.get("/guarantees/pending", response_model=List[PendingGuaranteeRead])
def get_pending_guarantees(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    guarantees = session.exec(
        select(LoanGuarantee).where(
            LoanGuarantee.guarantor_id == current_user.id,
            LoanGuarantee.status == "PENDING",
        )
    ).all()
    result = []
    for g in guarantees:
        loan = session.get(Loan, g.loan_id)
        borrower = session.get(User, loan.borrower_id) if loan else None
        result.append(PendingGuaranteeRead(
            guarantee_id=g.id,
            loan_id=g.loan_id,
            borrower_phone=borrower.phone if borrower else "",
            loan_amount=loan.amount if loan else 0,
            amount_to_guarantee=g.amount_locked,
            status=g.status,
            created_at=loan.created_at if loan else datetime.utcnow(),
        ))
    return result


@router.post("/{loan_id}/guarantee/respond")
def respond_to_guarantee(
    loan_id: int,
    data: GuaranteeResponse,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    guarantee = session.exec(
        select(LoanGuarantee).where(
            LoanGuarantee.loan_id == loan_id,
            LoanGuarantee.guarantor_id == current_user.id,
        )
    ).first()

    if not guarantee:
        raise HTTPException(status_code=404, detail="Demande de caution introuvable")
    if guarantee.status != "PENDING":
        raise HTTPException(status_code=400, detail="Vous avez déjà répondu à cette demande")

    loan = session.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Prêt introuvable")

    if not data.accept:
        guarantee.status = "REFUSED"
        session.add(guarantee)
        remaining = session.exec(
            select(LoanGuarantee).where(
                LoanGuarantee.loan_id == loan_id,
                LoanGuarantee.status == "PENDING",
                LoanGuarantee.id != guarantee.id,
            )
        ).all()
        if remaining:
            amount_to_cover = max(0.0, loan.amount - loan.borrower.wallet.balance_available)
            accepted_count = len(session.exec(
                select(LoanGuarantee).where(
                    LoanGuarantee.loan_id == loan_id,
                    LoanGuarantee.status == "ACCEPTED",
                )
            ).all())
            pending_count = len(remaining)
            if pending_count > 0 and amount_to_cover > 0:
                new_amount = amount_to_cover / pending_count
                for g in remaining:
                    g.amount_locked = round(new_amount, 2)
                    session.add(g)
        else:
            loan.status = "REJECTED"
            session.add(loan)
        session.add(Notification(
            user_id=loan.borrower_id,
            type="LOAN_GUARANTEE_REFUSED",
            message="Une caution a refusé votre demande ALOBA.",
        ))
        session.commit()
        return {"message": "Caution refusée"}

    wallet = current_user.wallet
    if wallet.balance_available < guarantee.amount_locked:
        guarantee.status = "REFUSED"
        session.add(guarantee)
        session.commit()
        raise HTTPException(status_code=400, detail="Fonds insuffisants — caution retirée du processus")

    wallet.balance_available -= guarantee.amount_locked
    wallet.balance_locked += guarantee.amount_locked
    guarantee.status = "ACCEPTED"
    session.add(wallet)
    session.add(guarantee)

    all_guarantees = session.exec(
        select(LoanGuarantee).where(LoanGuarantee.loan_id == loan_id)
    ).all()

    if all(g.status == "ACCEPTED" for g in all_guarantees):
        borrower_wallet = loan.borrower.wallet
        borrower_wallet.balance_available += loan.amount
        loan.status = "ACTIVE"
        session.add(borrower_wallet)
        session.add(loan)
        session.add(Transaction(
            type="LOAN_DISBURSEMENT",
            amount=loan.amount,
            status="SUCCESS",
            reference=f"LOAN-DISB-{uuid.uuid4()}",
            receiver_wallet_id=borrower_wallet.id,
        ))
        session.add(Notification(
            user_id=loan.borrower_id,
            type="LOAN_DISBURSED",
            message=f"Votre prêt ALOBA de {loan.amount:.0f} FCFA a été versé sur votre wallet.",
        ))

    session.commit()
    return {"message": "Caution acceptée"}


@router.get("/", response_model=List[LoanRead])
def get_loans(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    loans = session.exec(
        select(Loan).where(Loan.borrower_id == current_user.id).order_by(Loan.created_at.desc())
    ).all()
    return loans


@router.get("/history", response_model=List[LoanRead])
def get_loan_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    loans = session.exec(
        select(Loan).where(Loan.borrower_id == current_user.id).order_by(Loan.created_at.desc())
    ).all()
    return loans


def _weeks_elapsed(created_at: datetime) -> int:
    days = (datetime.utcnow() - created_at).days
    return min(MAX_LOAN_WEEKS, max(1, (days // 7) + (1 if days % 7 else 0)))


@router.post("/{loan_id}/repay")
def repay_loan(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    loan = session.exec(
        select(Loan).where(Loan.id == loan_id, Loan.borrower_id == current_user.id)
    ).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Prêt introuvable")
    if loan.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Ce prêt n'est pas actif")

    weeks = _weeks_elapsed(loan.created_at)
    total_due = round(loan.amount * (1 + WEEKLY_INTEREST_RATE * weeks), 2)

    wallet = current_user.wallet
    if wallet.balance_available < total_due:
        raise HTTPException(
            status_code=400,
            detail=f"Solde insuffisant. Montant dû : {total_due:.0f} FCFA (intérêts recalculés sur {weeks} semaine(s))",
        )

    wallet.balance_available -= total_due
    loan.status = "REPAID"
    loan.total_amount = total_due

    guarantees = session.exec(
        select(LoanGuarantee).where(LoanGuarantee.loan_id == loan_id)
    ).all()
    interest_share = total_due - loan.amount
    if guarantees and interest_share > 0:
        total_locked = sum(g.amount_locked for g in guarantees)
        for g in guarantees:
            guarantor_wallet = g.guarantor.wallet
            share = (g.amount_locked / total_locked) * (interest_share * 0.4) if total_locked else 0
            guarantor_wallet.balance_locked -= g.amount_locked
            guarantor_wallet.balance_available += g.amount_locked + share
            g.status = "RELEASED"
            session.add(guarantor_wallet)
            session.add(g)
    else:
        for g in guarantees:
            guarantor_wallet = g.guarantor.wallet
            guarantor_wallet.balance_locked -= g.amount_locked
            guarantor_wallet.balance_available += g.amount_locked
            g.status = "RELEASED"
            session.add(guarantor_wallet)
            session.add(g)

    loan_profile = _get_or_create_loan_profile(session, current_user)
    if loan.due_date < datetime.utcnow():
        loan_profile.delay_count += 1
        if loan_profile.delay_count >= 2:
            loan_profile.suspended_until = datetime.utcnow() + timedelta(days=90)
            loan_profile.aloba_multiplier = ALOBA_REDUCED_MULTIPLIER
        elif loan_profile.delay_count == 1:
            loan_profile.aloba_multiplier = ALOBA_REDUCED_MULTIPLIER
    elif loan_profile.delay_count > 0 and loan_profile.aloba_multiplier < ALOBA_DEFAULT_MULTIPLIER:
        loan_profile.aloba_multiplier = ALOBA_DEFAULT_MULTIPLIER
        loan_profile.delay_count = max(0, loan_profile.delay_count - 1)

    session.add(loan_profile)
    session.add(wallet)
    session.add(loan)
    session.add(Transaction(
        type="LOAN_REPAYMENT",
        amount=total_due,
        status="SUCCESS",
        reference=f"LOAN-REPAY-{uuid.uuid4()}",
        sender_wallet_id=wallet.id,
    ))
    session.commit()
    return {
        "message": "Prêt remboursé avec succès",
        "amount_paid": total_due,
        "weeks_charged": weeks,
    }
