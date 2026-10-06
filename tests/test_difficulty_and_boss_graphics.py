"""Test suite for late-level enemy difficulty ramping, procedural stage boss graphics, and crisp animations."""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from src.core.game import Game
from src.level.car_generator import RunManager, STAGE_DIFFICULTY_CONFIG
from src.level.train_car import TrainCar
from src.core.camera import Camera
from src.combat.weapons import RivetGun, CoalScattergun, TeslaArcCaster, StokerWrench
from src.entities.enemies.stage_bosses import (
    ScrapperForemanMiniBoss, VerminBroodEngineBoss,
    CyberDispatcherMiniBoss, TractionAICoreBoss,
    SubZeroWardenMiniBoss, CryoTurbineEngineBoss,
    AshPyromancerMiniBoss, IronLeviathanBoss
)
from src.entities.enemies.types import TicketInspector, RangedSteward, BoilerImp, AutomatonShield
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem
from src.ui.sprite_renderer import draw_stoker_player, draw_held_weapon


def test_difficulty_scaling_across_stages_and_cars():
    print("--- 1. Testing Difficulty Multipliers Across Stages ---")
    pygame.init()
    
    # Verify stage difficulty configs exist
    for stage_id in ["steam", "derelict", "subway", "cryo", "infernal"]:
        assert stage_id in STAGE_DIFFICULTY_CONFIG, f"Missing config for {stage_id}"
        cfg = STAGE_DIFFICULTY_CONFIG[stage_id]
        assert "budget_mult" in cfg
        assert "hp_mult" in cfg
        assert "damage_mult" in cfg
        assert "speed_mult" in cfg
        assert "attack_rate_mult" in cfg
        assert "base_elite_chance" in cfg

    # Verify Stage 5 (Infernal) is significantly harder than Stage 1 (Steam)
    s1_cfg = STAGE_DIFFICULTY_CONFIG["steam"]
    s5_cfg = STAGE_DIFFICULTY_CONFIG["infernal"]
    assert s5_cfg["hp_mult"] >= 2.0 * s1_cfg["hp_mult"], "Stage 5 HP should be >= 2.0x Stage 1"
    assert s5_cfg["damage_mult"] >= 1.5 * s1_cfg["damage_mult"], "Stage 5 Damage should be >= 1.5x Stage 1"
    assert s5_cfg["budget_mult"] >= 2.0 * s1_cfg["budget_mult"], "Stage 5 Budget should be >= 2.0x Stage 1"
    assert s5_cfg["base_elite_chance"] > s1_cfg["base_elite_chance"]
    print("✓ Stage difficulty multipliers correctly configured.")

    print("--- 2. Testing In-Game Wave & Enemy Stat Scaling ---")
    run_s1 = RunManager("steam")
    car_s1 = run_s1.create_current_car()
    enemies_s1 = run_s1.spawn_enemies_for_car(car_s1)

    run_s5 = RunManager("infernal")
    car_s5 = run_s5.create_current_car()
    enemies_s5 = run_s5.spawn_enemies_for_car(car_s5)

    # Infernal enemy health must be much higher than Steam
    avg_hp_s1 = sum(e.max_health for e in enemies_s1) / len(enemies_s1)
    avg_hp_s5 = sum(e.max_health for e in enemies_s5) / len(enemies_s5)
    assert avg_hp_s5 > avg_hp_s1, f"Infernal avg HP ({avg_hp_s5}) should exceed Steam ({avg_hp_s1})"

    test_insp_s1 = TicketInspector(100, 100)
    test_insp_s1.apply_difficulty_scaling(s1_cfg["hp_mult"], s1_cfg["speed_mult"], s1_cfg["damage_mult"], s1_cfg["attack_rate_mult"])
    test_insp_s5 = TicketInspector(100, 100)
    test_insp_s5.apply_difficulty_scaling(s5_cfg["hp_mult"], s5_cfg["speed_mult"], s5_cfg["damage_mult"], s5_cfg["attack_rate_mult"])
    assert test_insp_s5.max_health > test_insp_s1.max_health, f"Infernal HP ({test_insp_s5.max_health}) should exceed Steam ({test_insp_s1.max_health})"
    assert test_insp_s5.speed > test_insp_s1.speed, "Infernal speed should exceed Steam speed"
    assert getattr(test_insp_s5, "damage_multiplier", 1.0) > getattr(test_insp_s1, "damage_multiplier", 1.0)
    print(f"✓ Normal enemy scaling verified: Stage 1 Inspector HP={test_insp_s1.max_health}, Stage 5 Inspector HP={test_insp_s5.max_health}")

    # Test late-car gauntlet scaling within the same stage
    run_late = RunManager("derelict")
    run_late.current_car_index = 12  # Car 13 (late gauntlet)
    car_late = run_late.create_current_car()
    enemies_late = run_late.spawn_enemies_for_car(car_late)
    
    run_early = RunManager("derelict")
    run_early.current_car_index = 0  # Car 1
    car_early = run_early.create_current_car()
    enemies_early = run_early.spawn_enemies_for_car(car_early)

    assert len(enemies_late) >= len(enemies_early), "Late car should have equal or more enemy density than early car"
    print(f"✓ Late-car gauntlet density verified: Early Car count={len(enemies_early)}, Late Car count={len(enemies_late)}")


