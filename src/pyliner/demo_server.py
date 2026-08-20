"""
Local static web server for the Pyliner browser demo.
"""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence

DEFAULT_DEMO_PORT = 8000


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the demo server command line argument parser.
    """

    parser = argparse.ArgumentParser(description="Serve the Pyliner browser demo locally.")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the local demo server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_DEMO_PORT,
        help="Port for the local demo server.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Optional repository root containing the demo directory.",
    )
    return parser


def find_project_root(start_path: Path | None = None) -> Path:
    """
    Find a project root containing the demo index page.
    """

    current_path = (start_path or Path.cwd()).resolve()
    candidates = (current_path, *current_path.parents)

    for candidate in candidates:
        if (candidate / "demo" / "index.html").is_file():
            return candidate

    raise FileNotFoundError("Could not find demo/index.html from the current directory.")


def create_server(host: str, port: int, project_root: Path) -> ThreadingHTTPServer:
    """
    Create a static HTTP server rooted at the project directory.
    """

    handler = partial(SimpleHTTPRequestHandler, directory=str(project_root))
    return ThreadingHTTPServer((host, port), handler)


def main(argv: Sequence[str] | None = None) -> None:
    """
    Run the local static demo web server.
    """

    arguments = build_argument_parser().parse_args(argv)
    project_root = find_project_root(arguments.root)
    server = create_server(arguments.host, arguments.port, project_root)
    demo_url = f"http://{arguments.host}:{arguments.port}/demo/index.html"

    print(f"Serving Pyliner demo at {demo_url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
