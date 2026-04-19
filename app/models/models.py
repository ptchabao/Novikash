from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship

# --- User & Wallet ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True)
    password_hash: str
    pin_hash: Optional[str] = None
    role: str = Field(default="USER") # USER, ADMIN, SUPERADMIN
    is_verified: bool = Field(default=False)
    otp_code: Optional[str] = None
    otp_expiry: Optional[datetime] = None
    
    # KYC Fields
    identity_type: Optional[str] = None # CIN, Passport, etc.
    identity_number: Optional[str] = None
    identity_expiry: Optional[datetime] = None
    identity_document_url: Optional[str] = None # Link to uploaded document
    is_kyc_verified: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    wallet: "Wallet" = Relationship(back_populates="user")
    loans: List["Loan"] = Relationship(back_populates="borrower")
    guarantees: List["LoanGuarantee"] = Relationship(back_populates="guarantor")

class Wallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    balance_available: float = Field(default=0.0)
    balance_locked: float = Field(default=0.0)
    currency: str = Field(default="XOF") # CFA Franc
    
    user: User = Relationship(back_populates="wallet")

# --- Transactions ---

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str  # TRANSFER, DEPOSIT, WITHDRAW, LOAN_DISBURSEMENT, etc.
    amount: float
    currency: str = Field(default="XOF")
    exchange_rate: float = Field(default=1.0) # Rate vs USD at transaction time
    status: str = Field(default="PENDING") # PENDING, SUCCESS, FAILED
    reference: str = Field(unique=True)
    sender_wallet_id: Optional[int] = Field(default=None, foreign_key="wallet.id")
    receiver_wallet_id: Optional[int] = Field(default=None, foreign_key="wallet.id")
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- Loans & Guarantees ---

class Loan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    borrower_id: int = Field(foreign_key="user.id")
    loan_type: str = Field(default="ALOBA")  # NOVI+, ALOBA
    amount: float
    interest_rate: float
    total_amount: float
    status: str = Field(default="PENDING") # PENDING, ACTIVE, REPAID, DEFAULTED
    due_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    borrower: User = Relationship(back_populates="loans")
    guarantees: List["LoanGuarantee"] = Relationship(back_populates="loan")

class LoanGuarantee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    loan_id: int = Field(foreign_key="loan.id")
    guarantor_id: int = Field(foreign_key="user.id")
    amount_locked: float
    status: str = Field(default="PENDING") # PENDING, ACCEPTED, REFUSED, RELEASED, DEBITED
    
    loan: Loan = Relationship(back_populates="guarantees")
    guarantor: User = Relationship(back_populates="guarantees")

# --- Extras ---

class Contact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    contact_user_id: int = Field(foreign_key="user.id")
    alias: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    type: str
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentMethod(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str # e.g., MTN Mobile Money, Moov Money
    code: str # e.g., MTN, MOOV
    is_active: bool = Field(default=True)
    minimum_amount: float = Field(default=100.0)
    maximum_amount: float = Field(default=500000.0)
    fee_percentage: float = Field(default=0.01) # 1%

class SystemConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True) # e.g., loan_interest_rate
    value: str # Store as string, cast as needed
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
