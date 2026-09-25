"""Base Entity class defining physics, collision, health, and flash timers."""
import pygame
from src.combat.damage import DamageEvent

class Entity:
    """Base class for all living game objects (Player, Enemies, Bosses)."""
    def __init__(self, x: float, y: float, radius: float, max_health: int, speed: float):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.radius = radius
        self.max_health = max_health
        self.health = max_health
        self.base_speed = speed
        self.speed = speed
        self.friction = 1400.0
        
        # Combat feedback states
        self.flash_timer = 0.0          # Seconds to flash white on hit
        self.invulnerable_timer = 0.0   # Seconds to ignore incoming damage
        self.is_dead = False
        self.walk_distance = 0.0        # Cumulative distance traveled for walk cycle animations

    def is_alive(self) -> bool:
        return not self.is_dead and self.health > 0

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        """Process incoming damage. Returns True if damage was applied."""
        if not self.is_alive() or self.invulnerable_timer > 0:
            return False

        self.health = max(0, self.health - damage_event.amount)
        self.flash_timer = 0.12
        
        # Apply knockback
        if damage_event.knockback.length_squared() > 0:
            self.vel += damage_event.knockback

        # Floating combat text
        game_state.particles.add_damage_number(
            self.pos.x, self.pos.y,
            damage_event.amount,
            is_crit=damage_event.is_crit,
            damage_type=damage_event.damage_type
        )

        if self.health <= 0:
            self.die(game_state)

        return True

    def heal(self, amount: int):
        """Restore health up to max."""
        self.health = min(self.max_health, self.health + amount)

    def die(self, game_state):
        """Called upon reaching 0 health."""
        self.is_dead = True

    def resolve_obstacle_collisions(self, train_car):
        """Resolve circular collision with train car walls and rectangular obstacles."""
        if not train_car:
            return

        # 1. Clamp to train car interior boundaries
        bounds = train_car.get_playable_bounds()
        door_mid_y = (train_car.top_wall_y + train_car.bottom_wall_y) // 2
        in_doorway = (door_mid_y - 65 <= self.pos.y <= door_mid_y + 65)
        
        if getattr(train_car, "exit_unlocked", False) and in_doorway:
            max_x = train_car.width + 40
        else:
            max_x = bounds.right - self.radius

        self.pos.x = max(bounds.left + self.radius, min(self.pos.x, max_x))
        self.pos.y = max(bounds.top + self.radius, min(self.pos.y, bounds.bottom - self.radius))

        # 2. Rectangular obstacles (seats, crates, tables)
        for obs in train_car.obstacles:
            # Find closest point on rectangle to circle center
            closest_x = max(obs.left, min(self.pos.x, obs.right))
            closest_y = max(obs.top, min(self.pos.y, obs.bottom))
            
            diff_x = self.pos.x - closest_x
            diff_y = self.pos.y - closest_y
            dist_sq = diff_x * diff_x + diff_y * diff_y
            
            if dist_sq < self.radius * self.radius and dist_sq > 0.0001:
                dist = dist_sq ** 0.5
                overlap = self.radius - dist
                normal_x = diff_x / dist
                normal_y = diff_y / dist
                self.pos.x += normal_x * overlap
                self.pos.y += normal_y * overlap
                # Dampen velocity along collision normal
                dot = self.vel.x * normal_x + self.vel.y * normal_y
                if dot < 0:
                    self.vel.x -= dot * normal_x
                    self.vel.y -= dot * normal_y

    def update_physics(self, dt: float):
        """Apply friction drag and integrate velocity."""
        if self.vel.length_squared() > 0:
            drag = self.friction * dt
            if self.vel.length() <= drag:
                self.vel = pygame.math.Vector2(0, 0)
            else:
                self.vel -= self.vel.normalize() * drag

        self.pos += self.vel * dt
        spd = self.vel.length()
        if spd > 10.0:
            self.walk_distance += spd * dt

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
