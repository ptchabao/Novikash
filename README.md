# NoviKash Fintech API

NoviKash is a fintech API built with FastAPI, providing a unique **Social Loan** system based on community guarantees.

## Features

- **Auth**: JWT-based authentication (phone-centric).
- **Wallet**: Manage available and locked balances (for guarantees).
- **Transactions**: Peer-to-peer transfers, deposits, and withdrawals.
- **Social Loans**: 
    - Request a loan with multiple guarantors.
    - Automated fund locking for guarantors upon acceptance.
    - Automated disbursement when all guarantors approve.
    - Automated recovery (debiting guarantors) on default.
- **Mobile Money Mocks**: Simulated integration for MTN and Moov Money.
- **Notifications**: System alerts for loan requests and financial updates.

## Tech Stack

- **Framework**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Database**: PostgreSQL (production), SQLite (development)
- **Security**: Passlib (bcrypt) & Python-Jose (JWT)

## Deployment

### Docker

Build and run with Docker:

```bash
# Build the image
docker build -t novikash-api .

# Run the container
docker run -p 8000:8000 -e SECRET_KEY=your-secret-key-here novikash-api
```

### Docker Compose

For local development with persistent database:

```bash
docker-compose up --build
```

### Dokploy

1. Connect your GitHub repository to Dokploy
2. Create a new service using the Dockerfile
3. Set environment variables in Dokploy:
   - `DATABASE_URL`: Your database URL (SQLite for simple deployments)
   - `SECRET_KEY`: A secure random string
   - `ALGORITHM`: HS256
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: 30
   - `LOAN_INTEREST_RATE`: 0.1
   - `DEFAULT_REPAYMENT_DAYS`: 7

## Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access Documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Endpoints Overview

- `POST /auth/register`: Create a new account.
- `POST /auth/login`: Get a JWT token.
- `GET /wallet/me`: View balance.
- `POST /loans/request`: Request a social loan.
- `POST /loans/{id}/guarantee/respond`: Accept/Refuse a guarantee request.
- `POST /payments/deposit`: Initiate a Mobile Money deposit.
- `POST /admin/process-defaults`: Trigger recovery for expired loans.
