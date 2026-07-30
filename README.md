# Apso Python Service Template

The GitHub template behind every Apso Python backend: FastAPI, SQLAlchemy 2.0 (async), Alembic, and PostgreSQL. `apso init --name my-api --language python` clones this repository, and `apso generate` turns your `.apsorc` schema into models, routers, schemas, and services inside it. The generated code is yours: Apache-2.0 licensed, no Apso SDK, no runtime dependency.

New to Apso? The [quickstart](https://docs.apso.ai/get-started/quickstart) goes from schema to running API in about ten minutes. All three language templates are listed at [apso.ai/templates](https://apso.ai/templates).

## Stack

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Database**: PostgreSQL (asyncpg driver)

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py               # Application entry point
│   ├── database.py           # Database configuration
│   ├── autogen/              # Auto-generated code (DO NOT EDIT)
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routers/          # FastAPI routers
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Service layer
│   ├── observability/        # OpenTelemetry tracing bootstrap
│   │   └── tracing.py        # setup_tracing() — off by default, wired in main.py
│   └── extensions/           # Custom/manual code
│       └── middleware/       # Custom middleware
├── tests/                    # Test files
├── alembic/                  # Database migrations
├── .apsorc                   # APSO configuration
├── .env.example              # Environment template
├── Dockerfile                # Docker build configuration
├── pyproject.toml            # Project configuration
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Docker (optional)

### Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Copy environment file:
   ```bash
   cp .env.example .env
   ```

4. Update `.env` with your database credentials.

5. Run the server:
   ```bash
   python -m app.main
   ```

   Or with uvicorn:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
   ```

### Docker

Build and run with Docker:

```bash
docker build -t my-api .
docker run -p 3000:3000 --env-file .env my-api
```

## API Documentation

Swagger documentation is available at: `http://localhost:3000/_docs`
ReDoc documentation is available at: `http://localhost:3000/_redoc`

## APSO CLI Integration

This template is designed to work with the APSO CLI. To add entities:

```bash
apso scaffold
```

The CLI will generate:
- Models in `app/autogen/models/`
- Schemas in `app/autogen/schemas/`
- Routers in `app/autogen/routers/`
- Services in `app/autogen/services/`

## Extending the Template

Add custom code in the `app/extensions/` folder:
- Custom middleware in `app/extensions/middleware/`
- Create additional folders as needed for your custom logic

**Important:** Never modify files in the `app/autogen/` folder as they will be overwritten by the APSO CLI.

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback one migration:
```bash
alembic downgrade -1
```

## Testing

Run tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Code Quality

Format code:
```bash
black app tests
```

Lint code:
```bash
ruff check app tests
```

Type checking:
```bash
mypy app
```

## Observability (OpenTelemetry)

Every service built from this template ships with OpenTelemetry auto-instrumentation wired in. When enabled, each incoming HTTP request becomes a trace/span with route, method, status, latency, DB queries, and errors, exported over OTLP HTTP to a collector you point it at (an OpenTelemetry Collector feeding a Grafana/Tempo stack, or Grafana Cloud's managed OTLP endpoint).

The export destination is never hardwired to an Apso endpoint. You own where telemetry goes.

### Off by default

Tracing is a no-op unless you turn it on. With no OTLP endpoint and no enable flag set, the instrumentation does not start, does not export anything, and cannot block startup on an unreachable collector. Local dev and CI run exactly as before. Setup is wrapped in try/except, so telemetry can never take the app down.

### Enabling it

Set the OTLP endpoint (and optionally a service name):

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=my-api
python -m app.main
```

You should see `[otel] tracing enabled (...)` on startup, and traces begin flowing to your collector.

### Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP HTTP endpoint (OpenTelemetry Collector or Grafana Cloud). Setting this enables tracing. | unset (tracing off) |
| `OTEL_SERVICE_NAME` | `service.name` reported on every trace. | falls back to `APP_NAME`, then the `.apsorc` serviceName, then `apso-service` |
| `OTEL_ENABLED` | Force-enable (`true`/`1`/`yes`/`on`) or force-disable (`false`/`0`/`no`/`off`), overriding endpoint detection. | unset |

Standard `OTEL_*` environment variables (headers, resource attributes, sampling) are honored by the OpenTelemetry SDK as well.

### How it is wired

`app/observability/tracing.py` builds a `TracerProvider` with an OTLP HTTP span exporter and resource attributes (`service.name`, `service.version`), then instruments the FastAPI app (`FastAPIInstrumentor`) and the SQLAlchemy engine (`SQLAlchemyInstrumentor`). `setup_tracing(app, engine)` is called from the FastAPI lifespan in `app/main.py` after the app and engine exist. Spans are exported on a background thread via `BatchSpanProcessor` and flushed on shutdown so in-flight spans are not lost.

## License

Apache License 2.0. See the [LICENSE](LICENSE) file.
