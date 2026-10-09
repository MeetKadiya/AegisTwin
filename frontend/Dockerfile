FROM node:22-alpine AS builder

WORKDIR /app

ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=${BACKEND_URL}
ENV NEXT_PUBLIC_BACKEND_URL=${BACKEND_URL}

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN mkdir -p public
RUN npm run build

# Stage 2: Production Hardened Non-Root Alpine Runner
FROM node:22-alpine AS runner

LABEL maintainer="AegisTwin Frontend Engineering <frontend@aegistwin.internal>" \
      org.opencontainers.image.title="AegisTwin Operations Dashboard" \
      org.opencontainers.image.description="Real-time SOC & OT security twin user interface" \
      org.opencontainers.image.version="2.0.0"

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Copy built application assets and ensure ownership belongs to non-root 'node' user (UID 1000)
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static
COPY --chown=node:node docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh

# Non-root user execution context
USER node:node

EXPOSE 3000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["node", "server.js"]
