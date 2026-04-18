from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta
import os
import uuid

from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.models import User, Wallet, Loan, LoanGuarantee, Transaction, Notification, SystemConfig
from app.schemas.schemas import LoanRequest, LoanRead, GuaranteeResponse

router = APIRouter()

INTEREST_RATE = float(os.getenv("LOAN_INTEREST_RATE", "0.1"))
REPAYMENT_DAYS = int(os.getenv("DEFAULT_REPAYMENT_DAYS", "7"))

@router.post("/request", response_model=LoanRead)
def request_loan(
    data: LoanRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not current_user.is_kyc_verified:
        raise HTTPException(status_code=403, detail="KYC verification required to request a loan")
        
    # Fetch interest rate from DB or use default
    rate_config = session.exec(select(SystemConfig).where(SystemConfig.key == "loan_interest_rate")).first()
    interest_rate = float(rate_config.value) if rate_config else INTEREST_RATE
    
    if len(data.guarantors) < 1:
        raise HTTPException(status_code=400, detail="At least one guarantor is required")
    
    total_to_repay = data.amount * (1 + interest_rate)
    amount_per_guarantor = total_to_repay / len(data.guarantors)
    
    # 1. Create Loan in PENDING status
    new_loan = Loan(
        borrower_id=current_user.id,
        amount=data.amount,
        interest_rate=interest_rate,
        total_amount=total_to_repay,
        status="PENDING",
        due_date=datetime.utcnow() + timedelta(days=REPAYMENT_DAYS)
    )
    session.add(new_loan)
    session.commit()
    session.refresh(new_loan)
    
    # 2. Create LoanGuarantees and Notify
    for phone in data.guarantors:
        guarantor = session.exec(select(User).where(User.phone == phone)).first()
        if not guarantor:
            # In a real app, we might send an SMS invite. For now, we error.
            raise HTTPException(status_code=404, detail=f"Guarantor with phone {phone} not found")
        
        if guarantor.id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot be your own guarantor")
            
        guarantee = LoanGuarantee(
            loan_id=new_loan.id,
            guarantor_id=guarantor.id,
            amount_locked=amount_per_guarantor,
            status="PENDING"
        )
        session.add(guarantee)
        
        # Notify guarantor
        notification = Notification(
            user_id=guarantor.id,
            type="LOAN_GUARANTEE_REQUEST",
            message=f"{current_user.phone} requested you as a guarantor for a loan of {data.amount} XOF. Amount to guarantee: {amount_per_guarantor} XOF."
        )
        session.add(notification)
        
    session.commit()
    session.refresh(new_loan)
    return new_loan

@router.post("/{loan_id}/guarantee/respond")
def respond_to_guarantee(
    loan_id: int,
    data: GuaranteeResponse,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    guarantee = session.exec(
        select(LoanGuarantee).where(
            LoanGuarantee.loan_id == loan_id,
            LoanGuarantee.guarantor_id == current_user.id
        )
    ).first()
    
    if not guarantee:
        raise HTTPException(status_code=404, detail="Guarantee request not found")
    
    if guarantee.status != "PENDING":
        raise HTTPException(status_code=400, detail="You have already responded to this request")
    
    if not data.accept:
        guarantee.status = "REFUSED"
        loan = session.exec(select(Loan).where(Loan.id == loan_id)).first()
        loan.status = "REJECTED" # If one refuses, current logic rejects the loan
        session.add(guarantee)
        session.add(loan)
        session.commit()
        return {"message": "Guarantee refused, loan application rejected"}

    # ACCEPTED logic
    wallet = current_user.wallet
    if wallet.balance_available < guarantee.amount_locked:
        raise HTTPException(status_code=400, detail="Insufficient funds to serve as guarantor")
    
    # Lock funds
    wallet.balance_available -= guarantee.amount_locked
    wallet.balance_locked += guarantee.amount_locked
    guarantee.status = "ACCEPTED"
    
    session.add(wallet)
    session.add(guarantee)
    session.commit()
    
    # Check if all guarantors have accepted
    loan = session.exec(select(Loan).where(Loan.id == loan_id)).first()
    all_guarantees = session.exec(select(LoanGuarantee).where(LoanGuarantee.loan_id == loan_id)).all()
    
    if all(g.status == "ACCEPTED" for g in all_guarantees):
        # DISBURSE LOAN
        borrower = loan.borrower
        borrower_wallet = borrower.wallet
        borrower_wallet.balance_available += loan.amount
        loan.status = "ACTIVE"
        
        # Record transaction
        transaction = Transaction(
            type="LOAN_DISBURSEMENT",
            amount=loan.amount,
            status="SUCCESS",
            reference=f"LOAN-DISB-{uuid.uuid4()}",
            receiver_wallet_id=borrower_wallet.id
        )
        
        session.add(borrower_wallet)
        session.add(loan)
        session.add(transaction)
        
        # Notification
        notification = Notification(
            user_id=borrower.id,
            type="LOAN_DISBURSED",
            message=f"Your loan of {loan.amount} XOF has been disbursed! Repayment due: {loan.due_date}."
        )
        session.add(notification)
        
        session.commit()
        return {"message": "Guarantee accepted and loan disbursed!"}
    
    return {"message": "Guarantee accepted, waiting for other guarantors."}

@router.get("/", response_model=List[LoanRead])
def get_loans(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    loans = session.exec(select(Loan).where(Loan.borrower_id == current_user.id)).all()
    return loans

@router.post("/{loan_id}/repay")
def repay_loan(
    loan_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    loan = session.exec(select(Loan).where(Loan.id == loan_id, Loan.borrower_id == current_user.id)).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    if loan.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Loan is not active")
    
    wallet = current_user.wallet
    if wallet.balance_available < loan.total_amount:
        raise HTTPException(status_code=400, detail="Insufficient funds to repay loan")
    
    # Atomic Repayment
    wallet.balance_available -= loan.total_amount
    loan.status = "REPAID"
    
    # Unlock guarantors' funds
    guarantees = session.exec(select(LoanGuarantee).where(LoanGuarantee.loan_id == loan_id)).all()
    for g in guarantees:
        guarantor_wallet = g.guarantor.wallet
        guarantor_wallet.balance_locked -= g.amount_locked
        guarantor_wallet.balance_available += g.amount_locked
        g.status = "RELEASED"
        session.add(guarantor_wallet)
        session.add(g)
        
    transaction = Transaction(
        type="LOAN_REPAYMENT",
        amount=loan.total_amount,
        status="SUCCESS",
        reference=f"LOAN-REPAY-{uuid.uuid4()}",
        sender_wallet_id=wallet.id
    )
    
    session.add(wallet)
    session.add(loan)
    session.add(transaction)
    session.commit()
    
    return {"message": "Loan repaid and guarantors released successfully"}
