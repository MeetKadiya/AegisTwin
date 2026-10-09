# Stage 1: Build statically compiled Go binary
FROM golang:1.23-alpine AS builder

WORKDIR /build

RUN apk add --no-cache git ca-certificates tzdata

COPY go.mod ./
RUN go mod download

COPY . .

# Pre-create data directory with distroless non-root ownership (UID 65532)
RUN mkdir -p /data && chown 65532:65532 /data

# Build statically linked, stripped binary with zero external libc dependencies
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -trimpath \
    -ldflags="-w -s -extldflags '-static'" \
    -o /edge-agent main.go

# Stage 2: Distroless Static Non-Root Runtime (Zero shell, zero package manager)
FROM gcr.io/distroless/static-debian12:nonroot

LABEL maintainer="AegisTwin Edge Engineering <edge@aegistwin.internal>" \
      org.opencontainers.image.title="AegisTwin Edge Gateway Agent" \
      org.opencontainers.image.description="Hardened ICS/OT Sparkplug B / MQTT Telemetry Agent" \
      org.opencontainers.image.version="2.0.0"

WORKDIR /app

# Copy root CA certificates, timezones, data volume mount, and binary
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder --chown=65532:65532 /data /data
COPY --from=builder /edge-agent /app/edge-agent

VOLUME /data
ENV BUFFER_DB_PATH=/data/edge_buffer.db \
    PORT=9090

# Enforce distroless nonroot user
USER 65532:65532

EXPOSE 9090

# ponytail: [ceiling: static binary with in-memory buffer ring and local SQLite spool]
ENTRYPOINT ["/app/edge-agent"]
