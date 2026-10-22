"""Player weapons system featuring ranged rivet guns, melee wrenches, and scatterguns with Ranks 1-5."""
import pygame
import math
import random
from src.config import (
    COLOR_BRASS, COLOR_BRASS_HIGHLIGHT, COLOR_WHITE,
    COLOR_EMBER_ORANGE, COLOR_LIGHTNING_CYAN, COLOR_CRIT_YELLOW
)
from src.entities.projectile import Projectile
from src.combat.damage import roll_damage

class Weapon:
    """Base class for all weaponry."""
    def __init__(self, weapon_id: str, name: str, desc: str, fire_rate: float, base_damage: int, sound_name: str = "shoot", rank: int = 1):
        self.weapon_id = weapon_id
        self.id = weapon_id
        self.name = name
        self.desc = desc
        self.fire_rate = fire_rate          # Baseline cooldown seconds between shots
        self.base_damage = base_damage
        self.sound_name = sound_name
        self.rank = max(1, min(5, int(rank)))
        self.cooldown_timer = 0.0

    def update(self, dt: float):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    def can_attack(self) -> bool:
        return self.cooldown_timer <= 0.0

    def get_effective_fire_rate(self, player) -> float:
        """Returns fire rate cooldown, applying rank and timed overcharge buff if active."""
        rate = self.fire_rate
        if player and getattr(player, "attack_boost_timer", 0.0) > 0:
            return max(0.06, rate * 0.65)  # 35% faster attack speed
        return rate

    def get_effective_damage(self, player) -> int:
        """Returns base damage, applying timed overcharge buff if active."""
        dmg = self.base_damage
        if player and getattr(player, "attack_boost_timer", 0.0) > 0:
            return int(dmg * 1.25)  # 25% attack damage boost
        return dmg

    def attack(self, player, aim_world_pos: pygame.math.Vector2, game_state) -> bool:
        """Trigger attack towards aim_world_pos. Returns True if shot was fired."""
        raise NotImplementedError


class RivetGun(Weapon):
    """Rapid-fire pneumatic rivet gun with Ranks 1 to 5."""
    def __init__(self, rank: int = 1):
        # Scale stats with rank
        fire_rate = 0.18 if rank == 1 else (0.13 if rank >= 2 else 0.18)
        base_dmg = 16 + (rank - 1) * 4
        super().__init__("rivet_gun", "Pneumatic Riveter", "Rapid needle fire with pinpoint accuracy.", fire_rate=fire_rate, base_damage=base_dmg, sound_name="shoot", rank=rank)
        self.speed = 900.0 if rank == 1 else 1150.0
        self.projectile_count = 2 if rank >= 4 else 1

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)

        dir_vec = aim_world_pos - player.pos
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.math.Vector2(1, 0)
        dir_vec = dir_vec.normalize()

        pierce = 2 if self.rank >= 3 else 0
        bounces = 3 if self.rank >= 5 else 0
        dmg_val = self.get_effective_damage(player)

        shots = []
        if self.rank >= 4:
            # Rank 4 & 5: Twin-Barrel Micro-Rockets (offset parallel needles)
            perp = pygame.math.Vector2(-dir_vec.y, dir_vec.x) * 8.0
            shots.append(player.pos + perp)
            shots.append(player.pos - perp)
        else:
            shots.append(player.pos)

        for spawn_pos in shots:
            angle = math.atan2(dir_vec.y, dir_vec.x) + random.uniform(-0.04, 0.04)
            vel = pygame.math.Vector2(math.cos(angle) * self.speed, math.sin(angle) * self.speed)
            dmg_event = roll_damage(dmg_val, crit_chance=player.crit_chance + (0.10 if self.rank >= 5 else 0.0), crit_mult=player.crit_mult)
            proj = Projectile(
                x=spawn_pos.x + dir_vec.x * 20,
                y=spawn_pos.y + dir_vec.y * 20,
                vel=vel,
                damage_event=dmg_event,
                radius=4.5,
                lifetime=1.4,
                color=COLOR_BRASS_HIGHLIGHT,
                owner="player",
                pierce=pierce,
                bounces=bounces,
                is_explosive=(self.rank >= 4),
                explosion_radius=40.0 if self.rank >= 4 else 0.0
            )
            for boon in player.boons:
                boon.modify_projectile(proj)
                boon.on_attack(player, self, game_state)
            game_state.projectiles.append(proj)
            game_state.particles.spawn_rivet_fire(spawn_pos.x + dir_vec.x * 20, spawn_pos.y + dir_vec.y * 20, dir_vec)

        player.recoil_timer = 0.08
        game_state.audio.play(self.sound_name)
        game_state.camera.add_trauma(0.06 if self.rank < 4 else 0.10)
        return True


