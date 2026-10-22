"""Launch the Cozy Study Desk window or run its headless smoke check."""

from __future__ import annotations

import argparse
from datetime import datetime
import math
import os

import pygame

from src.pet import DeskPet, PetState

WIDTH, HEIGHT = 800, 520
FPS = 60
BACKGROUND = (246, 238, 231)
INK = (72, 62, 78)
MUTED = (135, 119, 132)
DESK = (194, 145, 112)
DESK_EDGE = (165, 113, 87)


def headless_check() -> None:
    """Exercise import, construction, drag/throw, gravity, and drawing headlessly."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    surface = pygame.Surface((WIDTH, HEIGHT))
    bounds = pygame.Rect(0, 0, WIDTH, HEIGHT)
    pet = DeskPet(280, 360, floor_y=430, seed=7)

    assert pet.begin_drag(280, 360, 0.0), "Pet should respond to a centered grab"
    pet.drag_to(350, 310, 0.10)
    pet.release_drag(0.11)
    assert pet.state is PetState.FALLING, "Release should enter FALLING"
    for tick in range(1, 121):
        pet.update(1 / 60, bounds, tick / 60)
    assert bounds.left + pet.radius <= pet.x <= bounds.right - pet.radius
    pet.draw(surface, 2.0)
    font = pygame.font.SysFont("segoeui,arial", 17, bold=True)
    small = pygame.font.SysFont("segoeui,arial", 14)
    test_time = datetime(2026, 1, 2, 3, 4, 5).astimezone()
    draw_wall_clock(surface, test_time)
    draw_desk(surface, test_time)
    assert surface.get_at((WIDTH - 126, 151))[:3] == (190, 103, 99), "Clock center should be drawn"
    draw_status(surface, font, small, pet, test_time)
    pet.reset(280, 430)
    assert pet.state is PetState.IDLE
    pygame.quit()
    print("Headless check passed: import, drag/throw, gravity, bounds, draw, reset.")


def draw_wall_clock(surface: pygame.Surface, current_time: datetime) -> None:
    """Draw a decorative analog wall clock showing the computer's local time."""
    width, _ = surface.get_size()
    cx, cy = width - 126, 151
    radius = 54

    # Small hanging loop, soft shadow, and warm wooden bezel.
    pygame.draw.circle(surface, (166, 137, 121), (cx, cy - radius - 8), 8, 3)
    pygame.draw.circle(surface, (230, 219, 209), (cx + 2, cy + 3), radius + 5)
    pygame.draw.circle(surface, (128, 91, 82), (cx, cy), radius + 4)
    pygame.draw.circle(surface, (226, 188, 139), (cx, cy), radius)
    pygame.draw.circle(surface, (255, 250, 237), (cx, cy), radius - 6)

    # Minute marks and larger hour markers around the dial.
    for minute in range(60):
        # Start at 12 o'clock and turn clockwise.
        angle = minute * (2 * math.pi / 60) - math.pi / 2
        is_hour = minute % 5 == 0
        outer = radius - 11
        inner = radius - (20 if is_hour else 15)
        start = (cx + round(outer * math.cos(angle)), cy + round(outer * math.sin(angle)))
        end = (cx + round(inner * math.cos(angle)), cy + round(inner * math.sin(angle)))
        pygame.draw.line(surface, (114, 86, 81), start, end, 2 if is_hour else 1)

    # Delicate numerals at the quarter hours.
    numeral_font = pygame.font.SysFont("segoeui,arial", 12, bold=True)
    for label, angle in (("12", -90), ("3", 0), ("6", 90), ("9", 180)):
        radians = math.radians(angle)
        pos = (cx + round(34 * math.cos(radians)), cy + round(34 * math.sin(radians)))
        text = numeral_font.render(label, True, (104, 79, 77))
        surface.blit(text, text.get_rect(center=pos))

    # Hands use local wall-clock time: hour, minute, and second.
    seconds = current_time.second + current_time.microsecond / 1_000_000
    minutes = current_time.minute + seconds / 60
    hours = (current_time.hour % 12) + minutes / 60
    for value, units, length, color, thickness in (
        (hours, 12, 22, (81, 68, 72), 4),
        (minutes, 60, 34, (81, 68, 72), 3),
        (seconds, 60, 40, (190, 103, 99), 1),
    ):
        angle = value * (2 * math.pi / units) - math.pi / 2
        endpoint = (cx + round(length * math.cos(angle)), cy + round(length * math.sin(angle)))
        pygame.draw.line(surface, color, (cx, cy), endpoint, thickness)
    pygame.draw.circle(surface, (190, 103, 99), (cx, cy), 3)


