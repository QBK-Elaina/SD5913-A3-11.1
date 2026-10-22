"""Launch the Cozy Study Desk window or run its headless smoke check."""

from __future__ import annotations

import argparse
from datetime import datetime
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
    draw_status(surface, font, small, pet, datetime(2026, 1, 2, 3, 4, 5).astimezone())
    assert small.render("03:04:05", True, INK).get_width() > 0, "Clock text should render"
    pet.reset(280, 430)
    assert pet.state is PetState.IDLE
    pygame.quit()
    print("Headless check passed: import, drag/throw, gravity, bounds, draw, reset.")


def draw_desk(surface: pygame.Surface) -> None:
    """Paint the warm study-desk background with subtle room details."""
    surface.fill(BACKGROUND)
    # Window and soft panes.
    pygame.draw.rect(surface, (230, 219, 219), (34, 42, 146, 144), border_radius=12)
    pygame.draw.rect(surface, (249, 247, 239), (42, 50, 130, 128), border_radius=8)
    pygame.draw.line(surface, (225, 214, 207), (107, 52), (107, 176), 3)
    pygame.draw.line(surface, (225, 214, 207), (44, 114), (170, 114), 3)
    # A tiny plant silhouette at the edge of the desk.
    pygame.draw.rect(surface, (177, 122, 102), (700, 338, 40, 34), border_radius=6)
    pygame.draw.ellipse(surface, (105, 145, 120), (690, 293, 24, 48))
    pygame.draw.ellipse(surface, (119, 159, 127), (710, 276, 24, 52))
    pygame.draw.ellipse(surface, (95, 137, 115), (728, 300, 22, 43))
    # Desk top and front edge.
    pygame.draw.rect(surface, DESK, (0, 424, WIDTH, HEIGHT - 424))
    pygame.draw.rect(surface, DESK_EDGE, (0, 424, WIDTH, 9))
    pygame.draw.line(surface, (218, 174, 139), (0, 442), (WIDTH, 442), 2)


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
    time_label = small.render(current_time.strftime("%H:%M:%S"), True, INK)
    surface.blit(time_label, time_label.get_rect(center=(WIDTH // 2, 19)))
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

        draw_desk(screen)
        pet.draw(screen, now)
        draw_status(screen, font, small, pet, datetime.now().astimezone())
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
