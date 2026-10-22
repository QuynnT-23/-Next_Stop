"""Roguelite Boon & Synergy upgrade system with 3-tier leveling and evolutions."""
import random
import math
import pygame
from src.config import (
    COLOR_LIGHTNING_CYAN, COLOR_EMBER_ORANGE, COLOR_CRIT_YELLOW,
    COLOR_HEALTH_GREEN, COLOR_WHITE, COLOR_BRASS_HIGHLIGHT
)
from src.combat.damage import DamageEvent

RARITY_COLORS = {
    "Common": (185, 200, 220),       # Silver Steel
    "Rare": (60, 205, 255),          # Searing Electric Cyan
    "Epic": (195, 80, 255),          # Royal Amethyst Violet
    "Legendary": (255, 215, 30),     # Radiant Sun Gold
}

class Boon:
    """Base class for ability upgrades supporting 3-tier leveling and evolutions."""
    def __init__(self, boon_id: str, name: str, rarity: str, tag: str, description: str, color: tuple, element: str = "KINETIC"):
        self.id = boon_id
        self.name = name
        self.rarity = rarity          # Common, Rare, Epic, Legendary
        self.tag = tag                # Tesla, Steam, Kinetic, Alchemical, Cryo, Pyro
        self.description = description
        self.color = color if color else RARITY_COLORS.get(rarity, COLOR_WHITE)
        self.element = element        # ELECTRIC, PYRO, CRYO, KINETIC, ALCHEMICAL, DEFENSIVE, MOBILITY
        self.level = 1
        self.max_level = 3

    def is_max_level(self) -> bool:
        return self.level >= self.max_level

    def get_display_name(self) -> str:
        if self.level >= self.max_level:
            return f"{self.name} [TIER {self.level} - MAX]"
        return f"{self.name} [TIER {self.level}/{self.max_level}]"

    def get_upgrade_description(self) -> str:
        """Returns preview text for next level tier."""
        return "Increases power and effectiveness."

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        """Returns structured stat metrics [(label, value)] for detailed UI inspector."""
        return [
            ("Tier Level", f"Tier {self.level}/{self.max_level}"),
            ("Effect Scaling", f"+{self.level * 25}% Base Power")
        ]

    def upgrade(self, player):
        """Advance to next level tier."""
        if self.level < self.max_level:
            self.level += 1
            self.apply_level_up(player)

    def apply_level_up(self, player):
        """Hook for stat changes on level up."""
        pass

    def on_acquire(self, player):
        pass

    def modify_projectile(self, proj):
        pass

    def on_attack(self, player, weapon, game_state):
        pass

    def on_hit(self, player, target, damage_event, game_state):
        pass

    def on_dash(self, player, start_pos: pygame.math.Vector2, end_pos: pygame.math.Vector2, game_state):
        pass

    def on_kill(self, player, target, game_state):
        pass

    def on_take_damage(self, player, damage_event, game_state):
        pass


