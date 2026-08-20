"""
Tests for the Pygame entry point.
"""

# pylint: disable=too-few-public-methods,too-many-instance-attributes

from __future__ import annotations

from dataclasses import dataclass

import pytest

from pyliner import main


def test_calculate_window_size_caps_windowed_mode() -> None:
    """
    It caps windowed mode while preserving the aspect ratio.
    """

    assert main.calculate_window_size(1920, 1080, 800, fullscreen=False) == (800, 450)


def test_calculate_window_size_uses_native_fullscreen_size() -> None:
    """
    It uses the native size in fullscreen mode.
    """

    assert main.calculate_window_size(1920, 1080, 800, fullscreen=True) == (1920, 1080)


@dataclass(frozen=True)
class FakeDisplayInfo:
    """
    Fake Pygame display information.
    """

    current_w: int = 1600
    current_h: int = 900


class FakeScreen:
    """
    Fake Pygame screen surface.
    """

    def __init__(self) -> None:
        """
        Initialize recorded blits.
        """

        self.blit_calls: list[tuple[object, tuple[int, int]]] = []

    def blit(self, surface: object, position: tuple[int, int]) -> None:
        """
        Record a blit call.
        """

        self.blit_calls.append((surface, position))


class FakeDisplay:
    """
    Fake Pygame display module.
    """

    def __init__(self) -> None:
        """
        Initialize display calls.
        """

        self.caption = ""
        self.flip_count = 0
        self.set_mode_calls: list[tuple[tuple[int, int], int]] = []
        self.screens: list[FakeScreen] = []

    def set_caption(self, caption: str) -> None:
        """
        Record the window caption.
        """

        self.caption = caption

    def Info(self) -> FakeDisplayInfo:  # pylint: disable=invalid-name
        """
        Return fake display information.
        """

        return FakeDisplayInfo()

    def set_mode(self, size: tuple[int, int], flags: int = 0) -> FakeScreen:
        """
        Record a display mode change.
        """

        screen = FakeScreen()
        self.set_mode_calls.append((size, flags))
        self.screens.append(screen)
        return screen

    def flip(self) -> None:
        """
        Record a display flip.
        """

        self.flip_count += 1


class FakeImageModule:
    """
    Fake Pygame image module.
    """

    def __init__(self) -> None:
        """
        Initialize created surfaces.
        """

        self.frombuffer_calls: list[tuple[object, tuple[int, int], str]] = []

    def frombuffer(self, buffer: object, size: tuple[int, int], mode: str) -> object:
        """
        Record a surface backed by a framebuffer.
        """

        surface = object()
        self.frombuffer_calls.append((buffer, size, mode))
        return surface


class FakeClock:
    """
    Fake Pygame clock.
    """

    def __init__(self) -> None:
        """
        Initialize tick calls.
        """

        self.tick_calls: list[int] = []

    def tick(self, frames_per_second: int) -> None:
        """
        Record the requested frame rate.
        """

        self.tick_calls.append(frames_per_second)


class FakeTimeModule:
    """
    Fake Pygame time module.
    """

    def __init__(self) -> None:
        """
        Initialize clocks.
        """

        self.clocks: list[FakeClock] = []

    def Clock(self) -> FakeClock:  # pylint: disable=invalid-name
        """
        Create a fake clock.
        """

        clock = FakeClock()
        self.clocks.append(clock)
        return clock


class FakeFont:
    """
    Fake Pygame font.
    """

    def render(self, text: str, antialias: bool, color: tuple[int, int, int]) -> str:
        """
        Render fake text.
        """

        return f"{text}:{antialias}:{color}"


class FakeFontModule:
    """
    Fake Pygame font module.
    """

    def Font(self, _name: object, _size: int) -> FakeFont:  # pylint: disable=invalid-name
        """
        Create a fake font.
        """

        return FakeFont()


@dataclass(frozen=True)
class FakeEvent:
    """
    Fake Pygame event.
    """

    type: int
    key: int | None = None


class FakeEventModule:
    """
    Fake Pygame event module.
    """

    def __init__(self, event_batches: list[list[FakeEvent]]) -> None:
        """
        Initialize event batches.
        """

        self._event_batches = event_batches

    def get(self) -> list[FakeEvent]:
        """
        Return the next event batch.
        """

        if not self._event_batches:
            return []
        return self._event_batches.pop(0)


