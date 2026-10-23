#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
./scripts/check-toolchain.sh
./scripts/check-content.sh
# Use a fresh destination for release builds; never publish a stale draft preview.
exec python3 scripts/build.py "$@"
