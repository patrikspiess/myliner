"""
Pygame entry point for running Myliner in graphics mode.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from .engine import (
    DEFAULT_HISTORY,
    DEFAULT_SPEED,
    DEFAULT_THICKNESS,
    MylinerEngine,
    MylinerSettings,
    next_fibonacci_speed,
    previous_fibonacci_speed,
)
from .geometry import MAX_LONG_SIDE, calculate_graphics_size

HELP_LINES = (
    "q/a: line count",
    "w/s: speed",
    "e/d: line thickness",
    "h: toggle help",
    "f: toggle fullscreen",
    "esc/click: quit",
)


@dataclass(slots=True)
class RuntimeSettings:
    """
    Track settings that can change while the animation is running.
    """

    speed: int
    line_count: int
    thickness: int


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build the command line argument parser.

    Returns:
        A configured argument parser.
    """

    parser = argparse.ArgumentParser(description="Run the Myliner line animation.")
    parser.add_argument("--lines", type=int, default=1, help="Number of animated lines.")
    parser.add_argument("--history", type=int, default=DEFAULT_HISTORY, help="Line history length.")
    parser.add_argument(
        "--max-long-side", type=int, default=MAX_LONG_SIDE, help="Maximum long side size."
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Optional deterministic random seed."
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=DEFAULT_SPEED,
        help="Number of new line frames drawn per second.",
    )
    parser.add_argument(
        "--thickness",
        type=int,
        default=DEFAULT_THICKNESS,
        help="Line thickness in pixels.",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Run with the native screen size in fullscreen mode.",
    )
    return parser


def load_pygame() -> Any:
    """
    Load pygame lazily so importing the package stays lightweight.
    """

    return import_module("pygame")


def calculate_window_size(
    screen_width: int,
    screen_height: int,
    max_long_side: int,
    fullscreen: bool,
) -> tuple[int, int]:
    """
    Calculate the window size for the current display mode.
    """

    if fullscreen:
        return screen_width, screen_height
    return calculate_graphics_size(screen_width, screen_height, max_long_side)


def build_settings(
    arguments: argparse.Namespace,
    width: int,
    height: int,
    runtime_settings: RuntimeSettings,
) -> MylinerSettings:
    """
    Build engine settings for the current runtime mode.
    """

    return MylinerSettings(
        width=width,
        height=height,
        line_count=runtime_settings.line_count,
        history=arguments.history,
        speed=runtime_settings.speed,
        thickness=runtime_settings.thickness,
    )


def main() -> None:  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    """
    Run the Myliner Pygame animation.
    """

    arguments = build_argument_parser().parse_args()
    pygame = load_pygame()
    pygame.init()
    pygame.display.set_caption("Myliner")

    display_info = pygame.display.Info()
    fullscreen = arguments.fullscreen
    runtime_settings = RuntimeSettings(
        speed=arguments.speed,
        line_count=arguments.lines,
        thickness=arguments.thickness,
    )
    help_is_visible = False
    width, height = calculate_window_size(
        display_info.current_w,
        display_info.current_h,
        arguments.max_long_side,
        fullscreen,
    )
    engine = MylinerEngine(
        build_settings(arguments, width, height, runtime_settings),
        seed=arguments.seed,
    )
    screen = pygame.display.set_mode(
        (width, height),
        pygame.FULLSCREEN if fullscreen else 0,
    )
    surface = pygame.image.frombuffer(engine.rgb_buffer, (width, height), "RGB")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    running = True

    def recreate_display() -> None:
        """
        Recreate the display and engine after fullscreen changes.
        """

        nonlocal engine, height, screen, surface, width

        width, height = calculate_window_size(
            display_info.current_w,
            display_info.current_h,
            arguments.max_long_side,
            fullscreen,
        )
        engine = MylinerEngine(
            build_settings(arguments, width, height, runtime_settings),
            seed=arguments.seed,
        )
        screen = pygame.display.set_mode(
            (width, height),
            pygame.FULLSCREEN if fullscreen else 0,
        )
        surface = pygame.image.frombuffer(engine.rgb_buffer, (width, height), "RGB")

    def render_help() -> None:
        """
        Render the help overlay on top of the animation.
        """

        if not help_is_visible:
            return

        for line_index, help_line in enumerate(HELP_LINES):
            text_surface = font.render(help_line, True, (255, 255, 255))
            screen.blit(text_surface, (16, 16 + line_index * 28))

    while running:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN):
                running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_q:
                if engine.add_line():
                    runtime_settings.line_count = engine.current_line_count
            elif event.key == pygame.K_a:
                if engine.remove_line():
                    runtime_settings.line_count = engine.current_line_count
            elif event.key == pygame.K_w:
                runtime_settings.speed = next_fibonacci_speed(runtime_settings.speed)
            elif event.key == pygame.K_s:
                runtime_settings.speed = previous_fibonacci_speed(runtime_settings.speed)
            elif event.key == pygame.K_e:
                runtime_settings.thickness += 1
                engine.set_thickness(runtime_settings.thickness)
            elif event.key == pygame.K_d:
                runtime_settings.thickness = max(1, runtime_settings.thickness - 1)
                engine.set_thickness(runtime_settings.thickness)
            elif event.key == pygame.K_h:
                help_is_visible = not help_is_visible
            elif event.key == pygame.K_f:
                fullscreen = not fullscreen
                recreate_display()
            elif event.key == pygame.K_ESCAPE:
                running = False

        engine.step(return_frames=False)
        screen.blit(surface, (0, 0))
        render_help()
        pygame.display.flip()
        clock.tick(runtime_settings.speed)

    pygame.quit()


if __name__ == "__main__":
    main()
