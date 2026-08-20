"""
Geometry primitives for moving lines through a screen-sized canvas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import cos, radians, sin
from random import Random

DEFAULT_OFFSET = 5
MIN_OFFSET = 5
MAX_OFFSET = 20
MAX_LONG_SIDE = 800
MIN_ANGLE = 15
MAX_ANGLE = 165


class Side(StrEnum):
    """
    Screen border side.
    """

    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"

    @property
    def opposite(self) -> "Side":
        """
        Return the opposing screen side.
        """

        if self is Side.TOP:
            return Side.BOTTOM
        if self is Side.RIGHT:
            return Side.LEFT
        if self is Side.BOTTOM:
            return Side.TOP
        return Side.RIGHT


@dataclass(frozen=True, slots=True)
class EdgePoint:
    """
    Represent a moving point that starts at and bounces away from screen borders.
    """

    side: Side
    x_position: float
    y_position: float
    angle_degrees: int
    offset: int = DEFAULT_OFFSET

    def __post_init__(self) -> None:
        """
        Validate movement settings.
        """

        if not MIN_ANGLE <= self.angle_degrees <= MAX_ANGLE:
            raise ValueError("angle_degrees must be between 15 and 165")
        if not MIN_OFFSET <= self.offset <= MAX_OFFSET:
            raise ValueError("offset must be between 5 and 20")

    def to_xy(self, width: int, height: int) -> tuple[int, int]:
        """
        Convert the edge point to screen coordinates.

        Args:
            width: Canvas width in pixels.
            height: Canvas height in pixels.

        Returns:
            A tuple with x and y coordinates.
        """

        return (
            _clamp(self.x_position, 0, width - 1),
            _clamp(self.y_position, 0, height - 1),
        )

    def moved(self, width: int, height: int, random_generator: Random) -> "EdgePoint":
        """
        Move the point through the canvas.

        Args:
            width: Canvas width in pixels.
            height: Canvas height in pixels.
            random_generator: Random number generator used after hitting a border.

        Returns:
            A new edge point after movement.
        """

        delta_x, delta_y = _movement_delta(self.side, self.angle_degrees, self.offset)
        next_x = self.x_position + delta_x
        next_y = self.y_position + delta_y
        hit_side = _hit_side(next_x, next_y, width, height)

        if hit_side is None:
            return EdgePoint(
                side=self.side,
                x_position=next_x,
                y_position=next_y,
                angle_degrees=self.angle_degrees,
                offset=self.offset,
            )

        return EdgePoint(
            side=hit_side,
            x_position=_clamp(next_x, 0, width - 1),
            y_position=_clamp(next_y, 0, height - 1),
            angle_degrees=random_generator.randint(MIN_ANGLE, MAX_ANGLE),
            offset=random_generator.randint(MIN_OFFSET, MAX_OFFSET),
        )


@dataclass(frozen=True, slots=True)
class LineFrame:
    """
    Capture one rendered line between two edge points.
    """

    start: EdgePoint
    end: EdgePoint
    pixels: tuple[tuple[int, int], ...]


def calculate_graphics_size(
    screen_width: int,
    screen_height: int,
    max_long_side: int = MAX_LONG_SIDE,
) -> tuple[int, int]:
    """
    Calculate a graphics size preserving the monitor aspect ratio.

    Args:
        screen_width: Native screen width in pixels.
        screen_height: Native screen height in pixels.
        max_long_side: Maximum size of the long side.

    Returns:
        A tuple with width and height capped at the long side.

    Raises:
        ValueError: If a dimension or max_long_side is smaller than one.
    """

    if screen_width < 1 or screen_height < 1:
        raise ValueError("screen dimensions must be positive")
    if max_long_side < 1:
        raise ValueError("max_long_side must be positive")

    if screen_width >= screen_height:
        width = min(screen_width, max_long_side)
        height = max(1, round(width * screen_height / screen_width))
        return width, height

    height = min(screen_height, max_long_side)
    width = max(1, round(height * screen_width / screen_height))
    return width, height


def random_edge_point_pair(
    width: int,
    height: int,
    random_generator: Random,
) -> tuple[EdgePoint, EdgePoint]:
    """
    Create two edge points on opposite sides of the canvas.

    Args:
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        random_generator: Random number generator used for placement.

    Returns:
        A tuple containing two points on opposite screen sides.
    """

    first_side = random_generator.choice((Side.TOP, Side.RIGHT, Side.BOTTOM, Side.LEFT))
    second_side = first_side.opposite

    return (
        _random_edge_point(first_side, width, height, random_generator),
        _random_edge_point(second_side, width, height, random_generator),
    )


def rasterize_line(
    start: tuple[int, int],
    end: tuple[int, int],
) -> tuple[tuple[int, int], ...]:
    """
    Return all integer pixels on a line using Bresenham rasterization.

    Args:
        start: Start coordinate.
        end: End coordinate.

    Returns:
        A tuple of x and y coordinates.
    """

    start_x, start_y = start
    end_x, end_y = end
    delta_x = abs(end_x - start_x)
    step_x = 1 if start_x < end_x else -1
    delta_y = -abs(end_y - start_y)
    step_y = 1 if start_y < end_y else -1
    error = delta_x + delta_y
    pixels: list[tuple[int, int]] = []

    while True:
        pixels.append((start_x, start_y))
        if start_x == end_x and start_y == end_y:
            return tuple(pixels)

        doubled_error = 2 * error
        if doubled_error >= delta_y:
            error += delta_y
            start_x += step_x
        if doubled_error <= delta_x:
            error += delta_x
            start_y += step_y


def _random_edge_point(
    side: Side,
    width: int,
    height: int,
    random_generator: Random,
) -> EdgePoint:
    """
    Create a random point on the given side.
    """

    x_position, y_position = _random_edge_coordinates(side, width, height, random_generator)

    return EdgePoint(
        side=side,
        x_position=x_position,
        y_position=y_position,
        angle_degrees=random_generator.randint(MIN_ANGLE, MAX_ANGLE),
        offset=random_generator.randint(MIN_OFFSET, MAX_OFFSET),
    )


def _random_edge_coordinates(
    side: Side,
    width: int,
    height: int,
    random_generator: Random,
) -> tuple[int, int]:
    """
    Create a random coordinate on the given side.
    """

    max_x = width - 1
    max_y = height - 1

    if side is Side.TOP:
        return random_generator.randrange(width), 0
    if side is Side.RIGHT:
        return max_x, random_generator.randrange(height)
    if side is Side.BOTTOM:
        return random_generator.randrange(width), max_y
    return 0, random_generator.randrange(height)


def _movement_delta(side: Side, angle_degrees: int, offset: int) -> tuple[float, float]:
    """
    Convert a border-relative inward angle and offset to a movement vector.
    """

    angle_radians = radians(angle_degrees)
    edge_delta = cos(angle_radians) * offset
    inward_delta = sin(angle_radians) * offset

    if side is Side.TOP:
        return edge_delta, inward_delta
    if side is Side.RIGHT:
        return -inward_delta, edge_delta
    if side is Side.BOTTOM:
        return edge_delta, -inward_delta
    return inward_delta, edge_delta


def _hit_side(x_position: float, y_position: float, width: int, height: int) -> Side | None:
    """
    Return the side crossed by a moving point.
    """

    if x_position < 0:
        return Side.LEFT
    if x_position > width - 1:
        return Side.RIGHT
    if y_position < 0:
        return Side.TOP
    if y_position > height - 1:
        return Side.BOTTOM
    return None


def _clamp(value: float | int, minimum: int, maximum: int) -> int:
    """
    Clamp a numeric value to an integer range.
    """

    return min(maximum, max(minimum, round(value)))
