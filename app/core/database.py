import os
from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./novikash.db")

# Ensure we use SQLite for local development
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
else:
    # For production databases like PostgreSQL
    engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
