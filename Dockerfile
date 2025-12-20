# DataSens E1 - Production Monolith (Python 3.10)
# Version: v1.2.0 (Phase 0 Complete - E1 Isolated)
FROM python:3.10-slim

# Metadata
LABEL maintainer="DataSens Team"
LABEL description="DataSens E1 Pipeline - Isolated & Production Ready"
LABEL version="1.2.0"
LABEL phase="0-complete"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DB_PATH=/app/data/datasens.db \
    METRICS_PORT=8000

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

# Copy application code (E1 isolated structure)
COPY . .

# Create data directories with proper permissions
RUN mkdir -p /app/data/raw /app/data/silver /app/data/gold /app/exports /app/zzdb && \
    chmod -R 755 /app/data /app/exports

# Verify E1 structure
RUN python -c "from src.e1.pipeline import E1Pipeline; print('✅ E1 Pipeline importable')" && \
    python -c "from src.shared.interfaces import E1DataReader; print('✅ E1DataReader importable')"

# Health check - Verify E1 can be imported and DB is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from src.e1.pipeline import E1Pipeline; import sqlite3; import os; db_path = os.getenv('DB_PATH', '/app/data/datasens.db'); conn = sqlite3.connect(db_path); conn.close(); print('✅ Health check OK')" || exit 1

# Expose Prometheus metrics port
EXPOSE 8000

# Run pipeline (E1 isolated)
CMD ["python", "main.py"]
