#!/bin/sh
set -e

TARGET_BACKEND="${BACKEND_URL:-http://backend:8000}"
if [ -f "./.next/routes-manifest.json" ]; then
  sed -i "s|http://localhost:8000|${TARGET_BACKEND}|g" ./.next/routes-manifest.json
fi

exec "$@"
