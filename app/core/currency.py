from sqlmodel import Session, select
from app.models.models import SystemConfig

def get_exchange_rate(session: Session, from_currency: str, to_currency: str) -> float:
    """
    Returns the exchange rate between two currencies.
    All currencies are internally pegged to USD.
    Example: to convert XOF to USD, we look for 'RATE_XOF_TO_USD'.
    Default XOF to USD is 0.0016 (approx).
    """
    if from_currency == to_currency:
        return 1.0
        
    # Get rates relative to USD
    # If USD is the base, we use RATE_{CURRENCY}_TO_USD
    # For now, let's assume we store RATE_XOF_TO_USD = 0.0016
    # And RATE_USD_TO_XOF = 600.0
    
    key = f"RATE_{from_currency}_TO_{to_currency}"
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    
    if config:
        return float(config.value)
        
    # Default fallback rates (simplified)
    fallbacks = {
        "RATE_XOF_TO_USD": 0.0016,
        "RATE_USD_TO_XOF": 625.0,
        "RATE_EUR_TO_USD": 1.08,
        "RATE_USD_TO_EUR": 0.92,
    }
    
    return fallbacks.get(key, 1.0)

def convert_amount(session: Session, amount: float, from_currency: str, to_currency: str) -> float:
    rate = get_exchange_rate(session, from_currency, to_currency)
    return amount * rate
