"""Comprehensive test suite for Single-Track Linear Progression, Departed Track Lockouts, Track 1+ Loop Cycle & Modifiers."""
import os
import pygame
import tempfile
import json

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.core.game import Game
from src.core.progression import ProgressionManager, ALL_STAGES
from src.ui.hub_station import HubStation
from src.level.car_generator import RunManager, TRACK_MODIFIERS, STAGE_DIFFICULTY_CONFIG
from src.entities.enemies.boss import ConductorBoss
from src.combat.damage import DamageEvent


def test_single_track_progression_lifecycle():
    """Verify single-track availability, departed track lockout, and loop cycling."""
    print("--- 1. Testing Single-Track Progression & Departed Lockouts ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_save = tf.name

    try:
        pm = ProgressionManager(save_path=temp_save)
        assert pm.current_track_idx == 0, "Initial track must be Track 1 (idx 0)"
        assert pm.loop_count == 0, "Initial loop count must be 0"
        assert pm.get_active_route_id() == "steam"
        assert pm.get_track_display_name(0) == "TRACK 1"
        assert pm.get_track_state(0) == "active"
        assert pm.get_track_state(1) == "locked"
        assert pm.get_track_state(2) == "locked"
        print("  ✓ Initial state: Track 1 is active, Tracks 2-5 are locked.")

        # Test Hub interaction with initial state
        hub = HubStation(pm)
        test_surface = pygame.Surface((1280, 720))
        hub.draw(test_surface)

        # Attempt to board Track 2 (locked)
        bay_2 = hub.docking_bays[1]
        clicked_locked = hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=bay_2["door_rect"].center)])
        assert not clicked_locked, "Locked Track 2 must not be boardable"

        # Board Track 1 (active)
        bay_1 = hub.docking_bays[0]
        clicked_active = hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=bay_1["door_rect"].center)])
        assert clicked_active is True, "Active Track 1 must be boardable"
        assert hub.get_selected_route_id() == "steam"
        print("  ✓ Hub correctly boards active Track 1 and blocks locked Track 2.")

        # Simulate beating Track 1
        res1 = pm.advance_track_on_victory()
        assert res1["previous_track_idx"] == 0
        assert res1["active_track_idx"] == 1
        assert res1["active_route"] == "derelict"
        assert res1["new_loop"] is False

        # Verify Track states after Track 1 victory
        assert pm.get_track_state(0) == "completed", "Track 1 must now be completed/departed"
        assert pm.get_track_state(1) == "active", "Track 2 must now be active"
        assert pm.get_track_state(2) == "locked", "Track 3 must remain locked"
        print("  ✓ Track 1 marked departed/completed. Track 2 is now active.")

        # Test Hub: Attempting to re-board departed Track 1 must fail!
        hub.reset_player()
        hub.board_cooldown = 0.0
        hub.draw(test_surface)
        reboard_1 = hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=bay_1["door_rect"].center)])
        assert not reboard_1, "Departed Track 1 must NOT be re-boardable during this cycle"

        # Walking into departed Track 1 door also must not board
        hub.player_pos = pygame.math.Vector2(bay_1["door_rect"].center)
        walk_1 = hub.handle_input([])
        assert not walk_1, "Walking into departed Track 1 door must NOT board"

        # Board Track 2
        board_2 = hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=bay_2["door_rect"].center)])
        assert board_2 is True, "Track 2 must now board cleanly"
        assert hub.get_selected_route_id() == "derelict"
        print("  ✓ Departed Track 1 lockout verified. Track 2 boarding verified.")

        # Advance through Tracks 2, 3, 4
        pm.advance_track_on_victory()  # Beats derelict -> subway
        assert pm.get_active_route_id() == "subway"
        pm.advance_track_on_victory()  # Beats subway -> cryo
        assert pm.get_active_route_id() == "cryo"
        pm.advance_track_on_victory()  # Beats cryo -> infernal (Track 5)
        assert pm.get_active_route_id() == "infernal"
        assert pm.current_track_idx == 4
        assert pm.loop_count == 0
        print("  ✓ Successfully advanced sequentially to Track 5 (The Infernal Boiler).")

        # Now beat Track 5 (The Iron Leviathan) -> Loop Cycle triggers!
        res_loop = pm.advance_track_on_victory()
        assert res_loop["new_loop"] is True, "Completing Track 5 must advance to new loop"
        assert res_loop["active_track_idx"] == 0, "Loop must reset active track to Track 1"
        assert res_loop["loop_count"] == 1, "Loop count must now be 1"
        assert pm.get_loop_suffix() == "+", "Loop suffix must be '+'"
        assert pm.get_track_display_name(0) == "TRACK 1+", "Track 1 display name must be 'TRACK 1+'"
        assert pm.get_track_state(0) == "active", "Track 1+ must now be active"
        assert pm.get_track_state(1) == "locked", "Track 2+ must be locked"
        print("  ✓ Track 5 completed: Advanced to TRACK 1+ (Loop 1)!")

        # Verify JSON reload persistence
        pm2 = ProgressionManager(save_path=temp_save)
        assert pm2.current_track_idx == 0
        assert pm2.loop_count == 1
        assert pm2.get_track_display_name(0) == "TRACK 1+"
        print("  ✓ Persistence verified: Save file correctly reloaded Track 1+ (Loop 1).")

    finally:
        if os.path.exists(temp_save):
            os.remove(temp_save)


