import click
from sqlalchemy import select
from liveintent_shared.db import session_scope
from liveintent_shared.models import Publisher

@click.command("add-publisher")
@click.argument("domain")
@click.option("--email", required=True, help="Catch-all alias subscribed to this publisher")
@click.option("--name", default=None)
def add_publisher(domain: str, email: str, name: str | None):
    """Register a publisher and its seed email alias."""
    with session_scope() as s:
        existing = s.scalar(select(Publisher).where(Publisher.domain == domain))
        if existing:
            click.echo(f"Publisher {domain} already exists (id={existing.id})")
            return
        p = Publisher(domain=domain, name=name, seed_email_address=email)
        s.add(p); s.flush()
        click.echo(f"Created publisher {domain} (id={p.id}). Subscribe {email} to the newsletter and confirm double-opt-in.")

@click.command("list-publishers")
def list_publishers():
    with session_scope() as s:
        rows = s.scalars(select(Publisher).order_by(Publisher.domain)).all()
        for p in rows:
            click.echo(f"{p.domain:30s}  {p.seed_email_address:40s}  active={p.active}")
