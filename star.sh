#!/usr/bin/env bash
# Compatibility alias; use start.sh for new deployments.
exec bash "$(dirname "$0")/start.sh" "$@"
