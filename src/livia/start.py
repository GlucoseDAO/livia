"""CLI entry points for the Livia website."""

import typer

from reflex import constants
from reflex.config import get_config
from reflex.reflex import _init, _run
from reflex.utils import console
from reflex.utils import export as export_utils

app = typer.Typer(help="Livia website dev server")
build_app = typer.Typer(help="Build prerendered static files for production")
prod_app = typer.Typer(help="Run the production backend (WebSocket + API only)")


@app.command()
def start(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting"),
    loglevel: str = typer.Option("info", help="Log level"),
) -> None:
    """Initialise and start the dev server."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if init:
        _init(name=get_config().app_name)
    _run()


@build_app.command()
def build(
    loglevel: str = typer.Option("info", help="Log level"),
) -> None:
    """Export prerendered static HTML + assets to .web/build/client/."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    _init(name=get_config().app_name)
    export_utils.export(
        zipping=False,
        frontend=True,
        backend=False,
        env=constants.Env.PROD,
        loglevel=constants.LogLevel.from_string(loglevel),
    )


@prod_app.command()
def prod(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting"),
    loglevel: str = typer.Option("info", help="Log level"),
) -> None:
    """Start the production backend only (port 3011). Requires Caddy serving .web/build/client/."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if init:
        _init(name=get_config().app_name)
    _run(env=constants.Env.PROD, frontend=False, backend=True)


serve_app = typer.Typer(help="Run full production server (frontend + backend). Use when Caddy is not set up for file_server yet.")


@serve_app.command()
def serve(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting"),
    loglevel: str = typer.Option("info", help="Log level"),
) -> None:
    """Start both frontend (port 3010) and backend (port 3011) in production mode."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if init:
        _init(name=get_config().app_name)
    _run(env=constants.Env.PROD, frontend=True, backend=True)


if __name__ == "__main__":
    app()
