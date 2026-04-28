import click
from datetime import datetime, timezone
from sqlalchemy import select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Advertiser
from liveintent_shared.enums import Vertical, VerticalSource

@click.command("override-vertical")
@click.argument("domain")
@click.argument("vertical")
def override_vertical(domain: str, vertical: str):
    """Set advertiser vertical manually (sticky)."""
    valid = [v.value for v in Vertical]
    if vertical not in valid:
        click.echo(f"Invalid vertical. Choose: {', '.join(valid)}", err=True)
        raise click.Abort()
    with session_scope() as s:
        a = s.scalar(select(Advertiser).where(Advertiser.domain == domain))
        if not a:
            click.echo(f"Advertiser {domain} not found", err=True)
            raise click.Abort()
        a.vertical = vertical
        a.vertical_source = VerticalSource.MANUAL.value
        a.vertical_classified_at = datetime.now(timezone.utc)
    click.echo(f"Set {domain} → {vertical} (manual)")
