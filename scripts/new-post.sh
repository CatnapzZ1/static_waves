#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
slug=${1:?Usage: scripts/new-post.sh lowercase-slug}
[[ $slug =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || { echo 'Invalid slug' >&2; exit 1; }
[[ ! -e "content/posts/$slug" ]] || { echo 'Bundle already exists; refusing overwrite' >&2; exit 1; }
exec hugo new content --kind posts "posts/$slug/index.md"
