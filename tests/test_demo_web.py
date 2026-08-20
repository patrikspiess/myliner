"""
Tests for the static browser demo assets.
"""

from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1] / "demo"


def read_demo_asset(file_name: str) -> str:
    """
    Read one demo asset as UTF-8 text.
    """

    return (DEMO_ROOT / file_name).read_text(encoding="utf-8")


def test_web_component_keeps_default_orange_without_lighter_compositing() -> None:
    """
    It keeps the base line color orange instead of using additive yellow compositing.
    """

    source = read_demo_asset("myliner-web.js")

    assert "const DEFAULT_COLOR = [255, 102, 0];" in source
    assert '"lighter"' not in source
    assert "globalCompositeOperation" not in source


def test_web_component_uses_explicit_framebuffer_fading() -> None:
    """
    It fades the explicit pixel framebuffer back to black.
    """

    source = read_demo_asset("myliner-web.js")

    assert "this.context.createImageData(this.width, this.height)" in source
    assert "this.context.putImageData(this.imageData, 0, 0)" in source
    assert "fadeFrameBuffer()" in source
    assert "Math.max(0, this.pixelBuffer[index] - fadeStep)" in source


def test_web_component_help_uses_real_newline_characters() -> None:
    """
    It joins help lines with newline characters rather than visible backslash-n text.
    """

    source = read_demo_asset("myliner-web.js")

    assert 'helpLines.join("\\n");' in source
    assert '].join("\\\\n");' not in source


def test_web_component_can_disable_click_to_stop() -> None:
    """
    It keeps click-to-stop enabled by default but allows embedded views to disable it.
    """

    source = read_demo_asset("myliner-web.js")

    assert "if (this.clickToStop)" in source
    assert 'this.getAttribute("click-to-stop") !== "false"' in source
    assert 'this.clickToStop ? "Esc/click: quit" : "Esc: quit"' in source


def test_web_component_supports_compact_transparent_embedding() -> None:
    """
    It supports transparent fading, no frame, and configurable endpoint offsets.
    """

    source = read_demo_asset("myliner-web.js")

    assert ":host([frameless]) canvas" in source
    assert ":host([transparent-background]) canvas" in source
    assert 'this.hasAttribute("transparent-background")' in source
    assert 'this.getAttribute("offset-min")' in source
    assert 'this.getAttribute("offset-max")' in source
    assert "this.pixelBuffer[index + 3] - fadeStep" in source


def test_web_component_uses_fibonacci_speed_controls_without_fixed_cap() -> None:
    """
    It changes speed on the Fibonacci sequence and does not cap it at 1000.
    """

    source = read_demo_asset("myliner-web.js")

    assert "function nextFibonacciSpeed(speed)" in source
    assert "function previousFibonacciSpeed(speed)" in source
    assert "this.speed = nextFibonacciSpeed(this.speed);" in source
    assert "this.speed = previousFibonacciSpeed(this.speed);" in source
    assert "MAX_SPEED" not in source
    assert "SPEED_STEP" not in source
    assert '"q/a: line count"' in source


def test_web_component_toggles_browser_and_component_fullscreen() -> None:
    """
    It toggles browser fullscreen together with component fullscreen layout.
    """

    source = read_demo_asset("myliner-web.js")

    assert "toggleFullscreen()" in source
    assert "this.requestFullscreen?.();" in source
    assert "document.exitFullscreen?.();" in source
    assert ":host([fullscreen]) canvas" in source
    assert '"f: fullscreen"' in source


def test_demo_page_documents_runtime_fullscreen_key() -> None:
    """
    It shows the fullscreen runtime key in the React demo copy.
    """

    source = read_demo_asset("index.html")

    assert 'React.createElement("code", null, "f")' in source
    assert '" for fullscreen. Press "' in source
