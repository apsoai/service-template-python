"""
OpenTelemetry tracing bootstrap.

Safe by default: tracing is a no-op unless it is explicitly enabled. With no
OTLP endpoint and no enable flag set, nothing is instrumented, nothing is
exported, and startup can never block on an unreachable collector.

Enable it by setting ``OTEL_EXPORTER_OTLP_ENDPOINT`` (and optionally
``OTEL_SERVICE_NAME``), or by setting ``OTEL_ENABLED=true``. Every step is
wrapped in try/except so telemetry can never take the application down.

This mirrors the built-in OpenTelemetry wiring in the Apso TypeScript template.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("otel")

# Module-level handle to the provider so we can flush/shutdown on app shutdown.
_provider: Optional[Any] = None

# Truthy/falsy string sets for parsing OTEL_ENABLED.
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _tracing_enabled() -> bool:
    """
    Decide whether tracing should start.

    - ``OTEL_ENABLED`` truthy/falsy overrides everything.
    - Otherwise, tracing is enabled only when an OTLP endpoint is configured.
    """
    flag = _env("OTEL_ENABLED").lower()
    if flag in _TRUTHY:
        return True
    if flag in _FALSY:
        return False
    return bool(_env("OTEL_EXPORTER_OTLP_ENDPOINT"))


def _service_name() -> str:
    """
    Resolve the reported ``service.name``.

    Order: OTEL_SERVICE_NAME -> APP_NAME -> .apsorc serviceName -> package name.
    """
    for var in ("OTEL_SERVICE_NAME", "APP_NAME"):
        value = _env(var)
        if value:
            return value

    # Fall back to the .apsorc serviceName if the file has one.
    try:
        apsorc = Path(__file__).resolve().parents[2] / ".apsorc"
        if apsorc.is_file():
            data = json.loads(apsorc.read_text())
            name = str(data.get("serviceName") or "").strip()
            if name:
                return name
    except Exception:
        pass

    return "apso-service"


def _service_version() -> str:
    for var in ("OTEL_SERVICE_VERSION", "APP_VERSION"):
        value = _env(var)
        if value:
            return value
    return "0.0.0"


def setup_tracing(app: Any, engine: Any = None) -> bool:
    """
    Configure OpenTelemetry tracing and auto-instrument FastAPI + SQLAlchemy.

    Returns ``True`` if tracing was enabled and wired, ``False`` otherwise.
    Never raises: any failure is logged and swallowed so it cannot take the
    application down.

    Args:
        app: The FastAPI application instance.
        engine: The SQLAlchemy engine (sync or async). Optional.
    """
    global _provider

    if not _tracing_enabled():
        logger.debug("[otel] tracing disabled (no endpoint / OTEL_ENABLED not set)")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = _service_name()
        service_version = _service_version()

        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
            }
        )

        provider = TracerProvider(resource=resource)

        # OTLPSpanExporter reads OTEL_EXPORTER_OTLP_ENDPOINT (and the
        # signal-specific *_TRACES_ENDPOINT / headers) from the environment.
        # BatchSpanProcessor exports on a background thread, so an unreachable
        # collector never blocks request handling or startup.
        exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        _provider = provider

        # Instrument the FastAPI app.
        try:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[otel] FastAPI instrumentation failed: %s", exc)

        # Instrument the SQLAlchemy engine. Async engines expose the underlying
        # sync engine via ``.sync_engine``, which is what the instrumentor needs.
        if engine is not None:
            try:
                target = getattr(engine, "sync_engine", engine)
                SQLAlchemyInstrumentor().instrument(engine=target, tracer_provider=provider)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("[otel] SQLAlchemy instrumentation failed: %s", exc)

        endpoint = _env("OTEL_EXPORTER_OTLP_ENDPOINT") or "(default OTLP endpoint)"
        logger.info(
            "[otel] tracing enabled (service.name=%s, endpoint=%s)",
            service_name,
            endpoint,
        )
        return True
    except Exception as exc:
        # Never let telemetry setup crash the app.
        logger.warning("[otel] tracing setup failed, continuing without it: %s", exc)
        _provider = None
        return False


def shutdown_tracing() -> None:
    """Flush and shut down the tracer provider so in-flight spans are exported."""
    global _provider

    provider = _provider
    if provider is None:
        return

    try:
        # force_flush then shutdown; both are best-effort.
        flush = getattr(provider, "force_flush", None)
        if callable(flush):
            flush()
        shutdown = getattr(provider, "shutdown", None)
        if callable(shutdown):
            shutdown()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[otel] tracing shutdown failed: %s", exc)
    finally:
        _provider = None
