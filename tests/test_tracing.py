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


def test_identity_env_beats_apsorc(monkeypatch, tmp_path):
    (tmp_path / ".apsorc").write_text(
        '{"serviceName":"from-file","serviceId":"1","workspaceId":"9"}'
    )
    monkeypatch.setattr(
        tracing,
        "_read_apsorc",
        lambda: {"serviceName": "from-file", "serviceId": "1", "workspaceId": "9"},
    )
    for v in (
        "OTEL_SERVICE_NAME",
        "APP_NAME",
        "SERVICE_ID",
        "APSO_WORKSPACE_ID",
    ):
        monkeypatch.delenv(v, raising=False)
    assert tracing._service_name() == "from-file"
    assert tracing._identity_attributes()["apso.service.id"] == "1"
    assert tracing._identity_attributes()["apso.workspace.id"] == "9"
    monkeypatch.setenv("APSO_SERVICE_ID", "stack-id")  # access-token audience, not the id
    monkeypatch.setenv("SERVICE_ID", "42")
    assert tracing._identity_attributes()["apso.service.id"] == "42"


def test_request_produces_span_when_set_up_before_serving(monkeypatch):
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