class TeslaCoilBoon(Boon):
    """Hits discharge electric lightning that chains to nearby foes."""
    def __init__(self, rarity="Epic"):
        super().__init__(
            "tesla_coil", "Tesla Discharge", rarity, "Tesla",
            "Attacks shock the target and chain lightning arcs to 2 nearby foes for 45% damage.",
            RARITY_COLORS["Epic"],
            element="ELECTRIC"
        )
        self.chain_count = 2
        self.damage_mult = 0.45

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Chain Targets", "2 foes (-> 4 next)"), ("Arc Damage", "45% (-> 65% next)"), ("Shock Effect", "Stun (at Lvl 2)")]
        elif self.level == 2:
            return [("Chain Targets", "4 foes (-> 6 next)"), ("Arc Damage", "65% (-> 85% next)"), ("Shock Effect", "Stun + Fatal Detonation")]
        return [("Chain Targets", "6 foes (MAX)"), ("Arc Damage", "85% (MAX)"), ("Shock Effect", "Stun + Exploding Foes")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Chains to 4 foes for 65% damage, and electric shocks briefly stun foes."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): Chains to 6 foes for 85% damage. Defeated shocked foes explode!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.chain_count = 4
            self.damage_mult = 0.65
        elif self.level == 3:
            self.chain_count = 6
            self.damage_mult = 0.85

    def on_hit(self, player, target, damage_event, game_state):
        if damage_event.damage_type == "electric":
            return
            
        enemies = [e for e in game_state.enemies if e is not target and e.is_alive()]
        if not enemies:
            return
            
        enemies.sort(key=lambda e: (e.pos - target.pos).length_squared())
        chained = enemies[:self.chain_count]
        
        for next_target in chained:
            if (next_target.pos - target.pos).length() < 280:
                dmg = max(5, int(damage_event.amount * self.damage_mult))
                chain_event = DamageEvent(dmg, source_type="player", damage_type="electric", is_crit=False)
                next_target.take_damage(chain_event, game_state)
                
                # Level 2+ stun
                if self.level >= 2:
                    next_target.vel *= 0.1
                    
                game_state.particles.spawn_sparks(next_target.pos.x, next_target.pos.y, count=7, color=COLOR_LIGHTNING_CYAN)
                game_state.audio.play('zap')

    def on_kill(self, player, target, game_state):
        if self.level >= 3:
            # Level 3 shockwave burst
            game_state.particles.spawn_sparks(target.pos.x, target.pos.y, count=14, color=COLOR_LIGHTNING_CYAN)
            for e in game_state.enemies:
                if e.is_alive() and (e.pos - target.pos).length() < 120:
                    e.take_damage(DamageEvent(35, source_type="player", damage_type="electric"), game_state)


class SteamOverdriveDashBoon(Boon):
    """Dashes leave a trail of superheated steam."""
    def __init__(self, rarity="Common"):
        super().__init__(
            "steam_dash", "Boiler Jet Dash", rarity, "Steam",
            "Dashing vents burning steam, dealing 25 damage to enemies caught in your wake.",
            COLOR_EMBER_ORANGE,
            element="PYRO"
        )
        self.burn_damage = 25

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Trail Burn", "25 DMG (-> 45 next)"), ("Trail Width", "45px (-> 70px next)"), ("Bonus Dash", "+1 at Tier 3")]
        elif self.level == 2:
            return [("Trail Burn", "45 DMG (-> 70 next)"), ("Trail Width", "70px (MAX)"), ("Bonus Dash", "+1 at Tier 3")]
        return [("Trail Burn", "70 DMG (MAX)"), ("Trail Width", "70px (MAX)"), ("Backblast", "30 AoE DMG + 1 Dash")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Steam deals 45 damage with wider trail radius and longer burn."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): 70 damage + dashing releases an explosive backblast & grants +1 Dash Charge!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.burn_damage = 45
        elif self.level == 3:
            self.burn_damage = 70
            player.max_dash_charges += 1
            player.dash_charges += 1

    def on_dash(self, player, start_pos, end_pos, game_state):
        count = 10 if self.level == 1 else 18
        game_state.particles.spawn_steam(start_pos.x, start_pos.y, count=count, color=COLOR_EMBER_ORANGE)
        game_state.audio.play('shoot')
        
        # Level 3 Backblast explosion at dash start
        if self.level >= 3:
            game_state.particles.spawn_explosion(start_pos.x, start_pos.y, radius=60)
            game_state.audio.play('explosion')
            for enemy in game_state.enemies:
                if enemy.is_alive() and (enemy.pos - start_pos).length() < 90:
                    push = (enemy.pos - start_pos).normalize() * 400.0 if (enemy.pos - start_pos).length_squared() > 0 else pygame.math.Vector2(0, 0)
                    enemy.vel += push
                    enemy.take_damage(DamageEvent(30, source_type="player", damage_type="steam"), game_state)

        hit_width = 45.0 if self.level == 1 else 70.0
        for enemy in game_state.enemies:
            if not enemy.is_alive():
                continue
            dist = point_to_segment_dist(enemy.pos, start_pos, end_pos)
            if dist < hit_width:
                enemy.take_damage(DamageEvent(self.burn_damage, source_type="player", damage_type="steam"), game_state)
                game_state.particles.spawn_sparks(enemy.pos.x, enemy.pos.y, count=5, color=COLOR_EMBER_ORANGE)

        # Duo Synergy: Inferno Jet (Molten Fuel + Steam Dash)
        if any(b.id == "molten_core" for b in player.boons):
            for frac in [0.25, 0.5, 0.75, 1.0]:
                fx = start_pos.x + (end_pos.x - start_pos.x) * frac
                fy = start_pos.y + (end_pos.y - start_pos.y) * frac
                game_state.particles.spawn_sparks(fx, fy, count=6, color=(255, 90, 20))
                if hasattr(game_state, "train_car") and game_state.train_car:
                    for b in game_state.train_car.barrels:
                        if not b.is_dead and b.rect.collidepoint(fx, fy):
                            b.take_damage(DamageEvent(50, source_type="player", damage_type="fire"), game_state)

        # Duo Synergy: Cryo-Flashfreeze (Cryo Condenser + Steam Dash)
        if any(b.id == "cryo_condenser" for b in player.boons):
            for enemy in game_state.enemies:
                if enemy.is_alive() and point_to_segment_dist(enemy.pos, start_pos, end_pos) < hit_width:
                    enemy.vel = pygame.math.Vector2(0, 0)
                    game_state.particles.spawn_sparks(enemy.pos.x, enemy.pos.y, count=8, color=(140, 230, 255))


class TungstenPiercingBoon(Boon):
    """Projectiles pierce additional targets and gain speed."""
    def __init__(self, rarity="Common"):
        super().__init__(
            "tungsten_pierce", "Tungsten Rounds", rarity, "Kinetic",
            "Projectiles pierce +1 target and gain +20% velocity.",
            COLOR_BRASS_HIGHLIGHT,
            element="KINETIC"
        )
        self.extra_pierce = 1
        self.vel_mult = 1.20

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Pierce Count", "+1 (-> +2 next)"), ("Proj Velocity", "+20% (-> +35% next)"), ("Wall Ricochet", "Locked")]
        elif self.level == 2:
            return [("Pierce Count", "+2 (-> +3 next)"), ("Proj Velocity", "+35% (-> +50% next)"), ("Wall Ricochet", "Locked")]
        return [("Pierce Count", "+3 (MAX)"), ("Proj Velocity", "+50% (MAX)"), ("Wall Ricochet", "Active (Bounces)")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Pierce +2 targets, +35% projectile velocity, and +15% base damage."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): Pierce +3 targets, +50% velocity, and projectiles bounce off walls!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.extra_pierce = 2
            self.vel_mult = 1.35
        elif self.level == 3:
            self.extra_pierce = 3
            self.vel_mult = 1.50

    def modify_projectile(self, proj):
        proj.pierce += self.extra_pierce
        proj.vel *= self.vel_mult


class KineticPlatingBoon(Boon):
    """Taking damage triggers an outward kinetic repulsor shockwave."""
    def __init__(self, rarity="Rare"):
        super().__init__(
            "kinetic_plating", "Kinetic Repulsor", rarity, "Kinetic",
            "When struck, blasts surrounding foes backward and deals 20 damage.",
            (180, 200, 220),
            element="DEFENSIVE"
        )
        self.blast_dmg = 20
        self.blast_radius = 180.0

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Blast Damage", "20 DMG (-> 45 next)"), ("Radius", "180px (-> 240px next)"), ("Bullet Destroy", "Locked")]
        elif self.level == 2:
            return [("Blast Damage", "45 DMG (-> 70 next)"), ("Radius", "240px (MAX)"), ("Bonus i-frames", "+0.5s")]
        return [("Blast Damage", "70 DMG (MAX)"), ("Radius", "240px (MAX)"), ("Bullet Destroy", "Destroys Bullets")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Shockwave deals 45 damage, expands 35% larger, and grants 0.5s bonus i-frames."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): Deals 70 damage and destroys all incoming enemy bullets in a 240px radius!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.blast_dmg = 45
            self.blast_radius = 240.0
        elif self.level == 3:
            self.blast_dmg = 70
            self.blast_radius = 300.0

    def on_take_damage(self, player, damage_event, game_state):
        game_state.camera.add_trauma(0.45)
        game_state.particles.spawn_explosion(player.pos.x, player.pos.y, radius=70)
        game_state.audio.play('explosion')
        
        if self.level >= 2:
            player.invulnerable_timer = max(player.invulnerable_timer, 0.5)

        # Level 3 destroys incoming enemy projectiles
        if self.level >= 3:
            game_state.projectiles = [
                p for p in game_state.projectiles
                if p.owner != "enemy" or (p.pos - player.pos).length() > self.blast_radius
            ]

        for enemy in game_state.enemies:
            if not enemy.is_alive():
                continue
            diff = enemy.pos - player.pos
            dist = diff.length()
            if 0 < dist < self.blast_radius:
                push = diff.normalize() * (550.0 + self.level * 100)
                enemy.vel += push
                enemy.take_damage(DamageEvent(self.blast_dmg, source_type="player"), game_state)

                # Duo Synergy: Kinetic Cataclysm (Kinetic Repulsor + Boiler Rupture)
                if any(b.id == "explosive_shrapnel" for b in player.boons):
                    enemy.take_damage(DamageEvent(45, source_type="player", damage_type="fire", is_crit=True), game_state)
                    game_state.particles.spawn_explosion(enemy.pos.x, enemy.pos.y, radius=55)


class StokerSiphonBoon(Boon):
    """Eliminating an enemy restores health."""
    def __init__(self, rarity="Legendary"):
        super().__init__(
            "stoker_siphon", "Stoker's Feast", rarity, "Alchemical",
            "Eliminating an enemy has a 30% chance to restore 6 HP.",
            RARITY_COLORS["Legendary"],
            element="ALCHEMICAL"
        )
        self.chance = 0.30
        self.heal_amt = 6

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Proc Chance", "30% (-> 45% next)"), ("Heal on Kill", "6 HP (-> 10 next)"), ("Speed Surge", "Locked")]
        elif self.level == 2:
            return [("Proc Chance", "45% (-> 60% next)"), ("Heal on Kill", "10 HP (-> 15 next)"), ("Speed Surge", "Locked")]
        return [("Proc Chance", "60% (MAX)"), ("Heal on Kill", "15 HP (MAX)"), ("Speed Surge", "+25% Move Speed")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: 45% chance on kill to heal 10 HP."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): 60% chance to heal 15 HP + grants +25% move speed on kill."
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.chance = 0.45
            self.heal_amt = 10
        elif self.level == 3:
            self.chance = 0.60
            self.heal_amt = 15

    def on_kill(self, player, target, game_state):
        if random.random() < self.chance:
            player.heal(self.heal_amt)
            game_state.particles.add_damage_number(player.pos.x, player.pos.y, self.heal_amt, damage_type="heal")
            if self.level >= 3:
                player.vel *= 1.25


class LocomotiveGreaseBoon(Boon):
    """Enhances player movement speed and dash cooldown."""
    def __init__(self, rarity="Common"):
        super().__init__(
            "locomotive_grease", "Bearing Lubricant", rarity, "Overdrive",
            "+25% movement speed and your dash recharges 35% faster.",
            COLOR_CRIT_YELLOW,
            element="MOBILITY"
        )

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Move Speed", "+25% (-> +40% next)"), ("Dash CDR", "+35% (-> +55% next)"), ("Wake Slow", "Locked")]
        elif self.level == 2:
            return [("Move Speed", "+40% (-> +60% next)"), ("Dash CDR", "+55% (-> +70% next)"), ("Wake Slow", "Locked")]
        return [("Move Speed", "+60% (MAX)"), ("Dash CDR", "+70% (MAX)"), ("Wake Slow", "40% AoE Slow on Dash")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: +40% speed and dash recharges 55% faster."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): +60% speed, dash recharges 70% faster, and dashing slows enemies by 40%!"
        return "MAX LEVEL"

    def on_acquire(self, player):
        player.speed_multiplier *= 1.25
        player.dash_cooldown_mult *= 0.65

    def apply_level_up(self, player):
        if self.level == 2:
            player.speed_multiplier *= 1.15
            player.dash_cooldown_mult *= 0.70
        elif self.level == 3:
            player.speed_multiplier *= 1.20
            player.dash_cooldown_mult *= 0.65

    def on_dash(self, player, start_pos, end_pos, game_state):
        if self.level >= 3:
            for e in game_state.enemies:
                if e.is_alive() and (e.pos - player.pos).length() < 300:
                    e.vel *= 0.5


class ExplosiveShrapnelBoon(Boon):
    """Enemies detonate into explosive shrapnel upon death."""
    def __init__(self, rarity="Epic"):
        super().__init__(
            "explosive_shrapnel", "Boiler Rupture", rarity, "Steam",
            "Enemies explode violently upon death, dealing 40 area damage to nearby foes.",
            (255, 90, 30),
            element="PYRO"
        )
        self.blast_dmg = 40
        self.blast_radius = 130.0

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Explosion DMG", "40 DMG (-> 70 next)"), ("Blast Radius", "130px (-> 180px next)"), ("Secondary Frags", "Locked")]
        elif self.level == 2:
            return [("Explosion DMG", "70 DMG (-> 100 next)"), ("Blast Radius", "180px (-> 230px next)"), ("Secondary Frags", "Locked")]
        return [("Explosion DMG", "100 DMG (MAX)"), ("Blast Radius", "230px (MAX)"), ("Secondary Frags", "Chain Shrapnel Detonations")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: 70 explosion damage with 40% larger blast radius."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): 100 explosion damage and triggers secondary shrapnel fragments!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.blast_dmg = 70
            self.blast_radius = 180.0
        elif self.level == 3:
            self.blast_dmg = 100
            self.blast_radius = 230.0

    def on_kill(self, player, target, game_state):
        game_state.particles.spawn_explosion(target.pos.x, target.pos.y, radius=self.blast_radius * 0.6)
        game_state.audio.play('explosion')
        game_state.camera.add_trauma(0.3)
        for enemy in game_state.enemies:
            if enemy is not target and enemy.is_alive():
                dist = (enemy.pos - target.pos).length()
                if dist < self.blast_radius:
                    enemy.take_damage(DamageEvent(self.blast_dmg, source_type="player", damage_type="fire"), game_state)
                    # Duo Synergy: Electrified Shrapnel (Tesla Coil + Boiler Rupture)
                    if any(b.id == "tesla_coil" for b in player.boons):
                        enemy.take_damage(DamageEvent(35, source_type="player", damage_type="electric"), game_state)
                        game_state.particles.spawn_sparks(enemy.pos.x, enemy.pos.y, count=6, color=COLOR_LIGHTNING_CYAN)


class MoltenCoreBoon(Boon):
    """Attacks ignite enemies, causing burning damage over time."""
    def __init__(self, rarity="Rare"):
        super().__init__(
            "molten_core", "Molten Fuel", rarity, "Pyro",
            "Attacks ignite foes, inflicting 15 burning damage over 2 seconds.",
            (255, 110, 40),
            element="PYRO"
        )
        self.burn_dmg = 15

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Burn Damage", "15 DoT (-> 30 next)"), ("Duration", "2.0s (-> 3.0s next)"), ("Vulnerability", "Locked")]
        elif self.level == 2:
            return [("Burn Damage", "30 DoT (-> 55 next)"), ("Duration", "3.0s (-> 4.0s next)"), ("Vulnerability", "Locked")]
        return [("Burn Damage", "55 DoT (MAX)"), ("Duration", "4.0s (MAX)"), ("Vulnerability", "+35% Damage Taken")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Burn deals 30 damage, and critical strikes cause mini fiery bursts."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): 55 burn damage. Burning foes take +35% damage from all attacks!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.burn_dmg = 30
        elif self.level == 3:
            self.burn_dmg = 55

    def on_hit(self, player, target, damage_event, game_state):
        if damage_event.damage_type != "fire":
            target.take_damage(DamageEvent(self.burn_dmg, source_type="player", damage_type="fire"), game_state)
            game_state.particles.spawn_sparks(target.pos.x, target.pos.y, count=5, color=(255, 120, 30))

            # Duo Synergy: Thermal Shock (Molten Fuel + Cryo Condenser)
            if any(b.id == "cryo_condenser" for b in player.boons):
                game_state.particles.spawn_explosion(target.pos.x, target.pos.y, radius=70)
                game_state.particles.spawn_steam(target.pos.x, target.pos.y, count=10)
                game_state.audio.play('explosion')
                game_state.camera.add_trauma(0.25)
                for enemy in game_state.enemies:
                    if enemy.is_alive() and (enemy.pos - target.pos).length() < 120:
                        enemy.take_damage(DamageEvent(65, source_type="player", damage_type="steam", is_crit=True), game_state)
                        enemy.vel *= 0.3


class CryoCondenserBoon(Boon):
    """Attacks chill enemies, slowing movement and freezing them at high levels."""
    def __init__(self, rarity="Rare"):
        super().__init__(
            "cryo_condenser", "Cryo Condenser", rarity, "Cryo",
            "Attacks chill targets, slowing enemy movement by 35% for 2 seconds.",
            (120, 220, 255),
            element="CRYO"
        )
        self.slow_factor = 0.65

    def get_stat_breakdown(self) -> list[tuple[str, str]]:
        if self.level == 1:
            return [("Slow Intensity", "35% (-> 60% next)"), ("Duration", "2.0s (-> 3.5s next)"), ("Freeze Stun", "Locked")]
        elif self.level == 2:
            return [("Slow Intensity", "60% (-> 85% next)"), ("Bonus Dmg", "+15% Kinetic"), ("Freeze Stun", "Locked")]
        return [("Slow Intensity", "85% (MAX)"), ("Bonus Dmg", "+15% Kinetic"), ("Freeze Stun", "1.5s Frozen Solid on 3 hits")]

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Chilled foes are slowed by 60% and take +15% kinetic damage."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): Freezes enemies completely solid for 1.5s after 3 consecutive hits!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.slow_factor = 0.40
        elif self.level == 3:
            self.slow_factor = 0.15

    def on_hit(self, player, target, damage_event, game_state):
        target.vel *= self.slow_factor
        game_state.particles.spawn_sparks(target.pos.x, target.pos.y, count=4, color=(160, 230, 255))


def point_to_segment_dist(p: pygame.math.Vector2, a: pygame.math.Vector2, b: pygame.math.Vector2) -> float:
    ab = b - a
    length_sq = ab.length_squared()
    if length_sq == 0:
        return (p - a).length()
    t = max(0.0, min(1.0, (p - a).dot(ab) / length_sq))
    projection = a + ab * t
    return (p - projection).length()


class OverclockInjectorBoon(Boon):
    """Movement speed accelerates weapon fire rate and attack momentum."""
    def __init__(self, rarity="Rare"):
        super().__init__(
            "overclock_injector", "Overclock Injector", rarity, "Overdrive",
            "Gain +30% attack speed while in motion, and +50% attack speed for 2.0s after dashing.",
            (255, 190, 40)
        )
        self.dash_buff_duration = 2.0

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: +45% attack speed in motion, and +75% attack speed for 3.0s after dashing."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): +65% attack speed in motion. Dashing instantly reloads and primes your next attack!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.dash_buff_duration = 3.0
        elif self.level == 3:
            self.dash_buff_duration = 3.5

    def on_dash(self, player, start_pos, end_pos, game_state):
        player.attack_boost_timer = max(player.attack_boost_timer, self.dash_buff_duration)
        game_state.particles.spawn_sparks(player.pos.x, player.pos.y, count=6, color=(255, 200, 50))
        if self.level >= 3 and player.weapon:
            player.weapon.cooldown_timer = 0.0


class StaticDynamoBoon(Boon):
    """Movement and dashing generate Static Voltage for radial lightning discharges."""
    def __init__(self, rarity="Epic"):
        super().__init__(
            "static_dynamo", "Static Dynamo", rarity, "Tesla",
            "Moving and dashing generates Static Voltage. At 100%, next attack releases a radial 45-damage lightning burst.",
            COLOR_LIGHTNING_CYAN
        )
        self.charge = 0.0

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Charges 40% faster. Lightning burst deals 75 electric damage to all surrounding enemies."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): Discharges automatically upon dashing, and lightning stuns enemies for 1.2s!"
        return "MAX LEVEL"

    def on_dash(self, player, start_pos, end_pos, game_state):
        rate = 45.0 if self.level == 1 else (65.0 if self.level == 2 else 100.0)
        self.charge = min(100.0, self.charge + rate)
        if self.level >= 3 and self.charge >= 100.0:
            self._discharge(player, game_state)

    def on_attack(self, player, weapon, game_state):
        if self.charge >= 100.0:
            self._discharge(player, game_state)

    def _discharge(self, player, game_state):
        self.charge = 0.0
        dmg = 45 if self.level == 1 else (75 if self.level == 2 else 110)
        game_state.particles.spawn_sparks(player.pos.x, player.pos.y, count=20, color=COLOR_LIGHTNING_CYAN)
        game_state.audio.play('zap')
        game_state.camera.add_trauma(0.3)
        for enemy in game_state.enemies:
            if enemy.is_alive() and (enemy.pos - player.pos).length() < 220:
                enemy.take_damage(DamageEvent(dmg, source_type="player", damage_type="electric", is_crit=True), game_state)
                if self.level >= 3:
                    enemy.vel = pygame.math.Vector2(0, 0)
        # Check Duo Synergy: Vampiric Dynamo (Stoker Siphon + Static Dynamo)
        if any(b.id == "stoker_siphon" for b in player.boons):
            player.heal(12)
            game_state.particles.add_damage_number(player.pos.x, player.pos.y, 12, damage_type="heal")


class GlacialSpikesBoon(Boon):
    """Striking chilled foes shatters piercing ice spikes outward."""
    def __init__(self, rarity="Rare"):
        super().__init__(
            "glacial_spikes", "Glacial Spikes", rarity, "Cryo",
            "Attacks on chilled enemies shatter 3 piercing ice shards outward dealing 22 damage.",
            (150, 235, 255)
        )
        self.shard_count = 3
        self.shard_dmg = 22

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: 5 piercing ice shards dealing 38 damage with longer frost slow."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): 7 shards that pierce obstacles and freeze enemies solid for 1s!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.shard_count = 5
            self.shard_dmg = 38
        elif self.level == 3:
            self.shard_count = 7
            self.shard_dmg = 55

    def on_hit(self, player, target, damage_event, game_state):
        if damage_event.damage_type == "cryo_shard":
            return
        base_angle = random.uniform(0, 2 * math.pi)
        step = (2 * math.pi) / self.shard_count
        for i in range(self.shard_count):
            ang = base_angle + i * step
            vel = pygame.math.Vector2(math.cos(ang), math.sin(ang)) * 420.0
            from src.entities.projectile import Projectile
            proj = Projectile(
                target.pos.x, target.pos.y,
                vel=vel,
                damage_event=DamageEvent(self.shard_dmg, source_type="player", damage_type="cryo_shard"),
                radius=4.0,
                lifetime=0.6,
                color=(160, 240, 255),
                owner="player",
                pierce=1 if self.level < 3 else 3
            )
            game_state.projectiles.append(proj)
        game_state.particles.spawn_sparks(target.pos.x, target.pos.y, count=6, color=(140, 230, 255))


class CombustionEngineBoon(Boon):
    """Consecutive attacks build cylinder pressure, detonating an internal area backfire."""
    def __init__(self, rarity="Epic"):
        super().__init__(
            "combustion_engine", "Combustion Engine", rarity, "Pyro",
            "Every 4th attack triggers a heavy cylinder combustion blast, dealing 45 area fire damage.",
            (255, 95, 30)
        )
        self.hit_counter = 0
        self.threshold = 4
        self.blast_dmg = 45

    def get_upgrade_description(self) -> str:
        if self.level == 1:
            return "LVL 2: Triggers every 3rd attack, dealing 70 area fire damage with heavy knockback."
        elif self.level == 2:
            return "LVL 3 (EVOLVED): Triggers every 2nd attack, dealing 100 damage and igniting the ground!"
        return "MAX LEVEL"

    def apply_level_up(self, player):
        if self.level == 2:
            self.threshold = 3
            self.blast_dmg = 70
        elif self.level == 3:
            self.threshold = 2
            self.blast_dmg = 100

    def on_attack(self, player, weapon, game_state):
        self.hit_counter += 1
        if self.hit_counter >= self.threshold:
            self.hit_counter = 0
            game_state.particles.spawn_explosion(player.pos.x, player.pos.y, radius=70)
            game_state.audio.play('explosion')
            game_state.camera.add_trauma(0.3)
            for enemy in game_state.enemies:
                if enemy.is_alive():
                    diff = enemy.pos - player.pos
                    if diff.length() < 170:
                        push = diff.normalize() * 450.0 if diff.length_squared() > 0 else pygame.math.Vector2(0, 0)
                        enemy.vel += push
                        enemy.take_damage(DamageEvent(self.blast_dmg, source_type="player", damage_type="fire", is_crit=True), game_state)


ALL_BOON_CLASSES = [
    TeslaCoilBoon,
    SteamOverdriveDashBoon,
    TungstenPiercingBoon,
    KineticPlatingBoon,
    StokerSiphonBoon,
    LocomotiveGreaseBoon,
    ExplosiveShrapnelBoon,
    MoltenCoreBoon,
    CryoCondenserBoon,
    OverclockInjectorBoon,
    StaticDynamoBoon,
    GlacialSpikesBoon,
    CombustionEngineBoon,
]


# =========================================================================
# DUO SYNERGY REGISTRY
# =========================================================================

SYNERGY_DEFINITIONS = [
    {
        "id": "thermal_shock",
        "name": "Thermal Shock",
        "requires": ["molten_core", "cryo_condenser"],
        "tag": "Pyro + Cryo",
        "description": "Fire attacks on chilled foes trigger catastrophic 65-damage vapor explosions!",
        "color": (255, 175, 70),
    },
    {
        "id": "superconductor_arc",
        "name": "Superconductor Arc",
        "requires": ["tesla_coil", "tungsten_pierce"],
        "tag": "Tesla + Kinetic",
        "description": "Piercing projectiles discharge chain lightning arcs continuously to all nearby enemies in flight!",
        "color": COLOR_LIGHTNING_CYAN,
    },
    {
        "id": "electrified_shrapnel",
        "name": "Electrified Shrapnel",
        "requires": ["tesla_coil", "explosive_shrapnel"],
        "tag": "Tesla + Steam",
        "description": "Enemy shrapnel explosions emit powerful chain lightning arcs to all surviving enemies in the car!",
        "color": (160, 220, 255),
    },
    {
        "id": "inferno_jet",
        "name": "Inferno Jet",
        "requires": ["molten_core", "steam_dash"],
        "tag": "Pyro + Steam",
        "description": "Boiler Jet Dash leaves a boiling napalm trail that ignites the deck, damaging enemies and detonating barrels!",
        "color": (255, 80, 20),
    },
    {
        "id": "cryo_freeze_wake",
        "name": "Cryo-Flashfreeze",
        "requires": ["cryo_condenser", "steam_dash"],
        "tag": "Cryo + Steam",
        "description": "Your dash releases a flash-freezing blizzard mist that freezes all enemies caught in your wake solid!",
        "color": (130, 235, 255),
    },
    {
        "id": "vampiric_dynamo",
        "name": "Vampiric Dynamo",
        "requires": ["stoker_siphon", "static_dynamo"],
        "tag": "Alchemical + Tesla",
        "description": "Static discharges have a guaranteed life-siphon heal, and life-steals instantly grant 50% static charge!",
        "color": (120, 255, 160),
    },
    {
        "id": "kinetic_cataclysm",
        "name": "Kinetic Cataclysm",
        "requires": ["kinetic_plating", "explosive_shrapnel"],
        "tag": "Kinetic + Steam",
        "description": "When struck, Kinetic Repulsor triggers immediate secondary shrapnel detonations on all nearby enemies!",
        "color": (255, 130, 80),
    },
]


def get_active_synergies(player_boons: list[Boon]) -> list[dict]:
    """Returns all unlocked duo synergies based on owned player boons."""
    owned_ids = {b.id for b in player_boons}
    active = []
    for syn in SYNERGY_DEFINITIONS:
        if all(req in owned_ids for req in syn["requires"]):
            active.append(syn)
    return active


def get_synergy_preview_for_boon(boon_id: str, existing_boons: list[Boon]) -> dict | None:
    """If picking this boon will unlock a new duo synergy with an owned boon, return it."""
    owned_ids = {b.id for b in existing_boons}
    if boon_id in owned_ids:
        return None
    for syn in SYNERGY_DEFINITIONS:
        if boon_id in syn["requires"]:
            other_req = [r for r in syn["requires"] if r != boon_id][0]
            if other_req in owned_ids:
                return syn
    return None


def get_random_boon_choices(count: int = 3, existing_boons: list[Boon] = None) -> list[Boon]:
    """Select 3 distinct boons, offering upgrades for owned boons and new boons."""
    if existing_boons is None:
        existing_boons = []

    candidates = []
    
    # 1. Offer upgrades for current boons that aren't max level yet
    upgradeable = [b for b in existing_boons if not b.is_max_level()]
    for owned in upgradeable:
        for cls in ALL_BOON_CLASSES:
            inst = cls()
            if inst.id == owned.id:
                inst.level = owned.level
                candidates.append(inst)
                break

    # 2. Offer new unowned boons
    owned_ids = {b.id for b in existing_boons}
    unowned = [cls() for cls in ALL_BOON_CLASSES if cls().id not in owned_ids]
    candidates.extend(unowned)

    random.shuffle(candidates)
    return candidates[:min(count, len(candidates))]
