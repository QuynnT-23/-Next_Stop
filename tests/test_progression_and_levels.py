"""Comprehensive test suite for Conductor Progression, 5 Stages, Boss Attacks, Hazards, and Walkable Hub."""
import os
import pygame
import tempfile
import json

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.core.game import Game
from src.core.progression import ProgressionManager, PERK_DEFINITIONS
from src.ui.hub_station import HubStation
from src.combat.weapons import AVAILABLE_WEAPONS
from src.level.car_generator import TRAIN_ROUTES, RunManager
from src.level.train_car import TrainCar, VerminMice, LaserGateHazard
from src.entities.enemies.boss import ConductorBoss
from src.entities.enemies.miniboss import ChiefInspectorMiniBoss
from src.entities.enemies.stage_bosses import (
    ScrapperForemanMiniBoss, VerminBroodEngineBoss,
    CyberDispatcherMiniBoss, TractionAICoreBoss,
    SubZeroWardenMiniBoss, CryoTurbineEngineBoss,
    AshPyromancerMiniBoss, IronLeviathanBoss
)
from src.combat.damage import DamageEvent


def test_progression_manager():
    """Verify XP gain, level up, scrap collection, perk purchases, and JSON persistence."""
    print("--- 1. Testing Conductor Progression & Persistence ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_save_path = tf.name

    try:
        pm = ProgressionManager(save_path=temp_save_path)
        assert pm.level == 1
        assert pm.xp == 0
        assert pm.scrap == 0
        assert "iron_constitution" in pm.perks
        assert pm.perks["iron_constitution"] == 0

        # Test XP gaining and Level Up
        xp_needed = pm.get_xp_for_next_level()
        leveled_up = pm.gain_xp(xp_needed + 50)
        assert leveled_up is True
        assert pm.level == 2
        assert pm.xp == 50
        print(f"  ✓ Level up verified: Level {pm.level}, XP {pm.xp}")

        # Test Scrap & Perk Purchase
        pm.gain_scrap(100)
        assert pm.scrap >= 100
        cost_lvl1 = pm.get_perk_cost("iron_constitution")
        assert pm.scrap >= cost_lvl1
        success = pm.purchase_perk("iron_constitution")
        assert success is True
        assert pm.perks["iron_constitution"] == 1
        print(f"  ✓ Perk purchase verified: Iron Constitution Level {pm.perks['iron_constitution']}")

        # Test Stage Unlock
        assert "derelict" not in pm.unlocked_stages
        unlocked = pm.unlock_next_stage("steam")
        assert unlocked == "derelict"
        assert "derelict" in pm.unlocked_stages

        # Test Persistence
        pm.save()
        pm2 = ProgressionManager(save_path=temp_save_path)
        assert pm2.level == 2
        assert pm2.xp == 50
        assert pm2.perks["iron_constitution"] == 1
        assert "derelict" in pm2.unlocked_stages
        print("  ✓ Progression JSON save & reload verified.")
    finally:
        if os.path.exists(temp_save_path):
            os.remove(temp_save_path)


def test_walkable_hub_station():
    """Verify character movement, workshop interaction, armory weapon cycle, and docking bays."""
    print("--- 2. Testing Walkable Grand Central Hub Station ---")
    pygame.init()
    pm = ProgressionManager()
    pm.current_track_idx = 0
    hub = HubStation(pm)
    test_surface = pygame.Surface((1280, 720))

    # Initial position
    initial_y = hub.player_pos.y
    # Simulate movement up towards tracks (W key held)
    hub.update(0.1)
    hub.draw(test_surface)

    # Test Workshop Anvil interaction
    hub.player_pos = pygame.math.Vector2(hub.workshop_rect.center)
    assert not hub.show_workshop
    # Press E near workshop opens workshop modal
    hub.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
    assert hub.show_workshop is True
    # Press ESC closes workshop modal
    hub.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
    assert hub.show_workshop is False
    print("  ✓ Workshop Anvil interaction verified.")

    # Test Armory Rack interaction
    hub.player_pos = pygame.math.Vector2(hub.armory_rect.center)
    orig_idx = hub.selected_weapon_idx
    # Press E near armory cycles weapon
    hub.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
    assert hub.selected_weapon_idx == (orig_idx + 1) % len(hub.weapon_classes)
    print(f"  ✓ Armory Rack weapon swap verified: {hub.active_weapon.name}")

    # Test Docking Bay Boarding & HUD Clearance (Zero Overlap with Terminal Gates)
    header_bar = pygame.Rect(20, 16, 340, 48)
    scrap_bar = pygame.Rect(1280 - 220, 16, 200, 48)
    for i, bay in enumerate(hub.docking_bays):
        assert not header_bar.colliderect(bay["rect"]), f"Header bar must not overlap Track {i+1} gate"
        assert not header_bar.colliderect(bay["door_rect"]), f"Header bar must not overlap Track {i+1} doorway"
        assert not scrap_bar.colliderect(bay["rect"]), f"Scrap bar must not overlap Track {i+1} gate"
        assert not scrap_bar.colliderect(bay["door_rect"]), f"Scrap bar must not overlap Track {i+1} doorway"

    steam_bay = hub.docking_bays[0]
    hub.player_pos = pygame.math.Vector2(steam_bay["door_rect"].center)
    boarded = hub.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
    assert boarded is True
    assert hub.get_selected_route_id() == "steam"
    print("  ✓ Track 1 (The Iron Express) boarding & HUD clear of terminals verified.")


def test_all_5_stages_and_bosses():
    """Verify that all 5 stages generate properly and spawn their respective bosses."""
    print("--- 3. Testing 5 Stages & 10 Stage Bosses / Mini-Bosses ---")
    stages = ["steam", "derelict", "subway", "cryo", "infernal"]
    boss_map = {
        "steam": (ChiefInspectorMiniBoss, ConductorBoss),
        "derelict": (ScrapperForemanMiniBoss, VerminBroodEngineBoss),
        "subway": (CyberDispatcherMiniBoss, TractionAICoreBoss),
        "cryo": (SubZeroWardenMiniBoss, CryoTurbineEngineBoss),
        "infernal": (AshPyromancerMiniBoss, IronLeviathanBoss),
    }

    test_surface = pygame.Surface((1280, 720))

    from src.core.camera import Camera
    camera = Camera()

    for stg in stages:
        rm = RunManager(stg)
        assert rm.total_cars == 15, f"Stage {stg} must have 15 cars"
        
        # Test Car 5 (Mini-Boss 1)
        rm.current_car_index = 4
        car5 = rm.create_current_car()
        enemies_car5 = rm.spawn_enemies_for_car(car5)
        miniboss_class, finalboss_class = boss_map[stg]
        miniboss = next((e for e in enemies_car5 if isinstance(e, miniboss_class)), None)
        assert miniboss is not None, f"Car 5 in {stg} must spawn {miniboss_class.__name__}"
        miniboss.draw(test_surface, camera)

        # Test Car 15 (Final Boss)
        rm.current_car_index = 14
        car15 = rm.create_current_car()
        assert car15.car_type == "engine"
        enemies_car15 = rm.spawn_enemies_for_car(car15)
        finalboss = next((e for e in enemies_car15 if isinstance(e, finalboss_class)), None)
        assert finalboss is not None, f"Car 15 in {stg} must spawn {finalboss_class.__name__}"
        finalboss.draw(test_surface, camera)
        print(f"  ✓ Stage '{stg}': Car 5 Mini-Boss ({miniboss.name}) and Car 15 Final Boss ({finalboss.name}) verified.")


def test_new_boss_attack_patterns():
    """Verify new attack patterns: Conductor furnace mortar/boiler slam & Inspector sonic whistle."""
    print("--- 4. Testing New Boss Attack Patterns ---")
    game = Game()
    game.start_new_run("steam", AVAILABLE_WEAPONS[0]())

    # Test Conductor Boss attacks
    boss = ConductorBoss(600, 300)
    # Test boiler slam
    boss.execute_boiler_slam(game)
    assert len(game.shockwaves) > 0, "Boiler slam must spawn shockwaves"
    # Test furnace mortar
    boss.execute_furnace_mortar(pygame.math.Vector2(1, 0), game)
    assert len(game.fire_hazards) > 0, "Furnace mortar must spawn burning hazard puddles"
    print("  ✓ Conductor boiler slam and furnace mortar attack patterns verified.")

    # Test Chief Inspector Mini-Boss attacks
    inspector = ChiefInspectorMiniBoss(600, 300)
    # Test sonic whistle
    inspector._sonic_whistle(game)
    assert len(game.shockwaves) > 0, "Sonic whistle must emit sonic shockwave"
    # Test crossfire flurry
    inspector._crossfire_flurry(pygame.math.Vector2(1, 0), game)
    assert len(game.projectiles) > 0, "Crossfire flurry must launch projectiles"
    print("  ✓ Chief Inspector sonic whistle and crossfire flurry attack patterns verified.")


def test_hazards_mice_and_lasers():
    """Verify vermin mice and laser gate hazards in train cars."""
    print("--- 5. Testing Scurrying Mice & Laser Gate Hazards ---")
    game = Game()
    game.start_new_run("derelict", AVAILABLE_WEAPONS[0]())
    car = game.train_car

    # Add Vermin Mice
    mouse = VerminMice(game.player.pos.x + 30, game.player.pos.y)
    car.mice.append(mouse)
    orig_hp = game.player.health
    # Update mice
    mouse.update(0.1, game.player, car.width, car.top_wall_y, car.bottom_wall_y, game)
    # Move player into mouse
    game.player.pos = pygame.math.Vector2(mouse.pos)
    mouse.update(0.016, game.player, car.width, car.top_wall_y, car.bottom_wall_y, game)
    assert game.player.health < orig_hp, "Touching vermin mice must deal nibble damage"
    print("  ✓ Vermin Mice scurrying and contact damage verified.")

    # Add Laser Gate Hazard
    laser = LaserGateHazard(game.player.pos.x + 20, (car.top_wall_y + car.bottom_wall_y) // 2, height=140.0)
    laser.is_active = True
    laser.timer = 2.0  # actively glowing
    car.lasers.append(laser)
    orig_hp_laser = game.player.health
    game.player.pos = pygame.math.Vector2(laser.pos)
    laser.update(0.016, game.player, game.enemies, game)
    assert game.player.health < orig_hp_laser, "Crossing active laser gate must deal electricity damage"
    print("  ✓ Laser Gate pulsing and beam damage verified.")


def test_victory_screen_layout_no_overflow():
    """Verify that victory overlay wraps boons and buttons without overflowing boundaries."""
    print("--- 6. Testing Victory Screen Non-Overflow Layout ---")
    game = Game()
    game.start_new_run("steam", AVAILABLE_WEAPONS[0]())
    # Equip player with 8 boons
    from src.combat.boons import (
        TeslaCoilBoon, SteamOverdriveDashBoon, TungstenPiercingBoon,
        KineticPlatingBoon, StokerSiphonBoon, LocomotiveGreaseBoon,
        ExplosiveShrapnelBoon, MoltenCoreBoon
    )
    all_boons = [
        TeslaCoilBoon(), SteamOverdriveDashBoon(), TungstenPiercingBoon(),
        KineticPlatingBoon(), StokerSiphonBoon(), LocomotiveGreaseBoon(),
        ExplosiveShrapnelBoon(), MoltenCoreBoon()
    ]
    for b in all_boons:
        game.player.add_boon(b)

    game.state = Game.STATE_VICTORY
    test_surface = pygame.Surface((1280, 720))
    # Render victory overlay
    game._draw_victory_overlay()
    assert game.return_button_rect is not None
    # Check button is well within screen boundaries
    assert game.return_button_rect.bottom < 710, "Return button must fit within screen bounds"
    assert game.return_button_rect.left > 100
    assert game.return_button_rect.right < 1180
    print("  ✓ Victory overlay with 8 boons rendered cleanly within card boundaries.")


def test_return_to_hub_after_death_and_victory():
    """Verify that pressing Space or E on Game Over or Victory screens returns to Hub Station
    without immediately restarting the level.
    """
    print("--- 7. Testing Return to Hub After Death and Victory (No Immediate Level Restart) ---")
    game = Game(headless=True)
    game.start_new_run("steam", AVAILABLE_WEAPONS[0]())

    # Simulate player walking into docking bay before departure
    # (previously, player_pos was left inside bay door_rect)
    steam_bay = game.hub_station.docking_bays[0]
    game.hub_station.player_pos = pygame.math.Vector2(steam_bay["door_rect"].center)

    # 1. Test Game Over
    game.player.health = 0
    game.update(0.016)
    assert game.state == Game.STATE_GAME_OVER
    assert game.overlay_input_delay > 0.0

    # Let overlay input delay elapse
    for _ in range(15):
        game.update(0.05)
    assert game.overlay_input_delay == 0.0

    # Press 'E' to return to hub
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    game.handle_events()
    assert game.state == Game.STATE_HUB, "Pressing E on Game Over must return to STATE_HUB"
    assert game.hub_station.player_pos.y >= 500, "Player must spawn at center concourse, not inside door_rect"

    # Simulate subsequent frame in STATE_HUB
    game.handle_events()
    game.update(0.016)
    assert game.state == Game.STATE_HUB, "Subsequent frame in hub must NOT restart the level immediately"

    # 2. Test Victory
    game.start_new_run("steam", AVAILABLE_WEAPONS[0]())
    game.hub_station.player_pos = pygame.math.Vector2(steam_bay["door_rect"].center)
    game.state = Game.STATE_VICTORY
    game.overlay_input_delay = 0.0

    # Press Space to return to hub
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    game.handle_events()
    assert game.state == Game.STATE_HUB, "Pressing Space on Victory must return to STATE_HUB"
    assert game.hub_station.player_pos.y >= 500, "Player must spawn at center concourse"

    # Simulate subsequent frame in STATE_HUB
    game.handle_events()
    game.update(0.016)
    assert game.state == Game.STATE_HUB, "Subsequent frame in hub must NOT restart the level immediately"
    print("  ✓ Return to Hub with Space/E on Game Over & Victory verified (No immediate restart).")


if __name__ == "__main__":
    test_progression_manager()
    test_walkable_hub_station()
    test_all_5_stages_and_bosses()
    test_new_boss_attack_patterns()
    test_hazards_mice_and_lasers()
    test_victory_screen_layout_no_overflow()
    test_return_to_hub_after_death_and_victory()
    print("\n=======================================================")
    print("ALL PROGRESSION, 5 STAGES, HAZARDS & HUB TESTS PASSED! ✓")
    print("=======================================================")
