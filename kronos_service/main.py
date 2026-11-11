import os
import sys
import logging
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

# Add kronos_repo to path so 'model' can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kronos_repo"))

try:
    from model import Kronos, KronosTokenizer, KronosPredictor
except Exception as e:
    Kronos = None
    KronosTokenizer = None
    KronosPredictor = None
    print(f"Warning: could not import Kronos: {e}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("kronos_service")

app = FastAPI(title="VinBot 4th Brain - Kronos Mini Inference API", version="1.0.0")

class KlineBar(BaseModel):
    timestamp: int  # ms timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None

class ForecastRequest(BaseModel):
    symbol: str
    klines: List[KlineBar]
    pred_len: int = 10  # number of 1m bars into future

class ForecastResponse(BaseModel):
    symbol: str
    status: str
    direction: str  # BULLISH, BEARISH, NEUTRAL
    expected_pct: float
    confidence: float
    predicted_close: float
    current_close: float
    predicted_path: List[float]
    inference_time_ms: float

# Global model state and thread synchronization lock
_inference_lock = threading.Lock()
_state = {
    "model": None,
    "tokenizer": None,
    "predictor": None,
    "ready": False,
    "error": None,
    "total_forecasts": 0,
    "last_latency_ms": 0.0,
    "symbol_latency": {}
}

@app.on_event("startup")
async def startup_event():
    """Load Kronos-mini model and tokenizer."""
    try:
        logger.info("Loading Kronos-Tokenizer-2k and Kronos-mini...")
        tok_name = "NeoQuasar/Kronos-Tokenizer-2k"
        model_name = "NeoQuasar/Kronos-mini"
        
        tokenizer = KronosTokenizer.from_pretrained(tok_name)
        model = Kronos.from_pretrained(model_name)
        model.eval()
        
        predictor = KronosPredictor(model, tokenizer, max_context=512)
        _state["tokenizer"] = tokenizer
        _state["model"] = model
        _state["predictor"] = predictor
        _state["ready"] = True
        logger.info("✅ Kronos-mini loaded and ready for CPU inference!")
    except Exception as e:
        logger.error(f"Failed to load Kronos model: {e}")
        _state["error"] = str(e)
        _state["ready"] = False

@app.get("/health")
def health():
    return {
        "status": "healthy" if _state["ready"] else "loading_or_failed",
        "ready": _state["ready"],
        "model": "NeoQuasar/Kronos-mini (4.1M)",
        "tokenizer": "NeoQuasar/Kronos-Tokenizer-2k",
        "error": _state["error"]
    }

@app.get("/metrics")
def metrics():
    ready_val = 1 if _state["ready"] else 0
    lines = [
        "# HELP kronos_model_ready Whether Kronos-mini model is loaded and ready",
        "# TYPE kronos_model_ready gauge",
        f"kronos_model_ready {ready_val}",
        "# HELP kronos_forecasts_total Total count of forecasts generated",
        "# TYPE kronos_forecasts_total counter",
        f'kronos_forecasts_total {_state.get("total_forecasts", 0)}',
        "# HELP kronos_last_inference_latency_ms Latency of most recent inference in milliseconds",
        "# TYPE kronos_last_inference_latency_ms gauge",
        f'kronos_last_inference_latency_ms {_state.get("last_latency_ms", 0.0)}',
    ]
    for sym, ms in _state.get("symbol_latency", {}).items():
        lines.append(f'kronos_inference_time_ms{{symbol="{sym}"}} {ms}')
    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")

@app.post("/forecast", response_model=ForecastResponse)
def forecast(req: ForecastRequest):
    if not _state["ready"] or _state["predictor"] is None:
        raise HTTPException(status_code=503, detail="Kronos model not ready yet")

    if len(req.klines) < 30:
        raise HTTPException(status_code=400, detail="At least 30 klines required for context")

    start_time = datetime.now()
    
    # 1. Format input klines into DataFrame
    data_rows = []
    for k in req.klines:
        vol = float(k.volume)
        amt = float(k.amount) if k.amount is not None else float(k.close) * vol
        data_rows.append({
            "timestamps": pd.to_datetime(k.timestamp, unit="ms"),
            "open": float(k.open),
            "high": float(k.high),
            "low": float(k.low),
            "close": float(k.close),
            "volume": vol,
            "amount": amt
        })

    df = pd.DataFrame(data_rows)
    df = df.drop_duplicates(subset=["timestamps"]).sort_values("timestamps").reset_index(drop=True)

    # Use up to 300 historical bars for context
    context_len = min(len(df), 300)
    df = df.tail(context_len).reset_index(drop=True)

    # Enforce strictly monotonic 1-minute sequence for model stability
    last_ts = df["timestamps"].iloc[-1]
    if last_ts <= pd.to_datetime("2020-01-01"):
        last_ts = pd.Timestamp.now(tz=timezone.utc).floor("1min").tz_localize(None)
    clean_ts = pd.date_range(end=last_ts, periods=len(df), freq="1min")

    x_df = df[["open", "high", "low", "close", "volume", "amount"]].reset_index(drop=True)
    x_ts = pd.Series(clean_ts)

    # Generate future timestamps as pandas Series
    y_ts_idx = pd.date_range(start=last_ts + timedelta(minutes=1), periods=req.pred_len, freq="1min")
    y_ts = pd.Series(y_ts_idx)

    current_close = float(x_df["close"].iloc[-1])

    try:
        with _inference_lock:
            pred_df = _state["predictor"].predict(
                df=x_df,
                x_timestamp=x_ts,
                y_timestamp=y_ts,
                pred_len=req.pred_len,
                T=0.8,
                top_p=0.9,
                sample_count=1,
                verbose=False
            )
        
        pred_closes = [float(c) for c in pred_df["close"].tolist()]
        final_pred_close = pred_closes[-1]
        
        # Calculate expected percentage change
        expected_pct = ((final_pred_close - current_close) / current_close) * 100.0
        
        # Classify direction
        if expected_pct >= 0.25:
            direction = "BULLISH"
        elif expected_pct <= -0.25:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # Confidence based on trajectory consistency
        up_steps = sum(1 for i in range(1, len(pred_closes)) if pred_closes[i] > pred_closes[i-1])
        down_steps = len(pred_closes) - 1 - up_steps
        if direction == "BULLISH":
            consistency = up_steps / max(1, len(pred_closes) - 1)
        elif direction == "BEARISH":
            consistency = down_steps / max(1, len(pred_closes) - 1)
        else:
            consistency = 0.5

        confidence = round(float(0.5 + 0.5 * consistency), 2)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000.0

        # Update service telemetry for Prometheus /metrics
        _state["total_forecasts"] = _state.get("total_forecasts", 0) + 1
        _state["last_latency_ms"] = round(elapsed_ms, 1)
        if "symbol_latency" not in _state or not isinstance(_state["symbol_latency"], dict):
            _state["symbol_latency"] = {}
        _state["symbol_latency"][req.symbol] = round(elapsed_ms, 1)

        return ForecastResponse(
            symbol=req.symbol,
            status="success",
            direction=direction,
            expected_pct=round(expected_pct, 2),
            confidence=confidence,
            predicted_close=round(final_pred_close, 4),
            current_close=round(current_close, 4),
            predicted_path=[round(p, 4) for p in pred_closes],
            inference_time_ms=round(elapsed_ms, 1)
        )
    except Exception as e:
        logger.error(f"Inference error for {req.symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

