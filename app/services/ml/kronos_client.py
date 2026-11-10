import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)

class KronosClient:
    """Async HTTP client to communicate with vinbot-kronos inference container."""

    def __init__(self):
        self.service_url = os.getenv("KRONOS_SERVICE_URL", "http://kronos:8005")
        self.timeout = 5.0  # 5s max wait in async background task to allow queueing
        self.models_dir = os.getenv("ML_MODEL_PATH", "data/ml_models")
        os.makedirs(self.models_dir, exist_ok=True)
        self.cached_predictions: Dict[str, Dict[str, Any]] = {}

    async def get_forecast(self, symbol: str, klines: List[Dict[str, Any]], pred_len: int = 10) -> Optional[Dict[str, Any]]:
        """
        Request Kronos-mini forecast for given symbol and historical klines.
        klines format: [{'timestamp': int, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': float}, ...]
        """
        if not klines or len(klines) < 30:
            return None

        payload = {
            "symbol": symbol,
            "klines": klines[-250:],  # send last 250 bars for context
            "pred_len": pred_len
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.service_url}/forecast", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    self.cached_predictions[symbol] = data
                    # Persist to disk so all containers and dashboard share telemetry
                    try:
                        save_path = os.path.join(self.models_dir, f"{symbol}_kronos.json")
                        with open(save_path, "w", encoding="utf-8") as f:
                            json.dump(data, f)
                    except Exception as pe:
                        logger.debug(f"Could not persist Kronos forecast for {symbol}: {pe}")
                    return data
                else:
                    logger.debug(f"Kronos HTTP {resp.status_code}: {resp.text}")
                    return None
        except httpx.TimeoutException:
            logger.debug(f"Kronos inference timed out for {symbol} (> {self.timeout}s)")
            return self.cached_predictions.get(symbol)
        except Exception as e:
            logger.debug(f"Kronos connection error: {e}")
            return self.cached_predictions.get(symbol)

# Global singleton client
kronos_client = KronosClient()

