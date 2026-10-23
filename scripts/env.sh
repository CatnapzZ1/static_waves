#!/usr/bin/env bash
# Source from project scripts; caches remain inside this checkout.
BLOG_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export PATH="$BLOG_ROOT/.tools:$BLOG_ROOT/.venv/bin:$PATH"
export GOMODCACHE="$BLOG_ROOT/.cache/go-mod"
export GOCACHE="$BLOG_ROOT/.cache/go-build"
export HUGO_CACHEDIR="$BLOG_ROOT/.cache/hugo"
export GOTOOLCHAIN=local
cd "$BLOG_ROOT"
