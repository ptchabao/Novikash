from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select
from datetime import datetime
from app.core.database import engine
from app.models.models import Loan, LoanGuarantee, Transaction, Notification
import uuid

scheduler = BackgroundScheduler()

def process_expired_loans():
    """
    Background job to handle expired loans.
    """
    print(f"[{datetime.utcnow()}] Running cron: Checking for expired loans...")
    with Session(engine) as session:
        expired_loans = session.exec(
            select(Loan).where(
                Loan.status == "ACTIVE",
                Loan.due_date < datetime.utcnow()
            )
        ).all()
        
        for loan in expired_loans:
            guarantees = session.exec(select(LoanGuarantee).where(LoanGuarantee.loan_id == loan.id)).all()
            for g in guarantees:
                if g.status == "ACCEPTED":
                    guarantor_wallet = g.guarantor.wallet
                    guarantor_wallet.balance_locked -= g.amount_locked
                    g.status = "DEBITED"
                    
                    transaction = Transaction(
                        type="GUARANTEE_DEBIT",
                        amount=g.amount_locked,
                        status="SUCCESS",
                        reference=f"CRON-DEFAULT-{loan.id}-{uuid.uuid4()}",
                        sender_wallet_id=guarantor_wallet.id,
                        processed_at=datetime.utcnow()
                    )
                    session.add(guarantor_wallet)
                    session.add(g)
                    session.add(transaction)
                    
                    notification = Notification(
                        user_id=g.guarantor_id,
                        type="GUARANTEE_DEBITED",
                        message=f"Loan {loan.id} (Borrower: {loan.borrower.phone}) has defaulted. Your guarantee of {g.amount_locked} XOF has been debited."
                    )
                    session.add(notification)
            
            loan.status = "DEFAULTED"
            session.add(loan)
            print(f"Loan {loan.id} marked as DEFAULTED.")
            
        session.commit()

def start_scheduler():
    # Run every hour
    scheduler.add_job(process_expired_loans, 'interval', minutes=60)
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()
