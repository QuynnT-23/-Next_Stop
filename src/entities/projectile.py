"""Projectile entities for bullets, shrapnel, and electric plasma."""
import pygame
from src.combat.damage import DamageEvent
from src.config import COLOR_WHITE

class Projectile:
    """Moving hitbox that deals damage on collision with entities or dissipates on walls."""
    def __init__(self, x: float, y: float, vel: pygame.math.Vector2,
                 damage_event: DamageEvent, radius: float = 4.0,
                 lifetime: float = 1.0, color: tuple = COLOR_WHITE,
                 owner: str = "player", pierce: int = 0, bounces: int = 0,
                 is_explosive: bool = False, explosion_radius: float = 0.0,
                 is_dragon_breath: bool = False):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = vel
        self.damage_event = damage_event
        self.radius = radius
        self.lifetime = lifetime
        self.color = color
        self.owner = owner  # "player" or "enemy"
        self.pierce = pierce
        self.bounces = bounces
        self.is_explosive = is_explosive
        self.explosion_radius = explosion_radius
        self.is_dragon_breath = is_dragon_breath
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
                if self.bounces > 0:
                    self.bounces -= 1
                    if self.pos.y <= train_car.top_wall_y + self.radius or self.pos.y >= train_car.bottom_wall_y - self.radius:
                        self.vel.y *= -1.0
                    else:
                        self.vel.x *= -1.0
                    self.pos.x = max(train_car.left_wall_x + 6, min(train_car.width - 6, self.pos.x))
                    self.pos.y = max(train_car.top_wall_y + 6, min(train_car.bottom_wall_y - 6, self.pos.y))
                    self.damage_event.amount = int(self.damage_event.amount * 1.5)
                else:
                    return False
            for obs in train_car.obstacles:
                if obs.collidepoint(self.pos.x, self.pos.y):
                    if self.bounces > 0:
                        self.bounces -= 1
                        self.vel.x *= -1.0
                        self.vel.y *= -1.0
                        self.damage_event.amount = int(self.damage_event.amount * 1.5)
                    else:
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