class StokerWrench(Weapon):
    """Heavy industrial melee wrench that cleaves in a wide frontal arc with Ranks 1 to 5."""
    def __init__(self, rank: int = 1):
        base_dmg = 62 + (rank - 1) * 16
        fire_rate = 0.45 if rank < 2 else 0.38
        super().__init__("stoker_wrench", "Stoker's Heavy Cleaver", "Wide melee arc with heavy knockback.", fire_rate=fire_rate, base_damage=base_dmg, sound_name="swing", rank=rank)
        self.arc_angle = math.pi * 0.65 if rank == 1 else math.pi * 0.88  # 158 degree cleave at rank 2+
        self.reach = 85.0 if rank == 1 else 115.0
        self.swing_count = 0

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)
        self.swing_count += 1
        player.recoil_timer = 0.16

        aim_vec = aim_world_pos - player.pos
        if aim_vec.length_squared() == 0:
            aim_vec = pygame.math.Vector2(1, 0)
        aim_vec = aim_vec.normalize()
        aim_angle = math.atan2(aim_vec.y, aim_vec.x)

        # Rank 5: Berserker Whirlwind every 3rd swing
        is_cyclone = (self.rank >= 5 and self.swing_count % 3 == 0)
        current_arc = math.pi * 2.0 if is_cyclone else self.arc_angle
        current_reach = self.reach * 1.35 if is_cyclone else self.reach

        if is_cyclone:
            player.invulnerable_timer = max(player.invulnerable_timer, 1.2)
            game_state.camera.add_trauma(0.40)
            game_state.audio.play('super')

        if hasattr(player, "start_melee_swing"):
            player.start_melee_swing(duration=0.22, aim_angle=aim_angle, arc_span=current_arc)

        game_state.audio.play(self.sound_name)
        game_state.camera.add_trauma(0.20)
        game_state.particles.spawn_cleave_fire(player.pos.x, player.pos.y, aim_angle, current_arc, current_reach)

        effective_dmg = self.get_effective_damage(player) * (1.6 if is_cyclone else 1.0)

        # Rank 3+: Sonic Crescent Shockwave launched forward
        if self.rank >= 3 and not is_cyclone:
            wave_dmg = roll_damage(int(effective_dmg * 0.75), crit_chance=player.crit_chance, crit_mult=2.0)
            wave_proj = Projectile(
                x=player.pos.x + aim_vec.x * 30,
                y=player.pos.y + aim_vec.y * 30,
                vel=aim_vec * 750.0,
                damage_event=wave_dmg,
                radius=18.0,
                lifetime=0.8,
                color=(240, 220, 160),
                owner="player",
                pierce=99
            )
            game_state.projectiles.append(wave_proj)

        # Rank 4+: Parries and reverses enemy bullets as 3x homing critical missiles!
        if self.rank >= 4:
            for proj in list(game_state.projectiles):
                if proj.owner == "enemy" and (proj.pos - player.pos).length() <= current_reach + 30:
                    proj.owner = "player"
                    proj.color = COLOR_CRIT_YELLOW
                    proj.vel = aim_vec * 1100.0
                    proj.damage_event.amount = int(proj.damage_event.amount * 3.0)
                    proj.damage_event.is_crit = True
                    game_state.audio.play('block')

        # Check enemies in melee sector
        for enemy in game_state.enemies:
            if not enemy.is_alive():
                continue
            diff = enemy.pos - player.pos
            dist = diff.length()
            if dist <= current_reach + enemy.radius:
                enemy_angle = math.atan2(diff.y, diff.x)
                angle_diff = (enemy_angle - aim_angle + math.pi) % (2 * math.pi) - math.pi
                if is_cyclone or abs(angle_diff) <= current_arc / 2:
                    dmg_event = roll_damage(effective_dmg, crit_chance=player.crit_chance + 0.15, crit_mult=2.4)
                    push_dir = (player.pos - enemy.pos).normalize() * -1.0 if is_cyclone else (diff.normalize() if dist > 0 else aim_vec)
                    enemy.vel += push_dir * (650.0 if is_cyclone else 480.0)
                    enemy.take_damage(dmg_event, game_state)
                    if hasattr(enemy, "hitstop_timer"):
                        enemy.hitstop_timer = 0.05
                    game_state.particles.spawn_sparks(enemy.pos.x, enemy.pos.y, count=16, color=COLOR_CRIT_YELLOW)
                    game_state.audio.play('hit')

        # Check interactive props
        if hasattr(game_state, "train_car") and game_state.train_car:
            for barrel in game_state.train_car.barrels:
                if not barrel.is_dead and (barrel.pos - player.pos).length() <= current_reach + barrel.radius:
                    barrel.take_damage(roll_damage(effective_dmg), game_state)
            for crate in game_state.train_car.crates:
                if not crate.is_dead and (crate.pos - player.pos).length() <= current_reach + crate.radius:
                    crate.take_damage(roll_damage(effective_dmg), game_state)
            if hasattr(game_state.train_car, "windows"):
                for win in game_state.train_car.windows:
                    if win.state != win.STATE_SHATTERED and (win.pos - player.pos).length() <= current_reach + 35:
                        win.take_damage(effective_dmg, game_state)

        for boon in player.boons:
            boon.on_attack(player, self, game_state)

        return True


