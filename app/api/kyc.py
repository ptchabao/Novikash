from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlmodel import Session, select
import shutil
import os
import uuid
from app.core.database import get_session
from app.api.auth import get_current_user
from app.models.models import User
from app.schemas.schemas import KYCSubmission, UserRead

router = APIRouter()

@router.post("/submit", response_model=UserRead)
def submit_kyc(data: KYCSubmission, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    User submits identity information for KYC verification.
    """
    current_user.identity_type = data.identity_type
    current_user.identity_number = data.identity_number
    current_user.identity_expiry = data.identity_expiry
    # Reset verification if they submit new info? Or keep pending.
    # For now, just store it.
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.post("/upload")
def upload_kyc_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    User uploads a photo of their identity document.
    """
    # Create directory if not exists
    upload_dir = "uploads/kyc"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    file_name = f"{current_user.id}_{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Update user record
    current_user.identity_document_url = f"/static/kyc/{file_name}"
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {"url": current_user.identity_document_url}

@router.get("/status")
def get_kyc_status(current_user: User = Depends(get_current_user)):
    return {
        "is_kyc_verified": current_user.is_kyc_verified,
        "identity_type": current_user.identity_type,
        "identity_number": current_user.identity_number
    }
