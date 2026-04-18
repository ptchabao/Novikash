FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set default environment variables for SQLite
ENV DATABASE_URL=sqlite:///./novikash.db
ENV SECRET_KEY=yoursecretkeyhere
ENV ALGORITHM=HS256
ENV ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV LOAN_INTEREST_RATE=0.1
ENV DEFAULT_REPAYMENT_DAYS=7

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
