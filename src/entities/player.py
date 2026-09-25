"""Player entity featuring smooth physics, dashing with i-frames, and weapon handling."""
import pygame
import math
import random
from src.entities.base import Entity
from src.combat.damage import DamageEvent
from src.combat.weapons import RivetGun
from src.ui.sprite_renderer import draw_stoker_player
from src.config import (
    PLAYER_RADIUS, PLAYER_BASE_SPEED, PLAYER_ACCELERATION,
    PLAYER_DASH_SPEED, PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN,
    PLAYER_DASH_CHARGES, COLOR_BRASS, COLOR_BRASS_HIGHLIGHT,
    COLOR_WHITE, COLOR_STAMINA_CYAN, COLOR_STEEL_DARK, COLOR_CARPET_RED,
    COLOR_LIGHTNING_CYAN
)

class Player(Entity):
    """The player character fighting through the train."""
    def __init__(self, x: float, y: float):
        super().__init__(
            x=x, y=y,
            radius=PLAYER_RADIUS,
            max_health=100,
            speed=PLAYER_BASE_SPEED
        )
        # Stats & Modifiers
        self.speed_multiplier = 1.0
        self.crit_chance = 0.12
        self.crit_mult = 2.0
        self.dash_cooldown_mult = 1.0
        
        # Dash state machine
        self.max_dash_charges = PLAYER_DASH_CHARGES
        self.dash_charges = self.max_dash_charges
        self.dash_recharge_timer = 0.0
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_dir = pygame.math.Vector2(1, 0)
        self.dash_ghost_timer = 0.0
        
        # Weapons & Boons
        self.weapon = RivetGun()
        self.boons = []
        
        # Timed Attack Boost / Overcharge (from Supply Crates)
        self.attack_boost_timer = 0.0
        self.attack_boost_max_duration = 12.0
        
        # Animation & Visuals
        self.walk_distance = 0.0
        self.recoil_timer = 0.0
        
        # Visual aim angle
        self.aim_angle = 0.0
        self.facing_dir = pygame.math.Vector2(1, 0)

    def apply_attack_boost(self, duration: float = 8.0):
        """Apply or extend timed overcharge attack boost (capped at max duration)."""
        if self.attack_boost_timer > 0:
            self.attack_boost_timer = min(self.attack_boost_max_duration, self.attack_boost_timer + duration * 0.5)
        else:
            self.attack_boost_timer = duration

    def equip_weapon(self, new_weapon):
        self.weapon = new_weapon

    def add_boon(self, boon):
        existing = next((b for b in self.boons if b.id == boon.id), None)
        if existing:
            existing.upgrade(self)
        else:
            self.boons.append(boon)
            boon.on_acquire(self)

    def trigger_dash(self, game_state, dir_override: pygame.math.Vector2 = None) -> bool:
        """Attempt to dash in current movement direction or facing direction."""
        if self.is_dashing or self.dash_charges <= 0:
            return False

        self.dash_charges -= 1
        self.is_dashing = True
        self.dash_timer = PLAYER_DASH_DURATION
        self.invulnerable_timer = PLAYER_DASH_DURATION + 0.06  # i-frames!
        
        # Determine dash direction: override if provided (e.g. double-tap WASD)
        if dir_override and dir_override.length_squared() > 0:
            self.dash_dir = dir_override.normalize()
        elif self.vel.length_squared() > 10.0:
            self.dash_dir = self.vel.normalize()
        else:
            self.dash_dir = self.facing_dir

        start_pos = pygame.math.Vector2(self.pos)
        self.vel = self.dash_dir * PLAYER_DASH_SPEED

        # Trigger on_dash hooks for boons
        end_pos = start_pos + self.dash_dir * (PLAYER_DASH_SPEED * PLAYER_DASH_DURATION)
        for boon in self.boons:
            boon.on_dash(self, start_pos, end_pos, game_state)

        game_state.particles.spawn_dash_ghost(self.pos.x, self.pos.y, self.radius)
        game_state.audio.play('dash')
        return True

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        """Process damage taken and trigger defensive boons."""
        if not super().take_damage(damage_event, game_state):
            return False

        game_state.camera.add_trauma(0.3)
        game_state.audio.play('hit')

        for boon in self.boons:
            boon.on_take_damage(self, damage_event, game_state)

        return True

    def update(self, dt: float, input_handler, train_car, game_state):
        if not self.is_alive():
            return

        # Cold Storage car reduces ground friction for ice sliding!
        if train_car and getattr(train_car, "car_type", None) == "cold_storage":
            self.friction = 350.0
        else:
            self.friction = 1400.0

        # Aim direction towards mouse world position
        aim_vec = input_handler.mouse_world_pos - self.pos
        if aim_vec.length_squared() > 0:
            self.aim_angle = math.atan2(aim_vec.y, aim_vec.x)
            self.facing_dir = aim_vec.normalize()

        # Update weapon cooldown
        if self.weapon:
            self.weapon.update(dt)

        # Handle Dash
        if input_handler.dash_pressed:
            self.trigger_dash(game_state, input_handler.dash_dir_override)

        if self.is_dashing:
            self.dash_timer -= dt
            self.vel = self.dash_dir * PLAYER_DASH_SPEED
            
            # Emit ghost trails
            self.dash_ghost_timer -= dt
            if self.dash_ghost_timer <= 0:
                self.dash_ghost_timer = 0.04
                game_state.particles.spawn_dash_ghost(self.pos.x, self.pos.y, self.radius)

            if self.dash_timer <= 0:
                self.is_dashing = False
                self.vel = self.dash_dir * (self.base_speed * self.speed_multiplier)
        else:
            # Normal movement input
            move = input_handler.move_dir
            if move.length_squared() > 0:
                target_vel = move * (self.base_speed * self.speed_multiplier)
                # Smooth acceleration
                self.vel.x += (target_vel.x - self.vel.x) * min(1.0, dt * 14.0)
                self.vel.y += (target_vel.y - self.vel.y) * min(1.0, dt * 14.0)
            else:
                # Apply friction when no input
                super().update_physics(dt)

        # Dash charge recharge logic
        if self.dash_charges < self.max_dash_charges:
            self.dash_recharge_timer += dt
            effective_cd = PLAYER_DASH_COOLDOWN * self.dash_cooldown_mult
            if self.dash_recharge_timer >= effective_cd:
                self.dash_charges += 1
                self.dash_recharge_timer = 0.0

        # Handle attacking
        if input_handler.attack_held and self.weapon:
            self.weapon.attack(self, input_handler.mouse_world_pos, game_state)

        # Integrate velocity & resolve walls
        self.pos += self.vel * dt
        self.resolve_obstacle_collisions(train_car)

        # Update timers
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.invulnerable_timer > 0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        if self.recoil_timer > 0:
            self.recoil_timer = max(0.0, self.recoil_timer - dt)
        if self.attack_boost_timer > 0:
            self.attack_boost_timer = max(0.0, self.attack_boost_timer - dt)
            if random.random() < 0.25:
                game_state.particles.spawn_sparks(
                    self.pos.x + random.uniform(-self.radius, self.radius),
                    self.pos.y + random.uniform(-self.radius, self.radius),
                    count=1,
                    color=COLOR_LIGHTNING_CYAN
                )

        # Track movement distance for footstep walk cycle
        if self.vel.length_squared() > 100.0:
            self.walk_distance += self.vel.length() * dt

    def draw(self, surface: pygame.Surface, camera):
        screen_pos = camera.apply(self.pos)
        is_moving = self.vel.length_squared() > 200.0
        draw_stoker_player(
            surface=surface,
            screen_pos=screen_pos,
            aim_angle=self.aim_angle,
            walk_dist=self.walk_distance,
            weapon=self.weapon,
            is_moving=is_moving,
            recoil_timer=self.recoil_timer,
            attack_boost_timer=self.attack_boost_timer,
            flash_timer=self.flash_timer,
            invuln_timer=self.invulnerable_timer,
            radius=self.radius
        )
