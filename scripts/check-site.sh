#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
./scripts/check-toolchain.sh
hugo mod verify
./scripts/check-content.sh
python3 scripts/test-quality.py
python3 scripts/test-site.py
python3 scripts/test-deploy.py
while IFS= read -r -d '' file; do bash -n "$file"; done < <(find scripts deploy .githooks -type f \( -name '*.sh' -o -name pre-commit \) -print0)
node --check assets/js/math.js
node --input-type=module --check < assets/js/mermaid.js
printf '%s\n' 'PASS 本地统一检查完成；素材与上线条件另见 check-launch-readiness.sh'
