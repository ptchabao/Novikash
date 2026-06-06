from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import os
import httpx
import logging
from urllib.parse import quote
from app.core.database import get_session
from app.api.auth import get_current_user, get_admin_user
from app.models.models import User, Wallet, Transaction, Notification
from app.schemas.schemas import PaymentRequest, TransactionRead, PayGateInitiateRequest, PayGateInitiateResponse, PayGatePageRequest, PayGatePageResponse, PayGateStatusRequest, PayGateStatusResponse, PayGateBalanceResponse, PayGateWebhookData

logger = logging.getLogger(__name__)

router = APIRouter()

PAYGATE_API_KEY = os.getenv("PAYGATE_API_KEY")
PAYGATE_BASE_URL = os.getenv("PAYGATE_BASE_URL", "https://paygateglobal.com")
PAYGATE_CALLBACK_URL = os.getenv("PAYGATE_CALLBACK_URL", "https://novikash.com/payment-callback")

if not PAYGATE_API_KEY:
    logger.warning("PAYGATE_API_KEY is not configured. PayGateGlobal endpoints will fail until it is set.")

async def initiate_paygate_payment(phone_number: str, amount: float, description: str, identifier: str, network: str) -> Dict[str, Any]:
    """Initiate a payment using PayGateGlobal API Method 1"""
    if not PAYGATE_API_KEY:
        raise HTTPException(status_code=500, detail="PAYGATE_API_KEY is not configured")

    url = f"{PAYGATE_BASE_URL}/api/v1/pay"
    payload = {
        "auth_token": PAYGATE_API_KEY,
        "phone_number": phone_number,
        "amount": amount,
        "description": description,
        "identifier": identifier,
        "network": network
    }
    
    logger.info(f"Initiating PayGateGlobal payment: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            logger.info(f"PayGateGlobal response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"PayGateGlobal HTTP error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"PayGateGlobal API error: {response.text}")
            
            data = response.json()
            logger.info(f"PayGateGlobal response data: {data}")
            return data
            
    except httpx.RequestError as e:
        logger.error(f"PayGateGlobal request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment service connection error: {str(e)}")
    except Exception as e:
        logger.error(f"PayGateGlobal unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")

async def check_payment_status(tx_reference: Optional[str] = None, identifier: Optional[str] = None) -> Dict[str, Any]:
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
    
    logger.info(f"Checking PayGateGlobal payment status: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            logger.info(f"PayGateGlobal status response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"PayGateGlobal HTTP error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"PayGateGlobal API error")
            
            data = response.json()
            logger.info(f"PayGateGlobal status data: {data}")
            return data
            
    except httpx.RequestError as e:
        logger.error(f"PayGateGlobal status request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")

async def check_paygate_balance() -> Dict[str, Any]:
    """Check PayGateGlobal account balance"""
    if not PAYGATE_API_KEY:
        raise HTTPException(status_code=500, detail="PAYGATE_API_KEY is not configured")

    url = f"{PAYGATE_BASE_URL}/api/v1/check-balance"
    payload = {
        "auth_token": PAYGATE_API_KEY
    }
    
    logger.info("Checking PayGateGlobal balance")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            logger.info(f"PayGateGlobal balance response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"PayGateGlobal HTTP error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"PayGateGlobal API error")
            
            data = response.json()
            logger.info(f"PayGateGlobal balance data: {data}")
            return data
            
    except httpx.RequestError as e:
        logger.error(f"PayGateGlobal balance request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")

@router.post("/deposit")
async def deposit(data: PaymentRequest, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Initiate a deposit using PayGateGlobal. Requires network (FLOOZ or TMONEY)"""
    try:
        # Validate network first (required)
        if not data.network:
            raise HTTPException(status_code=400, detail="Network is required. Must be 'FLOOZ' or 'TMONEY'")
        
        network_upper = data.network.upper().strip()
        if network_upper not in ["FLOOZ", "TMONEY"]:
            raise HTTPException(status_code=400, detail=f"Invalid network: {data.network}. Must be FLOOZ or TMONEY")
        
        # Get phone number from either field
        phone_number = (data.phone or data.phone_number or "").strip()
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required. Provide 'phone' or 'phone_number'")
        
        # Generate unique identifier for this transaction
        identifier = str(uuid.uuid4())
        
        # Initiate payment with PayGateGlobal
        paygate_response = await initiate_paygate_payment(
            phone_number=phone_number,
            amount=data.amount,
            description=f"Deposit to NoviKash wallet",
            identifier=identifier,
            network=network_upper
        )
        
        # Check response status code
        response_status = paygate_response.get("status")
        if response_status is None:
            logger.error(f"Missing status in PayGateGlobal response: {paygate_response}")
            raise HTTPException(status_code=500, detail="Invalid response from payment service")
        
        if response_status != 0:
            # Handle PayGateGlobal errors
            error_messages = {
                2: "Invalid authentication token",
                4: "Invalid parameters",
                6: "Duplicate transaction identifier"
            }
            error_msg = error_messages.get(response_status, f"Payment service error (code: {response_status})")
            logger.warning(f"PayGateGlobal returned error status {response_status}: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Payment initiation failed: {error_msg}")
        
        # Get tx_reference from response
        tx_reference = paygate_response.get("tx_reference")
        if not tx_reference:
            logger.error(f"Missing tx_reference in PayGateGlobal response: {paygate_response}")
            raise HTTPException(status_code=500, detail="Invalid response from payment service")
        
        # Create transaction record
        transaction = Transaction(
            type="DEPOSIT",
            amount=data.amount,
            status="PENDING",
            reference=tx_reference,
            receiver_wallet_id=current_user.wallet.id
        )
        session.add(transaction)
        session.commit()
        
        logger.info(f"Deposit transaction created: tx_ref={tx_reference}, identifier={identifier}, network={network_upper}, user_id={current_user.id}")
        
        return {
            "message": "Deposit initiated successfully. USSD prompt will appear on your phone.",
            "tx_reference": tx_reference,
            "identifier": identifier,
            "network": network_upper,
            "status": "pending",
            "action": "show_ussd_prompt"  # Frontend should display USSD code or wait for device prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Deposit error: {str(e)}")
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

@router.post("/status", response_model=PayGateStatusResponse)
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

@router.post("/page-link", response_model=PayGatePageResponse)
async def generate_paygate_page_link(
    data: PayGatePageRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a PayGateGlobal redirect page URL (Method 2)."""
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    identifier = data.identifier or f"{current_user.id}-{uuid.uuid4()}"
    query = [
        ("token", PAYGATE_API_KEY),
        ("amount", str(data.amount)),
        ("identifier", identifier)
    ]

    if data.description:
        query.append(("description", data.description))
    if data.url:
        query.append(("url", data.url))
    else:
        query.append(("url", PAYGATE_CALLBACK_URL))
    if data.phone:
        query.append(("phone", data.phone))
    if data.network:
        query.append(("network", data.network))

    payment_page_url = f"{PAYGATE_BASE_URL}/v1/page?" + "&".join(
        f"{key}={quote(value)}" for key, value in query if value is not None
    )

    return {
        "payment_link": payment_page_url,
        "identifier": identifier,
        "amount": data.amount,
        "description": data.description,
        "phone": data.phone,
        "network": data.network
    }

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
