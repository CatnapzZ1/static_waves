#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
exec hugo server --renderToMemory --environment development --bind 127.0.0.1 "$@"
