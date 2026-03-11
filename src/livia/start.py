"""CLI entry point for the Livia website."""

import subprocess
import sys

import typer

app = typer.Typer(help="Livia website CLI")


@app.command()
def start(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting the server"),
    loglevel: str = typer.Option("info", help="Reflex log level"),
) -> None:
    """Initialise the Reflex project (if requested) and start the dev server."""
    if init:
        subprocess.check_call([sys.executable, "-m", "reflex", "init"])
    subprocess.check_call([sys.executable, "-m", "reflex", "run", "--loglevel", loglevel])


if __name__ == "__main__":
    app()