class CoalScattergun(Weapon):
    """High-spread blunderbuss firing a burst of heated shrapnel with Ranks 1 to 5."""
    def __init__(self, rank: int = 1):
        pellets = 5 if rank == 1 else 8
        base_dmg = 14 + (rank - 1) * 3
        fire_rate = 0.65 if rank == 1 else 0.52
        super().__init__("coal_scattergun", "Coal Scattergun", "Pellet burst. Deadly at close range.", fire_rate=fire_rate, base_damage=base_dmg, sound_name="shotgun", rank=rank)
        self.pellets = pellets
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
        game_state.camera.add_trauma(0.24)

        spread_factor = 0.12 if self.rank == 1 else 0.08
        is_dragon = (self.rank >= 3)

        for i in range(self.pellets):
            spread = (i - (self.pellets - 1) / 2) * spread_factor + random.uniform(-0.03, 0.03)
            vel = pygame.math.Vector2(math.cos(base_angle + spread), math.sin(base_angle + spread)) * (self.speed * random.uniform(0.9, 1.1))
            dmg = roll_damage(self.get_effective_damage(player), crit_chance=player.crit_chance, crit_mult=player.crit_mult)
            proj = Projectile(
                x=player.pos.x + dir_vec.x * 20,
                y=player.pos.y + dir_vec.y * 20,
                vel=vel,
                damage_event=dmg,
                radius=5.0,
                lifetime=0.55,
                color=COLOR_EMBER_ORANGE,
                owner="player",
                is_dragon_breath=is_dragon
            )
            for boon in player.boons:
                boon.modify_projectile(proj)
            game_state.projectiles.append(proj)

        # Rank 5: High-Explosive Breacher Artillery Slug
        if self.rank >= 5:
            slug_dmg = roll_damage(int(self.get_effective_damage(player) * 5.0), crit_chance=player.crit_chance + 0.2, crit_mult=2.5)
            slug = Projectile(
                x=player.pos.x + dir_vec.x * 24,
                y=player.pos.y + dir_vec.y * 24,
                vel=dir_vec * (self.speed * 1.1),
                damage_event=slug_dmg,
                radius=10.0,
                lifetime=0.7,
                color=(255, 120, 30),
                owner="player",
                is_explosive=True,
                explosion_radius=130.0
            )
            game_state.projectiles.append(slug)
            game_state.audio.play('explosion')

        # Rank 4+: Heavy concussion knockback to nearby enemies
        if self.rank >= 4:
            for enemy in game_state.enemies:
                if enemy.is_alive() and (enemy.pos - player.pos).length() <= 160.0:
                    diff = enemy.pos - player.pos
                    enemy.vel += diff.normalize() * 850.0
                    if hasattr(enemy, "hitstop_timer"):
                        enemy.hitstop_timer = 0.55

        game_state.particles.spawn_scattergun_fire(player.pos.x + dir_vec.x * 22, player.pos.y + dir_vec.y * 22, dir_vec)
        for boon in player.boons:
            boon.on_attack(player, self, game_state)

        return True


