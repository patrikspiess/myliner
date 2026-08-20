"""
Tests for the local browser demo server.
"""

from pathlib import Path

import pytest

from myliner import demo_server


def test_find_project_root_finds_demo_directory(tmp_path: Path) -> None:
    """
    It finds the nearest parent containing the demo index page.
    """

    project_root = tmp_path / "project"
    nested_path = project_root / "src" / "myliner"
    demo_path = project_root / "demo"
    nested_path.mkdir(parents=True)
    demo_path.mkdir()
    (demo_path / "index.html").write_text("<!doctype html>", encoding="utf-8")

    assert demo_server.find_project_root(nested_path) == project_root


def test_find_project_root_rejects_missing_demo(tmp_path: Path) -> None:
    """
    It raises a clear error when the demo page cannot be found.
    """

    with pytest.raises(FileNotFoundError, match="demo/index.html"):
        demo_server.find_project_root(tmp_path)


def test_create_server_uses_requested_address(tmp_path: Path) -> None:
    """
    It creates a static server for the requested local address.
    """

    server = demo_server.create_server("127.0.0.1", 0, tmp_path)

    try:
        assert server.server_address[0] == "127.0.0.1"
        assert server.server_address[1] > 0
    finally:
        server.server_close()
