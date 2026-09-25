"""Damage calculation and combat event data structures."""
import pygame
import random

class DamageEvent:
    """Encapsulates a combat damage instance with elemental tags and knockback."""
    def __init__(self, amount: int, source_type: str = "player",
                 damage_type: str = "normal", is_crit: bool = False,
                 knockback: pygame.math.Vector2 = None):
        self.amount = amount
        self.source_type = source_type  # 'player', 'enemy', 'hazard'
        self.damage_type = damage_type  # 'normal', 'electric', 'steam', 'fire'
        self.is_crit = is_crit
        self.knockback = knockback if knockback else pygame.math.Vector2(0, 0)

def roll_damage(base_dmg: int, crit_chance: float = 0.15, crit_mult: float = 2.0, damage_type: str = "normal") -> DamageEvent:
    """Roll for critical strike and compute final damage number."""
    # Slight damage variance (+-15%)
    variance = random.uniform(0.88, 1.12)
    raw = max(1, int(base_dmg * variance))
    
    is_crit = random.random() < crit_chance
    final_amount = int(raw * crit_mult) if is_crit else raw
    
    return DamageEvent(
        amount=final_amount,
        damage_type=damage_type,
        is_crit=is_crit
    )
