# Python/FastAPI Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the project and install it. pyproject.toml names README.md and the app
# package, so the install needs more than pyproject.toml.
COPY . .
RUN pip install --no-cache-dir .

# Expose port
EXPOSE 3000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
