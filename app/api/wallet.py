from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any
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
    data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Generate a payment link for external payments.
    
    Request body (JSON):
    {
        "amount": 1000.0,
        "network": "FLOOZ",  # Optional: FLOOZ or TMONEY
        "description": "Payment for service",  # Optional
        "phone": "+228XXXXXXXX"  # Optional
    }
    """
    from app.schemas.schemas import PayGatePageRequest
    from urllib.parse import urlencode
    import os
    
    try:
        # Validate input data
        amount = data.get("amount")
        if not amount or float(amount) <= 0:
            raise HTTPException(status_code=400, detail="Valid amount is required")
        
        network = data.get("network", "")
        if network and network.upper() not in ["FLOOZ", "TMONEY"]:
            raise HTTPException(status_code=400, detail="Network must be FLOOZ or TMONEY")
        
        description = data.get("description", f"Payment for NoviKash")
        phone = data.get("phone", "")
        
        # Generate a unique link for PayGateGlobal Method 2
        identifier = str(uuid.uuid4())
        
        # Build PayGateGlobal payment page URL using Method 2
        api_key = os.getenv("PAYGATE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="PayGate API not configured")
        
        base_url = os.getenv("PAYGATE_BASE_URL", "https://paygateglobal.com")
        callback_url = os.getenv("PAYGATE_CALLBACK_URL", "https://novikash.com/payment-callback")
        
        # Build query parameters
        params = {
            "token": api_key,
            "amount": float(amount),
            "identifier": identifier,
            "url": callback_url,
            "description": description
        }
        
        # Add optional parameters
        if network:
            params["network"] = network.upper()
        if phone:
            params["phone"] = phone
        
        # Build the payment URL
        query_string = urlencode(params)
        payment_page_url = f"{base_url}/v1/page?{query_string}"
        
        # Create transaction record
        transaction = Transaction(
            type="DEPOSIT",
            amount=float(amount),
            status="PENDING",
            reference=identifier,
            receiver_wallet_id=current_user.wallet.id
        )
        session.add(transaction)
        session.commit()
        
        return {
            "payment_link": payment_page_url,
            "identifier": identifier,
            "amount": float(amount),
            "network": network.upper() if network else None,
            "description": description,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

@router.get("/check-user/{phone}")
def check_user_exists(
    phone: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.phone == phone)).first()
    return {"exists": user is not None}
