"""
Tests for the Pyliner animation engine.
"""

import pytest
import numpy as np

from pyliner import PylinerEngine, PylinerSettings
from pyliner.engine import DEFAULT_HISTORY, next_fibonacci_speed, previous_fibonacci_speed


def test_engine_rejects_too_small_canvas() -> None:
    """
    It requires at least two pixels for each dimension.
    """

    with pytest.raises(ValueError, match="at least 2"):
        PylinerSettings(1, 10)


def test_engine_uses_required_default_history() -> None:
    """
    It uses the required default line history.
    """

    assert PylinerSettings(20, 10).history == DEFAULT_HISTORY == 150


def test_engine_rejects_invalid_speed() -> None:
    """
    It requires a positive line rate.
    """

    with pytest.raises(ValueError, match="speed"):
        PylinerSettings(20, 10, speed=0)


def test_engine_accepts_high_speed_without_fixed_cap() -> None:
    """
    It does not enforce a fixed upper speed cap.
    """

    assert PylinerSettings(20, 10, speed=1597).speed == 1597


def test_fibonacci_speed_steps_move_to_neighboring_values() -> None:
    """
    It maps arbitrary speeds to neighboring Fibonacci runtime steps.
    """

    assert next_fibonacci_speed(1) == 2
    assert next_fibonacci_speed(10) == 13
    assert next_fibonacci_speed(13) == 21
    assert previous_fibonacci_speed(1) == 1
    assert previous_fibonacci_speed(10) == 8
    assert previous_fibonacci_speed(13) == 8


def test_engine_rejects_too_many_lines() -> None:
    """
    It limits the number of animated lines.
    """

    with pytest.raises(ValueError, match="line_count"):
        PylinerSettings(20, 10, line_count=21)


def test_engine_rejects_invalid_thickness() -> None:
    """
    It requires a positive line thickness.
    """

    with pytest.raises(ValueError, match="thickness"):
        PylinerSettings(20, 10, thickness=0)


def test_step_draws_frame_and_moves_points() -> None:
    """
    It renders a line frame and advances endpoints.
    """

    engine = PylinerEngine(PylinerSettings(20, 10), seed=1)
    previous_points = engine.line_points
    frames = engine.step()

    assert len(frames) == 1
    assert frames[0].pixels
    assert engine.line_points != previous_points
    assert engine.history_size == 1
    assert max(engine.coverage) > 0


def test_step_can_skip_frame_objects_for_realtime_rendering() -> None:
    """
    It can update the framebuffer without returning line frame objects.
    """

    engine = PylinerEngine(PylinerSettings(20, 10), seed=1)

    frames = engine.step(return_frames=False)

    assert not frames
    assert engine.history_size == 1
    assert max(engine.coverage) > 0


def test_step_applies_line_thickness() -> None:
    """
    It expands rendered line pixels by the configured thickness.
    """

    thin_engine = PylinerEngine(PylinerSettings(20, 10, thickness=1), seed=1)
    thick_engine = PylinerEngine(PylinerSettings(20, 10, thickness=3), seed=1)

    thin_frame = thin_engine.step()[0]
    thick_frame = thick_engine.step()[0]

    assert len(thick_frame.pixels) > len(thin_frame.pixels)
    assert all(
        0 <= x_position < 20 and 0 <= y_position < 10
        for x_position, y_position in thick_frame.pixels
    )


def test_history_removal_reduces_brightness_to_default() -> None:
    """
    It removes old line brightness without going below the default value.
    """

    engine = PylinerEngine(
        PylinerSettings(2, 2, history=1, intensity_step=100, thickness=1),
        seed=3,
    )

    engine.step()
    engine.step()
    engine.step()

    assert engine.history_size == 1
    assert min(engine.brightness) == engine.default_brightness
    assert all(brightness >= engine.default_brightness for brightness in engine.brightness)


def test_history_is_kept_per_line() -> None:
    """
    It keeps the configured history length for each animated line.
    """

    engine = PylinerEngine(PylinerSettings(20, 10, line_count=3, history=2), seed=5)

    engine.step()
    engine.step()
    engine.step()

    assert engine.history_size == 6


def test_line_count_can_change_at_runtime_with_limits() -> None:
    """
    It adds and removes animated lines within the configured runtime limits.
    """

    engine = PylinerEngine(PylinerSettings(20, 10, line_count=1), seed=6)

    assert engine.current_line_count == 1
    assert not engine.remove_line()

    for _ in range(19):
        assert engine.add_line()

    assert engine.current_line_count == 20
    assert not engine.add_line()

    assert engine.remove_line()
    assert engine.current_line_count == 19


def test_runtime_thickness_applies_to_new_frames() -> None:
    """
    It changes the thickness used for newly rendered frames.
    """

    engine = PylinerEngine(PylinerSettings(20, 10, thickness=1), seed=1)
    thin_frame = engine.step()[0]

    engine.set_thickness(3)
    thick_frame = engine.step()[0]

    assert len(thick_frame.pixels) > len(thin_frame.pixels)


