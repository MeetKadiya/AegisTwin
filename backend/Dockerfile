# Stage 1: Build & Dependency Wheel Compilation
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Minimal Distroless/Alpine-grade Hardened Runtime
FROM python:3.12-slim AS runtime

LABEL maintainer="AegisTwin Security Engineering <security@aegistwin.internal>" \
      org.opencontainers.image.title="AegisTwin Enterprise Digital Twin Engine" \
      org.opencontainers.image.description="Real-time security digital twin platform backend" \
      org.opencontainers.image.version="2.0.0"

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPYCACHEPREFIX=/tmp/pycache \
    PORT=8000

# Install runtime-only library dependencies and strip package caches
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create unprivileged non-root user (UID 10001) for strict PodSecurityStandards
RUN groupadd -g 10001 aegis && \
    useradd -u 10001 -g aegis -m -d /app -s /usr/sbin/nologin aegis && \
    mkdir -p /tmp/pycache && \
    chown -R aegis:aegis /app /tmp/pycache

# Copy virtualenv and application assets
COPY --from=builder /opt/venv /opt/venv
COPY --chown=aegis:aegis . /app/

# Container Healthcheck (Kubernetes will use readiness/liveness probes)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Enforce non-root execution context
USER 10001:10001

EXPOSE 8000

# ponytail: [ceiling: 4 workers per pod; scale horizontally via Kubernetes HPA]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
