#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec python -m rasa_sdk --actions actions --port "${ACTION_PORT:-5055}" "$@"
