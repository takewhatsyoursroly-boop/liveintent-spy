#!/usr/bin/env bash
# Run on a fresh Hetzner Ubuntu 24.04 box, as root.
set -euo pipefail

apt-get update
apt-get install -y postgresql-16 tesseract-ocr git curl python3.12 python3.12-venv

# Postgres
sudo -u postgres psql <<EOF
CREATE USER liveintent WITH PASSWORD 'CHANGEME';
CREATE DATABASE liveintent OWNER liveintent;
EOF

# App user
useradd -m -s /bin/bash liveintent || true

# Code
sudo -u liveintent bash <<'EOF'
cd /home/liveintent
git clone https://github.com/<your-github>/liveintent-spy.git || (cd liveintent-spy && git pull)
cd liveintent-spy
curl -LsSf https://astral.sh/uv/install.sh | sh
~/.local/bin/uv sync
~/.local/bin/uv run playwright install --with-deps chromium
EOF

# Symlink to /opt for systemd
ln -sfn /home/liveintent/liveintent-spy /opt/liveintent-spy

# Write .env (operator must edit)
[ -f /opt/liveintent-spy/.env ] || cp /opt/liveintent-spy/.env.example /opt/liveintent-spy/.env
chown liveintent:liveintent /opt/liveintent-spy/.env
chmod 600 /opt/liveintent-spy/.env

# Migrations
sudo -u liveintent bash -c "cd /opt/liveintent-spy && ~/.local/bin/uv run alembic -c packages/shared/alembic.ini upgrade head"

# systemd
cp /opt/liveintent-spy/infra/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable scraper-worker.service enrichment-worker.service
systemctl restart scraper-worker.service enrichment-worker.service

echo "Done. Edit /opt/liveintent-spy/.env, then 'systemctl restart scraper-worker enrichment-worker'."
