#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -n "${CORS_ORIGIN:-}" ]]; then
  exec python -m rasa run --model "${MODEL_PATH:-models/admissions-week4.tar.gz}" --port "${PORT:-5005}" --cors "$CORS_ORIGIN" --endpoints endpoints.yml "$@"
fi
exec python -m rasa run --model "${MODEL_PATH:-models/admissions-week4.tar.gz}" --port "${PORT:-5005}" --endpoints endpoints.yml "$@"
