"""Player weapons system featuring ranged rivet guns, melee wrenches, and scatterguns."""
import pygame
import math
import random
from src.config import (
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_WHITE,
    COLOR_EMBER_ORANGE, COLOR_LIGHTNING_CYAN
)
from src.entities.projectile import Projectile
from src.combat.damage import roll_damage

class Weapon:
    """Base class for all weaponry."""
    def __init__(self, name: str, desc: str, fire_rate: float, base_damage: int, sound_name: str = "shoot"):
        self.name = name
        self.desc = desc
        self.fire_rate = fire_rate          # Baseline cooldown seconds between shots
        self.base_damage = base_damage
        self.sound_name = sound_name
        self.cooldown_timer = 0.0

    def update(self, dt: float):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    def can_attack(self) -> bool:
        return self.cooldown_timer <= 0.0

    def get_effective_fire_rate(self, player) -> float:
        """Returns fire rate cooldown, applying timed overcharge buff if active."""
        if player and getattr(player, "attack_boost_timer", 0.0) > 0:
            return max(0.08, self.fire_rate * 0.65)  # 35% faster attack speed
        return self.fire_rate

    def get_effective_damage(self, player) -> int:
        """Returns base damage, applying timed overcharge buff if active."""
        if player and getattr(player, "attack_boost_timer", 0.0) > 0:
            return int(self.base_damage * 1.25)  # 25% attack damage boost
        return self.base_damage

    def attack(self, player, aim_world_pos: pygame.math.Vector2, game_state) -> bool:
        """Trigger attack towards aim_world_pos. Returns True if shot was fired."""
        raise NotImplementedError


class RivetGun(Weapon):
    """Rapid-fire pneumatic rivet gun. High accuracy and steady DPS."""
    def __init__(self):
        super().__init__("Pneumatic Riveter", "Rapid needle fire with pinpoint accuracy.", fire_rate=0.18, base_damage=16, sound_name="shoot")
        self.speed = 900.0

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)

        dir_vec = aim_world_pos - player.pos
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.math.Vector2(1, 0)
        dir_vec = dir_vec.normalize()

        # Slight spread
        angle = math.atan2(dir_vec.y, dir_vec.x) + random.uniform(-0.06, 0.06)
        vel = pygame.math.Vector2(math.cos(angle) * self.speed, math.sin(angle) * self.speed)

        dmg_event = roll_damage(self.get_effective_damage(player), crit_chance=player.crit_chance, crit_mult=player.crit_mult)
        
        proj = Projectile(
            x=player.pos.x + dir_vec.x * 20,
            y=player.pos.y + dir_vec.y * 20,
            vel=vel,
            damage_event=dmg_event,
            radius=4.0,
            lifetime=1.4,
            color=COLOR_BRASS_HIGHLIGHT,
            owner="player"
        )
        
        # Apply boon modifications
        for boon in player.boons:
            boon.modify_projectile(proj)
            boon.on_attack(player, self, game_state)

        game_state.projectiles.append(proj)
        game_state.particles.spawn_rivet_fire(player.pos.x + dir_vec.x * 20, player.pos.y + dir_vec.y * 20, dir_vec)
        player.recoil_timer = 0.08
        game_state.audio.play(self.sound_name)
        game_state.camera.add_trauma(0.06)
        return True


class StokerWrench(Weapon):
    """Heavy industrial melee wrench that cleaves in a wide frontal arc."""
    def __init__(self):
        super().__init__("Stoker's Cleaver", "Wide melee arc with heavy knockback.", fire_rate=0.45, base_damage=48, sound_name="swing")
        self.arc_angle = math.pi * 0.65  # 120 degree cleave
        self.reach = 85.0

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)
        player.recoil_timer = 0.16

        aim_vec = aim_world_pos - player.pos
        if aim_vec.length_squared() == 0:
            aim_vec = pygame.math.Vector2(1, 0)
        aim_vec = aim_vec.normalize()
        aim_angle = math.atan2(aim_vec.y, aim_vec.x)

        game_state.audio.play(self.sound_name)
        game_state.camera.add_trauma(0.18)

        # Fiery crescent slash arc particles
        game_state.particles.spawn_cleave_fire(player.pos.x, player.pos.y, aim_angle, self.arc_angle, self.reach)

        effective_dmg = self.get_effective_damage(player)

        # Check enemies in melee sector
        for enemy in game_state.enemies:
            if not enemy.is_alive():
                continue
            diff = enemy.pos - player.pos
            dist = diff.length()
            if dist <= self.reach + enemy.radius:
                # Check angle alignment
                enemy_angle = math.atan2(diff.y, diff.x)
                angle_diff = (enemy_angle - aim_angle + math.pi) % (2 * math.pi) - math.pi
                if abs(angle_diff) <= self.arc_angle / 2:
                    dmg_event = roll_damage(effective_dmg, crit_chance=player.crit_chance + 0.1, crit_mult=2.2)
                    # Push back heavily
                    push_dir = diff.normalize() if dist > 0 else aim_vec
                    enemy.vel += push_dir * 450.0
                    enemy.take_damage(dmg_event, game_state)
                    game_state.particles.spawn_sparks(enemy.pos.x, enemy.pos.y, count=10, color=COLOR_WHITE)
                    game_state.audio.play('hit')

        # Check interactive props in melee sector
        if hasattr(game_state, "train_car") and game_state.train_car:
            for barrel in game_state.train_car.barrels:
                if not barrel.is_dead and (barrel.pos - player.pos).length() <= self.reach + barrel.radius:
                    barrel.take_damage(roll_damage(effective_dmg), game_state)
            for crate in game_state.train_car.crates:
                if not crate.is_dead and (crate.pos - player.pos).length() <= self.reach + crate.radius:
                    crate.take_damage(roll_damage(effective_dmg), game_state)
            if hasattr(game_state.train_car, "windows"):
                for win in game_state.train_car.windows:
                    if win.state != win.STATE_SHATTERED and (win.pos - player.pos).length() <= self.reach + 35:
                        win.take_damage(effective_dmg, game_state)

        for boon in player.boons:
            boon.on_attack(player, self, game_state)

        return True