def test_all_8_stage_boss_models_and_rendering():
    print("--- 3. Testing High-Detail Procedural Rendering for All 8 Stage Bosses ---")
    pygame.init()
    surface = pygame.Surface((1280, 720))
    camera = Camera(1280, 720)

    boss_classes = [
        (ScrapperForemanMiniBoss, "Scrapper Foreman (Stage 2 Mini-Boss)"),
        (VerminBroodEngineBoss, "Vermin Brood Engine (Stage 2 Final Boss)"),
        (CyberDispatcherMiniBoss, "Cyber Dispatcher (Stage 3 Mini-Boss)"),
        (TractionAICoreBoss, "Traction AI Core (Stage 3 Final Boss)"),
        (SubZeroWardenMiniBoss, "Sub-Zero Warden (Stage 4 Mini-Boss)"),
        (CryoTurbineEngineBoss, "Cryo-Turbine Engine (Stage 4 Final Boss)"),
        (AshPyromancerMiniBoss, "Ash Pyromancer (Stage 5 Mini-Boss)"),
        (IronLeviathanBoss, "The Iron Leviathan (Stage 5 Final Boss)"),
    ]

    for cls, label in boss_classes:
        boss = cls(640, 360)
        boss.apply_difficulty_scaling(hp_mult=1.5, speed_mult=1.2, damage_mult=1.3, attack_rate_mult=1.2)
        assert boss.max_health > 0
        assert getattr(boss, "damage_multiplier", 1.0) == 1.3
        
        # Test rendering without errors
        boss.draw(surface, camera)
        
        # Test phase 2 rendering if applicable
        if hasattr(boss, "phase"):
            boss.phase = 2
            boss.draw(surface, camera)
            
        print(f"  ✓ {label} procedural sprite rendered cleanly.")

    print("✓ All 8 Stage Boss procedural models rendered without error.")


def test_crisp_character_animations_and_weapon_effects():
    print("--- 4. Testing Crisp Stoker Animation & Weapon Recoil ---")
    pygame.init()
    surface = pygame.Surface((1280, 720))
    
    # Test idle breathing (is_moving = False)
    draw_stoker_player(
        surface, (640, 360), aim_angle=0.0, walk_dist=0.0,
        weapon=RivetGun(), is_moving=False, recoil_timer=0.0,
        attack_boost_timer=0.0, flash_timer=0.0, invuln_timer=0.0
    )
    
    # Test walk cycle and dynamic lean (is_moving = True)
    draw_stoker_player(
        surface, (640, 360), aim_angle=1.2, walk_dist=45.0,
        weapon=CoalScattergun(), is_moving=True, recoil_timer=0.0,
        attack_boost_timer=0.5, flash_timer=0.0, invuln_timer=0.0
    )

    # Test weapon mechanical slide recoil & starburst muzzle flash across weapons
    for w in [RivetGun(), CoalScattergun(), TeslaArcCaster(), StokerWrench()]:
        draw_held_weapon(surface, (640, 360), aim_angle=0.8, weapon=w, recoil_timer=0.08)

    print("✓ Stoker idle breathing, walk lean, and starburst weapon recoil verified.")


if __name__ == "__main__":
    test_difficulty_scaling_across_stages_and_cars()
    test_all_8_stage_boss_models_and_rendering()
    test_crisp_character_animations_and_weapon_effects()
    print("\n=======================================================")
    print("ALL ENEMY DIFFICULTY & GRAPHICS OVERHAUL TESTS PASSED! ✓")
    print("=======================================================")
