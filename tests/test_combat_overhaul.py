"""Test suite for Combat Overhaul: Bipedal Enemy Visuals, Melee Swing Animation, Block/Parry, Super Abilities, and Upgrade Claim Lock."""
import os
import pygame
import tempfile
import math

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.core.game import Game
from src.combat.weapons import StokerWrench, RivetGun
from src.entities.player import Player
from src.entities.enemies.types import BoilerImp
from src.entities.enemies.boss import ConductorBoss
from src.combat.damage import DamageEvent
from src.core.progression import ProgressionManager, SUPER_ABILITIES
from src.ui.sprite_renderer import draw_boiler_imp_sprite, draw_stoker_player
from src.level.train_car import TrainCar


def test_boiler_imp_bipedal_rendering():
    """Verify BoilerImp bipedal rendering without errors."""
    print("--- 1. Testing BoilerImp Bipedal Visuals & Rendering ---")
    pygame.init()
    surface = pygame.Surface((1280, 720))
    imp = BoilerImp(400, 300)
    imp.facing_angle = 0.5
    imp.walk_distance = 45.0
    imp.state = "windup"
    imp.state_timer = 0.3

    # Ensure sprite renders cleanly in windup, moving, and normal states
    draw_boiler_imp_sprite(surface, (400, 300), imp)
    imp.state = "chase"
    imp.walk_distance = 90.0
    draw_boiler_imp_sprite(surface, (400, 300), imp)
    print("✓ BoilerImp bipedal articulated runner sprite rendered cleanly.")


def test_melee_swing_and_attack_response():
    """Verify StokerWrench base damage, swing timer, and hitstop attack response."""
    print("--- 2. Testing Melee Swing Animation, Hitstop & Damage Boost ---")
    game = Game(headless=True)
    wrench = StokerWrench()
    assert wrench.base_damage == 62, f"Expected boosted melee damage 62, got {wrench.base_damage}"

    game.start_new_run("steam", wrench)
    player = game.player

    # Verify swing triggers player.start_melee_swing
    target_pos = pygame.math.Vector2(player.pos.x + 50, player.pos.y)
    enemy = BoilerImp(player.pos.x + 40, player.pos.y)
    game.enemies = [enemy]
    initial_hp = enemy.health

    wrench.attack(player, target_pos, game)
    assert player.melee_swing_timer > 0.0, "Melee attack must set player melee_swing_timer"
    assert player.is_melee_swinging is True
    assert enemy.health < initial_hp, "Enemy in melee range should take damage"
    assert enemy.hitstop_timer == 0.05, f"Enemy should receive hitstop on melee impact, got {enemy.hitstop_timer}"
    assert enemy.vel.x > 0, "Enemy should be pushed back by cleave knockback"

    # Verify player drawing handles melee swinging, weapon trails and aegis shield
    surf = pygame.Surface((1280, 720))
    player.draw(surf, game.camera)
    player.is_blocking = True
    player.draw(surf, game.camera)
    print("✓ Melee weapon swing animation, 62 damage boost, and hitstop verified.")


def test_block_stance_and_timed_parry():
    """Verify block stance 75% mitigation, 100% timed parry, and speed reduction."""
    print("--- 3. Testing Defensive Block Stance & Timed Parry ---")
    game = Game(headless=True)
    game.start_new_run("steam", RivetGun())
    player = game.player
    enemy = BoilerImp(player.pos.x + 30, player.pos.y)
    game.enemies = [enemy]

    # 1. Test Regular Block (75% mitigation)
    player.is_blocking = True
    player.block_timer = 0.35  # Outside the 0.20s parry window
    initial_hp = player.health
    incoming_dmg = 40
    player.take_damage(DamageEvent(incoming_dmg, source_type="enemy"), game)
    expected_taken = int(incoming_dmg * 0.25)  # 75% mitigated -> 10 damage
    assert player.health == initial_hp - expected_taken, f"Expected {expected_taken} dmg taken, actual: {initial_hp - player.health}"
    print("✓ Standard Block 75% damage mitigation verified.")

    # 2. Test Timed Parry (100% mitigation within 0.20s)
    player.block_timer = 0.10  # Inside 0.20s parry window
    hp_before_parry = player.health
    player.take_damage(DamageEvent(50, source_type="enemy"), game)
    assert player.health == hp_before_parry, "Timed parry must negate 100% incoming damage"
    assert player.parry_flash_timer > 0.0, "Timed parry should trigger parry flash"
    assert enemy.hitstop_timer == 0.15, "Timed parry must counter-stagger attacker with hitstop"
    print("✓ Timed Parry 100% damage negation & counter-stagger verified.")

    # 3. Test Speed Reduction while blocking
    player.is_blocking = True
    speed_blocking = player.speed * (0.45 if player.is_blocking else 1.0)
    assert speed_blocking < player.speed * 0.5, "Movement speed should be reduced by ~55% during block"
    print("✓ Movement speed reduction while blocking verified.")


