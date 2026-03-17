import hmac
import hashlib
import time
from typing import Dict, Any

def generate_signature(query_string: str, secret_key: str) -> str:
    """Generate HMAC-SHA256 signature for Binance API."""
    return hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def get_timestamp() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)
