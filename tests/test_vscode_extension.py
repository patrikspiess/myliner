"""
Tests for the VS Code extension metadata and static assets.
"""

import json
from pathlib import Path
from xml.etree import ElementTree

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXTENSION_ROOT = PROJECT_ROOT / "vscode-extension"


def read_extension_asset(file_name: str) -> str:
    """
    Read one VS Code extension asset as UTF-8 text.
    """

    return (EXTENSION_ROOT / file_name).read_text(encoding="utf-8")


def test_vscode_extension_contributes_explorer_webview() -> None:
    """
    It contributes a small Webview inside the existing Explorer.
    """

    package = json.loads(read_extension_asset("package.json"))

    assert package["main"] == "./extension.js"
    assert "keybindings" not in package["contributes"]
    assert "viewsContainers" not in package["contributes"]
    assert package["contributes"]["views"] == {
        "explorer": [
            {
                "type": "webview",
                "id": "myliner.sidebar",
                "name": "Myliner",
                "icon": "media/myliner.svg",
            }
        ]
    }
    assert "onView:myliner.sidebar" in package["activationEvents"]


def test_vscode_extension_exposes_menu_commands() -> None:
    """
    It exposes all runtime controls as VS Code menu commands.
    """

    package = json.loads(read_extension_asset("package.json"))
    command_ids = {command["command"] for command in package["contributes"]["commands"]}

    assert command_ids == {
        "myliner.showPanel",
        "myliner.addLine",
        "myliner.removeLine",
        "myliner.speedUp",
        "myliner.speedDown",
    }
    assert all(
        "icon" in command
        for command in package["contributes"]["commands"]
        if command["command"] != "myliner.showPanel"
    )
    title_menu = package["contributes"]["menus"]["view/title"]

    assert [item["command"] for item in title_menu] == [
        "myliner.removeLine",
        "myliner.addLine",
        "myliner.speedDown",
        "myliner.speedUp",
    ]
    assert all(menu_item["command"] in command_ids for menu_item in title_menu)
    assert all(menu_item["when"] == "view == myliner.sidebar" for menu_item in title_menu)
    assert [item["group"] for item in title_menu] == [
        "navigation@1",
        "navigation@2",
        "navigation@3",
        "navigation@4",
    ]


def test_vscode_extension_uses_web_component_without_keyboard_controls() -> None:
    """
    It embeds the shared overlay and disables in-webview keyboard shortcuts.
    """

    source = read_extension_asset("extension.js")

    assert "vscode.window.registerWebviewViewProvider" in source
    assert "vscode.window.createWebviewPanel" not in source
    assert "myliner.sidebar.focus" not in source
    assert "`${VIEW_TYPE}.focus`" in source
    assert 'media", "myliner-web.js"' in source
    assert 'keyboard-controls="false"' in source
    assert 'click-to-stop="false"' in source
    assert "background: var(--vscode-sideBar-background, transparent);" in source
    assert "frameless" in source
    assert "transparent-background" in source
    assert 'lines="2"' in source
    assert 'speed="10"' in source
    assert 'thickness="1"' in source
    assert 'offset-min="1"' in source
    assert 'offset-max="10"' in source
    assert 'vscodeApi.postMessage({ type: "ready" });' in source
    assert "overlay.speedUp();" in source
    assert "overlay.toggleHelp();" not in source
    assert "overlay.toggleFullscreen();" not in source
    assert "overlay.start();" not in source
    assert "overlay.stop();" not in source


def test_vscode_extension_web_component_matches_browser_demo() -> None:
    """
    It keeps the VS Code view animation code in sync with the browser demo.
    """

    demo_source = (PROJECT_ROOT / "demo" / "myliner-web.js").read_text(encoding="utf-8")
    extension_source = read_extension_asset("media/myliner-web.js")

    assert extension_source == demo_source


def test_vscode_extension_icon_uses_straight_lines() -> None:
    """
    It renders the Myliner icon without curved path segments.
    """

    icon = ElementTree.parse(EXTENSION_ROOT / "media" / "myliner.svg").getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    assert len(icon.findall("svg:polyline", namespace)) == 2
    assert not icon.findall("svg:path", namespace)
