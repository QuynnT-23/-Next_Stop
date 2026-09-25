"""Projectile entities for bullets, shrapnel, and electric plasma."""
import pygame
from src.combat.damage import DamageEvent
from src.config import COLOR_WHITE

class Projectile:
    """Moving hitbox that deals damage on collision with entities or dissipates on walls."""
    def __init__(self, x: float, y: float, vel: pygame.math.Vector2,
                 damage_event: DamageEvent, radius: float = 4.0,
                 lifetime: float = 1.0, color: tuple = COLOR_WHITE,
                 owner: str = "player", pierce: int = 0):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = vel
        self.damage_event = damage_event
        self.radius = radius
        self.lifetime = lifetime
        self.color = color
        self.owner = owner  # "player" or "enemy"
        self.pierce = pierce
        self.hit_entities = set()
        self.is_alive = True

    def update(self, dt: float, train_car) -> bool:
        """Update position and check train car wall collisions. Returns False when dead."""
        if not self.is_alive:
            return False
            
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        self.pos += self.vel * dt

        # Check collision with train car boundaries and obstacles
        if train_car:
            if not train_car.is_inside_playable_area(self.pos):
                return False
            for obs in train_car.obstacles:
                if obs.collidepoint(self.pos.x, self.pos.y):
                    return False

        return True

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        r = int(self.radius)
        if r <= 0:
            return
            
        # Draw glowing core and border
        pygame.draw.circle(surface, self.color, screen_pos, r)
        # Glow ring
        if r >= 3:
            pygame.draw.circle(surface, (255, 255, 255), screen_pos, max(1, r - 2))
