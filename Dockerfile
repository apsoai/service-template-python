# Python/FastAPI Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
