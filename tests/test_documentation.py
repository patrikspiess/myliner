"""
Tests for documentation assets.
"""

from pathlib import Path
from xml.etree import ElementTree

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_core_diagram_contains_editable_drawio_model() -> None:
    """
    The rendered SVG embeds a complete diagrams.net model for editing.
    """

    svg_root = ElementTree.parse(PROJECT_ROOT / "docs" / "myliner-core.drawio.svg").getroot()
    drawio_content = svg_root.attrib["content"]
    mxfile = ElementTree.fromstring(drawio_content)
    graph_model = mxfile.find("./diagram/mxGraphModel")

    assert mxfile.tag == "mxfile"
    assert graph_model is not None

    cells = graph_model.findall("./root/mxCell")
    assert {cell.attrib["id"] for cell in cells if cell.attrib.get("vertex") == "1"} >= {
        "settings",
        "engine",
        "state",
        "step",
        "rasterize",
        "pixels",
        "history",
        "movement",
        "controls",
    }
    assert sum(cell.attrib.get("edge") == "1" for cell in cells) == 10