def draw_desk(surface: pygame.Surface, current_time: datetime | None = None) -> None:
    """Paint the warm study-desk background with subtle room details."""
    if current_time is None:
        current_time = datetime.now().astimezone()
    width, height = surface.get_size()
    desk_top = min(424, height - 70)
    pygame.draw.rect(surface, BACKGROUND, (0, 0, width, height))
    draw_wall_clock(surface, current_time)
    # Warm study-room window and soft panes.
    pygame.draw.rect(surface, (230, 219, 219), (34, 42, 146, 144), border_radius=12)
    pygame.draw.rect(surface, (249, 247, 239), (42, 50, 130, 128), border_radius=8)
    pygame.draw.line(surface, (225, 214, 207), (107, 52), (107, 176), 3)
    pygame.draw.line(surface, (225, 214, 207), (44, 114), (170, 114), 3)
    # A tiny plant silhouette at the edge of the desk.
    pygame.draw.rect(surface, (177, 122, 102), (width - 100, desk_top - 86, 40, 34), border_radius=6)
    pygame.draw.ellipse(surface, (105, 145, 120), (width - 110, desk_top - 131, 24, 48))
    pygame.draw.ellipse(surface, (119, 159, 127), (width - 90, desk_top - 148, 24, 52))
    pygame.draw.ellipse(surface, (95, 137, 115), (width - 72, desk_top - 124, 22, 43))
    # Desk top and front edge.
    pygame.draw.rect(surface, DESK, (0, desk_top, width, height - desk_top))
    pygame.draw.rect(surface, DESK_EDGE, (0, desk_top, width, 9))
    pygame.draw.line(surface, (218, 174, 139), (0, desk_top + 18), (width, desk_top + 18), 2)


def draw_status(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small: pygame.font.Font,
    pet: DeskPet,
    current_time: datetime | None = None,
) -> None:
    """Render status, current local computer time, and the short instructions."""
    if current_time is None:
        current_time = datetime.now().astimezone()

    pygame.draw.rect(surface, (255, 251, 247), (0, 0, WIDTH, 38))
    pygame.draw.line(surface, (229, 218, 215), (0, 37), (WIDTH, 37), 1)
    title = font.render("Cozy Study Desk", True, INK)
    surface.blit(title, (18, 9))
    state_color = (121, 102, 157) if pet.state == PetState.IDLE else (180, 121, 93)
    state = small.render(f"{pet.state_name}  ·  {pet.mood}", True, state_color)
    surface.blit(state, (WIDTH - state.get_width() - 18, 11))
    instructions = small.render("Drag & throw pet  |  Press R to Reset", True, INK)
    surface.blit(instructions, (18, HEIGHT - 28))
    energy_label = small.render(f"energy {int(pet.energy * 100):02d}%", True, MUTED)
    surface.blit(energy_label, (WIDTH - energy_label.get_width() - 18, HEIGHT - 28))


def run() -> None:
    """Run the interactive Pygame window."""
    pygame.init()
    pygame.display.set_caption("Cozy Desk Companion")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("segoeui,arial", 17, bold=True)
    small = pygame.font.SysFont("segoeui,arial", 14)
    width, height = screen.get_size()
    floor_y = height - 96
    pet = DeskPet(width * 0.5, floor_y - 38, floor_y=floor_y)
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        now = pygame.time.get_ticks() / 1000.0
        width, height = screen.get_size()
        floor_y = height - 96
        bounds = pygame.Rect(0, 0, width, height)
        pet.floor_y = floor_y

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    pet.reset(width * 0.5, floor_y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pet.begin_drag(event.pos[0], event.pos[1], now)
            elif event.type == pygame.MOUSEMOTION and pet.state == PetState.DRAGGED:
                pet.drag_to(event.pos[0], event.pos[1], now)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                pet.release_drag(now)
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        if pet.state == PetState.DRAGGED:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            pet.drag_to(mouse_x, mouse_y, now)
        pet.update(dt, bounds, now)

        current_time = datetime.now().astimezone()
        draw_desk(screen, current_time)
        pet.draw(screen, now)
        draw_status(screen, font, small, pet, current_time)
        pygame.display.flip()

    pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="A tiny witch-hat companion for a cozy study desk.")
    parser.add_argument("--headless-check", action="store_true", help="run a smoke test without opening a window")
    args = parser.parse_args()
    if args.headless_check:
        headless_check()
    else:
        run()


if __name__ == "__main__":
    main()
