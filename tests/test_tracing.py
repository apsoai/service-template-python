import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.observability import tracing


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    for v in ("OTEL_ENABLED", "OTEL_EXPORTER_OTLP_ENDPOINT", "APSO_TELEMETRY"):
        monkeypatch.delenv(v, raising=False)
    yield
    tracing.shutdown_tracing()


def test_off_by_default():
    assert tracing._tracing_enabled() is False


def test_endpoint_enables_and_kill_switch_wins(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318")
    assert tracing._tracing_enabled() is True
    monkeypatch.setenv("APSO_TELEMETRY", "off")
    assert tracing._tracing_enabled() is False


def test_request_produces_span_when_set_up_before_serving(monkeypatch):
    from opentelemetry import trace
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318")
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    assert tracing.setup_tracing(app) is True
    mem = InMemorySpanExporter()
    tracing._provider.add_span_processor(SimpleSpanProcessor(mem))
    with TestClient(app) as c:
        assert c.get("/ping").status_code == 200
    assert any("/ping" in s.name for s in mem.get_finished_spans())
