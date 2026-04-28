import click
from .publishers import add_publisher, list_publishers

@click.group()
def cli():
    """LiveIntent Spy admin CLI."""
    pass

cli.add_command(add_publisher)
cli.add_command(list_publishers)

if __name__ == "__main__":
    cli()
