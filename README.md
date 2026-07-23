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

## License

Apache License 2.0. See the [LICENSE](LICENSE) file.
