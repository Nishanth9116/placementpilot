# PlacementPilot - Production Container Image
FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATABASE_PATH=/app/data/placementpilot.db

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first for Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure persistent data directory exists
RUN mkdir -p /app/data

# Expose default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/overview || exit 1

# Start the Starlette web server
CMD ["sh", "-c", "uvicorn src.web.app:app --host 0.0.0.0 --port ${PORT:-8000}"]

