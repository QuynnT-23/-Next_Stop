"""Specialized enemy variants with distinct combat behaviors and telegraphing."""
import pygame
import math
import random
from src.entities.enemies.base_enemy import BaseEnemy
from src.combat.damage import DamageEvent
from src.entities.projectile import Projectile
from src.ui.sprite_renderer import (
    draw_ticket_inspector_sprite, draw_luggage_steward_sprite,
    draw_boiler_imp_sprite, draw_freight_warden_sprite
)
from src.config import (
    COLOR_WHITE, COLOR_EMBER_ORANGE, COLOR_STEEL_DARK,
    COLOR_STEEL_MID, COLOR_CARPET_RED, COLOR_BRASS
)

class TicketInspector(BaseEnemy):
    """Melee bruiser who rushes the player and executes a heavy baton swing."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=20, max_health=78, speed=190.0, name="Ticket Inspector")
        self.attack_range = 75.0
        self.windup_duration = 0.45
        self.cooldown_duration = 0.50
        self.lunge_dir = pygame.math.Vector2(1, 0)

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        self.target_dist = to_player.length()
        if self.target_dist > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)

        separation = self.get_flocking_separation(game_state.enemies)

        if self.state == self.STATE_CHASE:
            if to_player.length_squared() > 0:
                chase_dir = to_player.normalize()
                move_vel = (chase_dir * self.base_speed) + (separation * 140.0)
                self.vel.x += (move_vel.x - self.vel.x) * min(1.0, dt * 8.0)
                self.vel.y += (move_vel.y - self.vel.y) * min(1.0, dt * 8.0)

            if self.target_dist <= self.attack_range:
                self.state = self.STATE_WINDUP
                self.state_timer = self.windup_duration
                self.lunge_dir = to_player.normalize() if to_player.length_squared() > 0 else pygame.math.Vector2(1, 0)
                game_state.audio.play('alarm')

        elif self.state == self.STATE_WINDUP:
            self.state_timer -= dt
            self.vel *= (0.85 ** (dt * 60))  # Slow down during windup
            if self.state_timer <= 0:
                self.state = self.STATE_ATTACK
                self.vel = self.lunge_dir * 420.0  # Burst lunge!
                game_state.audio.play('swing')

        elif self.state == self.STATE_ATTACK:
            # Check hit against player
            if (player.pos - self.pos).length() <= (self.radius + player.radius + 16):
                push = self.lunge_dir * 380.0
                player.take_damage(DamageEvent(18, source_type="enemy", knockback=push), game_state)
            self.state = self.STATE_COOLDOWN
            self.state_timer = self.cooldown_duration

        elif self.state == self.STATE_COOLDOWN:
            self.state_timer -= dt
            self.vel *= (0.80 ** (dt * 60))
            if self.state_timer <= 0:
                self.state = self.STATE_CHASE

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        
        # Windup telegraph ring
        if self.state == self.STATE_WINDUP:
            prog = 1.0 - (self.state_timer / self.windup_duration)
            self.draw_windup_telegraph(surface, camera, self.attack_range, prog)

        draw_ticket_inspector_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class RangedSteward(BaseEnemy):
    """Ranged attacker that kites away from the player and lobs steam canisters."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=18, max_health=64, speed=160.0, name="Luggage Steward")
        self.ideal_dist = 280.0
        self.windup_duration = 0.55
        self.cooldown_duration = 1.2
        self.shot_speed = 460.0

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        self.target_dist = to_player.length()
        if self.target_dist > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)

        separation = self.get_flocking_separation(game_state.enemies)

        if self.state == self.STATE_CHASE:
            # Kite logic: back up if too close, approach if too far
            if self.target_dist < self.ideal_dist - 60:
                desired_dir = -to_player.normalize()
            elif self.target_dist > self.ideal_dist + 80:
                desired_dir = to_player.normalize()
            else:
                # Strafe laterally
                desired_dir = pygame.math.Vector2(-to_player.y, to_player.x).normalize()

            move_vel = (desired_dir * self.base_speed) + (separation * 120.0)
            self.vel.x += (move_vel.x - self.vel.x) * min(1.0, dt * 6.0)
            self.vel.y += (move_vel.y - self.vel.y) * min(1.0, dt * 6.0)

            # Fire check (only within reasonable range)
            if self.target_dist <= 650.0:
                self.state_timer += dt
                if self.state_timer >= self.cooldown_duration:
                    self.state = self.STATE_WINDUP
                    self.state_timer = self.windup_duration
            else:
                self.state_timer = 0.0

        elif self.state == self.STATE_WINDUP:
            self.state_timer -= dt
            self.vel *= (0.85 ** (dt * 60))
            if self.state_timer <= 0:
                # Fire projectile!
                self.state = self.STATE_CHASE
                self.state_timer = 0.0
                aim_dir = to_player.normalize() if to_player.length_squared() > 0 else pygame.math.Vector2(1, 0)
                proj_vel = aim_dir * self.shot_speed
                proj = Projectile(
                    self.pos.x + aim_dir.x * 20,
                    self.pos.y + aim_dir.y * 20,
                    vel=proj_vel,
                    damage_event=DamageEvent(15, source_type="enemy", damage_type="steam"),
                    radius=5.5,
                    lifetime=1.8,
                    color=COLOR_EMBER_ORANGE,
                    owner="enemy"
                )
                game_state.projectiles.append(proj)
                game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=4)
                game_state.audio.play('shoot')

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)

        if self.state == self.STATE_WINDUP:
            prog = 1.0 - (self.state_timer / self.windup_duration)
            self.draw_windup_telegraph(surface, camera, 32.0, prog)

        draw_luggage_steward_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class BoilerImp(BaseEnemy):
    """Fast suicidal scrapper that dashes into range and detonates into scalding steam."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=14, max_health=38, speed=260.0, name="Boiler Imp")
        self.detonation_range = 50.0
        self.fuse_time = 0.38

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        self.target_dist = to_player.length()
        separation = self.get_flocking_separation(game_state.enemies)

        if self.state == self.STATE_CHASE:
            if to_player.length_squared() > 0:
                dir_vec = to_player.normalize()
                move_vel = (dir_vec * self.base_speed) + (separation * 160.0)
                self.vel.x += (move_vel.x - self.vel.x) * min(1.0, dt * 10.0)
                self.vel.y += (move_vel.y - self.vel.y) * min(1.0, dt * 10.0)

            if self.target_dist <= self.detonation_range:
                self.state = self.STATE_WINDUP
                self.state_timer = self.fuse_time
                game_state.audio.play('alarm')

        elif self.state == self.STATE_WINDUP:
            self.state_timer -= dt
            self.vel *= (0.90 ** (dt * 60))
            if self.state_timer <= 0:
                # Detonate!
                self.health = 0
                self.die(game_state)
                game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=65)
                game_state.audio.play('explosion')
                game_state.camera.add_trauma(0.35)
                
                # Area damage to player
                if (player.pos - self.pos).length() <= 85.0:
                    player.take_damage(DamageEvent(28, source_type="enemy", damage_type="steam"), game_state)
                return

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        # Flickering orange/yellow fuse
        if self.state == self.STATE_WINDUP:
            prog = 1.0 - (self.state_timer / self.fuse_time)
            self.draw_windup_telegraph(surface, camera, 70.0, prog)

        draw_boiler_imp_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class AutomatonShield(BaseEnemy):
    """Heavily armored mechanical sentry. Deflects frontal fire with a riot shield."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=24, max_health=130, speed=115.0, name="Freight Warden")
        self.shield_angle_span = math.pi * 0.55  # 100 degree frontal shield
        self.fire_timer = 1.8

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        """Check if damage came from the front. Frontal hits are deflected!"""
        if damage_event.knockback.length_squared() > 0:
            attack_angle = math.atan2(-damage_event.knockback.y, -damage_event.knockback.x)
            angle_diff = (attack_angle - self.facing_angle + math.pi) % (2 * math.pi) - math.pi
            if abs(angle_diff) < self.shield_angle_span / 2:
                # Deflected!
                game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=6, color=COLOR_WHITE)
                game_state.audio.play('hit')
                # Reduce damage by 75%
                damage_event.amount = max(1, int(damage_event.amount * 0.25))

        return super().take_damage(damage_event, game_state)

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        if to_player.length_squared() > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)
            chase_dir = to_player.normalize()
            self.vel.x += (chase_dir.x * self.base_speed - self.vel.x) * min(1.0, dt * 5.0)
            self.vel.y += (chase_dir.y * self.base_speed - self.vel.y) * min(1.0, dt * 5.0)

        # Firing burst
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = 2.2
            game_state.audio.play('shotgun')
            aim_dir = to_player.normalize()
            base_ang = math.atan2(aim_dir.y, aim_dir.x)
            for spread in (-0.14, 0.14):
                ang = base_ang + spread
                vel = pygame.math.Vector2(math.cos(ang) * 440, math.sin(ang) * 440)
                proj = Projectile(
                    self.pos.x + math.cos(ang) * 26,
                    self.pos.y + math.sin(ang) * 26,
                    vel=vel,
                    damage_event=DamageEvent(14, source_type="enemy"),
                    radius=4.5,
                    lifetime=1.5,
                    color=(220, 180, 50),
                    owner="enemy"
                )
                game_state.projectiles.append(proj)

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_freight_warden_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)
