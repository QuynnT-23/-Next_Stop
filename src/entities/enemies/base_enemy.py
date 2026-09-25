"""Base Enemy class with AI state machines, telegraphing, and flocking separation."""
import pygame
import math
import random
from src.entities.base import Entity
from src.combat.damage import DamageEvent
from src.config import COLOR_WHITE, COLOR_EMBER_ORANGE

class BaseEnemy(Entity):
    """Base class for all enemy types with state-machine AI."""
    STATE_CHASE = "chase"
    STATE_WINDUP = "windup"
    STATE_ATTACK = "attack"
    STATE_COOLDOWN = "cooldown"

    def __init__(self, x: float, y: float, radius: float, max_health: int, speed: float, name: str):
        super().__init__(x, y, radius, max_health, speed)
        self.name = name
        self.state = self.STATE_CHASE
        self.state_timer = 0.0
        self.facing_angle = 0.0
        
        # Flocking & separation parameters
        self.separation_radius = radius * 2.2
        self.target_dist = 0.0

        # Elite enemy attributes
        self.is_elite = False
        self.elite_modifier = None

    def make_elite(self, modifier: str = None):
        """Elevates this enemy to an Elite variant with bonus stats and modifier behavior."""
        self.is_elite = True
        mods = ["overclocked", "armored", "volatile"]
        self.elite_modifier = modifier or random.choice(mods)

        if self.elite_modifier == "overclocked":
            self.base_speed *= 1.25
            self.speed *= 1.25
            self.max_health = int(self.max_health * 1.25)
            self.health = self.max_health
        elif self.elite_modifier == "armored":
            self.max_health = int(self.max_health * 1.60)
            self.health = self.max_health
        elif self.elite_modifier == "volatile":
            self.max_health = int(self.max_health * 1.35)
            self.health = self.max_health

    def get_flocking_separation(self, all_enemies) -> pygame.math.Vector2:
        """Compute repulsive force away from nearby enemy neighbors to prevent clumping."""
        force = pygame.math.Vector2(0, 0)
        count = 0
        for other in all_enemies:
            if other is not self and other.is_alive():
                diff = self.pos - other.pos
                dist_sq = diff.length_squared()
                if 0 < dist_sq < self.separation_radius * self.separation_radius:
                    dist = dist_sq ** 0.5
                    # Repulsive force inversely proportional to distance
                    force += (diff / dist) * (self.separation_radius - dist)
                    count += 1
        if count > 0:
            force /= count
        return force

    def take_damage(self, damage_event, game_state):
        applied = super().take_damage(damage_event, game_state)
        if applied and hasattr(game_state, "damage_dealt") and damage_event.source_type == "player":
            game_state.damage_dealt += damage_event.amount
        return applied

    def die(self, game_state):
        super().die(game_state)
        if hasattr(game_state, "enemies_killed"):
            game_state.enemies_killed += 1

        # Volatile elite explosion on death
        if getattr(self, "is_elite", False) and getattr(self, "elite_modifier", "") == "volatile":
            game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=75)
            game_state.audio.play('explosion')
            for e in game_state.enemies:
                if e is not self and e.is_alive() and (e.pos - self.pos).length() < 90:
                    e.take_damage(DamageEvent(35, source_type="environment", damage_type="fire"), game_state)

        # Notify player boons of kill event
        for boon in game_state.player.boons:
            boon.on_kill(game_state.player, self, game_state)
        game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=8, color=COLOR_EMBER_ORANGE)

    def draw_health_bar(self, surface: pygame.Surface, camera):
        """Draw small overhead health bar if damaged."""
        if self.health >= self.max_health:
            return
            
        screen_pos = camera.apply(self.pos)
        bar_w = int(self.radius * 2.2)
        bar_h = 4
        bar_x = screen_pos[0] - bar_w // 2
        bar_y = screen_pos[1] - int(self.radius + 10)

        # Background
        pygame.draw.rect(surface, (20, 20, 25), (bar_x, bar_y, bar_w, bar_h))
        # Health fill
        fill_w = int(bar_w * (self.health / self.max_health))
        pygame.draw.rect(surface, (230, 70, 70), (bar_x, bar_y, fill_w, bar_h))

    def draw_windup_telegraph(self, surface: pygame.Surface, camera, radius: float, progress: float):
        """Draw circular warning ring that fills as attack approaches."""
        screen_pos = camera.apply(self.pos)
        # Outer ring
        pygame.draw.circle(surface, (255, 60, 60), screen_pos, int(radius), 1)
        # Growing indicator
        cur_r = max(2, int(radius * progress))
        surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 50, 50, int(60 * progress)), (int(radius + 2), int(radius + 2)), cur_r)
        surface.blit(surf, (screen_pos[0] - radius - 2, screen_pos[1] - radius - 2))
