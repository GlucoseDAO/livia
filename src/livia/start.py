"""CLI entry point for the Livia website."""

import typer

from reflex import constants
from reflex.config import get_config
from reflex.reflex import _init, _run
from reflex.utils import console

app = typer.Typer(help="Livia website CLI")


@app.command()
def start(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting the server"),
    loglevel: str = typer.Option("info", help="Reflex log level"),
) -> None:
    """Initialise the Reflex project and start the dev server."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if init:
        _init(name=get_config().app_name)
    _run()


if __name__ == "__main__":
    app()
