"""Stage-specific Mini-Bosses and Final Bosses for Stages 2 through 5."""
import pygame
import math
import random
from src.entities.enemies.base_enemy import BaseEnemy
from src.combat.damage import DamageEvent
from src.entities.projectile import Projectile
from src.config import (
    COLOR_WHITE, COLOR_CRIT_YELLOW, COLOR_EMBER_ORANGE, COLOR_BRASS,
    COLOR_BRASS_HIGHLIGHT, COLOR_STEEL_DARK, COLOR_STEEL_LIGHT, COLOR_SHADOW
)
from src.ui.sprite_renderer import (
    draw_scrapper_foreman_sprite, draw_vermin_brood_engine_sprite,
    draw_cyber_dispatcher_sprite, draw_traction_ai_core_sprite,
    draw_sub_zero_warden_sprite, draw_cryo_turbine_engine_sprite,
    draw_ash_pyromancer_sprite, draw_iron_leviathan_sprite
)

# ==============================================================================
# STAGE 2: THE DERELICT FREIGHT
# ==============================================================================

class ScrapperForemanMiniBoss(BaseEnemy):
    """Stage 2 Mini-Boss (Car 5): A burly junkyard raider with a giant pipe wrench."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=40, max_health=760, speed=160.0, name="Scrapper Foreman")
        self.is_miniboss = True
        self.attack_timer = 1.8
        self.current_attack = None
        self.attack_state = 0
        self.state_timer = 0.0
        self.rush_dir = pygame.math.Vector2(0, 0)
        self.melee_damage = 28

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_player = player.pos - self.pos
        dist = to_player.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_player.y, to_player.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        if self.current_attack == "whirlwind":
            self.state_timer -= dt
            # Spin wrench and fire scrap shrapnel
            self.facing_angle += dt * 14.0 * rate_mult
            if random.random() < 0.25:
                ang = self.facing_angle
                vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (340.0 * (self.speed / 160.0))
                p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(14 * dmg_mult), source_type="enemy"), radius=5, lifetime=1.2, color=(180, 140, 90), owner="enemy")
                game_state.projectiles.append(p)
            if dist < self.radius + player.radius + 20:
                player.take_damage(DamageEvent(int(self.melee_damage * dmg_mult), source_type="enemy", knockback=to_player.normalize() * 450), game_state)
            if self.state_timer <= 0:
                self.current_attack = None
                self.attack_timer = 2.0 / rate_mult
            return

        self.attack_timer -= dt
        if self.attack_timer <= 0:
            if dist < 180:
                self.current_attack = "whirlwind"
                self.state_timer = 1.4 / rate_mult
                game_state.audio.play('swing')
            else:
                # Scrap Hook throw
                self.current_attack = "hook"
                game_state.audio.play('shoot')
                ang = self.facing_angle
                for o in (-0.2, 0.0, 0.2):
                    vel = pygame.math.Vector2(math.cos(ang + o), math.sin(ang + o)) * (400.0 * (self.speed / 160.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(16 * dmg_mult), source_type="enemy"), radius=6, lifetime=1.5, color=(200, 110, 50), owner="enemy")
                    game_state.projectiles.append(p)
                self.current_attack = None
                self.attack_timer = 2.2 / rate_mult

        if dist > 110:
            self.vel = self.vel.lerp(to_player.normalize() * self.speed, min(1.0, dt * 5.0))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_scrapper_foreman_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class VerminBroodEngineBoss(BaseEnemy):
    """Stage 2 Final Boss (Car 15): Rusted industrial incinerator infected by mutant vermin."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=60, max_health=1480, speed=120.0, name="The Vermin Brood Engine")
        self.phase = 1
        self.attack_timer = 2.0
        self.current_attack = None
        self.state_timer = 0.0

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        damage_event.amount = max(1, int(damage_event.amount * 0.85))
        damage_event.knockback *= 0.1
        was_alive = self.is_alive()
        applied = super().take_damage(damage_event, game_state)
        if was_alive and self.phase == 1 and self.health <= self.max_health * 0.5:
            self.phase = 2
            self.speed = 160.0
            game_state.audio.play('alarm')
            game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=100)
        return applied

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = (random.uniform(1.8, 2.8) if self.phase == 1 else random.uniform(1.2, 2.0)) / rate_mult
            pattern = random.choice(["toxic_puddles", "rat_burst", "nail_barrage"])
            if pattern == "toxic_puddles":
                # Spits 3 toxic slag balls that linger
                game_state.audio.play('shoot')
                for _ in range(3 if self.phase == 1 else 5):
                    target_x = player.pos.x + random.uniform(-80, 80)
                    target_y = player.pos.y + random.uniform(-60, 60)
                    diff = pygame.math.Vector2(target_x, target_y) - self.pos
                    vel = diff.normalize() * (380.0 * (self.speed / 120.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(15 * dmg_mult), source_type="enemy", damage_type="toxic"), radius=7, lifetime=1.2, color=(120, 220, 50), owner="enemy")
                    game_state.projectiles.append(p)
            elif pattern == "nail_barrage":
                # Arc of rusty nails
                game_state.audio.play('shotgun')
                base = self.facing_angle
                count = 7 if self.phase == 2 else 5
                for i in range(count):
                    ang = base + (i - count // 2) * 0.22
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (440.0 * (self.speed / 120.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(16 * dmg_mult), source_type="enemy"), radius=5, lifetime=2.0, color=(210, 130, 40), owner="enemy")
                    game_state.projectiles.append(p)
            elif pattern == "rat_burst":
                # Ring of scurrying scrap teeth
                game_state.audio.play('explosion')
                count = 12
                for i in range(count):
                    ang = (math.tau / count) * i
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (320.0 * (self.speed / 120.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(12 * dmg_mult), source_type="enemy"), radius=5, lifetime=1.8, color=(140, 100, 70), owner="enemy")
                    game_state.projectiles.append(p)

        if dist > 130:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 3.5))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_vermin_brood_engine_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)

