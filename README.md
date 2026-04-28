# liveintent-spy

LiveIntent ad spy tool — subscribes to publisher newsletters, parses LiveIntent ad slots out of rendered emails, classifies advertisers by vertical, and surfaces top advertisers via Telegram digest + Next.js dashboard.

Design spec: `docs/superpowers/specs/2026-04-27-liveintent-spy-design.md` (in parent project).

## Local development

```bash
cp .env.example .env  # edit values
docker compose up -d  # local Postgres
uv sync
uv run playwright install chromium
uv run alembic -c packages/shared/alembic.ini upgrade head
uv run pytest

# Run a worker locally
uv run python -m liveintent_scraper.main
uv run python -m liveintent_enrichment.main

# Run API
uv run uvicorn liveintent_api.main:app --reload

# Run web
cd apps/web && pnpm dev

# Use the CLI
uv run liveintent-spy add-publisher morningbrew.com --email r.alvarez@yourdomain.com
```

## Deploy

- Scraper + enrichment workers + Postgres → Hetzner via `infra/deploy.sh`
- API → Railway (`packages/api/railway.json`)
- Web → Vercel (`apps/web/vercel.ts`)
- Backups → Backblaze B2 nightly via `infra/backup.sh`

See `infra/README.md` for first-deploy details.

## Onboarding a publisher

1. `uv run liveintent-spy add-publisher <domain> --email <alias>@<your-catchall> --name "<Display Name>"`
2. Visit publisher's signup form, enter the alias, complete double-opt-in.
3. Wait for next scraper cycle (~5 min). Check `/health` and `journalctl -u scraper-worker`.

## Daily digest

Cron on Railway hits `POST /digest/run` at 9am UTC. Output sent to Telegram chat configured via `TELEGRAM_CHAT_ID`.

On-demand commands (Telegram):
- `/topadvertisers [days]`
- `/advertiser <domain>`
- `/vertical <name>`