class CoalScattergun(Weapon):
    """High-spread blunderbuss firing a burst of heated shrapnel."""
    def __init__(self):
        super().__init__("Coal Scattergun", "5-pellet burst. Deadly at close range.", fire_rate=0.65, base_damage=14, sound_name="shotgun")
        self.pellets = 5
        self.speed = 850.0

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)
        player.recoil_timer = 0.22

        dir_vec = aim_world_pos - player.pos
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.math.Vector2(1, 0)
        dir_vec = dir_vec.normalize()
        base_angle = math.atan2(dir_vec.y, dir_vec.x)

        game_state.audio.play(self.sound_name)
        game_state.camera.add_trauma(0.22)

        for i in range(self.pellets):
            spread = (i - (self.pellets - 1) / 2) * 0.12 + random.uniform(-0.04, 0.04)
            vel = pygame.math.Vector2(math.cos(base_angle + spread), math.sin(base_angle + spread)) * (self.speed * random.uniform(0.9, 1.1))
            dmg = roll_damage(self.get_effective_damage(player), crit_chance=player.crit_chance, crit_mult=player.crit_mult)
            proj = Projectile(
                x=player.pos.x + dir_vec.x * 20,
                y=player.pos.y + dir_vec.y * 20,
                vel=vel,
                damage_event=dmg,
                radius=4.5,
                lifetime=0.55,
                color=COLOR_EMBER_ORANGE,
                owner="player"
            )
            for boon in player.boons:
                boon.modify_projectile(proj)
            game_state.projectiles.append(proj)

        game_state.particles.spawn_scattergun_fire(player.pos.x + dir_vec.x * 22, player.pos.y + dir_vec.y * 22, dir_vec)
        for boon in player.boons:
            boon.on_attack(player, self, game_state)

        return True


class TeslaArcCaster(Weapon):
    """Discharges concentrated ball lightning that hums and zaps nearby foes."""
    def __init__(self):
        super().__init__("Tesla Arc Caster", "Piercing plasma spheres that shock foes.", fire_rate=0.40, base_damage=24, sound_name="zap")
        self.speed = 680.0

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)
        player.recoil_timer = 0.12

        dir_vec = aim_world_pos - player.pos
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.math.Vector2(1, 0)
        dir_vec = dir_vec.normalize()

        vel = dir_vec * self.speed
        dmg_event = roll_damage(self.get_effective_damage(player), crit_chance=player.crit_chance + 0.15, crit_mult=2.5, damage_type="electric")

        proj = Projectile(
            x=player.pos.x + dir_vec.x * 22,
            y=player.pos.y + dir_vec.y * 22,
            vel=vel,
            damage_event=dmg_event,
            radius=7.0,
            lifetime=1.2,
            color=COLOR_LIGHTNING_CYAN,
            owner="player",
            pierce=2
        )
        for boon in player.boons:
            boon.modify_projectile(proj)
            boon.on_attack(player, self, game_state)

        game_state.projectiles.append(proj)
        game_state.particles.spawn_tesla_fire(player.pos.x + dir_vec.x * 22, player.pos.y + dir_vec.y * 22, dir_vec)
        game_state.audio.play(self.sound_name)
        game_state.camera.add_trauma(0.12)
        return True


AVAILABLE_WEAPONS = [
    RivetGun,
    StokerWrench,
    CoalScattergun,
    TeslaArcCaster,
]
