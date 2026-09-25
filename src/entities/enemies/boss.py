"""Final Boss: The Conductor / Locomotive Overlord with multi-phase mechanics."""
import pygame
import math
import random
from src.entities.enemies.base_enemy import BaseEnemy
from src.combat.damage import DamageEvent
from src.entities.projectile import Projectile
from src.config import (
    COLOR_WHITE, COLOR_EMBER_ORANGE, COLOR_CRIT_YELLOW,
    COLOR_STEEL_DARK, COLOR_BRASS, COLOR_CARPET_RED,
    COLOR_BRASS_HIGHLIGHT, COLOR_SHADOW
)

class ConductorBoss(BaseEnemy):
    """The final encounter: Master of the Iron Locomotive."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=46, max_health=920, speed=130.0, name="The Conductor")
        self.phase = 1
        self.attack_timer = 2.0
        self.current_attack = None
        self.attack_state = 0
        self.rush_target = pygame.math.Vector2(0, 0)
        self.rush_dir = pygame.math.Vector2(0, 0)
        self.summon_cooldown = 12.0
        self.summon_timer = 4.0

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        was_alive = self.is_alive()
        # Boss has 15% armor reduction
        damage_event.amount = max(1, int(damage_event.amount * 0.85))
        # Reduce knockback on boss
        damage_event.knockback *= 0.1
        
        applied = super().take_damage(damage_event, game_state)
        
        # Check phase transition at 50% HP
        if was_alive and self.phase == 1 and self.health <= self.max_health * 0.5:
            self.enter_phase_2(game_state)
            
        return applied

    def enter_phase_2(self, game_state):
        self.phase = 2
        self.base_speed = 180.0
        game_state.camera.add_trauma(0.8)
        game_state.audio.play('alarm')
        game_state.audio.play('explosion')
        game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=120)
        # Repel player and shockwave
        for _ in range(30):
            game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=2, color=COLOR_EMBER_ORANGE)

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        if to_player.length_squared() > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)

        # Summon adds occasionally
        self.summon_timer -= dt
        if self.summon_timer <= 0 and len([e for e in game_state.enemies if e is not self and e.is_alive()]) < 3:
            self.summon_timer = self.summon_cooldown
            self.summon_minions(train_car, game_state)

        # Attack state machine
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.choose_next_attack(to_player, game_state)

        # Execute ongoing attack patterns
        if self.current_attack == "rush":
            self.execute_rush(dt, player, train_car, game_state)
        elif self.current_attack == "steam_ring":
            self.execute_steam_ring(dt, game_state)
        else:
            # Default tracking movement
            if to_player.length_squared() > 0:
                chase_dir = to_player.normalize()
                self.vel.x += (chase_dir.x * self.base_speed - self.vel.x) * min(1.0, dt * 4.0)
                self.vel.y += (chase_dir.y * self.base_speed - self.vel.y) * min(1.0, dt * 4.0)

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def choose_next_attack(self, to_player: pygame.math.Vector2, game_state):
        patterns = ["salvo", "steam_ring"]
        if self.phase == 2:
            patterns.append("rush")
            self.attack_timer = random.uniform(1.2, 2.0)
        else:
            self.attack_timer = random.uniform(2.2, 3.2)

        self.current_attack = random.choice(patterns)
        
        if self.current_attack == "salvo":
            self.fire_salvo(to_player, game_state)
        elif self.current_attack == "steam_ring":
            self.attack_state = 0  # 0 = windup, 1 = release
            self.state_timer = 0.5
            game_state.audio.play('alarm')
        elif self.current_attack == "rush":
            self.attack_state = 0
            self.state_timer = 0.7  # Windup telegraph before launching
            self.rush_target = pygame.math.Vector2(game_state.player.pos)
            diff = self.rush_target - self.pos
            self.rush_dir = diff.normalize() if diff.length_squared() > 0 else pygame.math.Vector2(1, 0)
            game_state.audio.play('alarm')

    def fire_salvo(self, to_player: pygame.math.Vector2, game_state):
        """Fires an arc of 5 heavy steam rivets."""
        base_angle = math.atan2(to_player.y, to_player.x)
        count = 7 if self.phase == 2 else 5
        spread = 0.2
        game_state.audio.play('shotgun')
        game_state.camera.add_trauma(0.2)

        for i in range(count):
            ang = base_angle + (i - (count - 1) / 2) * spread
            vel = pygame.math.Vector2(math.cos(ang) * 480, math.sin(ang) * 480)
            proj = Projectile(
                self.pos.x + math.cos(ang) * 50,
                self.pos.y + math.sin(ang) * 50,
                vel=vel,
                damage_event=DamageEvent(18, source_type="enemy", damage_type="steam"),
                radius=6.0,
                lifetime=2.5,
                color=COLOR_EMBER_ORANGE,
                owner="enemy"
            )
            game_state.projectiles.append(proj)

    def execute_steam_ring(self, dt: float, game_state):
        self.state_timer -= dt
        if self.state_timer <= 0:
            # Emit full 360 ring of steam bolts
            count = 16 if self.phase == 2 else 12
            game_state.audio.play('explosion')
            game_state.camera.add_trauma(0.3)
            for i in range(count):
                ang = (math.tau / count) * i
                vel = pygame.math.Vector2(math.cos(ang) * 360, math.sin(ang) * 360)
                proj = Projectile(
                    self.pos.x + math.cos(ang) * 48,
                    self.pos.y + math.sin(ang) * 48,
                    vel=vel,
                    damage_event=DamageEvent(15, source_type="enemy"),
                    radius=5.0,
                    lifetime=2.0,
                    color=(240, 140, 40),
                    owner="enemy"
                )
                game_state.projectiles.append(proj)
            self.current_attack = None

    def execute_rush(self, dt: float, player, train_car, game_state):
        """Telegraph, then charge at high speed across the room."""
        if self.attack_state == 0:
            # Windup
            self.state_timer -= dt
            self.vel *= (0.80 ** (dt * 60))
            if self.state_timer <= 0:
                self.attack_state = 1
                self.state_timer = 0.65  # Rush duration
                self.vel = self.rush_dir * 780.0
                game_state.audio.play('dash')
                game_state.camera.add_trauma(0.4)
        elif self.attack_state == 1:
            # Rushing
            self.state_timer -= dt
            game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=3, color=COLOR_EMBER_ORANGE)
            
            # Damage player on collision
            if (player.pos - self.pos).length() <= (self.radius + player.radius + 15):
                player.take_damage(DamageEvent(32, source_type="enemy", knockback=self.rush_dir * 550.0), game_state)

            if self.state_timer <= 0:
                self.attack_state = 2
                self.state_timer = 0.5  # Recovery
                self.vel *= 0.2
        elif self.attack_state == 2:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.current_attack = None

    def summon_minions(self, train_car, game_state):
        from src.entities.enemies.types import BoilerImp
        for offset_y in (-90, 90):
            imp_x = max(100, min(self.pos.x - 120, train_car.width - 100))
            imp_y = self.pos.y + offset_y
            imp = BoilerImp(imp_x, imp_y)
            game_state.enemies.append(imp)
            game_state.particles.spawn_steam(imp_x, imp_y, count=8)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        
        # Color based on phase & hit flash
        if self.flash_timer > 0:
            body_color = COLOR_WHITE
        elif self.phase == 2:
            # Pulsing rage red/orange
            pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
            body_color = (int(200 + 55 * pulse), 40, 20)
        else:
            body_color = COLOR_BRASS

        # Drop Shadow
        pygame.draw.circle(surface, COLOR_SHADOW, (screen_pos[0], screen_pos[1] + 12), int(self.radius * 1.05))

        # Rush telegraph line
        if self.current_attack == "rush" and self.attack_state == 0:
            prog = 1.0 - (self.state_timer / 0.7)
            start_pt = screen_pos
            end_pt = (
                screen_pos[0] + int(self.rush_dir.x * 500),
                screen_pos[1] + int(self.rush_dir.y * 500)
            )
            pygame.draw.line(surface, (255, 50, 50), start_pt, end_pt, 4)

        # Outer heavy steel armor shell with rivet studs
        pygame.draw.circle(surface, COLOR_STEEL_DARK, screen_pos, int(self.radius))
        pygame.draw.circle(surface, (25, 25, 30), screen_pos, int(self.radius - 2))
        for r_ang in range(0, 360, 45):
            rad = math.radians(r_ang)
            rx = screen_pos[0] + int(math.cos(rad) * (self.radius - 4))
            ry = screen_pos[1] + int(math.sin(rad) * (self.radius - 4))
            pygame.draw.circle(surface, COLOR_BRASS, (rx, ry), 2)

        # Main Boiler Hull
        pygame.draw.circle(surface, body_color, screen_pos, int(self.radius - 7))
        pygame.draw.circle(surface, COLOR_CARPET_RED, screen_pos, int(self.radius - 14))

        # Dual rear steam exhaust stacks
        rear_angle = self.facing_angle + math.pi
        stack_perp = pygame.math.Vector2(-math.sin(self.facing_angle), math.cos(self.facing_angle))
        for side in [-1, 1]:
            stack_pos = screen_pos + pygame.math.Vector2(math.cos(rear_angle), math.sin(rear_angle)) * (self.radius * 0.65) + stack_perp * (side * 18)
            pygame.draw.circle(surface, (20, 20, 25), (int(stack_pos.x), int(stack_pos.y)), 9)
            pygame.draw.circle(surface, COLOR_BRASS, (int(stack_pos.x), int(stack_pos.y)), 9, 2)
            pygame.draw.circle(surface, (10, 10, 15), (int(stack_pos.x), int(stack_pos.y)), 5)

        # Central Glowing Firebox Hatch
        firebox_pulse = (math.sin(pygame.time.get_ticks() * 0.012) + 1) * 0.5
        fire_col = (255, int(110 + 60 * firebox_pulse), 20)
        pygame.draw.circle(surface, (30, 20, 15), screen_pos, 16)
        pygame.draw.circle(surface, fire_col, screen_pos, 12)
        # Firebox iron grate bars
        pygame.draw.line(surface, (40, 25, 20), (screen_pos[0] - 10, screen_pos[1]), (screen_pos[0] + 10, screen_pos[1]), 2)
        pygame.draw.line(surface, (40, 25, 20), (screen_pos[0], screen_pos[1] - 10), (screen_pos[0], screen_pos[1] + 10), 2)

        # Heavy locomotive cowcatcher & headlights on front
        front_vec = pygame.math.Vector2(math.cos(self.facing_angle), math.sin(self.facing_angle))
        front_pt = screen_pos + front_vec * (self.radius + 4)
        left_corner = screen_pos + front_vec * (self.radius - 4) + stack_perp * 24
        right_corner = screen_pos + front_vec * (self.radius - 4) - stack_perp * 24
        # Cowcatcher V-wedge
        pygame.draw.polygon(surface, COLOR_STEEL_DARK, [front_pt, left_corner, right_corner])
        pygame.draw.polygon(surface, COLOR_BRASS, [front_pt, left_corner, right_corner], 2)

        # Twin forward brass headlights
        for corner in [left_corner, right_corner]:
            hl_pos = corner + front_vec * 4
            pygame.draw.circle(surface, COLOR_BRASS_HIGHLIGHT, (int(hl_pos.x), int(hl_pos.y)), 6)
            pygame.draw.circle(surface, COLOR_CRIT_YELLOW, (int(hl_pos.x), int(hl_pos.y)), 4)