# ==============================================================================
# STAGE 3: THE NEO-SUBWAY
# ==============================================================================

class CyberDispatcherMiniBoss(BaseEnemy):
    """Stage 3 Mini-Boss (Car 5): High-voltage transit officer with shock batons."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=38, max_health=720, speed=185.0, name="Cyber Dispatcher")
        self.is_miniboss = True
        self.attack_timer = 1.6
        self.current_attack = None
        self.melee_damage = 25

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = random.uniform(1.4, 2.2) / rate_mult
            # Stun Pulse Salvo
            game_state.audio.play('shoot')
            for ang_off in (-0.25, 0.0, 0.25):
                ang = self.facing_angle + ang_off
                vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (480.0 * (self.speed / 185.0))
                p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(18 * dmg_mult), source_type="enemy", damage_type="electric"), radius=6, lifetime=1.6, color=(50, 240, 255), owner="enemy")
                game_state.projectiles.append(p)
            game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=6, color=(40, 220, 255))

        if dist > 100:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 6.0))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_cyber_dispatcher_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class TractionAICoreBoss(BaseEnemy):
    """Stage 3 Final Boss (Car 15): The subway autonomous train traction AI."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=58, max_health=1550, speed=135.0, name="Traction AI Core")
        self.phase = 1
        self.attack_timer = 1.8
        self.laser_angle = 0.0

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        damage_event.amount = max(1, int(damage_event.amount * 0.85))
        damage_event.knockback *= 0.1
        was_alive = self.is_alive()
        applied = super().take_damage(damage_event, game_state)
        if was_alive and self.phase == 1 and self.health <= self.max_health * 0.5:
            self.phase = 2
            self.speed = 175.0
            game_state.audio.play('alarm')
            game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=120)
        return applied

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = (random.uniform(1.4, 2.4) if self.phase == 1 else random.uniform(0.9, 1.6)) / rate_mult
            atk = random.choice(["laser_cross", "plasma_salvo", "grid_pulse"])
            if atk == "laser_cross":
                # Quad rotating lasers
                game_state.audio.play('shoot')
                count = 8 if self.phase == 2 else 4
                base = self.facing_angle
                for i in range(count):
                    ang = base + (math.tau / count) * i
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (460.0 * (self.speed / 135.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(17 * dmg_mult), source_type="enemy", damage_type="electric"), radius=6, lifetime=1.8, color=(40, 240, 255), owner="enemy")
                    game_state.projectiles.append(p)
            elif atk == "plasma_salvo":
                game_state.audio.play('shotgun')
                for off in (-0.3, -0.15, 0.0, 0.15, 0.3):
                    ang = self.facing_angle + off
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (520.0 * (self.speed / 135.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(18 * dmg_mult), source_type="enemy"), radius=7, lifetime=1.5, color=(255, 60, 200), owner="enemy")
                    game_state.projectiles.append(p)
            elif atk == "grid_pulse":
                # 360 shock ring
                game_state.audio.play('explosion')
                count = 16
                for i in range(count):
                    ang = (math.tau / count) * i
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (340.0 * (self.speed / 135.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(14 * dmg_mult), source_type="enemy"), radius=5, lifetime=2.0, color=(120, 255, 230), owner="enemy")
                    game_state.projectiles.append(p)

        if dist > 140:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 4.0))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_traction_ai_core_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)

