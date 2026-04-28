# Infra

## First deploy

1. Provision a Hetzner CX22 (Ubuntu 24.04).
2. Copy `deploy.sh` to the box, run as root.
3. Edit `/opt/liveintent-spy/.env` with real values (DATABASE_URL points to the local Postgres; replace `CHANGEME`).
4. `systemctl restart scraper-worker enrichment-worker`.
5. Verify: `journalctl -u scraper-worker -f`.

## Backups

Cron entry (`crontab -e` as root):

```
0 3 * * * /opt/liveintent-spy/infra/backup.sh
```

## Updates

```
cd /opt/liveintent-spy
sudo -u liveintent git pull
sudo -u liveintent ~/.local/bin/uv sync
sudo -u liveintent ~/.local/bin/uv run alembic -c packages/shared/alembic.ini upgrade head
systemctl restart scraper-worker enrichment-worker
```
