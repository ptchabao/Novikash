from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional
import uuid
import os
import httpx
from app.core.database import get_session
from app.api.auth import get_current_user, get_admin_user
from app.models.models import User, Wallet, Transaction, Notification
from app.schemas.schemas import PaymentRequest, TransactionRead, PayGateInitiateRequest, PayGateInitiateResponse, PayGateStatusRequest, PayGateStatusResponse, PayGateBalanceResponse, PayGateWebhookData

router = APIRouter()

PAYGATE_API_KEY = os.getenv("PAYGATE_API_KEY")
PAYGATE_BASE_URL = os.getenv("PAYGATE_BASE_URL", "https://paygateglobal.com")

async def initiate_paygate_payment(phone_number: str, amount: float, description: str, identifier: str, network: str) -> PayGateInitiateResponse:
    """Initiate a payment using PayGateGlobal API Method 1"""
    url = f"{PAYGATE_BASE_URL}/api/v1/pay"
    payload = {
        "auth_token": PAYGATE_API_KEY,
        "phone_number": phone_number,
        "amount": amount,
        "description": description,
        "identifier": identifier,
        "network": network
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return PayGateInitiateResponse(**data)

async def check_payment_status(tx_reference: Optional[str] = None, identifier: Optional[str] = None) -> PayGateStatusResponse:
    """Check payment status using PayGateGlobal API"""
    if tx_reference:
        url = f"{PAYGATE_BASE_URL}/api/v1/status"
        payload = {
            "auth_token": PAYGATE_API_KEY,
            "tx_reference": tx_reference
        }
    elif identifier:
        url = f"{PAYGATE_BASE_URL}/api/v2/status"
        payload = {
            "auth_token": PAYGATE_API_KEY,
            "identifier": identifier
        }
    else:
        raise ValueError("Either tx_reference or identifier must be provided")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return PayGateStatusResponse(**data)

async def check_paygate_balance() -> PayGateBalanceResponse:
    """Check PayGateGlobal account balance"""
    url = f"{PAYGATE_BASE_URL}/api/v1/check-balance"
    payload = {
        "auth_token": PAYGATE_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return PayGateBalanceResponse(**data)

router = APIRouter()

@router.post("/deposit")
async def deposit(data: PaymentRequest, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Initiate a deposit using PayGateGlobal"""
    try:
        # Get phone number from either field
        phone_number = data.phone or data.phone_number
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Generate unique identifier for this transaction
        identifier = str(uuid.uuid4())
        
        # Determine network based on phone number or use provided network
        network = data.network or "FLOOZ"  # Default to FLOOZ, could be enhanced with phone number validation
        
        # Initiate payment with PayGateGlobal
        paygate_response = await initiate_paygate_payment(
            phone_number=phone_number,
            amount=data.amount,
            description=f"Deposit to NoviKash wallet",
            identifier=identifier,
            network=network
        )
        
        if paygate_response.status != 0:
            # Handle PayGateGlobal errors
            error_messages = {
                2: "Invalid authentication token",
                4: "Invalid parameters",
                6: "Duplicate transaction identifier"
            }
            error_msg = error_messages.get(paygate_response.status, "Unknown error")
            raise HTTPException(status_code=400, detail=f"Payment initiation failed: {error_msg}")
        
        # Create transaction record
        transaction = Transaction(
            type="DEPOSIT",
            amount=data.amount,
            status="PENDING",
            reference=paygate_response.tx_reference,
            receiver_wallet_id=current_user.wallet.id
        )
        session.add(transaction)
        session.commit()
        
        return {
            "message": "Deposit initiated successfully. Please complete payment on your phone.",
            "tx_reference": paygate_response.tx_reference,
            "identifier": identifier,
            "status": "pending"
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhook")
async def paygate_webhook(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Webhook for PayGateGlobal payment confirmations.
    """
    try:
        data = await request.json()
        webhook_data = PayGateWebhookData(**data)
        
        # Process the webhook asynchronously
        from app.core.database import DATABASE_URL
        background_tasks.add_task(process_paygate_webhook_async, webhook_data, DATABASE_URL)
        
        return {"status": "accepted_for_processing"}
        
    except Exception as e:
        # Log the error but still return success to PayGateGlobal
        print(f"Webhook processing error: {str(e)}")
        return {"status": "error", "message": str(e)}

def process_paygate_webhook_async(webhook_data: PayGateWebhookData, sqlite_db_path: str):
    """
    Background logic to process PayGateGlobal webhook and update transaction status.
    """
    from sqlmodel import create_engine
    engine = create_engine(sqlite_db_path)
    with Session(engine) as session:
        # Find transaction by tx_reference
        transaction = session.exec(
            select(Transaction).where(Transaction.reference == webhook_data.tx_reference)
        ).first()
        
        if not transaction:
            print(f"Transaction not found for tx_reference: {webhook_data.tx_reference}")
            return
        
        if transaction.status != "PENDING":
            print(f"Transaction already processed: {transaction.status}")
            return
        
        # Update transaction status
        transaction.status = "SUCCESS"
        transaction.processed_at = datetime.utcnow()
        
        # Update wallet balance
        wallet = session.exec(select(Wallet).where(Wallet.id == transaction.receiver_wallet_id)).first()
        if wallet:
            wallet.balance_available += transaction.amount
            session.add(wallet)
        
        # Create notification
        notification = Notification(
            user_id=wallet.user_id if wallet else None,
            type="PAYMENT_SUCCESS",
            message=f"Payment of {transaction.amount} XOF received successfully"
        )
        session.add(notification)
        
        session.add(transaction)
        session.commit()

@router.post("/status")
async def check_payment_status_endpoint(
    request: PayGateStatusRequest, 
    current_user: User = Depends(get_current_user)
):
    """Check the status of a payment"""
    try:
        status_response = await check_payment_status(
            tx_reference=request.tx_reference,
            identifier=request.identifier
        )
        return status_response
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/balance")
async def get_paygate_balance(admin_user: User = Depends(get_admin_user)):
    """Get PayGateGlobal account balance (Admin only)"""
    try:
        balance_response = await check_paygate_balance()
        return balance_response
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

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