# ==============================================================================
# STAGE 4: THE GLACIER LINE
# ==============================================================================

class SubZeroWardenMiniBoss(BaseEnemy):
    """Stage 4 Mini-Boss (Car 5): Heavily armored cryogenic security warden."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=40, max_health=780, speed=165.0, name="Sub-Zero Warden")
        self.is_miniboss = True
        self.attack_timer = 1.8

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = random.uniform(1.6, 2.4) / rate_mult
            game_state.audio.play('shoot')
            # Fan of 5 icicles
            for ang_off in (-0.35, -0.17, 0.0, 0.17, 0.35):
                ang = self.facing_angle + ang_off
                vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (430.0 * (self.speed / 165.0))
                p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(19 * dmg_mult), source_type="enemy", damage_type="cryo"), radius=6, lifetime=1.8, color=(160, 235, 255), owner="enemy")
                game_state.projectiles.append(p)
            game_state.particles.spawn_steam(self.pos.x, self.pos.y, count=8, color=(200, 240, 255))

        if dist > 110:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 5.0))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_sub_zero_warden_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class CryoTurbineEngineBoss(BaseEnemy):
    """Stage 4 Final Boss (Car 15): Dual cryogenic turbine reactor."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=62, max_health=1650, speed=125.0, name="The Cryo-Turbine Engine")
        self.phase = 1
        self.attack_timer = 2.0

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        damage_event.amount = max(1, int(damage_event.amount * 0.85))
        damage_event.knockback *= 0.1
        was_alive = self.is_alive()
        applied = super().take_damage(damage_event, game_state)
        if was_alive and self.phase == 1 and self.health <= self.max_health * 0.5:
            self.phase = 2
            self.speed = 170.0
            game_state.audio.play('alarm')
            game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=130)
        return applied

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = (random.uniform(1.5, 2.5) if self.phase == 1 else random.uniform(1.0, 1.8)) / rate_mult
            atk = random.choice(["blizzard_burst", "icicle_salvo", "frost_ring"])
            if atk == "blizzard_burst":
                game_state.audio.play('shoot')
                count = 12 if self.phase == 2 else 8
                for _ in range(count):
                    ang = self.facing_angle + random.uniform(-0.6, 0.6)
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(360, 520) * (self.speed / 125.0)
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(18 * dmg_mult), source_type="enemy", damage_type="cryo"), radius=6, lifetime=1.6, color=(190, 240, 255), owner="enemy")
                    game_state.projectiles.append(p)
            elif atk == "icicle_salvo":
                game_state.audio.play('shotgun')
                base = self.facing_angle
                for i in range(7):
                    ang = base + (i - 3) * 0.2
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (480.0 * (self.speed / 125.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(20 * dmg_mult), source_type="enemy"), radius=7, lifetime=1.8, color=(140, 220, 255), owner="enemy")
                    game_state.projectiles.append(p)
            elif atk == "frost_ring":
                game_state.audio.play('explosion')
                count = 18
                for i in range(count):
                    ang = (math.tau / count) * i
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (340.0 * (self.speed / 125.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(15 * dmg_mult), source_type="enemy"), radius=5, lifetime=2.0, color=(220, 250, 255), owner="enemy")
                    game_state.projectiles.append(p)

        if dist > 140:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 3.5))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_cryo_turbine_engine_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)

# ==============================================================================
# STAGE 5: THE INFERNAL BOILER
# ==============================================================================

