import json
import sys
import click
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Advertiser, Creative, Impression

@click.command("export")
@click.option("--days", default=30, type=int)
@click.option("--out", default="-", help="Output file or '-' for stdout")
def export(days: int, out: str):
    """Export advertiser/creative/impression data as JSON."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    with session_scope() as s:
        advs = s.scalars(select(Advertiser).where(Advertiser.last_seen_at >= since)).all()
        result = []
        for a in advs:
            creatives = s.scalars(select(Creative).where(Creative.advertiser_id == a.id)).all()
            result.append({
                "domain": a.domain, "vertical": a.vertical, "vertical_source": a.vertical_source,
                "first_seen_at": a.first_seen_at.isoformat(),
                "creatives": [
                    {"hash": c.creative_hash, "headline": c.headline,
                     "final_landing_url": c.final_landing_url}
                    for c in creatives
                ],
            })
    payload = json.dumps(result, indent=2)
    if out == "-":
        sys.stdout.write(payload)
    else:
        from pathlib import Path
        Path(out).write_text(payload)
        click.echo(f"Wrote {len(result)} advertisers to {out}")
