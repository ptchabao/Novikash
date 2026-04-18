from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional
import uuid
from app.core.database import get_session
from app.api.auth import get_current_user, get_admin_user
from app.models.models import User, Wallet, Transaction, Notification
from app.schemas.schemas import PaymentRequest, TransactionRead

router = APIRouter()

@router.post("/deposit")
def deposit(data: PaymentRequest, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Simulate redirection to payment gateway or USSD prompt
    # In a real app, we'd call MTN/Moov API here.
    
    # We create a PENDING transaction
    ref = str(uuid.uuid4())
    transaction = Transaction(
        type="DEPOSIT",
        amount=data.amount,
        status="PENDING",
        reference=ref,
        receiver_wallet_id=current_user.wallet.id
    )
    session.add(transaction)
    session.commit()
    
    return {
        "message": "Deposit initiated. Please confirm on your phone.",
        "reference": ref,
        "operator_url_mock": f"https://mock-momo.com/pay/{ref}"
    }

def process_transaction_async(ref: str, status: str, sqlite_db_path: str):
    """
    Background logic to update financial status.
    """
    from sqlmodel import create_engine
    engine = create_engine(sqlite_db_path)
    with Session(engine) as session:
        transaction = session.exec(select(Transaction).where(Transaction.reference == ref)).first()
        if not transaction or transaction.status != "PENDING":
            return
        
        if status == "SUCCESS":
            transaction.status = "SUCCESS"
            transaction.processed_at = datetime.utcnow()
            wallet = session.exec(select(Wallet).where(Wallet.id == transaction.receiver_wallet_id)).first()
            wallet.balance_available += transaction.amount
            session.add(wallet)
        else:
            transaction.status = "FAILED"
            transaction.processed_at = datetime.utcnow()
            
        session.add(transaction)
        session.commit()

@router.post("/webhook")
async def momo_webhook(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Mock webhook for Mobile Money operators (MTN/Moov).
    """
    data = await request.json()
    ref = data.get("reference")
    status = data.get("status") # SUCCESS or FAILED
    
    # We return immediately to the operator
    from app.core.database import DATABASE_URL
    background_tasks.add_task(process_transaction_async, ref, status, DATABASE_URL)
    
    return {"status": "accepted_for_processing"}

@router.post("/withdraw")
def withdraw(data: PaymentRequest, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    wallet = current_user.wallet
    if wallet.balance_available < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Atomic withdrawal
    wallet.balance_available -= data.amount
    
    transaction = Transaction(
        type="WITHDRAW",
        amount=data.amount,
        status="SUCCESS", # Usually pending, but we mock success for now
        reference=str(uuid.uuid4()),
        sender_wallet_id=wallet.id
    )
    
    session.add(wallet)
    session.add(transaction)
    session.commit()
    
    return {"message": "Withdrawal successful", "amount": data.amount}
