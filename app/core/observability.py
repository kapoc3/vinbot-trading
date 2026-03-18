import logging
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings

settings = get_settings()

def setup_observability(app: FastAPI):
    """Setup Prometheus metrics."""
    
    # 1. Prometheus Metrics
    Instrumentator().instrument(app).expose(
        app, 
        endpoint=settings.PROMETHEUS_METRICS_PATH
    )

    logging.info("Observability stack (Prometheus) initialized")
