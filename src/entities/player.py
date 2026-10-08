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
    COLOR_LIGHTNING_CYAN, COLOR_EMBER_ORANGE
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
        
        # Melee swing dynamic animation
        self.melee_swing_timer = 0.0
        self.melee_swing_duration = 0.22
        self.melee_swing_aim = 0.0
        self.melee_swing_arc = math.pi * 0.65

        # Block & Parry Stance (Shift key)
        self.is_blocking = False
        self.block_timer = 0.0
        self.block_parry_window = 0.20
        self.parry_flash_timer = 0.0

        # Super Ability ('E' key)
        self.super_charge = 0.0
        self.max_super_charge = 100.0
        self.equipped_super_id = "super_boiler_overdrive"

        # Test & Debug Mode flags
        self.god_mode = False

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

    def start_melee_swing(self, duration: float = 0.22, aim_angle: float = 0.0, arc_span: float = math.pi * 0.65):
        """Initiates dynamic rotational melee weapon swing."""
        self.melee_swing_duration = duration
        self.melee_swing_timer = duration
        self.melee_swing_aim = aim_angle
        self.melee_swing_arc = arc_span

    @property
    def is_melee_swinging(self) -> bool:
        return self.melee_swing_timer > 0.0

    def add_super_charge(self, amount: float):
        """Accumulates super charge points from dealing damage."""
        if self.super_charge < self.max_super_charge:
            self.super_charge = min(self.max_super_charge, self.super_charge + amount)

    def can_cast_super(self) -> bool:
        """Returns True if super gauge is 100% full and an ability is equipped."""
        return self.super_charge >= self.max_super_charge and bool(self.equipped_super_id)

    def cast_super_ability(self, game_state) -> bool:
        """Executes the equipped super ability and resets charge."""
        if not self.can_cast_super():
            return False

        self.super_charge = 0.0
        game_state.audio.play('super')
        super_id = self.equipped_super_id or "super_boiler_overdrive"

        if super_id == "super_boiler_overdrive":
            # 1. Boiler Overdrive: 360-degree superheated steam blast
            game_state.camera.add_trauma(0.55)
            game_state.audio.play('explosion')
            radius = 250.0
            # Cleanse bullets
            game_state.projectiles = [
                p for p in game_state.projectiles
                if p.owner == 'player' or (p.pos - self.pos).length() > radius
            ]
            # Damage & knockback all enemies in blast radius
            for enemy in game_state.enemies:
                if enemy.is_alive():
                    diff = enemy.pos - self.pos
                    if diff.length() <= radius:
                        push = diff.normalize() if diff.length() > 0 else pygame.math.Vector2(1, 0)
                        enemy.vel += push * 650.0
                        enemy.hitstop_timer = 0.08
                        enemy.take_damage(DamageEvent(130, is_crit=True, damage_type="steam", source_type="player"), game_state)
            self.invulnerable_timer = 2.5
            self.apply_attack_boost(5.0)
            for _ in range(20):
                game_state.particles.spawn_cleave_fire(self.pos.x, self.pos.y, random.uniform(0, math.tau), math.pi * 0.5, random.uniform(50, radius))
            game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=30, color=COLOR_BRASS_HIGHLIGHT)

        elif super_id == "super_tesla_rail":
            # 2. Tesla Rail Discharge: Hyper-voltage concentrated piercing beam cutting full car length
            game_state.camera.add_trauma(0.65)
            game_state.audio.play('zap')
            game_state.audio.play('explosion')
            ray_len = 1400.0
            beam_dir = self.facing_dir
            beam_start = pygame.math.Vector2(self.pos)
            # Cleanse bullets in beam path
            game_state.projectiles = [
                p for p in game_state.projectiles
                if p.owner == 'player' or (p.pos - beam_start).length() > ray_len
            ]
            for enemy in game_state.enemies:
                if enemy.is_alive():
                    to_enemy = enemy.pos - beam_start
                    proj_dist = to_enemy.dot(beam_dir)
                    if 0 <= proj_dist <= ray_len:
                        perp_dist = (to_enemy - beam_dir * proj_dist).length()
                        if perp_dist <= 55 + enemy.radius:
                            enemy.take_damage(DamageEvent(280, is_crit=True, damage_type="electric", source_type="player"), game_state)
                            enemy.vel += beam_dir * 700.0
                            enemy.hitstop_timer = 0.10
            for step_dist in range(40, int(ray_len), 45):
                pt = beam_start + beam_dir * step_dist
                game_state.particles.spawn_sparks(pt.x, pt.y, count=4, color=COLOR_LIGHTNING_CYAN)

        elif super_id == "super_infernal_cataclysm":
            # 3. Infernal Slag Cataclysm: 6 catastrophic molten shells raining across arena
            game_state.camera.add_trauma(0.8)
            game_state.audio.play('alarm')
            game_state.audio.play('explosion')
            car = getattr(game_state, "train_car", None)
            min_x = max(100, int(self.pos.x - 400))
            max_x = min(getattr(car, "width", 1500) - 100, int(self.pos.x + 500))
            for _ in range(6):
                strike_x = random.uniform(min_x, max_x)
                strike_y = random.uniform(car.top_wall_y + 40, car.bottom_wall_y - 40) if car else self.pos.y
                game_state.particles.spawn_explosion(strike_x, strike_y, radius=120)
                for enemy in game_state.enemies:
                    if enemy.is_alive():
                        dist = (enemy.pos - pygame.math.Vector2(strike_x, strike_y)).length()
                        if dist <= 140:
                            enemy.take_damage(DamageEvent(68, is_crit=True, damage_type="fire", source_type="player"), game_state)
                            enemy.hitstop_timer = 0.08
            game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=30, color=COLOR_EMBER_ORANGE)

        return True

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

    def refill_stats(self):
        """Restores health to maximum and charges super ability to 100%."""
        self.health = self.max_health
        self.super_charge = self.max_super_charge

    def take_damage(self, damage_event: DamageEvent, game_state) -> bool:
        """Process damage taken with active block and parry damage mitigation."""
        if not self.is_alive() or self.invulnerable_timer > 0:
            return False

        if self.god_mode:
            game_state.particles.spawn_sparks(self.pos.x, self.pos.y, count=4, color=COLOR_BRASS_HIGHLIGHT)
            return False

        if self.is_blocking:
            # Check for timed parry (within first 0.20s of raising guard)
            if self.block_timer <= self.block_parry_window:
                # 100% damage negated!
                self.parry_flash_timer = 0.25
                game_state.camera.add_trauma(0.18)
                game_state.audio.play('block')
                game_state.particles.spawn_sparks(self.pos.x + self.facing_dir.x * 20, self.pos.y + self.facing_dir.y * 20, count=18, color=COLOR_BRASS_HIGHLIGHT)
                game_state.particles.add_damage_number(self.pos.x, self.pos.y - 15, 0, is_crit=True, damage_type="buff")
                # Counter-stagger attacker if any
                for enemy in game_state.enemies:
                    if enemy.is_alive() and (enemy.pos - self.pos).length() <= 120:
                        enemy.vel -= self.facing_dir * 380.0
                        enemy.hitstop_timer = 0.15
                return False
            else:
                # Standard block: 75% damage mitigation!
                damage_event.amount = max(1, int(damage_event.amount * 0.25))
                self.vel -= self.facing_dir * 130.0
                game_state.audio.play('block')
                game_state.particles.spawn_sparks(self.pos.x + self.facing_dir.x * 15, self.pos.y + self.facing_dir.y * 15, count=10, color=COLOR_BRASS)

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

        # Update swing & parry timers
        if self.melee_swing_timer > 0:
            self.melee_swing_timer = max(0.0, self.melee_swing_timer - dt)
        if self.parry_flash_timer > 0:
            self.parry_flash_timer = max(0.0, self.parry_flash_timer - dt)

        # Handle Block state from Shift key
        if getattr(input_handler, "block_held", False):
            if not self.is_blocking:
                self.is_blocking = True
                self.block_timer = 0.0
            self.block_timer += dt
        else:
            self.is_blocking = False
            self.block_timer = 0.0

        # Handle Super Ability trigger ('E' key)
        if getattr(input_handler, "interact_pressed", False):
            # Guard against activating super if standing near unclaimed pedestal
            pedestal_nearby = False
            if train_car and getattr(train_car, "boon_pedestal_active", False) and not getattr(train_car, "boon_claimed", False):
                dist_ped = (self.pos - train_car.boon_pedestal_pos).length()
                if dist_ped <= 140:
                    pedestal_nearby = True
            if not pedestal_nearby and self.can_cast_super():
                self.cast_super_ability(game_state)

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
            # Normal movement input (slowed by 55% while in defensive block stance)
            move = input_handler.move_dir
            if move.length_squared() > 0:
                speed_mod = 0.45 if self.is_blocking else 1.0
                target_vel = move * (self.base_speed * self.speed_multiplier * speed_mod)
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

        # Handle attacking (cannot attack while holding block)
        if input_handler.attack_held and self.weapon and not self.is_blocking:
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
            radius=self.radius,
            is_blocking=self.is_blocking,
            block_timer=self.block_timer,
            parry_flash_timer=self.parry_flash_timer,
            melee_swing_timer=self.melee_swing_timer,
            melee_swing_duration=self.melee_swing_duration,
            melee_swing_arc=self.melee_swing_arc
        )
