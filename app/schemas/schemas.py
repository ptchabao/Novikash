from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Auth Schemas ---

class UserCreate(BaseModel):
    phone: str
    password: str
    email: Optional[EmailStr] = None

class UserLogin(BaseModel):
    phone: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    phone: Optional[str] = None

class OTPVerify(BaseModel):
    phone: str
    code: str

class PINSetup(BaseModel):
    pin: str # 4 or 6 digits

class PINVerify(BaseModel):
    phone: str
    pin: str

# --- User & Wallet Schemas ---

class WalletRead(BaseModel):
    id: int
    balance_available: float
    balance_locked: float
    currency: str

class UserRead(BaseModel):
    id: int
    phone: str
    email: Optional[str] = None
    created_at: datetime
    wallet: Optional[WalletRead] = None

# --- Tontine Schemas ---

class TontineTransactionRead(BaseModel):
    id: int
    type: str
    amount: float
    currency: str
    status: str
    reference: str
    description: Optional[str] = None
    created_at: datetime

class TontineRead(BaseModel):
    id: int
    balance: float
    currency: str
    status: str
    lock_duration_days: int
    lock_start_date: Optional[datetime] = None
    lock_end_date: Optional[datetime] = None
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    transactions: List[TontineTransactionRead] = []

class TontineCreate(BaseModel):
    lock_duration_days: int # 10, 20, 30, or 90

class TontineDepositRequest(BaseModel):
    amount: float
    
class TontineLockRequest(BaseModel):
    lock_duration_days: int # 10, 20, 30, or 90

# --- Transaction Schemas ---

class TransferRequest(BaseModel):
    receiver_phone: str
    amount: float
    type: str = "TRANSFER"

class TransactionRead(BaseModel):
    id: int
    amount: float
    currency: str
    exchange_rate: float
    type: str # DEPOSIT, WITHDRAW, TRANSFER, etc.
    status: str # PENDING, SUCCESS, FAILED
    reference: str
    created_at: datetime
    processed_at: Optional[datetime] = None

class PaymentRequest(BaseModel):
    amount: float
    currency: Optional[str] = "XOF"
    phone: Optional[str] = None # MTN/Moov number
    phone_number: Optional[str] = None # Alternative field name
    network: Optional[str] = None # FLOOZ or TMONEY
    
    class Config:
        # Allow population by field name
        populate_by_name = True

# --- PayGateGlobal Schemas ---

class PayGateInitiateRequest(BaseModel):
    phone_number: str
    amount: float
    description: Optional[str] = None
    identifier: str
    network: str  # FLOOZ or TMONEY

class PayGateInitiateResponse(BaseModel):
    tx_reference: str
    status: int  # 0: success, 2: invalid token, 4: invalid params, 6: duplicate

class PayGateStatusRequest(BaseModel):
    tx_reference: Optional[str] = None
    identifier: Optional[str] = None

class PayGateStatusResponse(BaseModel):
    tx_reference: str
    identifier: Optional[str] = None
    payment_reference: Optional[str] = None
    status: int  # 0: success, 2: pending, 4: expired, 6: cancelled
    datetime: Optional[str] = None
    payment_method: Optional[str] = None

class PayGateBalanceResponse(BaseModel):
    flooz: float
    tmoney: float

class PayGateWebhookData(BaseModel):
    tx_reference: str
    identifier: str
    payment_reference: str
    amount: float
    datetime: str
    payment_method: str
    phone_number: str

# --- Loan Schemas ---

class LoanRequest(BaseModel):
    loan_type: str = "ALOBA"  # NOVI+, ALOBA
    amount: float
    guarantors: List[str] # List of phone numbers

class GuaranteeResponse(BaseModel):
    accept: bool

class LoanRead(BaseModel):
    id: int
    borrower_id: int
    loan_type: str
    amount: float
    interest_rate: float
    total_amount: float
    status: str
    due_date: datetime
    created_at: datetime

# --- Admin Schemas ---

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_verified: Optional[bool] = None
    email: Optional[EmailStr] = None

class PaymentMethodBase(BaseModel):
    name: str
    code: str
    is_active: bool = True
    minimum_amount: float = 100.0
    maximum_amount: float = 500000.0
    fee_percentage: float = 0.01

class PaymentMethodRead(PaymentMethodBase):
    id: int

# --- KYC Schemas ---

class KYCSubmission(BaseModel):
    identity_type: str
    identity_number: str
    identity_expiry: datetime

class KYCUpdate(BaseModel):
    is_kyc_verified: bool
