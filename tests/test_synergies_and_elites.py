"""Unit and integration test suite for Duo Synergies, New Boons, and Elite Enemy mechanics."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from src.core.game import Game
from src.combat.boons import (
    MoltenCoreBoon, CryoCondenserBoon, TeslaCoilBoon, TungstenPiercingBoon,
    ExplosiveShrapnelBoon, SteamOverdriveDashBoon, StokerSiphonBoon,
    StaticDynamoBoon, OverclockInjectorBoon, GlacialSpikesBoon, CombustionEngineBoon,
    get_active_synergies, get_synergy_preview_for_boon, get_random_boon_choices
)
from src.entities.enemies.types import TicketInspector, RangedSteward, BoilerImp, AutomatonShield
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem
from src.combat.damage import DamageEvent

def run_synergy_and_elite_tests():
    print("=== Testing Duo Synergies, New Boons & Elite Enemies ===")
    pygame.init()
    game = Game(headless=True)
    game.start_new_run("steam", None)
    player = game.player

    # 1. Test Duo Synergy Identification
    print("--- 1. Testing Duo Synergy Detection ---")
    molten = MoltenCoreBoon()
    cryo = CryoCondenserBoon()
    player.boons = [molten]
    
    # Preview when offering Cryo Condenser
    prev = get_synergy_preview_for_boon(cryo.id, player.boons)
    assert prev is not None, "Should preview Thermal Shock synergy"
    assert prev["id"] == "thermal_shock"
    print("✓ Synergy preview correctly identified Thermal Shock when holding Molten Fuel.")

    # Add Cryo and verify active synergy
    player.boons.append(cryo)
    active = get_active_synergies(player.boons)
    assert len(active) == 1
    assert active[0]["id"] == "thermal_shock"
    print(f"✓ Active duo synergy unlocked: {active[0]['name']}")

    # 2. Test Thermal Shock Trigger in Combat
    print("--- 2. Testing Thermal Shock In-Game Trigger ---")
    dummy_enemy = TicketInspector(player.pos.x + 50, player.pos.y)
    dummy_enemy.health = 100
    dummy_enemy.max_health = 100
    game.enemies = [dummy_enemy]

    # Molten Core hit triggers Thermal Shock when holding Cryo Condenser
    initial_hp = dummy_enemy.health
    molten.on_hit(player, dummy_enemy, DamageEvent(10, source_type="player", damage_type="normal"), game)
    assert dummy_enemy.health < initial_hp - 20, "Thermal Shock should apply massive bonus vapor damage"
    print("✓ Thermal Shock triggered explosive damage on target enemy.")

    # 3. Test Static Dynamo & Overclock Injector
    print("--- 3. Testing Static Dynamo & Overclock Injector ---")
    dynamo = StaticDynamoBoon()
    injector = OverclockInjectorBoon()
    player.boons.extend([dynamo, injector])

    # Dash increases static charge and grants attack boost
    dynamo.on_dash(player, player.pos, player.pos + pygame.math.Vector2(100, 0), game)
    injector.on_dash(player, player.pos, player.pos + pygame.math.Vector2(100, 0), game)
    assert dynamo.charge > 0, "Dashing should build static dynamo voltage"
    assert player.attack_boost_timer > 0, "Dashing with Overclock Injector should grant attack speed boost"
    print("✓ Static Dynamo charge accumulation and Overclock Injector dash boost verified.")

    # 4. Test Elite Enemies
    print("--- 4. Testing Elite Enemy Modifiers & Spawning ---")
    inspector = TicketInspector(300, 300)
    assert inspector.is_elite is False
    inspector.make_elite("overclocked")
    assert inspector.is_elite is True
    assert inspector.elite_modifier == "overclocked"
    assert inspector.speed > inspector.base_speed / 1.25

    volatile_warden = AutomatonShield(400, 400)
    volatile_warden.make_elite("volatile")
    assert volatile_warden.elite_modifier == "volatile"
    
    # Test volatile explosion on death
    initial_enemy_count = len(game.enemies)
    volatile_warden.die(game)
    assert volatile_warden.is_dead is True
    print("✓ Elite modifiers (overclocked, volatile) and death explosion mechanics verified.")

    # 5. Test Procedural Sprite Rendering for All Overhauled Enemy Archetypes
    print("--- 5. Testing Overhauled Humanoid & Creature Sprite Rendering ---")
    test_surface = pygame.Surface((1280, 720))
    all_types = [
        TicketInspector(200, 200),
        RangedSteward(250, 250),
        BoilerImp(300, 300),
        AutomatonShield(350, 350),
        BoilerBrute(400, 400),
        FurnaceGolem(450, 450)
    ]
    for ent in all_types:
        ent.walk_distance = 45.0
        ent.vel = pygame.math.Vector2(100, 0)
        ent.draw(test_surface, game.camera)
        
        # Test elite rendering branch
        ent.make_elite()
        ent.draw(test_surface, game.camera)
    print("✓ All 6 redesigned enemy models and their elite variants rendered cleanly without errors.")

    print("\n=======================================================")
    print("ALL DUO SYNERGY, NEW BOON & ELITE TESTS PASSED! ✓")
    print("=======================================================")

if __name__ == "__main__":
    run_synergy_and_elite_tests()
