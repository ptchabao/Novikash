import os
from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mahizuconnectics:servicePONDIKPA2025@novikash-novi-l42sq2:5432/postgres")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
