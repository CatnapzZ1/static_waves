#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
# Local tools only; no sudo, system changes, or remote repository writes.
command -v go >/dev/null
command -v curl >/dev/null
command -v python3 >/dev/null
case "$(uname -sm)" in
  'Linux x86_64') platform=linux-amd64 ;;
  'Linux aarch64') platform=linux-arm64 ;;
  *) echo 'Unsupported installer platform; install Hugo Extended 0.145.0 manually.' >&2; exit 1 ;;
esac
mkdir -p .tools .cache/downloads
version=0.145.0
archive="hugo_extended_${version}_${platform}.tar.gz"
base="https://github.com/gohugoio/hugo/releases/download/v$version"
if [[ ! -x .tools/hugo ]]; then
  curl --fail --location --retry 3 "$base/$archive" -o ".cache/downloads/$archive"
  curl --fail --location --retry 3 "$base/hugo_${version}_checksums.txt" -o .cache/downloads/checksums.txt
  (cd .cache/downloads; grep "  $archive\$" checksums.txt | sha256sum --check --strict -)
  tar -xzf ".cache/downloads/$archive" -C .tools hugo
fi
hugo version
go mod download
hugo mod verify
python3 -c 'import yaml; assert yaml.__version__ == "6.0.3", "Install requirements-dev.txt in .venv"'
./scripts/check-toolchain.sh