class TeslaArcCaster(Weapon):
    """Discharges concentrated ball lightning with Ranks 1 to 5."""
    def __init__(self, rank: int = 1):
        base_dmg = 24 + (rank - 1) * 6
        speed = 680.0 if rank == 1 else 880.0
        fire_rate = 0.40 if rank < 2 else 0.32
        super().__init__("tesla_arc_caster", "Tesla Arc Caster", "Piercing plasma spheres that shock foes.", fire_rate=fire_rate, base_damage=base_dmg, sound_name="zap", rank=rank)
        self.speed = speed

    def attack(self, player, aim_world_pos, game_state):
        if not self.can_attack():
            return False
        self.cooldown_timer = self.get_effective_fire_rate(player)
        player.recoil_timer = 0.12

        dir_vec = aim_world_pos - player.pos
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.math.Vector2(1, 0)
        dir_vec = dir_vec.normalize()

        angles = [math.atan2(dir_vec.y, dir_vec.x)]
        if self.rank >= 4:
            # Rank 4 & 5: Dual Helix Orbs (two angled plasma spheres)
            angles = [angles[0] - 0.12, angles[0] + 0.12]

        pierce = 4 if self.rank >= 2 else 2

        for ang in angles:
            vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * self.speed
            dmg_event = roll_damage(self.get_effective_damage(player), crit_chance=player.crit_chance + 0.18, crit_mult=2.5, damage_type="electric")
            proj = Projectile(
                x=player.pos.x + dir_vec.x * 22,
                y=player.pos.y + dir_vec.y * 22,
                vel=vel,
                damage_event=dmg_event,
                radius=8.0 if self.rank >= 4 else 7.0,
                lifetime=1.3,
                color=COLOR_LIGHTNING_CYAN,
                owner="player",
                pierce=pierce,
                is_explosive=(self.rank >= 5),
                explosion_radius=90.0 if self.rank >= 5 else 0.0
            )
            for boon in player.boons:
                boon.modify_projectile(proj)
                boon.on_attack(player, self, game_state)
            game_state.projectiles.append(proj)

        # Rank 3+: Electrifies nearby foes with Static Ionization (+30% damage taken)
        if self.rank >= 3:
            for enemy in game_state.enemies:
                if enemy.is_alive() and (enemy.pos - player.pos).length() <= 200.0:
                    enemy.is_chilled = True  # Slow effect
                    if hasattr(enemy, "vulnerable_timer"):
                        enemy.vulnerable_timer = 4.0

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

def create_weapon_by_id(weapon_id: str, rank: int = 1) -> Weapon:
    """Factory creating weapon instance configured to the specified rank."""
    mapping = {
        "rivet_gun": RivetGun,
        "stoker_wrench": StokerWrench,
        "coal_scattergun": CoalScattergun,
        "tesla_arc_caster": TeslaArcCaster
    }
    cls = mapping.get(weapon_id, RivetGun)
    return cls(rank=rank)
