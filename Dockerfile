# Multi-stage image: build wheels in builder stage, keep runtime image minimal

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false
WORKDIR /wheels

# Build-time deps for compiling wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app

# Runtime system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Install wheels produced in builder stage (no build tools required here)
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy application source
COPY . /app

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser:appuser /app

# Entrypoint script chooses what to run from ROLE env var
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch to non-root user after setup
USER appuser

# Default role: worker (can be overridden with ROLE or command args)
ENV ROLE=worker \
    PORT=8080

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD []
