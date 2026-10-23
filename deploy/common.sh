#!/usr/bin/env bash
# Installed with deploy.sh/rollback.sh/releases.py in /opt/blog/scripts/.
set -Eeuo pipefail
umask 022
[[ $EUID -ne 0 ]] || { echo 'Use the existing ordinary SSH user, not root.' >&2; exit 1; }
[[ -f /opt/blog/deploy.env ]] || { echo 'Missing /opt/blog/deploy.env' >&2; exit 1; }
# Administrator-owned/local trusted shell configuration, never sourced from Git.
source /opt/blog/deploy.env
: "${BLOG_DOMAIN:?Set real root domain}"
: "${BLOG_REPOSITORY:?Set real git@github.com:owner/repository.git}"
[[ $BLOG_DOMAIN =~ ^[A-Za-z0-9][A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]] || exit 1
[[ $BLOG_DOMAIN != *example.com* && $BLOG_DOMAIN != *.invalid && $BLOG_DOMAIN != *..* ]] || exit 1
[[ $BLOG_REPOSITORY =~ ^git@github.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$ ]] || exit 1
BLOG_SOURCE=/opt/blog/source
BLOG_LOGS=/opt/blog/logs
BLOG_HELPER=/opt/blog/scripts/releases.py
[[ -d $BLOG_LOGS && -w $BLOG_LOGS ]] || exit 1
exec 9>"$BLOG_LOGS/deployment.lock"
flock -n 9 || { echo 'Another deployment/rollback is active.' >&2; exit 1; }
log="$BLOG_LOGS/${operation}-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
exec > >(tee -a "$log") 2>&1
step() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*"; }
helper() { python3 "$BLOG_HELPER" "$@"; }
health() {
  local expected=$1 actual path
  actual=$(curl --fail --silent --show-error --max-time 15 --retry 2 --resolve "$BLOG_DOMAIN:443:127.0.0.1" "https://$BLOG_DOMAIN/release-id.txt") || return 1
  [[ $actual == "$expected" ]] || { step 'Release ID mismatch'; return 1; }
  for path in / /search/ /index.json /index.xml /sitemap.xml /favicon.ico /images/site/logo.png /images/site/avatar.webp; do
    curl --fail --silent --show-error --max-time 15 --retry 2 --resolve "$BLOG_DOMAIN:443:127.0.0.1" "https://$BLOG_DOMAIN$path" -o /dev/null || return 1
  done
}
old=''
activated=0
success=0
finish() {
  status=$?
  trap - EXIT INT TERM
  if [[ $success == 0 && $activated == 1 ]]; then
    step "Failure; restoring previous release: ${old:-none}"
    if helper restore "$old"; then
      if [[ -n $old ]]; then health "$old" || step 'WARNING restored release also needs manual health diagnosis'; fi
    else
      step 'CRITICAL automatic rollback failed; inspect current symlink manually'
    fi
  fi
  [[ $success == 1 ]] || { step "FAILED; log: $log"; status=1; }
  exit "$status"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
