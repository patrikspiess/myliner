"""
Tests for geometry helpers.
"""

from random import Random

import pytest

from pyliner.geometry import (
    DEFAULT_OFFSET,
    MAX_ANGLE,
    MAX_OFFSET,
    MIN_ANGLE,
    MIN_OFFSET,
    EdgePoint,
    Side,
    calculate_graphics_size,
    random_edge_point_pair,
    rasterize_line,
)


def test_calculate_graphics_size_caps_landscape_long_side() -> None:
    """
    It preserves the aspect ratio for a landscape screen.
    """

    assert calculate_graphics_size(1920, 1080) == (800, 450)


def test_calculate_graphics_size_caps_portrait_long_side() -> None:
    """
    It preserves the aspect ratio for a portrait screen.
    """

    assert calculate_graphics_size(1080, 1920) == (450, 800)


def test_calculate_graphics_size_rejects_invalid_dimensions() -> None:
    """
    It rejects non-positive screen dimensions.
    """

    with pytest.raises(ValueError, match="screen dimensions"):
        calculate_graphics_size(0, 1080)


def test_edge_point_moves_inward_from_border() -> None:
    """
    It moves away from the last touched border.
    """

    point = EdgePoint(side=Side.TOP, x_position=5, y_position=0, angle_degrees=90, offset=5)
    moved_point = point.moved(width=10, height=10, random_generator=Random(0))

    assert moved_point.side is Side.TOP
    assert moved_point.to_xy(10, 10) == (5, 5)
    assert moved_point.angle_degrees == point.angle_degrees
    assert moved_point.offset == point.offset


def test_edge_point_randomizes_angle_and_offset_when_hitting_border() -> None:
    """
    It resets movement settings after reaching a screen border.
    """

    point = EdgePoint(side=Side.RIGHT, x_position=1, y_position=5, angle_degrees=90, offset=5)
    moved_point = point.moved(width=10, height=10, random_generator=Random(0))

    assert moved_point.side is Side.LEFT
    assert moved_point.to_xy(10, 10) == (0, 5)
    assert MIN_ANGLE <= moved_point.angle_degrees <= MAX_ANGLE
    assert MIN_OFFSET <= moved_point.offset <= MAX_OFFSET


def test_edge_point_uses_required_default_offset_range() -> None:
    """
    It validates offsets according to the required movement range.
    """

    point = EdgePoint(side=Side.TOP, x_position=0, y_position=0, angle_degrees=90)

    assert point.offset == DEFAULT_OFFSET

    with pytest.raises(ValueError, match="between 5 and 20"):
        EdgePoint(
            side=Side.TOP,
            x_position=0,
            y_position=0,
            angle_degrees=90,
            offset=MIN_OFFSET - 1,
        )


def test_edge_point_validates_angle_range() -> None:
    """
    It rejects angles outside the required range.
    """

    with pytest.raises(ValueError, match="angle_degrees"):
        EdgePoint(side=Side.TOP, x_position=0, y_position=0, angle_degrees=MIN_ANGLE - 1)


def test_random_edge_point_pair_uses_opposite_sides() -> None:
    """
    It creates endpoints on opposite borders with inward movement settings.
    """

    first_point, second_point = random_edge_point_pair(20, 10, Random(2))

    assert second_point.side is first_point.side.opposite
    assert MIN_ANGLE <= first_point.angle_degrees <= MAX_ANGLE
    assert MIN_ANGLE <= second_point.angle_degrees <= MAX_ANGLE
    assert MIN_OFFSET <= first_point.offset <= MAX_OFFSET
    assert MIN_OFFSET <= second_point.offset <= MAX_OFFSET


def test_rasterize_line_returns_all_pixels_for_diagonal() -> None:
    """
    It rasterizes diagonal lines with both endpoints.
    """

    assert rasterize_line((0, 0), (3, 3)) == ((0, 0), (1, 1), (2, 2), (3, 3))
