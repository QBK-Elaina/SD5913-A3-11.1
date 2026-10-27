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

# Soft pastel palette for the procedural character.
HAIR = (247, 204, 194)
HAIR_LIGHT = (253, 229, 219)
HAIR_SHADE = (229, 174, 168)
SKIN = (255, 238, 227)
SKIN_SHADE = (247, 213, 198)
CREAM = (253, 249, 244)
BOW = (214, 84, 96)
BOW_LIGHT = (232, 118, 124)
BOW_DARK = (176, 60, 76)
GOLD = (245, 198, 105)
EYE = (190, 112, 48)
EYE_LIGHT = (246, 190, 100)
EYE_DARK = (92, 52, 34)
MOUTH = (188, 116, 116)


class PetState(Enum):
    """The interaction/motion states used by :class:`DeskPet`."""

    IDLE = auto()
    WANDER = auto()
    REST = auto()
    NAP = auto()
    GROOM = auto()
    LOOK_AROUND = auto()
    GO_TO_CHAIR = auto()
    SIT_CHAIR = auto()
    GO_TO_BED = auto()
    NAP_BED = auto()
    RETURN_TO_FLOOR = auto()
    CHEER = auto()
    DRAGGED = auto()
    FALLING = auto()


class DeskPet:
    """A procedural cat-eared chibi companion with drag, throw, and soft-bounce physics."""

    GRAVITY = 980.0  # pixels per second squared, as in a simple Ball model
    FLOOR_BOUNCE = 0.28
    MAX_THROW_SPEED = 1500.0
    WALK_SPEED = 54.0
    WANDER_INTERVAL = (1.5, 4.0)
    TAP_COOLDOWN = 1.25
    CHEER_DURATION = 0.95

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
        self._return_x = self.x
        self._return_y = self.y
        self._furniture_kind = ""
        self._trip_start_x = self.x
        self._trip_start_y = self.y
        self._trip_target_x = self.x
        self._trip_target_y = self.y
        self._trip_elapsed = 0.0
        self._trip_duration = 0.0
        self._trip_arrival_state = PetState.IDLE
        self._furniture_timer = 0.0
        self._cheer_return_state = PetState.IDLE
        self._cheer_return_mood = "content"
        self.chair_x = self.x
        self.chair_y = self.y
        self.bed_x = self.x
        self.bed_y = self.y
        self._furniture_ready = False
        self._furniture_pause = 8.0

        self._rng = random.Random(seed)
        self._furniture_pause = self._rng.uniform(7.0, 13.0)
        self._wander_timer = 0.0
        self._behavior_timer = self._rng.uniform(1.0, 2.5)
        self._action_duration = 0.0
        self._action_elapsed = 0.0
        self._cheer_timer = 0.0
        self._cheer_was_falling = False
        self._tap_cooldown = 0.0
        self.feedback = ""
        self.feedback_timer = 0.0
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
        self._return_x = self.x
        self._return_y = self.y
        self._furniture_kind = ""
        self._furniture_pause = self._rng.uniform(7.0, 13.0)
        self._trip_start_x = self.x
        self._trip_start_y = self.y
        self._trip_target_x = self.x
        self._trip_target_y = self.y
        self._trip_elapsed = 0.0
        self._trip_duration = 0.0
        self._trip_arrival_state = PetState.IDLE
        self._furniture_timer = 0.0
        self._cheer_return_state = PetState.IDLE
        self.vx = self.vy = 0.0
        self.state = PetState.IDLE
        self.mood = "content"
        self.energy = 1.0
        self._wander_timer = 0.0
        self._behavior_timer = self._rng.uniform(1.0, 2.5)
        self._action_duration = 0.0
        self._action_elapsed = 0.0
        self._cheer_timer = 0.0
        self._cheer_was_falling = False
        self._tap_cooldown = 0.0
        self.feedback = ""
        self.feedback_timer = 0.0

    def set_furniture_spots(
        self,
        chair_x: float,
        chair_surface_y: float,
        bed_x: float,
        bed_surface_y: float,
    ) -> None:
        """Set furniture top-surface positions in the current window layout."""
        self.chair_x = float(chair_x)
        self.chair_y = float(chair_surface_y) - self.radius
        self.bed_x = float(bed_x)
        # The bed pose lies sideways, so raise its center to keep the sprite on the mattress.
        self.bed_y = float(bed_surface_y) - self.radius * 1.25
        self._furniture_ready = True

    def hit_test(self, mouse_x: float, mouse_y: float) -> bool:
        """Return whether a pointer position is inside the forgiving pet hit area."""
        return math.hypot(mouse_x - self.x, mouse_y - self.y) <= self.radius * 1.5

    def tap(self) -> bool:
        """Cheer on a deliberate tap, or explain the brief repeat-tap cooldown."""
        if self._tap_cooldown > 0:
            if not self.feedback.startswith("Wait"):
                self.feedback = "Wait a moment — let me enjoy that!"
                self.feedback_timer = 1.25
            return False

        self._cheer_was_falling = self.state == PetState.FALLING
        self._cheer_return_state = self.state
        self._cheer_return_mood = self.mood
        if not self._cheer_was_falling:
            self.vx = self.vy = 0.0
            if self.state not in (PetState.SIT_CHAIR, PetState.NAP_BED,
                                  PetState.GO_TO_CHAIR, PetState.GO_TO_BED,
                                  PetState.RETURN_TO_FLOOR):
                self._cheer_return_state = PetState.IDLE
        if self._cheer_return_state in (PetState.GO_TO_CHAIR, PetState.GO_TO_BED, PetState.RETURN_TO_FLOOR):
            remaining = math.hypot(self._trip_target_x - self.x, self._trip_target_y - self.y)
            self._trip_duration = max(0.35, remaining / (self.WALK_SPEED * 1.8))
            self._trip_elapsed = 0.0
            self._trip_start_x, self._trip_start_y = self.x, self.y
        self.state = PetState.CHEER
        self.mood = "happy"
        self._action_elapsed = 0.0
        self._cheer_timer = self.CHEER_DURATION
        self._tap_cooldown = self.TAP_COOLDOWN
        self.feedback = "Aww, that feels nice!"
        self.feedback_timer = 1.8
        return True

    def begin_drag(self, mouse_x: float, mouse_y: float, now: float) -> bool:
        """Pick the pet up if the mouse is inside its forgiving hit area."""
        if not self.hit_test(mouse_x, mouse_y):
            return False
        self._cheer_return_state = PetState.IDLE
        self._cheer_return_mood = "content"
        self._furniture_kind = ""
        self._trip_elapsed = 0.0
        self._trip_duration = 0.0
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
        self._furniture_pause = max(0.0, self._furniture_pause - dt)
        self._tap_cooldown = max(0.0, self._tap_cooldown - dt)
        self.feedback_timer = max(0.0, self.feedback_timer - dt)
        if self.feedback_timer == 0.0:
            self.feedback = ""

        self._blink_timer -= dt
        if self._blink_timer <= 0 and self._blink_remaining <= 0:
            self._blink_remaining = 0.12
            self._blink_timer = self._rng.uniform(2.2, 4.5)
        self._blink_remaining = max(0.0, self._blink_remaining - dt)

        if self.state == PetState.DRAGGED:
            self._keep_in_bounds(bounds)
            return

        if self.state == PetState.CHEER:
            self._cheer_timer = max(0.0, self._cheer_timer - dt)
            self._action_elapsed += dt
            if self._cheer_was_falling:
                self.vy += self.GRAVITY * dt
                self.x += self.vx * dt
                self.y += self.vy * dt
                if self.y + self.radius >= floor:
                    self.y = floor - self.radius
                    if abs(self.vy) > 65:
                        self.vy = -self.vy * self.FLOOR_BOUNCE
                    else:
                        self.vy = 0.0
                        self._cheer_was_falling = False
                        self.vx = 0.0
            if self._cheer_timer == 0.0:
                if self._cheer_was_falling:
                    self.state = PetState.FALLING
                    self.mood = "content"
                else:
                    self.state = self._cheer_return_state
                    self.mood = self._cheer_return_mood
                    if self.state in (PetState.GO_TO_CHAIR, PetState.GO_TO_BED, PetState.RETURN_TO_FLOOR):
                        self._trip_start_x = self.x
                        self._trip_start_y = self.y
                        self._trip_elapsed = 0.0
                    if self.state == PetState.IDLE:
                        self._behavior_timer = self._rng.uniform(0.8, 1.8)

        elif self.state in (PetState.GO_TO_CHAIR, PetState.GO_TO_BED, PetState.RETURN_TO_FLOOR):
            self._update_furniture_trip(dt)

        elif self.state in (PetState.SIT_CHAIR, PetState.NAP_BED):
            self.vx = self.vy = 0.0
            self._furniture_timer -= dt
            self._action_elapsed += dt
            if self.state == PetState.NAP_BED:
                self.energy = min(1.0, self.energy + dt * 0.16)
            if self._furniture_timer <= 0:
                self._start_return_trip(floor)

        elif self.state == PetState.IDLE:
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
        """Pick a floor activity or a furniture visit, weighted by energy."""
        choices = [PetState.WANDER, PetState.REST, PetState.GROOM, PetState.LOOK_AROUND]
        weights = [40, 17, 16, 17]
        if self.energy < 0.42:
            choices.append(PetState.NAP)
            weights.append(28)
            if self._furniture_ready and self._furniture_pause <= 0:
                choices.append(PetState.GO_TO_BED)
                weights.append(19)
        elif self._furniture_ready and self._furniture_pause <= 0:
            choices.extend((PetState.GO_TO_CHAIR, PetState.GO_TO_BED))
            weights.extend((11, 7))
        action = self._rng.choices(choices, weights=weights, k=1)[0]
        self.state = action
        self._action_elapsed = 0.0

        if action == PetState.WANDER:
            self._facing = self._rng.choice((-1, 1))
            self.vx = self._facing * self.WALK_SPEED
            self._action_duration = self._rng.uniform(1.4, 4.2)
            self.mood = "playful"
        elif action in (PetState.GO_TO_CHAIR, PetState.GO_TO_BED):
            if action == PetState.GO_TO_CHAIR:
                destination = (self.chair_x, self.chair_y)
                self._furniture_kind = "chair"
                self._trip_arrival_state = PetState.SIT_CHAIR
                self.mood = "curious"
            else:
                destination = (self.bed_x, self.bed_y)
                self._furniture_kind = "bed"
                self._trip_arrival_state = PetState.NAP_BED
                self.mood = "sleepy"
            self._return_x = self.x
            self._return_y = float(self.floor_y if self.floor_y is not None else self.y + self.radius)
            self._start_furniture_trip(*destination, arrival_state=self._trip_arrival_state)
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

    def _start_furniture_trip(self, target_x: float, target_y: float, *, arrival_state: PetState) -> None:
        """Start a smooth, hop-like route to a furniture surface."""
        self._trip_start_x = self.x
        self._trip_start_y = self.y
        self._trip_target_x = float(target_x)
        self._trip_target_y = float(target_y)
        self._trip_elapsed = 0.0
        self._trip_duration = max(0.7, abs(self._trip_target_x - self.x) / (self.WALK_SPEED * 1.8))
        self._trip_arrival_state = arrival_state
        self.state = PetState.GO_TO_CHAIR if arrival_state == PetState.SIT_CHAIR else PetState.GO_TO_BED
        self._action_elapsed = 0.0
        self.mood = "curious" if arrival_state == PetState.SIT_CHAIR else "sleepy"
        self._furniture_pause = self._rng.uniform(10.0, 18.0)

    def _start_return_trip(self, floor_y: float) -> None:
        """Hop back to the remembered floor position after using furniture."""
        self._start_furniture_trip(self._return_x, floor_y - self.radius, arrival_state=PetState.IDLE)
        self.state = PetState.RETURN_TO_FLOOR
        self._furniture_pause = self._rng.uniform(10.0, 18.0)

    def _update_furniture_trip(self, dt: float) -> None:
        """Advance the furniture route with a small arc and land at the target."""
        self._trip_elapsed = min(self._trip_duration, self._trip_elapsed + dt)
        progress = self._trip_elapsed / max(self._trip_duration, 0.001)
        self.x = self._trip_start_x + (self._trip_target_x - self._trip_start_x) * progress
        base_y = self._trip_start_y + (self._trip_target_y - self._trip_start_y) * progress
        self.y = base_y - math.sin(progress * math.pi) * self.radius * 0.9
        self._facing = 1 if self._trip_target_x >= self._trip_start_x else -1
        if progress >= 1.0:
            self.x = self._trip_target_x
            self.y = self._trip_target_y
            self.vx = self.vy = 0.0
            self._action_elapsed = 0.0
            if self._trip_arrival_state == PetState.IDLE:
                self.state = PetState.IDLE
                self.mood = "content"
                self._behavior_timer = self._rng.uniform(0.8, 1.8)
                self._furniture_kind = ""
                self._furniture_pause = self._rng.uniform(10.0, 18.0)
            else:
                self.state = self._trip_arrival_state
                self._furniture_timer = self._rng.uniform(3.0, 5.0)
                self.mood = "relaxed" if self.state == PetState.SIT_CHAIR else "sleepy"

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
        """Draw the cat-eared chibi companion, fully procedurally."""
        bob = 0.0
        lean = 0.0
        if self.state == PetState.IDLE:
            bob = math.sin(now * 2.3) * 2.0
        elif self.state == PetState.CHEER:
            bob = -abs(math.sin(self._action_elapsed * math.pi * 2.0)) * 6.0
        elif self.state == PetState.WANDER:
            bob = abs(math.sin(now * 10.0)) * 3.2
        elif self.state == PetState.DRAGGED:
            bob = math.sin(now * 8.0) * 2.0
        elif self.state == PetState.REST:
            lean = self._rest_side * 0.12
            bob = 3.0 + math.sin(now * 2.0) * 1.0
        elif self.state == PetState.SIT_CHAIR:
            bob = math.sin(now * 2.0) * 1.2
        elif self.state in (PetState.GO_TO_CHAIR, PetState.GO_TO_BED, PetState.RETURN_TO_FLOOR):
            bob = -abs(math.sin(self._trip_elapsed / max(self._trip_duration, 0.01) * math.pi)) * 5.0
        elif self.state == PetState.NAP_BED:
            lean = self._facing * 0.68
            bob = 2.0 + math.sin(now * 2.4) * 1.0
        elif self.state == PetState.NAP:
            lean = self._facing * 0.14
            bob = 5.0 + math.sin(now * 2.4) * 1.2
        elif self.state == PetState.GROOM:
            bob = math.sin(self._action_elapsed * 13.0) * 1.0

        r = float(self.radius)
        cx, cy = float(self.x), float(self.y + bob)

        # Contact shadow stays on the desk while the character bobs above it.
        shadow_w = max(10, int(r * 1.7))
        shadow = pygame.Rect(int(cx - shadow_w / 2), int(cy + r - 5), shadow_w, max(6, int(r * 0.18)))
        pygame.draw.ellipse(surface, (74, 58, 70), shadow)

        sprite = pygame.Surface((int(r * 4), int(r * 4.4)), pygame.SRCALPHA)
        ox, oy = r * 2, r * 2.2

        def rr(x: float, y: float, w: float, h: float) -> pygame.Rect:
            return pygame.Rect(
                round(ox + (x - w / 2) * r),
                round(oy + (y - h / 2) * r),
                max(1, round(w * r)),
                max(1, round(h * r)),
            )

        def pp(x: float, y: float) -> tuple[int, int]:
            return (round(ox + x * r), round(oy + y * r))

        def star(cx_: float, cy_: float, outer: float, inner: float, color: tuple[int, int, int]) -> None:
            points = []
            for index in range(10):
                angle = -math.pi / 2 + index * math.pi / 5
                radius = outer if index % 2 == 0 else inner
                points.append((round(ox + cx_ * r + radius * math.cos(angle)),
                               round(oy + cy_ * r + radius * math.sin(angle))))
            pygame.draw.polygon(sprite, color, points)

        # Hair silhouette behind the body: peach-pink hime cut with twin locks.
        pygame.draw.ellipse(sprite, HAIR_SHADE, rr(0, 0.10, 1.74, 1.82))
        pygame.draw.ellipse(sprite, HAIR, rr(0, 0.07, 1.64, 1.74))

        # White dress with red puff sleeves and a ribbon at the chest.
        pygame.draw.polygon(sprite, CREAM, [pp(-0.50, 0.16), pp(0.50, 0.16), pp(0.70, 0.92), pp(-0.70, 0.92)])
        pygame.draw.ellipse(sprite, CREAM, rr(0, 0.86, 1.40, 0.22))
        pygame.draw.line(sprite, (238, 226, 221), pp(0, 0.34), pp(0, 0.88), 1)
        for side in (-1, 1):
            pygame.draw.ellipse(sprite, BOW, rr(side * 0.56, 0.44, 0.36, 0.62))
            pygame.draw.ellipse(sprite, BOW_LIGHT, rr(side * 0.58, 0.34, 0.22, 0.20))
            pygame.draw.ellipse(sprite, CREAM, rr(side * 0.55, 0.71, 0.24, 0.16))
            pygame.draw.line(sprite, GOLD, pp(side * 0.48, 0.30), pp(side * 0.30, 0.48), 1)

        # Collar and red neck ribbon.
        pygame.draw.polygon(sprite, (255, 255, 255), [pp(-0.30, 0.14), pp(0.30, 0.14), pp(0.0, 0.34)])
        pygame.draw.line(sprite, GOLD, pp(-0.30, 0.16), pp(0.0, 0.34), 1)
        pygame.draw.line(sprite, GOLD, pp(0.30, 0.16), pp(0.0, 0.34), 1)
        pygame.draw.polygon(sprite, BOW, [pp(-0.02, 0.44), pp(-0.24, 0.35), pp(-0.24, 0.50), pp(-0.02, 0.47)])
        pygame.draw.polygon(sprite, BOW, [pp(0.02, 0.44), pp(0.24, 0.35), pp(0.24, 0.50), pp(0.02, 0.47)])
        pygame.draw.circle(sprite, BOW_DARK, pp(0, 0.44), max(2, round(0.05 * r)))

        # Long side locks fall in front of the shoulders.
        for side in (-1, 1):
            pygame.draw.polygon(sprite, HAIR, [
                pp(side * 0.44, -0.44), pp(side * 0.82, -0.26),
                pp(side * 0.76, 0.74), pp(side * 0.60, 0.94), pp(side * 0.50, 0.52),
            ])
            pygame.draw.ellipse(sprite, HAIR_LIGHT, rr(side * 0.70, 0.45, 0.10, 0.48))

        # Round chibi face.
        pygame.draw.ellipse(sprite, SKIN_SHADE, rr(0, -0.30, 1.10, 1.04))
        pygame.draw.ellipse(sprite, SKIN, rr(0, -0.32, 1.02, 0.94))

        # Face: big amber eyes, or closed eyes while resting.
        closed = self.state in (PetState.REST, PetState.NAP, PetState.NAP_BED) or self._blink_remaining > 0
        gaze = self._facing * 0.035 if self.state == PetState.LOOK_AROUND else 0.0
        for side in (-1, 1):
            ex = side * 0.26
            if self.state == PetState.GROOM and side == 1:
                # Playful wink while grooming.
                pygame.draw.lines(sprite, EYE_DARK, False,
                                  [pp(ex - 0.11, -0.25), pp(ex, -0.20), pp(ex + 0.11, -0.25)], 3)
                continue
            if closed:
                pygame.draw.lines(sprite, EYE_DARK, False,
                                  [pp(ex - 0.11, -0.25), pp(ex, -0.21), pp(ex + 0.11, -0.25)], 3)
                continue
            eye = rr(ex, -0.24, 0.34, 0.38)
            pygame.draw.ellipse(sprite, (146, 96, 84), eye)
            inner = eye.inflate(-max(2, round(0.045 * r)), -max(2, round(0.045 * r)))
            pygame.draw.ellipse(sprite, (255, 255, 255), inner)
            iris = pygame.Rect(
                inner.x + round(0.025 * r) + round(gaze * r),
                inner.y + round(0.02 * r),
                max(2, inner.w - round(0.05 * r)),
                max(2, inner.h - round(0.05 * r)),
            )
            pygame.draw.ellipse(sprite, EYE_DARK, iris)
            pygame.draw.ellipse(sprite, EYE, iris.inflate(-max(2, round(0.035 * r)), -max(2, round(0.035 * r))))
            pupil = iris.inflate(-max(2, round(0.13 * r)), -max(2, round(0.17 * r)))
            pygame.draw.ellipse(sprite, EYE_DARK, pupil)
            pygame.draw.circle(sprite, (255, 255, 255),
                               (iris.x + max(2, round(0.05 * r)), iris.y + max(2, round(0.06 * r))),
                               max(2, round(0.065 * r)))
            pygame.draw.circle(sprite, (255, 255, 255),
                               (iris.right - max(1, round(0.05 * r)), iris.bottom - max(1, round(0.05 * r))),
                               max(1, round(0.03 * r)))

        # Blush and a small smile.
        pygame.draw.ellipse(sprite, (250, 188, 184), rr(-0.40, -0.07, 0.19, 0.09))
        pygame.draw.ellipse(sprite, (250, 188, 184), rr(0.40, -0.07, 0.19, 0.09))
        if self.state == PetState.DRAGGED or self.mood == "surprised":
            pygame.draw.ellipse(sprite, MOUTH, rr(0, 0.01, 0.07, 0.09))
        else:
            pygame.draw.lines(sprite, MOUTH, False,
                              [pp(-0.07, 0.01), pp(-0.035, 0.05), pp(0, 0.065), pp(0.035, 0.05), pp(0.07, 0.01)], 2)

        # Soft parted fringe, drawn over the brow and the top of the eyes.
        pygame.draw.ellipse(sprite, HAIR, rr(0, -0.70, 1.06, 0.54))
        for x, y, w, h in (
            (-0.38, -0.60, 0.46, 0.48),
            (-0.12, -0.62, 0.42, 0.50),
            (0.12, -0.62, 0.42, 0.50),
            (0.38, -0.60, 0.46, 0.48),
            (0.0, -0.56, 0.26, 0.40),
        ):
            pygame.draw.ellipse(sprite, HAIR, rr(x, y, w, h))

        # Cat ears with pink inner fur, peeking above the bangs.
        for side in (-1, 1):
            outer_ear = [pp(side * 0.28, -0.78), pp(side * 0.60, -1.30), pp(side * 0.84, -0.68)]
            inner_ear = [pp(side * 0.44, -0.82), pp(side * 0.61, -1.12), pp(side * 0.73, -0.75)]
            pygame.draw.polygon(sprite, HAIR, outer_ear)
            pygame.draw.polygon(sprite, (248, 187, 186), inner_ear)
            pygame.draw.lines(sprite, HAIR_SHADE, True, outer_ear, 2)

        # A soft tuft of hair fills the crown under the ribbon.
        pygame.draw.ellipse(sprite, HAIR, rr(0, -0.86, 0.64, 0.40))
        pygame.draw.ellipse(sprite, HAIR_LIGHT, rr(-0.10, -0.94, 0.20, 0.05))

        # Curl of hair (ahoge) above the bow.
        pygame.draw.lines(sprite, HAIR_SHADE, False,
                          [pp(0.02, -0.92), pp(0.07, -1.10), pp(0.18, -1.18), pp(0.22, -1.10)], 2)

        # Big red ribbon tied on top, with a gentle idle sway.
        sway = math.sin(now * 1.7) * 0.02
        pygame.draw.polygon(sprite, BOW, [pp(-0.04, -1.10), pp(-0.44 + sway, -1.26), pp(-0.52 + sway, -0.94), pp(-0.06, -0.99)])
        pygame.draw.polygon(sprite, BOW, [pp(0.04, -1.10), pp(0.44 - sway, -1.26), pp(0.52 - sway, -0.94), pp(0.06, -0.99)])
        pygame.draw.polygon(sprite, BOW_LIGHT, [pp(-0.10, -1.10), pp(-0.33 + sway, -1.18), pp(-0.35 + sway, -1.03), pp(-0.10, -1.05)])
        pygame.draw.polygon(sprite, BOW_LIGHT, [pp(0.10, -1.10), pp(0.33 - sway, -1.18), pp(0.35 - sway, -1.03), pp(0.10, -1.05)])
        pygame.draw.circle(sprite, BOW_DARK, pp(0, -1.08), max(2, round(0.09 * r)))

        # Gold star hair clip.
        star(-0.44, -0.52, 0.10 * r, 0.045 * r, GOLD)

        # Raised paw for grooming, drawn over the cheek.
        if self.state == PetState.GROOM:
            paw_y = -0.10 + abs(math.sin(self._action_elapsed * 13.0)) * 0.07
            pygame.draw.ellipse(sprite, SKIN, rr(0.36, paw_y, 0.24, 0.20))
            pygame.draw.ellipse(sprite, SKIN_SHADE, rr(0.36, paw_y, 0.24, 0.20), 1)

        if lean:
            sprite = pygame.transform.rotozoom(sprite, math.degrees(-lean), 1.0)
        surface.blit(sprite, sprite.get_rect(center=(round(cx), round(cy))))

        # Tiny hearts float above the bow as a clear response to a gentle tap.
        if self.state == PetState.CHEER:
            progress = min(1.0, self._action_elapsed / self.CHEER_DURATION)
            for index in range(2):
                drift = (progress + index * 0.38) % 1.0
                hx = int(cx + r * (0.48 + index * 0.35))
                hy = int(cy - r * (1.28 + drift * 0.28))
                size = max(6, int(r * 0.15))
                color = (235, 112, 137)
                pygame.draw.circle(surface, color, (hx - size // 4, hy), size // 4)
                pygame.draw.circle(surface, color, (hx + size // 4, hy), size // 4)
                pygame.draw.polygon(surface, color,
                                    [(hx - size // 2, hy), (hx + size // 2, hy), (hx, hy + size // 2)])

        # Sleepy Zs drift upward while napping.
        if self.state in (PetState.NAP, PetState.NAP_BED):
            for index in range(2):
                t = (self._action_elapsed * 0.55 + index * 0.5) % 1.0
                zx = int(cx + r * (0.55 + t * 0.30))
                zy = int(cy - r * (0.60 + t * 0.55))
                size = max(3, int(r * (0.10 + t * 0.05)))
                pygame.draw.lines(surface, (150, 128, 170), False,
                                  [(zx, zy), (zx + size, zy), (zx, zy + size), (zx + size, zy + size)], 2)

    @property
    def state_name(self) -> str:
        """Human-readable state for the status bar."""
        return self.state.name
