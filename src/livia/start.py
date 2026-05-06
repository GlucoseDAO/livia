"""CLI entry points for the Livia website."""

import importlib
import inspect
import shutil
from typing import Any

import typer

from reflex import constants
from reflex.config import get_config
from reflex.reflex import _init, _run
from reflex.utils import console
from reflex.utils import export as export_utils
from reflex.utils.prerequisites import get_web_dir

app = typer.Typer(help="Livia website dev server")
build_app = typer.Typer(help="Build prerendered static files for production")
prod_app = typer.Typer(help="Run the production backend (WebSocket + API only)")


def _run_compat(
    *,
    env: constants.Env,
    frontend: bool,
    backend: bool,
    frontend_port: int | None = None,
    backend_port: int | None = None,
    backend_host: str | None = None,
) -> None:
    """Run Reflex across old/new internal _run signatures."""
    run_params = inspect.signature(_run).parameters
    if "running_mode" in run_params:
        running_mode_class = getattr(
            importlib.import_module("reflex.constants.base"),
            "RunningMode",
        )
        mode_map: dict[tuple[bool, bool], Any] = {
            (False, True): running_mode_class.BACKEND_ONLY,
            (True, False): running_mode_class.FRONTEND_ONLY,
            (True, True): running_mode_class.FULLSTACK,
        }
        mode = mode_map.get((frontend, backend))
        if mode is None:
            raise ValueError(
                "Invalid run mode combination; at least one of frontend/backend must be True."
            )
        _run(
            env=env,
            running_mode=mode,
            frontend_port=frontend_port,
            backend_port=backend_port,
            backend_host=backend_host,
        )
        return

    legacy_kwargs: dict[str, Any] = {"env": env, "frontend": frontend, "backend": backend}
    if "frontend_port" in run_params:
        legacy_kwargs["frontend_port"] = frontend_port
    if "backend_port" in run_params:
        legacy_kwargs["backend_port"] = backend_port
    if "backend_host" in run_params:
        legacy_kwargs["backend_host"] = backend_host
    _run(**legacy_kwargs)


@app.command()
def start(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting"),
    loglevel: str = typer.Option("info", help="Log level"),
) -> None:
    """Initialise and start the dev server."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if init:
        _init(name=get_config().app_name)
    config = get_config()
    _run_compat(
        env=constants.Env.DEV,
        frontend=True,
        backend=True,
        frontend_port=config.frontend_port,
        backend_port=config.backend_port,
        backend_host=config.backend_host,
    )


def _clean_build_cache() -> None:
    """Remove stale Vite / React-Router caches so the next build is fully fresh."""
    web = get_web_dir()
    for path in [
        web / "node_modules" / ".vite",
        web / ".react-router",
        web / "build",
    ]:
        if path.exists():
            shutil.rmtree(path)
            console.print(f"Cleaned {path}")


@build_app.command()
def build(
    loglevel: str = typer.Option("info", help="Log level"),
    clean: bool = typer.Option(True, help="Remove Vite/React-Router caches before building"),
) -> None:
    """Export prerendered static HTML + assets to .web/build/client/."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if clean:
        _clean_build_cache()
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
    config = get_config()
    _run_compat(
        env=constants.Env.PROD,
        frontend=False,
        backend=True,
        backend_port=config.backend_port,
        backend_host=config.backend_host,
    )


serve_app = typer.Typer(help="Run full production server (frontend + backend). Use when Caddy is not set up for file_server yet.")


@serve_app.command()
def serve(
    init: bool = typer.Option(True, help="Run 'reflex init' before starting"),
    loglevel: str = typer.Option("info", help="Log level"),
    port: int | None = typer.Option(
        None,
        "--port",
        "-p",
        help="Production fullstack port. Defaults to PORT from .env/environment.",
    ),
) -> None:
    """Start both frontend and backend on the configured frontend port in production mode."""
    console.set_log_level(constants.LogLevel.from_string(loglevel))
    if init:
        _init(name=get_config().app_name)
    config = get_config()
    serve_port = port or config.frontend_port
    # Reflex production fullstack runs the static server and backend on one port.
    _run_compat(
        env=constants.Env.PROD,
        frontend=True,
        backend=True,
        frontend_port=serve_port,
        backend_port=serve_port,
        backend_host=config.backend_host,
    )


if __name__ == "__main__":
    app()
