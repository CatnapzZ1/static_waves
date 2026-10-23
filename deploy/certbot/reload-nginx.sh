#!/usr/bin/env bash
set -euo pipefail
# Root-owned Certbot deploy hook; invoked only after successful issuance/renewal.
/usr/sbin/nginx -t
/usr/bin/systemctl reload nginx
