from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from jose import JWTError, jwt
from datetime import datetime, timedelta
import random
from app.core.database import get_session, init_db
from app.core.security import get_password_hash, verify_password, create_access_token, ALGORITHM, SECRET_KEY
from app.models.models import User, Wallet
from app.schemas.schemas import UserCreate, UserLogin, Token, TokenData, UserRead, OTPVerify, PINSetup

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/oauth")

@router.on_event("startup")
def on_startup():
    init_db()

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise credentials_exception
        token_data = TokenData(phone=phone)
    except JWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.phone == token_data.phone)).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["ADMIN", "SUPERADMIN"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def generate_otp():
    return str(random.randint(100000, 999999))

@router.post("/register", response_model=UserRead)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.phone == user_data.phone)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    otp = generate_otp()
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        phone=user_data.phone,
        email=user_data.email,
        password_hash=hashed_pwd,
        otp_code=otp,
        otp_expiry=datetime.utcnow() + timedelta(minutes=10),
        is_verified=False
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Mock SMS sending
    print(f"SMS to {new_user.phone}: Your NoviKash OTP is {otp}")
    
    # Create Wallet automatically
    new_wallet = Wallet(user_id=new_user.id)
    session.add(new_wallet)
    session.commit()
    session.refresh(new_user)
    
    return new_user

@router.post("/verify-otp")
def verify_otp(data: OTPVerify, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.phone == data.phone)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.otp_code != data.code or (user.otp_expiry and user.otp_expiry < datetime.utcnow()):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    session.add(user)
    session.commit()
    
    return {"message": "Phone number verified successfully"}

@router.post("/resend-otp")
def resend_otp(phone: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.phone == phone)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    session.add(user)
    session.commit()
    
    print(f"SMS to {user.phone}: Your new NoviKash OTP is {otp}")
    return {"message": "OTP resent"}

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.phone == user_data.phone)).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Phone number not verified")
    
    access_token = create_access_token(data={"sub": user.phone})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/set-pin")
def set_pin(data: PINSetup, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not data.pin.isdigit() or len(data.pin) not in [4, 6]:
        raise HTTPException(status_code=400, detail="PIN must be 4 or 6 digits")
    
    current_user.pin_hash = get_password_hash(data.pin) # Reusing pwd hash logic for simplicity
    session.add(current_user)
    session.commit()
    return {"message": "PIN set successfully"}

@router.post("/login-pin", response_model=Token)
def login_with_pin(phone: str, pin: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.phone == phone)).first()
    if not user or not user.pin_hash or not verify_password(pin, user.pin_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or PIN")
    
    access_token = create_access_token(data={"sub": user.phone})
    return {"access_token": access_token, "token_type": "bearer"}

# For Swagger UI OAuth2 compatibility
@router.post("/login/oauth", response_model=Token, include_in_schema=False)
def login_oauth(form_data: UserLogin = Depends(), session: Session = Depends(get_session)):
    return login(form_data, session)
