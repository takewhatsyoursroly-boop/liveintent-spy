# liveintent-spy

LiveIntent ad spy tool. See `docs/superpowers/specs/2026-04-27-liveintent-spy-design.md` in the parent project for design.

## Quick start

```
cp .env.example .env       # edit values
docker compose up -d       # local Postgres
uv sync
uv run alembic -c packages/shared/alembic.ini upgrade head
uv run python -m liveintent_scraper.main
```
