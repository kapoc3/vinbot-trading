import logging
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings

settings = get_settings()

def setup_observability(app: FastAPI):
    """Setup Prometheus metrics and OpenTelemetry tracing."""
    
    # 1. Prometheus Metrics
    Instrumentator().instrument(app).expose(
        app, 
        endpoint=settings.PROMETHEUS_METRICS_PATH
    )

    # 2. OpenTelemetry Tracing (Tempo)
    resource = Resource(attributes={
        ResourceAttributes.SERVICE_NAME: settings.PROJECT_NAME
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    
    logging.info("Observability stack (Prometheus + OTLP) initialized")
