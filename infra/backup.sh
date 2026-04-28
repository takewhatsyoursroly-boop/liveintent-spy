#!/usr/bin/env bash
# Nightly Postgres dump + upload to Backblaze B2.
# Requires: B2_KEY_ID, B2_APP_KEY, B2_BUCKET in /opt/liveintent-spy/.env
set -euo pipefail

source /opt/liveintent-spy/.env

DATE=$(date +%Y%m%d)
DUMP=/tmp/liveintent-${DATE}.sql.gz

sudo -u postgres pg_dump -d liveintent | gzip > "$DUMP"

# Upload via b2 CLI (install once: pip install b2)
b2 authorize-account "$B2_KEY_ID" "$B2_APP_KEY" >/dev/null
b2 upload-file "$B2_BUCKET" "$DUMP" "backups/$(basename "$DUMP")"

# Keep last 7 days locally
find /tmp -name 'liveintent-*.sql.gz' -mtime +7 -delete

echo "Backup uploaded: backups/$(basename "$DUMP")"