def test_track_modifiers_and_loop_scaling():
    """Verify that Loop 1+ activates modifiers and scales enemy HP, damage, and wave density."""
    print("--- 2. Testing Track Modifiers & Loop Difficulty Scaling ---")
    # Base run manager (Loop 0)
    rm_base = RunManager("steam", loop_count=0)
    assert len(rm_base.get_active_modifiers()) == 0, "Loop 0 should have no active modifiers"
    car_base = rm_base.create_current_car()
    enemies_base = rm_base.spawn_enemies_for_car(car_base)
    base_avg_hp = sum(e.health for e in enemies_base) / len(enemies_base)

    # Loop 1 run manager (Track 1+)
    rm_loop1 = RunManager("steam", loop_count=1)
    mods = rm_loop1.get_active_modifiers()
    assert len(mods) == len(TRACK_MODIFIERS["steam"]), "Track 1+ must have steam modifiers active"
    assert any(m["id"] == "overclocked_boiler" for m in mods)
    assert any(m["id"] == "dense_steam" for m in mods)

    car_loop1 = rm_loop1.create_current_car()
    enemies_loop1 = rm_loop1.spawn_enemies_for_car(car_loop1)
    loop1_avg_hp = sum(e.health for e in enemies_loop1) / len(enemies_loop1)

    total_hp_base = sum(e.health for e in enemies_base)
    total_hp_loop1 = sum(e.health for e in enemies_loop1)
    print(f"  Base Track 1: count={len(enemies_base)}, total_hp={total_hp_base}, avg_hp={base_avg_hp:.1f}")
    print(f"  Track 1+ (Loop 1): count={len(enemies_loop1)}, total_hp={total_hp_loop1}, avg_hp={loop1_avg_hp:.1f}, modifiers={[m['name'] for m in mods]}")

    assert total_hp_loop1 > total_hp_base, "Track 1+ wave must have significantly higher total HP than base Track 1"
    assert len(enemies_loop1) >= len(enemies_base), "Track 1+ must have higher enemy density"
    assert rm_loop1.get_loop_display() == "+"
    print("  ✓ Track 1+ modifiers and difficulty scaling verified.")


def test_game_integration_victory_cycle():
    """Test full game start and victory transition advancing track and loop."""
    print("--- 3. Testing In-Game Victory Sequence & Loop Banner ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_save = tf.name

    try:
        mock_pm = ProgressionManager(save_path=temp_save)
        mock_pm.current_track_idx = 4  # Start on Track 5
        mock_pm.loop_count = 0
        mock_pm.save()

        game = Game(progression=mock_pm)
        route = game.progression.get_active_route_id()
        assert route == "infernal"

        game.start_new_run(route, game.hub_station.get_selected_weapon())
        assert game.run_manager.route_id == "infernal"
        assert game.run_manager.loop_count == 0

        # Advance to Car 15
        game.run_manager.current_car_index = 14
        game.train_car = game.run_manager.create_current_car()
        game.enemies = game.run_manager.spawn_enemies_for_car(game.train_car)
        boss = game.enemies[0]
        
        # Slay the boss
        boss.health = 0
        boss.die(game)
        game.update(0.016)

        # Run out victory timer
        for _ in range(70):
            game.update(0.02)

        assert game.state == Game.STATE_VICTORY
        assert isinstance(game.newly_unlocked_stage, dict)
        assert game.newly_unlocked_stage["new_loop"] is True
        assert game.progression.loop_count == 1
        assert game.progression.current_track_idx == 0
        assert game.progression.get_track_display_name(0) == "TRACK 1+"
        print("  ✓ In-Game Car 15 boss defeat successfully triggered Loop 1 transition to TRACK 1+!")
    finally:
        if os.path.exists(temp_save):
            os.remove(temp_save)


if __name__ == "__main__":
    pygame.init()
    test_single_track_progression_lifecycle()
    test_track_modifiers_and_loop_scaling()
    test_game_integration_victory_cycle()
    print("\n=======================================================")
    print("ALL SINGLE-TRACK PROGRESSION & LOOP+ TESTS PASSED! ✓")
    print("=======================================================")