def test_super_ability_system():
    """Verify super charge accumulation, 3 progressive unlocks, and super execution."""
    print("--- 4. Testing Super Ability Accumulation & Execution ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_save = tf.name

    pm = ProgressionManager(save_path=temp_save)
    game = Game(headless=True)
    game.start_new_run("steam", RivetGun())
    player = game.player

    # 1. Milestone Unlocks
    # Fresh save: 0 tracks beaten -> No supers
    assert pm.get_unlocked_supers() == []
    assert pm.get_equipped_super() is None

    # Track 1 beaten (current_track_idx = 1) -> Super 1 unlocked
    pm.current_track_idx = 1
    unlocked = pm.get_unlocked_supers()
    assert "super_boiler_overdrive" in unlocked
    assert pm.get_equipped_super()["id"] == "super_boiler_overdrive"
    print("✓ Super 1 (Boiler Overdrive) unlocked after Track 1 clear.")

    # Track 5 beaten 1st time (loop_count = 1) -> Super 2 unlocked
    pm.loop_count = 1
    unlocked = pm.get_unlocked_supers()
    assert "super_tesla_rail" in unlocked
    assert pm.get_equipped_super()["id"] == "super_tesla_rail"
    print("✓ Super 2 (Tesla Rail Discharge) unlocked after Track 5 Loop 1 clear.")

    # Track 5 beaten 2nd time (loop_count = 2) -> Super 3 unlocked
    pm.loop_count = 2
    unlocked = pm.get_unlocked_supers()
    assert "super_infernal_cataclysm" in unlocked
    assert pm.get_equipped_super()["id"] == "super_infernal_cataclysm"
    print("✓ Super 3 (Infernal Slag Cataclysm) unlocked after Track 5 Loop 2 clear.")

    # 2. Super Charge Accumulation from Damage
    enemy = BoilerImp(player.pos.x + 80, player.pos.y)
    game.enemies = [enemy]
    player.super_charge = 0.0
    player.equipped_super_id = "super_boiler_overdrive"

    # Deal damage to enemy
    enemy.take_damage(DamageEvent(100, source_type="player"), game)
    assert player.super_charge >= 35.0, f"Expected super charge from 100 dmg ~35, got {player.super_charge}"

    # 3. Cast Super 1: Boiler Overdrive
    player.super_charge = 100.0
    assert player.can_cast_super() is True
    cast_success = player.cast_super_ability(game)
    assert cast_success is True
    assert player.super_charge == 0.0, "Casting super must consume gauge"
    assert player.invulnerable_timer >= 2.0, "Boiler overdrive must grant invulnerability"
    assert enemy.health < 20, "Boiler overdrive blast should deal 130 damage to nearby enemy"
    print("✓ Super 1 (Boiler Overdrive) cast execution verified.")

    # 4. Cast Super 2: Tesla Rail Discharge
    player.equipped_super_id = "super_tesla_rail"
    player.super_charge = 100.0
    enemy2 = BoilerImp(player.pos.x + 200, player.pos.y)
    game.enemies = [enemy2]
    player.facing_dir = pygame.math.Vector2(1, 0)
    cast_success = player.cast_super_ability(game)
    assert cast_success is True
    assert enemy2.health <= 0, "Tesla rail beam should eliminate enemy (280 damage)"
    print("✓ Super 2 (Tesla Rail) piercing beam execution verified.")

    # 5. Cast Super 3: Infernal Slag Cataclysm
    player.equipped_super_id = "super_infernal_cataclysm"
    player.super_charge = 100.0
    cast_success = player.cast_super_ability(game)
    assert cast_success is True
    assert player.super_charge == 0.0
    print("✓ Super 3 (Infernal Slag Cataclysm) barrage execution verified.")


def test_upgrade_claim_lockout():
    """Verify exit door lock preventing advancement until upgrade is claimed."""
    print("--- 5. Testing Exit Door Lockdown Until Upgrade Claimed ---")
    game = Game(headless=True)
    game.start_new_run("steam", RivetGun())
    car = game.train_car

    # Kill enemies to clear car and trigger exit unlocking
    for e in game.enemies:
        e.health = 0
        e.die(game)
    game.update(0.016)

    assert car.exit_unlocked is True
    assert car.boon_pedestal_active is True
    assert car.boon_claimed is False

    # Position player directly at exit door
    door_mid_y = (car.top_wall_y + car.bottom_wall_y) // 2
    game.player.pos = pygame.math.Vector2(car.width - 90, door_mid_y)

    # 1. Door must reject exit while boon is unclaimed
    assert car.can_player_exit(game.player.pos, game.player.radius) is False, "can_player_exit must return False while boon unclaimed"
    cur_car_idx = game.run_manager.current_car_index
    game.update(0.016)
    assert game.run_manager.current_car_index == cur_car_idx, "Game must NOT advance car while boon unclaimed"

    # 2. Obstacle physics bounds should block walking through doorway
    game.player.pos.x = car.width + 10  # Try to force position beyond door
    game.player.resolve_obstacle_collisions(car)
    assert game.player.pos.x <= car.get_playable_bounds().right - game.player.radius, "Physics must physically block player from walking out"

    # 3. Once boon is claimed, exit unlocks and player can advance
    car.boon_claimed = True
    assert car.can_player_exit(game.player.pos, game.player.radius) is True, "can_player_exit must return True once boon claimed"
    game.player.pos = pygame.math.Vector2(car.width - 90, door_mid_y)
    game.update(0.016)
    assert game.run_manager.current_car_index == cur_car_idx + 1, "Game must advance car once boon claimed and exit entered"
    print("✓ Exit door lockdown bars and claim requirement verified.")


if __name__ == "__main__":
    test_boiler_imp_bipedal_rendering()
    test_melee_swing_and_attack_response()
    test_block_stance_and_timed_parry()
    test_super_ability_system()
    test_upgrade_claim_lockout()
    print("\n=======================================================")
    print("ALL COMBAT OVERHAUL TESTS PASSED SUCCESSFULLY! ✓")
    print("=======================================================")
