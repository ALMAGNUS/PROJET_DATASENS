# DataSens E1 - Production Monolith (Python 3.10)
# Version: v1.0.0-stable (FREEZE)
FROM python:3.10-slim

# Metadata
LABEL maintainer="DataSens Team"
LABEL description="DataSens E1 Pipeline - Monolith Production Ready"
LABEL version="1.0.0-stable"
LABEL freeze="true"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Prometheus client
RUN pip install --no-cache-dir prometheus-client==0.20.0

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/raw /app/data/silver /app/data/gold /app/exports /app/zzdb

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('/app/data/datasens.db'); conn.close()" || exit 1

# Expose Prometheus metrics port
EXPOSE 8000

# Run pipeline
CMD ["python", "main.py"]
