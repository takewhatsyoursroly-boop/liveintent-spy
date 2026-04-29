import click
from sqlalchemy import select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Publisher

@click.command("add-publisher")
@click.argument("domain")
@click.option("--from-address", "from_address", required=True,
              help="Sender address used to identify emails from this publisher (e.g. crew@morningbrew.com)")
@click.option("--name", default=None)
@click.option("--seed-email", default=None,
              help="Optional metadata: which catch-all alias is subscribed to this publisher")
def add_publisher(domain: str, from_address: str, name: str | None, seed_email: str | None):
    """Register a publisher with the sender address used to identify its emails."""
    fa = from_address.strip().lower()
    with session_scope() as s:
        existing = s.scalar(select(Publisher).where(Publisher.from_address == fa))
        if existing:
            click.echo(f"Publisher row already exists for {fa} (id={existing.id}, domain={existing.domain})")
            return
        p = Publisher(domain=domain, name=name, from_address=fa, seed_email_address=seed_email)
        s.add(p); s.flush()
        click.echo(f"Created publisher row {domain} (from={fa}, id={p.id}).")

@click.command("list-publishers")
def list_publishers():
    with session_scope() as s:
        rows = s.scalars(select(Publisher).order_by(Publisher.domain)).all()
        for p in rows:
            click.echo(f"{p.domain:30s}  from={(p.from_address or '?'):35s}  active={p.active}  name={p.name or ''}")
