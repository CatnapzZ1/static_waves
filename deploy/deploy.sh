#!/usr/bin/env bash
set -Eeuo pipefail
operation=deploy
source "$(dirname "$0")/common.sh"
step 'Checking source repository and fast-forwarding main'
cd "$BLOG_SOURCE"
[[ $(git rev-parse --show-toplevel) == "$BLOG_SOURCE" ]] || exit 1
[[ $(git symbolic-ref --short HEAD) == main ]] || { step 'Expected main branch'; exit 1; }
[[ -z $(git status --porcelain) ]] || { step 'Source tree is not clean'; exit 1; }
[[ $(git remote get-url origin) == "$BLOG_REPOSITORY" ]] || { step 'Repository origin mismatch'; exit 1; }
git fetch --prune origin main
git merge --ff-only origin/main
source scripts/env.sh
./scripts/check-toolchain.sh
hugo mod verify
./scripts/check-content.sh
python3 scripts/check-launch.py --config-only
[[ -z $(git status --porcelain) ]] || { step 'Dependency files changed; review locally first'; exit 1; }
release_id="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short=12 HEAD)-$(python3 -c 'import secrets; print(secrets.token_hex(4))')"
release=$(helper create "$release_id")
step "Building release $release_id"
./scripts/build.sh --destination "$release"
python3 scripts/validate.py output "$release" "https://$BLOG_DOMAIN/" --strict-branding
python3 - "$BLOG_DOMAIN" <<'PY'
import sys,yaml
c=yaml.safe_load(open('hugo.yaml'))
assert c['baseURL']=='https://'+sys.argv[1]+'/', 'baseURL must match configured domain exactly'
PY
[[ -z $(git status --porcelain) ]] || { step 'Build changed tracked source'; exit 1; }
helper ready "$release_id"
old=$(helper current)
# Set guard before switch so interrupted activation is also recoverable.
activated=1
helper activate "$release_id"
step 'Checking HTTPS against local Nginx origin with certificate verification'
health "$release_id"
success=1
step "SUCCESS activated $release_id; previous=${old:-none}"
# Cleanup only after all critical health checks; failure is a warning.
helper cleanup || step 'WARNING cleanup failed; active website retained'
