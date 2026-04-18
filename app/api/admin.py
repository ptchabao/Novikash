from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional
from app.core.database import get_session
from app.api.auth import get_admin_user
from app.models.models import User, Transaction, PaymentMethod, SystemConfig
from app.schemas.schemas import UserRead, UserUpdate, TransactionRead, PaymentMethodRead, PaymentMethodBase, KYCUpdate

router = APIRouter()

# --- User Management ---

@router.get("/users", response_model=List[UserRead])
def list_users(admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, data: UserUpdate, admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.role:
        # Only SUPERADMIN can promote/demote to ADMIN/SUPERADMIN roles
        if admin.role != "SUPERADMIN":
             raise HTTPException(status_code=403, detail="Only SuperAdmin can change roles")
        user.role = data.role
        
    if data.is_verified is not None:
        user.is_verified = data.is_verified
    
    if data.email:
        user.email = data.email
        
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# --- Transaction Monitoring ---

@router.get("/transactions", response_model=List[TransactionRead])
def list_all_transactions(admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    transactions = session.exec(select(Transaction).order_by(Transaction.created_at.desc())).all()
    return transactions

# --- Payment Methods Management ---

@router.get("/payment-methods", response_model=List[PaymentMethodRead])
def list_payment_methods(admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    methods = session.exec(select(PaymentMethod)).all()
    return methods

@router.post("/payment-methods", response_model=PaymentMethodRead)
def create_payment_method(data: PaymentMethodBase, admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    method = PaymentMethod(**data.dict())
    session.add(method)
    session.commit()
    session.refresh(method)
    return method

@router.patch("/payment-methods/{method_id}", response_model=PaymentMethodRead)
def update_payment_method(method_id: int, data: PaymentMethodBase, admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    method = session.get(PaymentMethod, method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(method, key, value)
        
    session.add(method)
    session.commit()
    session.refresh(method)
    return method

# --- System Configuration ---

@router.post("/config")
def set_system_config(key: str, value: str, description: Optional[str] = None, admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    if admin.role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Only SuperAdmin can change system config")
        
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if config:
        config.value = value
        config.description = description
        config.updated_at = datetime.utcnow()
    else:
        config = SystemConfig(key=key, value=value, description=description)
        
    session.add(config)
    session.commit()
    return {"status": "ok", "key": key, "value": value}

# --- KYC Verification ---

@router.get("/kyc/pending", response_model=List[UserRead])
def list_pending_kyc(admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    users = session.exec(select(User).where(User.identity_number != None, User.is_kyc_verified == False)).all()
    return users

@router.patch("/kyc/{user_id}/verify", response_model=UserRead)
def verify_user_kyc(user_id: int, data: KYCUpdate, admin: User = Depends(get_admin_user), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_kyc_verified = data.is_kyc_verified
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