class AshPyromancerMiniBoss(BaseEnemy):
    """Stage 5 Mini-Boss (Car 5): Blazing fire zealot with twin flamethrowers."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=39, max_health=740, speed=175.0, name="Ash Pyromancer")
        self.is_miniboss = True
        self.attack_timer = 1.5

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = random.uniform(1.2, 2.0) / rate_mult
            game_state.audio.play('shoot')
            # Flame sweep
            base = self.facing_angle
            for ang_off in (-0.3, -0.15, 0.0, 0.15, 0.3):
                ang = base + ang_off
                vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (470.0 * (self.speed / 175.0))
                p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(22 * dmg_mult), source_type="enemy", damage_type="fire"), radius=7, lifetime=1.5, color=(255, 100, 30), owner="enemy")
                game_state.projectiles.append(p)
            game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=10, color=(255, 90, 20))

        if dist > 110:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 5.0))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_ash_pyromancer_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)


class IronLeviathanBoss(BaseEnemy):
    """Stage 5 Final Boss (Car 15): The ultimate doomsday locomotive furnace overlord."""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, radius=70, max_health=1950, speed=140.0, name="The Iron Leviathan")
        self.phase = 1
        self.attack_timer = 1.8

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        damage_event.amount = max(1, int(damage_event.amount * 0.85))
        damage_event.knockback *= 0.05
        was_alive = self.is_alive()
        applied = super().take_damage(damage_event, game_state)
        if was_alive and self.phase == 1 and self.health <= self.max_health * 0.5:
            self.phase = 2
            self.speed = 190.0
            game_state.audio.play('alarm')
            game_state.audio.play('explosion')
            game_state.particles.spawn_explosion(self.pos.x, self.pos.y, radius=150)
        return applied

    def update(self, dt: float, player, train_car, game_state):
        if not self.is_alive():
            return
        to_p = player.pos - self.pos
        dist = to_p.length()
        if dist > 0:
            self.facing_angle = math.atan2(to_p.y, to_p.x)

        dmg_mult = getattr(self, "damage_multiplier", 1.0)
        rate_mult = getattr(self, "attack_rate_multiplier", 1.0)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = (random.uniform(1.4, 2.2) if self.phase == 1 else random.uniform(0.8, 1.5)) / rate_mult
            atk = random.choice(["artillery", "magma_ring", "fire_cannonade"])
            if atk == "artillery":
                game_state.audio.play('explosion')
                # Dual heavy mortar shells towards player
                for _ in range(4 if self.phase == 2 else 2):
                    target_x = player.pos.x + random.uniform(-100, 100)
                    target_y = player.pos.y + random.uniform(-70, 70)
                    diff = pygame.math.Vector2(target_x, target_y) - self.pos
                    vel = diff.normalize() * (420.0 * (self.speed / 140.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(25 * dmg_mult), source_type="enemy", damage_type="fire"), radius=9, lifetime=1.4, color=(255, 60, 20), owner="enemy")
                    game_state.projectiles.append(p)
            elif atk == "fire_cannonade":
                game_state.audio.play('shotgun')
                count = 9 if self.phase == 2 else 7
                base = self.facing_angle
                for i in range(count):
                    ang = base + (i - count // 2) * 0.18
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (520.0 * (self.speed / 140.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(20 * dmg_mult), source_type="enemy"), radius=6, lifetime=1.8, color=(255, 140, 30), owner="enemy")
                    game_state.projectiles.append(p)
            elif atk == "magma_ring":
                game_state.audio.play('explosion')
                count = 20 if self.phase == 2 else 16
                for i in range(count):
                    ang = (math.tau / count) * i
                    vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * (360.0 * (self.speed / 140.0))
                    p = Projectile(self.pos.x, self.pos.y, vel=vel, damage_event=DamageEvent(int(17 * dmg_mult), source_type="enemy"), radius=6, lifetime=2.2, color=(255, 180, 40), owner="enemy")
                    game_state.projectiles.append(p)

        if dist > 150:
            self.vel = self.vel.lerp(to_p.normalize() * self.speed, min(1.0, dt * 4.0))
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)
        self.update_physics(dt)

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_iron_leviathan_sprite(surface, screen_pos, self)
        self.draw_health_bar(surface, camera)
