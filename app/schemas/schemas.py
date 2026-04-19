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
    currency: str = "XOF"
    phone: str # MTN/Moov number

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