def test_removing_line_deletes_its_history_immediately() -> None:
    """
    It removes visible history for the removed line immediately.
    """

    engine = PylinerEngine(PylinerSettings(20, 10, line_count=2, history=2), seed=7)

    engine.step()
    engine.step()
    assert engine.history_size == 4
    previous_coverage = sum(engine.coverage)

    assert engine.remove_line()

    assert engine.current_line_count == 1
    assert engine.history_size == 2
    assert sum(engine.coverage) < previous_coverage


def test_removing_lines_rebuilds_framebuffer_without_visual_ghosts() -> None:
    """
    It clears render-state leftovers when reducing multiple lines back to one.
    """

    engine = PylinerEngine(PylinerSettings(60, 30, line_count=1, history=3), seed=9)
    assert engine.add_line()
    assert engine.add_line()

    for _ in range(5):
        engine.step()

    assert engine.current_line_count == 3
    assert engine.remove_line()
    assert engine.remove_line()

    expected_coverage = np.zeros_like(engine._coverage)  # pylint: disable=protected-access
    assert set(engine._line_histories) == {2}  # pylint: disable=protected-access
    for pixel_indexes in engine._line_histories[2]:  # pylint: disable=protected-access
        np.add.at(expected_coverage, pixel_indexes, 1)

    visible_pixel_indexes = {
        rgb_index // 3 for rgb_index, channel in enumerate(engine.rgb_buffer) if int(channel) > 0
    }
    covered_pixel_indexes = {
        pixel_index for pixel_index, coverage in enumerate(engine.coverage) if coverage > 0
    }

    assert engine.current_line_count == 1
    assert np.array_equal(engine._coverage, expected_coverage)  # pylint: disable=protected-access
    assert visible_pixel_indexes <= covered_pixel_indexes


def test_rgb_rows_use_line_color_scaled_by_brightness() -> None:
    """
    It converts brightness values to RGB colors.
    """

    settings = PylinerSettings(3, 3, color=(255, 128, 0), intensity_step=255, thickness=1)
    engine = PylinerEngine(settings, seed=4)

    engine.step()
    rows = engine.rgb_rows()

    assert len(rows) == 3
    assert len(rows[0]) == 3
    assert "#000000" in {color for row in rows for color in row}
    assert "#ff8000" in {color for row in rows for color in row}


def test_rgb_bytes_use_black_background_and_orange_default_line() -> None:
    """
    It renders only covered pixels with the base color at default brightness.
    """

    engine = PylinerEngine(PylinerSettings(20, 10, thickness=1), seed=1)

    engine.step()
    rgb_bytes = engine.rgb_bytes()

    assert len(rgb_bytes) == 20 * 10 * 3
    assert bytes((0, 0, 0)) in {
        rgb_bytes[index : index + 3] for index in range(0, len(rgb_bytes), 3)
    }
    assert bytes((255, 102, 0)) in {
        rgb_bytes[index : index + 3] for index in range(0, len(rgb_bytes), 3)
    }
    assert rgb_bytes == bytes(engine.rgb_buffer)


def test_rgb_buffer_fades_without_underflow() -> None:
    """
    It darkens old framebuffer pixels without wrapping below black.
    """

    engine = PylinerEngine(PylinerSettings(20, 10, history=150), seed=1)
    engine.rgb_buffer[0:3] = [2, 1, 0]

    engine._fade_rgb_buffer()  # pylint: disable=protected-access

    assert tuple(int(channel) for channel in engine.rgb_buffer[0:3]) == (0, 0, 0)


def test_removing_history_does_not_repaint_covered_pixels() -> None:
    """
    It does not brighten faded pixels when old overlapping history expires.
    """

    engine = PylinerEngine(PylinerSettings(4, 4, intensity_step=12), seed=1)
    pixel_indexes = np.array([0], dtype=np.intp)
    engine._coverage[pixel_indexes] = 2  # pylint: disable=protected-access
    engine._brightness[pixel_indexes] = 24  # pylint: disable=protected-access
    engine.rgb_buffer[0:3] = [9, 4, 0]

    engine._decrease_brightness(pixel_indexes)  # pylint: disable=protected-access

    assert int(engine._coverage[0]) == 1  # pylint: disable=protected-access
    assert int(engine._brightness[0]) == 12  # pylint: disable=protected-access
    assert tuple(int(channel) for channel in engine.rgb_buffer[0:3]) == (9, 4, 0)

    engine._decrease_brightness(pixel_indexes)  # pylint: disable=protected-access

    assert int(engine._coverage[0]) == 0  # pylint: disable=protected-access
    final_brightness = int(engine._brightness[0])  # pylint: disable=protected-access

    assert final_brightness == engine.default_brightness
    assert tuple(int(channel) for channel in engine.rgb_buffer[0:3]) == (0, 0, 0)
