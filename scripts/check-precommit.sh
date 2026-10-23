#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
python3 scripts/validate.py staged
