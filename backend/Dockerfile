# ==============================================================================
# Stage 1: Build Dependencies
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install .

# ==============================================================================
# Stage 2: Runtime Container
# ==============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Install lightweight runtime utilities for health probes and entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built python dependencies from builder stage
COPY --from=builder /install /usr/local

# Security: Create non-root system user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Copy application source, migrations, configuration, and entrypoint
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh ./docker-entrypoint.sh

# Set executable permission and assign ownership
RUN chmod +x ./docker-entrypoint.sh && \
    chown -R appuser:appuser /app

# Run as non-root user
USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
