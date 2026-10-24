#!/usr/bin/env bash
set -Eeuo pipefail
operation=rollback
source "$(dirname "$0")/common.sh"
target=${1:-$(helper previous)}
[[ -n $target ]] || { step 'No previous release available'; exit 1; }
old=$(helper current)
[[ $old != "$target" ]] || { step 'Requested release is already current'; exit 1; }
step "Manual rollback from $old to $target"
activate_release "$target"
health "$target"
success=1
step "SUCCESS rollback to $target"
# Never clean history as a side effect of manual rollback.
