import sys
import os
from sqlmodel import Session, select, create_engine
from app.models.models import User
from app.core.security import get_password_hash
from app.core.database import DATABASE_URL

def create_superadmin(phone, password):
    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.phone == phone)).first()
        if existing:
            print(f"User with phone {phone} already exists. Updating to SUPERADMIN.")
            existing.role = "SUPERADMIN"
            existing.is_verified = True
            existing.password_hash = get_password_hash(password)
            session.add(existing)
        else:
            new_user = User(
                phone=phone,
                password_hash=get_password_hash(password),
                role="SUPERADMIN",
                is_verified=True
            )
            session.add(new_user)
        session.commit()
        print(f"SuperAdmin {phone} created/updated successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <phone> <password>")
    else:
        create_superadmin(sys.argv[1], sys.argv[2])
