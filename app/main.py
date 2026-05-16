import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import auth, wallet, loans, payments, notifications, admin, kyc, tontine
from app.core.database import init_db
from app.core.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="NoviKash API", version="0.1.0")

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
app.include_router(tontine.router, prefix="/tontine", tags=["Tontine"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(loans.router, prefix="/loans", tags=["Loans"])
app.include_router(kyc.router, prefix="/kyc", tags=["KYC"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])

# Serve static files for KYC documents
app.mount("/static", StaticFiles(directory="uploads"), name="static")

@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

@app.get("/")
async def root():
    return {"message": "Welcome to NoviKash API"}
