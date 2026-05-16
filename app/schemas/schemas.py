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

class AdminUserRead(BaseModel):
    id: int
    phone: str
    email: Optional[str] = None
    role: str
    is_verified: bool
    is_kyc_verified: bool
    identity_type: Optional[str] = None
    identity_number: Optional[str] = None
    identity_document_url: Optional[str] = None
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
    guarantors: List[str] = []  # List of phone numbers
    terms_accepted: bool = False

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

class NoviPlusActivateRequest(BaseModel):
    first_name: str
    last_name: str
    employer: str
    contract_type: str  # CDI, CDD
    contract_end_date: Optional[datetime] = None
    partner_bank: str
    account_number: str
    declared_salary: float
    identity_number: str
    bank_consent: bool = False

class NoviPlusProfileRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    employer: str
    contract_type: str
    contract_end_date: Optional[datetime] = None
    partner_bank: str
    account_number: str
    declared_salary: float
    verified_salary: Optional[float] = None
    status: str
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None

class LoanEligibilityRead(BaseModel):
    can_request: bool
    reason: Optional[str] = None
    max_amount: float = 0.0
    wallet_balance: float = 0.0
    multiplier: float = 5.0
    min_wallet_required: float = 2000.0
    global_cap: float = 100000.0
    weekly_interest_rate: float = 0.01
    max_weeks: int = 4
    is_suspended: bool = False
    suspended_until: Optional[datetime] = None

class LoanOverviewRead(BaseModel):
    active_loan: Optional[LoanRead] = None
    loans: List[LoanRead] = []
    has_active_loan: bool
    novi_plus: Optional[NoviPlusProfileRead] = None
    novi_plus_eligibility: LoanEligibilityRead
    aloba_eligibility: LoanEligibilityRead
    pending_guarantee_count: int = 0
    terms_accepted: bool = False

class LoanSimulationRead(BaseModel):
    amount: float
    weeks: int
    interest_rate_per_week: float
    interest_amount: float
    total_to_repay: float
    due_date: datetime

class PendingGuaranteeRead(BaseModel):
    guarantee_id: int
    loan_id: int
    borrower_phone: str
    loan_amount: float
    amount_to_guarantee: float
    status: str
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

class StaffMeRead(BaseModel):
    id: int
    phone: str
    email: Optional[str] = None
    role: str
    permissions: List[str]

class ManualWalletAdjustment(BaseModel):
    amount: float
    reason: str
    reference: Optional[str] = None

class AdminDashboardStats(BaseModel):
    total_users: int
    verified_users: int
    pending_kyc: int
    total_wallet_balance: float
    total_locked_balance: float
    active_loans: int
    pending_loans: int
    pending_novi_plus: int
    transactions_today: int
    deposits_today: float
    withdrawals_today: float
    manual_credits_today: float

class AdminTransactionRead(TransactionRead):
    sender_wallet_id: Optional[int] = None
    receiver_wallet_id: Optional[int] = None
    sender_phone: Optional[str] = None
    receiver_phone: Optional[str] = None

class LoanAdminRead(LoanRead):
    borrower_phone: Optional[str] = None

class NoviPlusAdminRead(NoviPlusProfileRead):
    user_id: int
    user_phone: Optional[str] = None

class NoviPlusVerifyRequest(BaseModel):
    approve: bool
    verified_salary: Optional[float] = None
    rejection_reason: Optional[str] = None

class LoanStatusUpdate(BaseModel):
    status: str  # ACTIVE, REPAID, REJECTED, DEFAULTED

class AdminAuditEntry(BaseModel):
    admin_id: int
    admin_phone: str
    action: str
    target: Optional[str] = None
    details: dict = {}
    created_at: str
