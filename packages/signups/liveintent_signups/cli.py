"""CLI for the sign-up automator."""
import asyncio
import json
from pathlib import Path
import click
from liveintent_shared.config import get_settings
from liveintent_shared.logging import configure_logging

from .personas import PERSONAS
from .publishers import PUBLISHERS
from .runner import run_signups


def _imap_kwargs() -> dict:
    s = get_settings()
    return dict(host=s.imap_host, user=s.imap_user, password=s.imap_pass,
                port=s.imap_port, ssl=s.imap_ssl)


@click.group()
def cli() -> None:
    """LiveIntent Spy — newsletter sign-up automator."""
    configure_logging()


@cli.command()
def list_publishers() -> None:
    """List the publishers we'll sign up to."""
    for p in PUBLISHERS:
        click.echo(f"{p.domain:30s}  {p.vertical:10s}  {p.subscribe_url}")


@cli.command()
def list_personas() -> None:
    """List the personas we'll use for sign-ups."""
    for p in PERSONAS:
        click.echo(f"{p.alias:15s}  {p.full_name:20s}  {p.email}")


@cli.command()
@click.option("--publisher", "publishers", multiple=True, help="Restrict to these publisher domains")
@click.option("--persona", "personas", multiple=True, help="Restrict to these persona aliases")
@click.option("--no-doi", is_flag=True, help="Skip the double-opt-in confirmation phase")
@click.option("--out", default="data/signup_results.json", help="Where to write the results JSON")
def run(publishers: tuple[str, ...], personas: tuple[str, ...], no_doi: bool, out: str) -> None:
    """Run sign-ups for the (publishers × personas) matrix."""
    out_path = Path(out)
    results = asyncio.run(run_signups(
        only_publishers=list(publishers) or None,
        only_personas=list(personas) or None,
        confirm_doi_after=not no_doi,
        imap_kwargs=_imap_kwargs(),
        out_path=out_path,
    ))
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    click.echo("")
    click.echo(f"Total: {len(results)}")
    for status, n in sorted(counts.items()):
        click.echo(f"  {status:12s} {n}")
    click.echo(f"\nDetailed results: {out_path}")


@cli.command()
@click.option("--persona", required=True, help="Persona alias whose inbox to poll")
@click.option("--timeout", default=120, type=int, help="How long to wait (seconds)")
def confirm_only(persona: str, timeout: int) -> None:
    """Just poll for confirmation emails for a persona and click their links.
    Useful if `run` was killed mid-DOI."""
    from .personas import by_alias
    from .runner import confirm_doi
    from playwright.async_api import async_playwright

    p = by_alias(persona)
    imap = _imap_kwargs()

    async def go() -> None:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                ctx = await browser.new_context()
                try:
                    visited = await confirm_doi(ctx, p, imap_kwargs=imap, timeout_seconds=timeout)
                    click.echo(f"Clicked {len(visited)} confirm links for {p.email}")
                finally:
                    await ctx.close()
            finally:
                await browser.close()

    asyncio.run(go())


if __name__ == "__main__":
    cli()
