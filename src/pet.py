"""The cozy desk companion and its simple Ball-inspired physics.

The motion model intentionally follows the Week 7 lecture's Ball example:
position (x, y), velocity (vx, vy), and a constant GRAVITY acceleration.
"""

from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import Optional

import pygame


class PetState(Enum):
    """The interaction/motion states used by :class:`DeskPet`."""

    IDLE = auto()
    WANDER = auto()
    REST = auto()
    NAP = auto()
    GROOM = auto()
    LOOK_AROUND = auto()
    DRAGGED = auto()
    FALLING = auto()


class DeskPet:
    """A procedural witch-hat pet with drag, throw, and soft-bounce physics."""

    GRAVITY = 980.0  # pixels per second squared, as in a simple Ball model
    FLOOR_BOUNCE = 0.28
    MAX_THROW_SPEED = 1500.0
    WALK_SPEED = 54.0
    WANDER_INTERVAL = (1.5, 4.0)

    def __init__(
        self,
        x: float,
        y: float,
        radius: float = 38,
        *,
        floor_y: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = float(radius)
        self.state = PetState.IDLE
        self.mood = "content"
        self.energy = 1.0
        self.floor_y = floor_y

        self._rng = random.Random(seed)
        self._wander_timer = 0.0
        self._behavior_timer = self._rng.uniform(1.0, 2.5)
        self._action_duration = 0.0
        self._action_elapsed = 0.0
        self._rest_side = 1
        self._facing = 1
        self._drag_offset = (0.0, 0.0)
        self._mouse_history: list[tuple[float, float, float]] = []
        self._time = 0.0
        self._blink_timer = self._rng.uniform(1.8, 4.0)
        self._blink_remaining = 0.0

    def reset(self, x: float, floor_y: float) -> None:
        """Return the pet to a calm starting position on the desk."""
        self.x = float(x)
        self.floor_y = float(floor_y)
        self.y = self.floor_y - self.radius
        self.vx = self.vy = 0.0
        self.state = PetState.IDLE
        self.mood = "content"
        self.energy = 1.0
        self._wander_timer = 0.0
        self._behavior_timer = self._rng.uniform(1.0, 2.5)
        self._action_duration = 0.0
        self._action_elapsed = 0.0

    def begin_drag(self, mouse_x: float, mouse_y: float, now: float) -> bool:
        """Pick the pet up if the mouse is inside its circular hit area."""
        if math.hypot(mouse_x - self.x, mouse_y - self.y) > self.radius * 1.25:
            return False
        self.state = PetState.DRAGGED
        self.mood = "curious"
        self._action_elapsed = 0.0
        self.vx = self.vy = 0.0
        self._drag_offset = (self.x - mouse_x, self.y - mouse_y)
        self._mouse_history = [(now, mouse_x, mouse_y)]
        return True

    def drag_to(self, mouse_x: float, mouse_y: float, now: float) -> None:
        """Follow the cursor while retaining the original grab offset."""
        if self.state != PetState.DRAGGED:
            return
        offset_x, offset_y = self._drag_offset
        self.x = mouse_x + offset_x
        self.y = mouse_y + offset_y
        self._mouse_history.append((now, mouse_x, mouse_y))
        cutoff = now - 0.14
        self._mouse_history = [sample for sample in self._mouse_history if sample[0] >= cutoff]

    def release_drag(self, now: float) -> None:
        """Release the pet, inheriting recent mouse velocity for a throw."""
        if self.state != PetState.DRAGGED:
            return
        if len(self._mouse_history) >= 2:
            first, last = self._mouse_history[0], self._mouse_history[-1]
            elapsed = max(last[0] - first[0], 1 / 240)
            self.vx = (last[1] - first[1]) / elapsed
            self.vy = (last[2] - first[2]) / elapsed
            speed = math.hypot(self.vx, self.vy)
            if speed > self.MAX_THROW_SPEED:
                scale = self.MAX_THROW_SPEED / speed
                self.vx *= scale
                self.vy *= scale
        else:
            self.vx = self.vy = 0.0
        self.state = PetState.FALLING
        self.mood = "surprised" if abs(self.vy) > 180 else "content"

    def update(self, dt: float, bounds: pygame.Rect, now: Optional[float] = None) -> None:
        """Advance the state machine and physics by ``dt`` seconds."""
        dt = max(0.0, min(float(dt), 0.05))  # stable after pauses/window drags
        if now is None:
            self._time += dt
        else:
            self._time = now
        floor = float(self.floor_y if self.floor_y is not None else bounds.bottom - 44)

        self._blink_timer -= dt
        if self._blink_timer <= 0 and self._blink_remaining <= 0:
            self._blink_remaining = 0.12
            self._blink_timer = self._rng.uniform(2.2, 4.5)
        self._blink_remaining = max(0.0, self._blink_remaining - dt)

        if self.state == PetState.DRAGGED:
            self._keep_in_bounds(bounds)
            return

        if self.state == PetState.IDLE:
            self.vx = self.vy = 0.0
            self._behavior_timer -= dt
            if self._behavior_timer <= 0:
                self._choose_autonomous_action()

        elif self.state == PetState.WANDER:
            self.x += self.vx * dt
            self._facing = 1 if self.vx >= 0 else -1
            self.energy = max(0.0, self.energy - dt * 0.045)
            self._action_elapsed += dt
            if self._action_elapsed >= self._action_duration:
                self._finish_autonomous_action()

        elif self.state in (PetState.REST, PetState.NAP, PetState.GROOM, PetState.LOOK_AROUND):
            self.vx = self.vy = 0.0
            self._action_elapsed += dt
            if self.state == PetState.NAP:
                self.energy = min(1.0, self.energy + dt * 0.13)
            if self._action_elapsed >= self._action_duration:
                self._finish_autonomous_action()

        elif self.state == PetState.FALLING:
            self.vy += self.GRAVITY * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.vx *= max(0.0, 1.0 - 0.8 * dt)
            if self.y + self.radius >= floor:
                self.y = floor - self.radius
                if abs(self.vy) > 65:
                    self.vy = -self.vy * self.FLOOR_BOUNCE
                    self.mood = "surprised"
                else:
                    self.vy = 0.0
                if abs(self.vy) < 28 and abs(self.vx) < 18:
                    self.vx = self.vy = 0.0
                    self.state = PetState.IDLE
                    self.mood = "content"
                    self._wander_timer = self._rng.uniform(*self.WANDER_INTERVAL)
                self.energy = min(1.0, self.energy + dt * 0.06)

        self._keep_in_bounds(bounds)

    def _choose_autonomous_action(self) -> None:
        """Pick a small autonomous activity, weighted by current energy."""
        choices = [PetState.WANDER, PetState.REST, PetState.GROOM, PetState.LOOK_AROUND]
        weights = [45, 18, 18, 19]
        if self.energy < 0.42:
            choices.append(PetState.NAP)
            weights = [16, 24, 12, 13, 35]
        action = self._rng.choices(choices, weights=weights, k=1)[0]
        self.state = action
        self._action_elapsed = 0.0

        if action == PetState.WANDER:
            self._facing = self._rng.choice((-1, 1))
            self.vx = self._facing * self.WALK_SPEED
            self._action_duration = self._rng.uniform(1.4, 4.2)
            self.mood = "playful"
        elif action == PetState.REST:
            self._rest_side = self._rng.choice((-1, 1))
            self._action_duration = self._rng.uniform(1.8, 3.5)
            self.mood = "relaxed"
        elif action == PetState.NAP:
            self._action_duration = self._rng.uniform(3.5, 7.0)
            self.mood = "sleepy"
        elif action == PetState.GROOM:
            self._action_duration = self._rng.uniform(1.2, 2.2)
            self.mood = "shy"
        else:
            self._facing = self._rng.choice((-1, 1))
            self._action_duration = self._rng.uniform(1.0, 2.0)
            self.mood = "curious"

    def _finish_autonomous_action(self) -> None:
        """Return from a finished pose to a short calm idle interval."""
        self.state = PetState.IDLE
        self.vx = self.vy = 0.0
        self._action_elapsed = 0.0
        self.mood = "content" if self.energy >= 0.3 else "sleepy"
        self._behavior_timer = self._rng.uniform(0.6, 1.8)

    def _keep_in_bounds(self, bounds: pygame.Rect) -> None:
        """Clamp the character inside the window and soften edge collisions."""
        left, right = bounds.left + self.radius, bounds.right - self.radius
        if self.x < left:
            self.x = left
            if self.vx < 0:
                self.vx = abs(self.vx) * 0.35
            self._facing = 1
        elif self.x > right:
            self.x = right
            if self.vx > 0:
                self.vx = -abs(self.vx) * 0.35
            self._facing = -1
        top = bounds.top + self.radius * 0.35
        bottom = bounds.bottom - self.radius
        if self.y < top:
            self.y = top
            if self.vy < 0:
                self.vy = 0.0
        elif self.y > bottom:
            self.y = bottom
            if self.vy > 0:
                self.vy = 0.0

    def draw(self, surface: pygame.Surface, now: float) -> None:
        """Draw a fully procedural witch-hat sprite with simple animation."""
        bob = 0.0
        lean = 0.0
        if self.state == PetState.IDLE:
            bob = math.sin(now * 2.3) * 2.2
        elif self.state == PetState.WANDER:
            bob = abs(math.sin(now * 11.0)) * 3.0
        elif self.state == PetState.DRAGGED:
            bob = math.sin(now * 8.0) * 2.0
        elif self.state == PetState.REST:
            lean = self._rest_side * 0.20
            bob = -3.0 + math.sin(now * 2.0) * 1.0
        elif self.state == PetState.NAP:
            lean = self._facing * 0.34
            bob = 3.0 + math.sin(now * 2.4) * 1.5
        elif self.state == PetState.GROOM:
            bob = math.sin(self._action_elapsed * 13.0) * 1.2

        cx, cy = int(self.x), int(self.y + bob)
        r = int(self.radius)
        shadow = pygame.Rect(cx - r + 7, cy + r - 8, r * 2 - 14, 9)
        pygame.draw.ellipse(surface, (50, 43, 71, 70), shadow)

        # Soft little body, cheeks, and feet; resting poses curl lower to the desk.
        body_top = -0.08 if self.state not in (PetState.REST, PetState.NAP) else 0.04
        body_height = 1.30 if self.state not in (PetState.REST, PetState.NAP) else 1.12
        body = pygame.Rect(cx - r * 0.72, cy + int(r * body_top), int(r * 1.44), int(r * body_height))
        pygame.draw.ellipse(surface, (250, 224, 196), body)
        pygame.draw.ellipse(surface, (255, 241, 222), body.inflate(-7, -6))
        pygame.draw.ellipse(surface, (239, 151, 151), (cx - r * 0.55, cy + 7, 10, 6))
        pygame.draw.ellipse(surface, (239, 151, 151), (cx + r * 0.36, cy + 7, 10, 6))
        foot_y = cy + (r - 3 if self.state not in (PetState.REST, PetState.NAP) else r - 5)
        pygame.draw.ellipse(surface, (87, 68, 83), (cx - 13, foot_y, 12, 7))
        pygame.draw.ellipse(surface, (87, 68, 83), (cx + 2, foot_y, 12, 7))

        # Tilt the hat by a few degrees while wandering and curl it for naps.
        tilt = -math.sin(now * 2.8) * 0.08 if self.state == PetState.WANDER else lean
        hat_points = [(-22, -7), (20, -7), (2, -r * 1.22)]
        rotated = []
        for px, py in hat_points:
            rx = px * math.cos(tilt) - py * math.sin(tilt)
            ry = px * math.sin(tilt) + py * math.cos(tilt)
            rotated.append((cx + int(rx), cy + int(ry)))
        pygame.draw.polygon(surface, (76, 62, 112), rotated)
        pygame.draw.ellipse(surface, (63, 49, 98), (cx - r * 0.78, cy - 12, int(r * 1.56), 12))
        pygame.draw.ellipse(surface, (244, 190, 107), (cx + 3, cy - 24, 8, 5))

        # Face expression changes with mood. Blink frames are time-based.
        eye_y = cy + 10
        if self.state == PetState.LOOK_AROUND:
            look_offset = self._facing * 3
            pygame.draw.ellipse(surface, (52, 46, 66), (cx - 11 + look_offset, eye_y - 3, 5, 8))
            pygame.draw.ellipse(surface, (52, 46, 66), (cx + 6 + look_offset, eye_y - 3, 5, 8))
            pygame.draw.circle(surface, (255, 255, 255), (cx - 9 + look_offset, eye_y - 1), 1)
            pygame.draw.circle(surface, (255, 255, 255), (cx + 8 + look_offset, eye_y - 1), 1)
        elif self.state == PetState.NAP:
            pygame.draw.arc(surface, (60, 49, 68), (cx - 13, eye_y, 8, 5), math.pi, math.tau, 2)
            pygame.draw.arc(surface, (60, 49, 68), (cx + 5, eye_y, 8, 5), math.pi, math.tau, 2)
            z_text = pygame.font.SysFont("segoeui,arial", 13, bold=True).render("z", True, (111, 94, 142))
            surface.blit(z_text, (cx + r - 4, cy - r - int((self._action_elapsed * 10) % 8)))
        elif self.state == PetState.GROOM:
            # A tiny paw rises to the cheek for a repeated washing motion.
            paw_y = eye_y + 4 + int(abs(math.sin(self._action_elapsed * 13.0)) * 5)
            pygame.draw.ellipse(surface, (250, 224, 196), (cx + 12, paw_y, 9, 8))
            pygame.draw.line(surface, (60, 49, 68), (cx - 11, eye_y + 1), (cx - 6, eye_y + 1), 2)
            pygame.draw.ellipse(surface, (52, 46, 66), (cx + 6, eye_y - 3, 5, 7))
        elif self.state == PetState.REST or self._blink_remaining > 0:
            pygame.draw.line(surface, (60, 49, 68), (cx - 12, eye_y + 2), (cx - 6, eye_y + 2), 2)
            pygame.draw.line(surface, (60, 49, 68), (cx + 6, eye_y + 2), (cx + 12, eye_y + 2), 2)
        else:
            pygame.draw.ellipse(surface, (52, 46, 66), (cx - 11, eye_y - 3, 5, 8))
            pygame.draw.ellipse(surface, (52, 46, 66), (cx + 6, eye_y - 3, 5, 8))
            pygame.draw.circle(surface, (255, 255, 255), (cx - 9, eye_y - 1), 1)
            pygame.draw.circle(surface, (255, 255, 255), (cx + 8, eye_y - 1), 1)
        if self.mood == "surprised":
            pygame.draw.ellipse(surface, (112, 68, 83), (cx - 2, eye_y + 8, 5, 6))
        else:
            pygame.draw.arc(surface, (135, 78, 89), (cx - 4, eye_y + 5, 8, 7), math.pi, math.tau, 2)

    @property
    def state_name(self) -> str:
        """Human-readable state for the status bar."""
        return self.state.name
