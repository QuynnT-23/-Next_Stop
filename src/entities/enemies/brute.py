"""Heavy brute enemies, ground-pound shockwaves, and environmental fire hazards."""
import pygame
import math
import random
from src.entities.enemies.base_enemy import BaseEnemy
from src.combat.damage import DamageEvent
from src.entities.projectile import Projectile
from src.ui.sprite_renderer import draw_boiler_brute_sprite, draw_furnace_golem_sprite
from src.config import (
    COLOR_WHITE, COLOR_EMBER_ORANGE, COLOR_CRIT_YELLOW,
    COLOR_STEEL_DARK, COLOR_STEEL_MID, COLOR_BRASS, COLOR_CARPET_RED
)

class ShockwaveRing:
    """An expanding circular ground shockwave emitted by brute hammer slams."""
    def __init__(self, x: float, y: float, max_radius: float = 260.0, speed: float = 340.0, damage: int = 24):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = 20.0
        self.max_radius = max_radius
        self.speed = speed
        self.damage = damage
        self.thickness = 14.0
        self.player_hit = False
        self.is_alive = True

    def update(self, dt: float, player, game_state) -> bool:
        self.radius += self.speed * dt
        if self.radius >= self.max_radius:
            self.is_alive = False
            return False

        # Collision with player
        if not self.player_hit and player and player.is_alive():
            dist = (player.pos - self.pos).length()
            if abs(dist - self.radius) <= (self.thickness / 2 + player.radius):
                self.player_hit = True
                push = (player.pos - self.pos).normalize() * 450.0 if dist > 0 else pygame.math.Vector2(1, 0)
                player.take_damage(DamageEvent(self.damage, source_type="enemy", knockback=push), game_state)
                game_state.particles.spawn_sparks(player.pos.x, player.pos.y, count=8, color=COLOR_EMBER_ORANGE)

        return True

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        progress = self.radius / self.max_radius
        alpha = int(220 * (1.0 - progress))
        
        surf = pygame.Surface((int(self.radius * 2 + 30), int(self.radius * 2 + 30)), pygame.SRCALPHA)
        center = (int(self.radius + 15), int(self.radius + 15))
        
        # Outer ring
        pygame.draw.circle(surf, (255, 60, 20, alpha), center, int(self.radius), int(self.thickness))
        # Inner glowing core ring
        pygame.draw.circle(surf, (255, 220, 100, alpha), center, int(self.radius), max(2, int(self.thickness // 3)))
        
        surface.blit(surf, (screen_pos[0] - center[0], screen_pos[1] - center[1]))


class FireHazard:
    """A puddle of burning slag/coals on the train deck that deals tick damage."""
    def __init__(self, x: float, y: float, radius: float = 38.0, duration: float = 3.5, damage_per_sec: int = 18):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = radius
        self.duration = duration
        self.timer = duration
        self.damage_per_sec = damage_per_sec
        self.tick_timer = 0.0

    def update(self, dt: float, player, enemies, game_state) -> bool:
        self.timer -= dt
        if self.timer <= 0:
            return False

        # Spawn ember particles
        if random.random() < 0.25:
            game_state.particles.spawn_sparks(
                self.pos.x + random.uniform(-self.radius * 0.7, self.radius * 0.7),
                self.pos.y + random.uniform(-self.radius * 0.7, self.radius * 0.7),
                count=2, color=COLOR_EMBER_ORANGE
            )

        # Damage check every 0.35s
        self.tick_timer += dt
        if self.tick_timer >= 0.35:
            self.tick_timer = 0.0
            tick_dmg = max(3, int(self.damage_per_sec * 0.35))
            
            # Damage player
            if player and player.is_alive() and (player.pos - self.pos).length() <= (self.radius + player.radius):
                player.take_damage(DamageEvent(tick_dmg, source_type="hazard", damage_type="fire"), game_state)

            # Damage enemies
            for enemy in enemies:
                if enemy.is_alive() and (enemy.pos - self.pos).length() <= (self.radius + enemy.radius):
                    enemy.take_damage(DamageEvent(tick_dmg, source_type="hazard", damage_type="fire"), game_state)

        return True

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        progress = self.timer / self.duration
        alpha = int(140 * min(1.0, progress * 2))
        
        surf = pygame.Surface((int(self.radius * 2 + 10), int(self.radius * 2 + 10)), pygame.SRCALPHA)
        center = (int(self.radius + 5), int(self.radius + 5))
        
        # Scorched ground
        pygame.draw.circle(surf, (40, 15, 5, alpha), center, int(self.radius))
        # Fiery molten center
        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
        r_inner = max(4, int(self.radius * (0.5 + 0.2 * pulse)))
        pygame.draw.circle(surf, (255, 100, 20, int(alpha * 0.8)), center, r_inner)
        pygame.draw.circle(surf, (255, 210, 50, int(alpha * 0.9)), center, max(2, r_inner // 2))
        
        surface.blit(surf, (screen_pos[0] - center[0], screen_pos[1] - center[1]))


class BoilerBrute(BaseEnemy):
    """Heavy ironclad juggernaut wielding a colossal steam-piston sledgehammer."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=32, max_health=250, speed=105.0, name="Boiler Brute")
        self.attack_range = 80.0
        self.slam_windup = 0.70
        self.cooldown_duration = 1.10
        self.slam_target = pygame.math.Vector2(0, 0)

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        # 20% passive armor plating
        damage_event.amount = max(1, int(damage_event.amount * 0.80))
        damage_event.knockback *= 0.25  # Highly resistant to knockback
        return super().take_damage(damage_event, game_state)

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
                move_vel = (chase_dir * self.base_speed) + (separation * 150.0)
                self.vel.x += (move_vel.x - self.vel.x) * min(1.0, dt * 5.0)
                self.vel.y += (move_vel.y - self.vel.y) * min(1.0, dt * 5.0)

            # Initiate ground slam when within range
            if self.target_dist <= 160.0:
                self.state = self.STATE_WINDUP
                self.state_timer = self.slam_windup
                self.slam_target = pygame.math.Vector2(self.pos)
                game_state.audio.play('alarm')

        elif self.state == self.STATE_WINDUP:
            self.state_timer -= dt
            self.vel *= (0.80 ** (dt * 60))
            if self.state_timer <= 0:
                # Execute Ground Slam!
                self.state = self.STATE_ATTACK
                game_state.audio.play('explosion')
                game_state.camera.add_trauma(0.50)
                game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=70)
                
                # Emit circular Shockwave ring!
                dmg_mult = getattr(self, "damage_multiplier", 1.0)
                shockwave = ShockwaveRing(self.pos.x, self.pos.y, max_radius=270.0, speed=360.0, damage=int(24 * dmg_mult))
                if hasattr(game_state, "shockwaves"):
                    game_state.shockwaves.append(shockwave)

                # Melee impact if player is right next to brute
                if (player.pos - self.pos).length() <= (self.radius + player.radius + 20):
                    player.take_damage(DamageEvent(int(28 * dmg_mult), source_type="enemy", knockback=to_player.normalize() * 500.0), game_state)

        elif self.state == self.STATE_ATTACK:
            self.state = self.STATE_COOLDOWN
            self.state_timer = self.cooldown_duration

        elif self.state == self.STATE_COOLDOWN:
            self.state_timer -= dt
            self.vel *= (0.85 ** (dt * 60))
            if self.state_timer <= 0:
                self.state = self.STATE_CHASE

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)

        # Pulsing slam warning ring
        if self.state == self.STATE_WINDUP:
            prog = 1.0 - (self.state_timer / self.slam_windup)
            self.draw_windup_telegraph(surface, camera, 270.0, prog)

        draw_boiler_brute_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class FurnaceGolem(BaseEnemy):
    """Molten coal brute that lobs burning fire globules, coating the deck in flame patches."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=26, max_health=240, speed=120.0, name="Furnace Golem")
        self.lob_cooldown = 2.4
        self.state_timer = 1.0

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return

        to_player = player.pos - self.pos
        self.target_dist = to_player.length()
        if self.target_dist > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)

        separation = self.get_flocking_separation(game_state.enemies)

        # Chase / kite range ~250px
        if self.target_dist > 280.0:
            move_dir = to_player.normalize()
        elif self.target_dist < 180.0:
            move_dir = -to_player.normalize()
        else:
            move_dir = pygame.math.Vector2(-to_player.y, to_player.x).normalize()

        move_vel = (move_dir * self.base_speed) + (separation * 120.0)
        self.vel.x += (move_vel.x - self.vel.x) * min(1.0, dt * 5.0)
        self.vel.y += (move_vel.y - self.vel.y) * min(1.0, dt * 5.0)

        # Fire globule attack
        self.state_timer -= dt
        if self.state_timer <= 0 and self.target_dist <= 550.0:
            self.state_timer = self.lob_cooldown
            self.lob_fire_globule(player, game_state)

        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def lob_fire_globule(self, player, game_state):
        game_state.audio.play('shoot')
        target_pos = pygame.math.Vector2(player.pos.x + random.uniform(-40, 40), player.pos.y + random.uniform(-40, 40))
        diff = target_pos - self.pos
        dist = diff.length()
        speed = 420.0
        lifetime = dist / speed if speed > 0 else 0.8
        vel = diff.normalize() * speed if dist > 0 else pygame.math.Vector2(1, 0) * speed

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        proj = Projectile(
            self.pos.x, self.pos.y, vel=vel,
            damage_event=DamageEvent(int(16 * dmg_mult), source_type="enemy", damage_type="fire"),
            radius=6.0, lifetime=lifetime, color=COLOR_EMBER_ORANGE, owner="enemy"
        )
        game_state.projectiles.append(proj)
        
        # When globule lands, spawn FireHazard puddle!
        if hasattr(game_state, "fire_hazards"):
            game_state.fire_hazards.append(FireHazard(target_pos.x, target_pos.y, radius=42.0, duration=3.5, damage_per_sec=int(18 * dmg_mult)))

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_furnace_golem_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)