class FakePygame:
    """
    Fake Pygame module.
    """

    FULLSCREEN = 1
    KEYDOWN = 2
    QUIT = 3
    K_q = 4
    K_a = 5
    K_w = 6
    K_s = 7
    K_h = 8
    K_f = 9
    K_e = 10
    K_d = 11
    K_ESCAPE = 12
    MOUSEBUTTONDOWN = 13

    def __init__(self, event_batches: list[list[FakeEvent]]) -> None:
        """
        Initialize fake Pygame modules.
        """

        self.display = FakeDisplay()
        self.event = FakeEventModule(event_batches)
        self.font = FakeFontModule()
        self.image = FakeImageModule()
        self.time = FakeTimeModule()
        self.init_count = 0
        self.quit_count = 0

    def init(self) -> None:
        """
        Record Pygame initialization.
        """

        self.init_count += 1

    def quit(self) -> None:
        """
        Record Pygame shutdown.
        """

        self.quit_count += 1


@dataclass
class FakeEngine:
    """
    Minimal engine replacement recording runtime changes.
    """

    settings: main.PylinerSettings
    seed: int | None = None
    add_line_count: int = 0
    remove_line_count: int = 0
    step_count: int = 0
    thickness_changes: list[int] | None = None

    @property
    def current_line_count(self) -> int:
        """
        Return the current fake line count.
        """

        return self.settings.line_count + self.add_line_count - self.remove_line_count

    @property
    def rgb_buffer(self) -> bytearray:
        """
        Return a fake RGB framebuffer.
        """

        return bytearray(self.settings.width * self.settings.height * 3)

    def step(self, *, return_frames: bool = True) -> tuple[object, ...]:
        """
        Record one animation step.
        """

        assert not return_frames
        self.step_count += 1
        return ()

    def set_thickness(self, thickness: int) -> None:
        """
        Record a runtime thickness change.
        """

        if self.thickness_changes is None:
            self.thickness_changes = []
        self.thickness_changes.append(thickness)

    def add_line(self) -> bool:
        """
        Record a line addition request.
        """

        self.add_line_count += 1
        return True

    def remove_line(self) -> bool:
        """
        Record a line removal request.
        """

        self.remove_line_count += 1
        return True


def test_main_uses_pygame_framebuffer_and_runtime_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    It runs with direct Pygame framebuffer blits and handles runtime controls.
    """

    fake_pygame = FakePygame(
        [
            [
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_q),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_a),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_w),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_e),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_d),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_h),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_f),
                FakeEvent(FakePygame.KEYDOWN, FakePygame.K_ESCAPE),
            ]
        ]
    )
    created_engines: list[FakeEngine] = []

    def create_engine(settings: main.PylinerSettings, *, seed: int | None = None) -> FakeEngine:
        engine = FakeEngine(settings=settings, seed=seed)
        created_engines.append(engine)
        return engine

    monkeypatch.setattr(main, "load_pygame", lambda: fake_pygame)
    monkeypatch.setattr(main, "PylinerEngine", create_engine)
    monkeypatch.setattr("sys.argv", ["pyliner", "--speed", "20", "--seed", "7"])

    main.main()

    assert fake_pygame.init_count == 1
    assert fake_pygame.display.caption == "Pyliner"
    assert fake_pygame.image.frombuffer_calls[0][1] == (800, 450)
    assert fake_pygame.display.set_mode_calls == [((800, 450), 0), ((1600, 900), 1)]
    assert created_engines[0].add_line_count == 1
    assert created_engines[0].remove_line_count == 1
    assert created_engines[0].thickness_changes == [4, 3]
    assert fake_pygame.time.clocks[0].tick_calls == [21]
    assert any(
        "q/a: line count" in str(blit_call[0])
        for blit_call in fake_pygame.display.screens[-1].blit_calls
    )
    assert fake_pygame.display.flip_count == 1
    assert fake_pygame.quit_count == 1


def test_main_quits_on_mouse_click(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    It exits when the user clicks the mouse.
    """

    fake_pygame = FakePygame([[FakeEvent(FakePygame.MOUSEBUTTONDOWN)]])

    monkeypatch.setattr(main, "load_pygame", lambda: fake_pygame)
    monkeypatch.setattr(main, "PylinerEngine", FakeEngine)
    monkeypatch.setattr("sys.argv", ["pyliner"])

    main.main()

    assert fake_pygame.quit_count == 1
