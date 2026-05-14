from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta
from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.models import User, Tontine, TontineTransaction, Wallet
from app.schemas.schemas import (
    TontineRead, TontineCreate, TontineDepositRequest, TontineLockRequest, TontineTransactionRead
)
import uuid

router = APIRouter()

# Get or create user's tontine
def get_or_create_tontine(user: User, session: Session) -> Tontine:
    """Get user's tontine or create one if it doesn't exist"""
    tontine = session.exec(
        select(Tontine).where(Tontine.user_id == user.id)
    ).first()
    
    if not tontine:
        tontine = Tontine(
            user_id=user.id,
            balance=0.0,
            currency="XOF",
            is_locked=False,
            status="ACTIVE"
        )
        session.add(tontine)
        session.commit()
        session.refresh(tontine)
    
    return tontine

@router.get("/me", response_model=TontineRead)
def get_tontine(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user's tontine account"""
    tontine = get_or_create_tontine(current_user, session)
    
    # Check if lock period has expired
    if tontine.is_locked and tontine.lock_end_date:
        if datetime.utcnow() >= tontine.lock_end_date:
            tontine.is_locked = False
            tontine.status = "ACTIVE"
            tontine.updated_at = datetime.utcnow()
            session.add(tontine)
            session.commit()
            session.refresh(tontine)
    
    transactions = session.exec(
        select(TontineTransaction).where(TontineTransaction.tontine_id == tontine.id)
    ).all()
    
    return TontineRead(
        id=tontine.id,
        balance=tontine.balance,
        currency=tontine.currency,
        status=tontine.status,
        lock_duration_days=tontine.lock_duration_days,
        lock_start_date=tontine.lock_start_date,
        lock_end_date=tontine.lock_end_date,
        is_locked=tontine.is_locked,
        created_at=tontine.created_at,
        updated_at=tontine.updated_at,
        transactions=[
            TontineTransactionRead(
                id=t.id,
                type=t.type,
                amount=t.amount,
                currency=t.currency,
                status=t.status,
                reference=t.reference,
                description=t.description,
                created_at=t.created_at
            )
            for t in transactions
        ]
    )

@router.post("/deposit", response_model=TontineTransactionRead)
def deposit_to_tontine(
    data: TontineDepositRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Deposit funds from main wallet to tontine account"""
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get main wallet
    wallet = current_user.wallet
    if wallet.balance_available < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in main wallet")
    
    # Get or create tontine
    tontine = get_or_create_tontine(current_user, session)
    
    # Deduct from main wallet
    wallet.balance_available -= data.amount
    session.add(wallet)
    
    # Add to tontine
    tontine.balance += data.amount
    tontine.updated_at = datetime.utcnow()
    session.add(tontine)
    
    # Record transaction
    transaction = TontineTransaction(
        tontine_id=tontine.id,
        type="DEPOSIT",
        amount=data.amount,
        currency="XOF",
        status="SUCCESS",
        reference=f"TONT-DEP-{uuid.uuid4().hex[:12].upper()}",
        description="Deposit from main wallet"
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return TontineTransactionRead(
        id=transaction.id,
        type=transaction.type,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        reference=transaction.reference,
        description=transaction.description,
        created_at=transaction.created_at
    )

@router.post("/lock", response_model=TontineRead)
def lock_tontine(
    data: TontineLockRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Lock tontine account for specified duration"""
    # Validate lock duration
    if data.lock_duration_days not in [10, 20, 30, 90]:
        raise HTTPException(
            status_code=400, 
            detail="Lock duration must be 10, 20, 30, or 90 days"
        )
    
    tontine = get_or_create_tontine(current_user, session)
    
    if tontine.is_locked:
        raise HTTPException(
            status_code=400,
            detail="Tontine account is already locked"
        )
    
    if tontine.balance <= 0:
        raise HTTPException(
            status_code=400,
            detail="Tontine account must have balance to lock"
        )
    
    # Lock the account
    tontine.is_locked = True
    tontine.status = "LOCKED"
    tontine.lock_duration_days = data.lock_duration_days
    tontine.lock_start_date = datetime.utcnow()
    tontine.lock_end_date = datetime.utcnow() + timedelta(days=data.lock_duration_days)
    tontine.updated_at = datetime.utcnow()
    
    session.add(tontine)
    session.commit()
    session.refresh(tontine)
    
    transactions = session.exec(
        select(TontineTransaction).where(TontineTransaction.tontine_id == tontine.id)
    ).all()
    
    return TontineRead(
        id=tontine.id,
        balance=tontine.balance,
        currency=tontine.currency,
        status=tontine.status,
        lock_duration_days=tontine.lock_duration_days,
        lock_start_date=tontine.lock_start_date,
        lock_end_date=tontine.lock_end_date,
        is_locked=tontine.is_locked,
        created_at=tontine.created_at,
        updated_at=tontine.updated_at,
        transactions=[
            TontineTransactionRead(
                id=t.id,
                type=t.type,
                amount=t.amount,
                currency=t.currency,
                status=t.status,
                reference=t.reference,
                description=t.description,
                created_at=t.created_at
            )
            for t in transactions
        ]
    )

@router.get("/transactions", response_model=List[TontineTransactionRead])
def get_tontine_transactions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all tontine transactions for current user"""
    tontine = get_or_create_tontine(current_user, session)
    
    transactions = session.exec(
        select(TontineTransaction).where(TontineTransaction.tontine_id == tontine.id)
    ).all()
    
    return [
        TontineTransactionRead(
            id=t.id,
            type=t.type,
            amount=t.amount,
            currency=t.currency,
            status=t.status,
            reference=t.reference,
            description=t.description,
            created_at=t.created_at
        )
        for t in transactions
    ]

@router.post("/withdraw", response_model=TontineTransactionRead)
def withdraw_from_tontine(
    data: TontineDepositRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Withdraw funds from tontine account to main wallet (only when not locked)"""
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get or create tontine
    tontine = get_or_create_tontine(current_user, session)
    
    # Check if tontine is locked
    if tontine.is_locked:
        raise HTTPException(
            status_code=400, 
            detail="Cannot withdraw from locked tontine account"
        )
    
    if tontine.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in tontine account")
    
    # Get main wallet
    wallet = current_user.wallet
    
    # Deduct from tontine
    tontine.balance -= data.amount
    tontine.updated_at = datetime.utcnow()
    session.add(tontine)
    
    # Add to main wallet
    wallet.balance_available += data.amount
    session.add(wallet)
    
    # Record transaction
    transaction = TontineTransaction(
        tontine_id=tontine.id,
        type="WITHDRAWAL",
        amount=data.amount,
        currency="XOF",
        status="SUCCESS",
        reference=f"TONT-WIT-{uuid.uuid4().hex[:12].upper()}",
        description="Withdrawal to main wallet"
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return TontineTransactionRead(
        id=transaction.id,
        type=transaction.type,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        reference=transaction.reference,
        description=transaction.description,
        created_at=transaction.created_at
    )
