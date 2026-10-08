# Build stage
FROM golang:1.23-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache git ca-certificates

# Cache dependencies
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Build statically linked binary
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /edge-agent main.go

# Production scratch/alpine container
FROM alpine:3.20

RUN apk add --no-cache ca-certificates tzdata

WORKDIR /app
COPY --from=builder /edge-agent /app/edge-agent

VOLUME /app/data
ENV BUFFER_DB_PATH=/app/data/edge_buffer.db
ENV PORT=9090

EXPOSE 9090

ENTRYPOINT ["/app/edge-agent"]
