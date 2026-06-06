from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.models import User, Wallet, Transaction, Notification
from app.schemas.schemas import WalletRead, TransactionRead, TransferRequest
from app.core.currency import convert_amount, get_exchange_rate
import uuid

router = APIRouter()

@router.get("/me", response_model=WalletRead)
def get_wallet(current_user: User = Depends(get_current_user)):
    return current_user.wallet

@router.get("/transactions", response_model=List[TransactionRead])
def get_transactions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    wallet_id = current_user.wallet.id
    transactions = session.exec(
        select(Transaction).where(
            (Transaction.sender_wallet_id == wallet_id) | 
            (Transaction.receiver_wallet_id == wallet_id)
        )
    ).all()
    return transactions

@router.post("/transfer", response_model=TransactionRead)
def transfer(
    data: TransferRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    sender_wallet = current_user.wallet
    if sender_wallet.balance_available < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    receiver = session.exec(select(User).where(User.phone == data.receiver_phone)).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    receiver_wallet = receiver.wallet
    
    # Deduct from sender
    sender_wallet.balance_available -= data.amount
    
    # Check if conversion is needed
    receiver_amount = data.amount
    rate = 1.0
    if sender_wallet.currency != receiver_wallet.currency:
        receiver_amount = convert_amount(session, data.amount, sender_wallet.currency, receiver_wallet.currency)
        rate = get_exchange_rate(session, sender_wallet.currency, receiver_wallet.currency)
        
    # Add to receiver
    receiver_wallet.balance_available += receiver_amount
    
    # Create transaction record
    transaction = Transaction(
        type="TRANSFER",
        amount=data.amount,
        currency=sender_wallet.currency,
        exchange_rate=rate,
        status="SUCCESS",
        reference=str(uuid.uuid4()),
        sender_wallet_id=sender_wallet.id,
        receiver_wallet_id=receiver_wallet.id
    )
    
    session.add(sender_wallet)
    session.add(receiver_wallet)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return transaction

@router.post("/transfer-external")
def transfer_external(
    data: TransferRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    sender_wallet = current_user.wallet
    # Add fees for external transfer
    fee = data.amount * 0.02  # 2% fee
    total_deduct = data.amount + fee
    if sender_wallet.balance_available < total_deduct:
        raise HTTPException(status_code=400, detail="Insufficient funds (including fees)")
    
    # Deduct from sender
    sender_wallet.balance_available -= total_deduct
    
    # Create transaction
    transaction = Transaction(
        type="EXTERNAL_TRANSFER",
        amount=data.amount,
        status="SUCCESS",  # Assume success for now
        reference=str(uuid.uuid4()),
        sender_wallet_id=sender_wallet.id
    )
    
    session.add(sender_wallet)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return transaction

@router.post("/generate-payment-link")
def generate_payment_link(
    amount: float,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Generate a payment link for external payments.
    Supports both query parameters and JSON body.
    
    Request body (JSON):
    {
        "amount": 1000.0
    }
    
    Query parameter:
    ?amount=1000.0
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    # Generate a unique link for PayGateGlobal Method 2
    link_id = str(uuid.uuid4())
    
    # Build PayGateGlobal payment page URL using Method 2
    import os
    api_key = os.getenv("PAYGATE_API_KEY")
    base_url = os.getenv("PAYGATE_BASE_URL", "https://paygateglobal.com")
    callback_url = os.getenv("PAYGATE_CALLBACK_URL", "https://novikash.com/payment-callback")
    
    # The payment link can be used to redirect customers to PayGateGlobal
    payment_page_url = f"{base_url}/v1/page?token={api_key}&amount={amount}&identifier={link_id}&url={callback_url}"
    
    return {
        "payment_link": payment_page_url,
        "identifier": link_id,
        "amount": amount
    }

@router.get("/check-user/{phone}")
def check_user_exists(
    phone: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.phone == phone)).first()
    return {"exists": user is not None}
