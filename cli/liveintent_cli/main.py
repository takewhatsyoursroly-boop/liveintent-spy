import click
from .publishers import add_publisher, list_publishers
from .advertisers import override_vertical
from .export import export

@click.group()
def cli():
    """LiveIntent Spy admin CLI."""
    pass

for c in (add_publisher, list_publishers, override_vertical, export):
    cli.add_command(c)

if __name__ == "__main__":
    cli()
