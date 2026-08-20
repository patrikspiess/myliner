"""
Animation engine for Pyliner.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from random import Random

import numpy as np
from numpy.typing import NDArray

from .geometry import EdgePoint, LineFrame, random_edge_point_pair

DEFAULT_COLOR = (255, 102, 0)
DEFAULT_BRIGHTNESS = 0
DEFAULT_HISTORY = 150
DEFAULT_INTENSITY_STEP = 12
DEFAULT_SPEED = 10
DEFAULT_THICKNESS = 3
MAX_LINE_COUNT = 20
MIN_LINE_COUNT = 1
MIN_SPEED = 1

LineHistory = deque[NDArray[np.intp]]


def next_fibonacci_speed(speed: int) -> int:
    """
    Return the next higher Fibonacci speed value.
    """

    if speed < MIN_SPEED:
        return MIN_SPEED

    previous_speed = 1
    current_speed = 2
    while current_speed <= speed:
        previous_speed, current_speed = current_speed, previous_speed + current_speed
    return current_speed


def previous_fibonacci_speed(speed: int) -> int:
    """
    Return the next lower Fibonacci speed value.
    """

    if speed <= MIN_SPEED:
        return MIN_SPEED

    previous_speed = 1
    current_speed = 2
    while current_speed < speed:
        previous_speed, current_speed = current_speed, previous_speed + current_speed
    return previous_speed


@dataclass(frozen=True, slots=True)
class LineState:
    """
    Track one animated line with a stable history identifier.
    """

    line_id: int
    start_point: EdgePoint
    end_point: EdgePoint


@dataclass(frozen=True, slots=True)
class PylinerSettings:  # pylint: disable=too-many-instance-attributes
    """
    Configure the Pyliner animation engine.
    """

    width: int
    height: int
    line_count: int = 1
    history: int = DEFAULT_HISTORY
    color: tuple[int, int, int] = DEFAULT_COLOR
    default_brightness: int = DEFAULT_BRIGHTNESS
    intensity_step: int = DEFAULT_INTENSITY_STEP
    speed: int = DEFAULT_SPEED
    thickness: int = DEFAULT_THICKNESS

    def __post_init__(self) -> None:
        """
        Validate engine settings.
        """

        if self.width < 2 or self.height < 2:
            raise ValueError("width and height must be at least 2")
        if not MIN_LINE_COUNT <= self.line_count <= MAX_LINE_COUNT:
            raise ValueError("line_count must be between 1 and 20")
        if self.history < 1:
            raise ValueError("history must be at least 1")
        if not all(0 <= channel <= 255 for channel in self.color):
            raise ValueError("color channels must be between 0 and 255")
        if not 0 <= self.default_brightness <= 255:
            raise ValueError("default_brightness must be between 0 and 255")
        if not 1 <= self.intensity_step <= 255:
            raise ValueError("intensity_step must be between 1 and 255")
        if self.speed < MIN_SPEED:
            raise ValueError("speed must be at least 1")
        if self.thickness < 1:
            raise ValueError("thickness must be at least 1")


class PylinerEngine:  # pylint: disable=too-many-instance-attributes
    """
    Run the line animation state and brightness accumulation.
    """

    def __init__(
        self,
        settings: PylinerSettings,
        *,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the animation engine.

        Args:
            settings: Engine settings.
            seed: Optional seed for deterministic animation.
        """

        self.settings = settings
        self._random_generator = Random(seed)
        self._brightness = np.full(
            settings.width * settings.height,
            settings.default_brightness,
            dtype=np.uint8,
        )
        self._coverage = np.zeros(settings.width * settings.height, dtype=np.uint16)
        self._rgb_buffer = np.zeros(settings.width * settings.height * 3, dtype=np.uint8)
        self._fade_step = max(1, round(255 / settings.history))
        self._next_line_id = 0
        self._thickness_offsets: dict[int, NDArray[np.int32]] = {}
        self._line_histories: dict[int, LineHistory] = {}
        self._line_states = [self._create_line_state() for _ in range(settings.line_count)]

    @property
    def default_brightness(self) -> int:
        """
        Return the minimum brightness value.
        """

        return self.settings.default_brightness

    @property
    def brightness(self) -> tuple[int, ...]:
        """
        Return an immutable snapshot of the current brightness map.
        """

        return tuple(int(brightness) for brightness in self._brightness)

    @property
    def coverage(self) -> tuple[int, ...]:
        """
        Return an immutable snapshot of the current line coverage map.
        """

        return tuple(int(coverage) for coverage in self._coverage)

    @property
    def rgb_buffer(self) -> NDArray[np.uint8]:
        """
        Return the mutable RGB framebuffer.
        """

        return self._rgb_buffer

    @property
    def line_points(self) -> tuple[tuple[EdgePoint, EdgePoint], ...]:
        """
        Return the current endpoint pairs.
        """

        return tuple(
            (line_state.start_point, line_state.end_point) for line_state in self._line_states
        )

    @property
    def history_size(self) -> int:
        """
        Return the number of currently visible line frames.
        """

        return sum(len(line_history) for line_history in self._line_histories.values())

    @property
    def current_line_count(self) -> int:
        """
        Return the number of currently animated lines.
        """

        return len(self._line_states)

    def add_line(self) -> bool:
        """
        Add one animated line if the maximum line count has not been reached.
        """

        if self.current_line_count >= MAX_LINE_COUNT:
            return False

        self._line_states.append(self._create_line_state())
        return True

    def set_thickness(self, thickness: int) -> None:
        """
        Set the line thickness used for newly rendered frames.
        """

        self.settings = replace(self.settings, thickness=thickness)

    def remove_line(self) -> bool:
        """
        Remove one animated line if the minimum line count has not been reached.
        """

        if self.current_line_count <= MIN_LINE_COUNT:
            return False

        removed_line_state = self._line_states.pop(0)
        self._remove_line_history(removed_line_state.line_id)
        return True

    def step(self, *, return_frames: bool = True) -> tuple[LineFrame, ...]:
        """
        Draw one animation step and move all endpoints.

        Returns:
            The rendered line frames for this step.
        """

        frames: list[LineFrame] = []

        self._fade_rgb_buffer()

        for line_state in self._line_states:
            pixel_indexes = self._line_pixel_indexes(
                line_state.start_point.to_xy(self.settings.width, self.settings.height),
                line_state.end_point.to_xy(self.settings.width, self.settings.height),
            )
            self._increase_brightness(pixel_indexes)
            line_history = self._line_histories[line_state.line_id]
            line_history.append(pixel_indexes)
            self._trim_line_history(line_history)

            if return_frames:
                frames.append(
                    LineFrame(
                        start=line_state.start_point,
                        end=line_state.end_point,
                        pixels=self._pixels_from_indexes(pixel_indexes),
                    )
                )

        self._line_states = [
            LineState(
                line_id=line_state.line_id,
                start_point=line_state.start_point.moved(
                    self.settings.width,
                    self.settings.height,
                    self._random_generator,
                ),
                end_point=line_state.end_point.moved(
                    self.settings.width,
                    self.settings.height,
                    self._random_generator,
                ),
            )
            for line_state in self._line_states
        ]

        return tuple(frames)

    def rgb_rows(self) -> tuple[tuple[str, ...], ...]:
        """
        Convert the brightness map to hex color rows.

        Returns:
            A tuple of color rows.
        """

        rows: list[tuple[str, ...]] = []
        red, green, blue = self.settings.color

        for y_position in range(self.settings.height):
            row: list[str] = []
            for x_position in range(self.settings.width):
                pixel_index = self._pixel_index(x_position, y_position)
                if self._coverage[pixel_index] == 0:
                    row.append("#000000")
                    continue

                brightness = self._brightness[pixel_index] / 255
                row.append(self._format_color(red, green, blue, brightness))
            rows.append(tuple(row))

        return tuple(rows)

    def rgb_bytes(self) -> bytes:
        """
        Convert the current frame to packed RGB bytes.
        """

        return bytes(self._rgb_buffer)

    def _pixel_index(self, x_position: int, y_position: int) -> int:
        """
        Convert a pixel coordinate to a brightness array index.
        """

        return y_position * self.settings.width + x_position

    def _create_line_state(self) -> LineState:
        """
        Create one animated line with a stable identifier.
        """

        start_point, end_point = random_edge_point_pair(
            self.settings.width,
            self.settings.height,
            self._random_generator,
        )
        line_state = LineState(
            line_id=self._next_line_id,
            start_point=start_point,
            end_point=end_point,
        )
        self._line_histories[line_state.line_id] = deque()
        self._next_line_id += 1
        return line_state

    def _pixel_indexes(self, pixels: tuple[tuple[int, int], ...]) -> NDArray[np.intp]:
        """
        Convert pixel coordinates to a NumPy brightness index array.
        """

        return np.fromiter(
            (self._pixel_index(x_position, y_position) for x_position, y_position in pixels),
            dtype=np.intp,
            count=len(pixels),
        )

    def _line_pixel_indexes(
        self,
        start_pixel: tuple[int, int],
        end_pixel: tuple[int, int],
    ) -> NDArray[np.intp]:
        """
        Rasterize one line directly to unique framebuffer indexes.
        """

        start_x, start_y = start_pixel
        end_x, end_y = end_pixel
        pixel_count = max(abs(end_x - start_x), abs(end_y - start_y)) + 1
        x_positions = np.rint(np.linspace(start_x, end_x, pixel_count)).astype(np.int32)
        y_positions = np.rint(np.linspace(start_y, end_y, pixel_count)).astype(np.int32)
        return self._thickened_pixel_indexes_from_arrays(x_positions, y_positions)

    def _thickened_pixel_indexes(self, pixels: tuple[tuple[int, int], ...]) -> NDArray[np.intp]:
        """
        Convert rasterized pixels to unique framebuffer indexes including thickness.
        """

        if not pixels:
            return np.array([], dtype=np.intp)
        if self.settings.thickness == 1:
            return self._pixel_indexes(pixels)

        pixel_array = np.asarray(pixels, dtype=np.int32)
        return self._thickened_pixel_indexes_from_arrays(pixel_array[:, 0], pixel_array[:, 1])

    def _thickened_pixel_indexes_from_arrays(
        self,
        x_positions: NDArray[np.int32],
        y_positions: NDArray[np.int32],
    ) -> NDArray[np.intp]:
        """
        Expand rasterized line coordinate arrays to unique framebuffer indexes.
        """

        if self.settings.thickness == 1:
            return y_positions.astype(np.intp) * self.settings.width + x_positions.astype(np.intp)

        offsets = self._get_thickness_offsets()
        if np.ptp(x_positions) >= np.ptp(y_positions):
            expanded_x = np.broadcast_to(
                x_positions[:, np.newaxis],
                (x_positions.size, offsets.size),
            )
            expanded_y = y_positions[:, np.newaxis] + offsets
        else:
            expanded_x = x_positions[:, np.newaxis] + offsets
            expanded_y = np.broadcast_to(
                y_positions[:, np.newaxis],
                (y_positions.size, offsets.size),
            )
        valid_pixels = (
            (expanded_x >= 0)
            & (expanded_x < self.settings.width)
            & (expanded_y >= 0)
            & (expanded_y < self.settings.height)
        )
        pixel_indexes = expanded_y[valid_pixels].astype(np.intp) * self.settings.width + expanded_x[
            valid_pixels
        ].astype(np.intp)

        if pixel_indexes.size < 2:
            return pixel_indexes

        pixel_indexes.sort()
        unique_pixels = np.empty(pixel_indexes.size, dtype=np.bool_)
        unique_pixels[0] = True
        unique_pixels[1:] = pixel_indexes[1:] != pixel_indexes[:-1]
        return pixel_indexes[unique_pixels]

    def _get_thickness_offsets(self) -> NDArray[np.int32]:
        """
        Return cached offsets for the current line thickness.
        """

        cached_offsets = self._thickness_offsets.get(self.settings.thickness)
        if cached_offsets is not None:
            return cached_offsets

        before_center = self.settings.thickness // 2
        after_center = self.settings.thickness - before_center
        cached_offsets = np.arange(-before_center, after_center, dtype=np.int32)
        self._thickness_offsets[self.settings.thickness] = cached_offsets
        return cached_offsets

    def _pixels_from_indexes(self, pixel_indexes: NDArray[np.intp]) -> tuple[tuple[int, int], ...]:
        """
        Convert framebuffer indexes back to pixel coordinates.
        """

        if pixel_indexes.size == 0:
            return ()

        y_positions, x_positions = np.divmod(pixel_indexes, self.settings.width)
        return tuple(
            (int(x_position), int(y_position))
            for x_position, y_position in zip(x_positions, y_positions, strict=True)
        )

    def _apply_thickness(self, pixels: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
        """
        Expand rasterized line pixels by the configured line thickness.
        """

        return self._pixels_from_indexes(self._thickened_pixel_indexes(pixels))

    def _increase_brightness(self, pixel_indexes: NDArray[np.intp]) -> None:
        """
        Increase brightness for the given pixel indexes.
        """

        if pixel_indexes.size == 0:
            return

        covered_indexes = pixel_indexes[self._coverage[pixel_indexes] > 0]
        if covered_indexes.size > 0:
            increased = self._brightness[covered_indexes].astype(np.uint16)
            increased += self.settings.intensity_step
            self._brightness[covered_indexes] = np.minimum(increased, 255).astype(np.uint8)

        self._coverage[pixel_indexes] += 1
        self._update_rgb_pixels(pixel_indexes)

    def _decrease_brightness(self, pixel_indexes: NDArray[np.intp]) -> None:
        """
        Decrease brightness for the given pixel indexes.
        """

        if pixel_indexes.size == 0:
            return

        self._coverage[pixel_indexes] = np.maximum(
            self._coverage[pixel_indexes].astype(np.int32) - 1,
            0,
        ).astype(np.uint16)
        uncovered_indexes = pixel_indexes[self._coverage[pixel_indexes] == 0]
        covered_indexes = pixel_indexes[self._coverage[pixel_indexes] > 0]

        if uncovered_indexes.size > 0:
            self._brightness[uncovered_indexes] = self.settings.default_brightness
        if covered_indexes.size > 0:
            decreased = self._brightness[covered_indexes].astype(np.int32)
            decreased -= self.settings.intensity_step
            self._brightness[covered_indexes] = np.maximum(
                decreased,
                self.settings.default_brightness,
            ).astype(np.uint8)

        self._clear_rgb_pixels(uncovered_indexes)

    def _trim_line_history(self, line_history: LineHistory) -> None:
        """
        Remove outdated line frames from the brightness map.
        """

        while len(line_history) > self.settings.history:
            expired_line = line_history.popleft()
            self._decrease_brightness(expired_line)

    def _remove_line_history(self, removed_line_id: int) -> None:
        """
        Remove all visible history for a removed line immediately.
        """

        line_history = self._line_histories.pop(removed_line_id, deque())

        while line_history:
            self._decrease_brightness(line_history.popleft())

    def _format_color(self, red: int, green: int, blue: int, brightness: float) -> str:
        """
        Format a base color lightened by the brightness value.
        """

        return (
            f"#{self._lighten_channel(red, brightness):02x}"
            f"{self._lighten_channel(green, brightness):02x}"
            f"{self._lighten_channel(blue, brightness):02x}"
        )

    def _lighten_channel(self, channel: int, brightness: float) -> int:
        """
        Lighten one color channel toward white.
        """

        return round(channel + (255 - channel) * brightness)

    def _update_rgb_pixels(self, pixel_indexes: NDArray[np.intp]) -> None:
        """
        Update pixels in the packed RGB framebuffer.
        """

        if pixel_indexes.size == 0:
            return

        uncovered_indexes = pixel_indexes[self._coverage[pixel_indexes] == 0]
        self._clear_rgb_pixels(uncovered_indexes)

        covered_indexes = pixel_indexes[self._coverage[pixel_indexes] > 0]
        if covered_indexes.size == 0:
            return

        covered_buffer_indexes = covered_indexes * 3
        red, green, blue = self.settings.color
        brightness = self._brightness[covered_indexes].astype(np.float32) / 255
        self._rgb_buffer[covered_buffer_indexes] = np.rint(red + (255 - red) * brightness).astype(
            np.uint8
        )
        self._rgb_buffer[covered_buffer_indexes + 1] = np.rint(
            green + (255 - green) * brightness
        ).astype(np.uint8)
        self._rgb_buffer[covered_buffer_indexes + 2] = np.rint(
            blue + (255 - blue) * brightness
        ).astype(np.uint8)

    def _clear_rgb_pixels(self, pixel_indexes: NDArray[np.intp]) -> None:
        """
        Clear pixels in the packed RGB framebuffer.
        """

        if pixel_indexes.size == 0:
            return

        buffer_indexes = pixel_indexes * 3
        self._rgb_buffer[buffer_indexes] = 0
        self._rgb_buffer[buffer_indexes + 1] = 0
        self._rgb_buffer[buffer_indexes + 2] = 0

    def _fade_rgb_buffer(self) -> None:
        """
        Darken already drawn pixels before drawing the next line frame.
        """

        dark_pixels = self._rgb_buffer <= self._fade_step
        np.subtract(
            self._rgb_buffer,
            self._fade_step,
            out=self._rgb_buffer,
            where=~dark_pixels,
        )
        self._rgb_buffer[dark_pixels] = 0
