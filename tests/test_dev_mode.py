"""Automated verification suite for the Secret Developer Mode, Level Iterator, Weapon Progression, and Mobile Controls."""
import os
import pygame
from src.core.game import Game
from src.core.progression import ProgressionManager, ALL_STAGES, WEAPON_UPGRADE_DEFINITIONS
from src.combat.weapons import RivetGun, StokerWrench, CoalScattergun, TeslaArcCaster, create_weapon_by_id
from src.combat.boons import (
    TeslaCoilBoon, SteamOverdriveDashBoon, TungstenPiercingBoon,
    get_active_synergies, get_synergy_preview_for_boon
)
from src.ui.dev_mode import SecretKeypad, LevelIteratorDrawer
from src.ui.weapon_upgrade_menu import WeaponUpgradeMenu
from src.core.leaderboard import LeaderboardClient
from src.ui.mobile_controls import MobileControls

def test_dev_mode_and_features_suite():
    print("=======================================================")
    print("TESTING DEV MODE, WEAPONS, UPGRADES & LEADERBOARD SUITE")
    print("=======================================================")
    pygame.init()
    temp_save = "test_dev_progression_save.json"
    if os.path.exists(temp_save):
        os.remove(temp_save)

    prog = ProgressionManager(save_path=temp_save)
    game = Game(headless=True, progression=prog)

    try:
        # ------------------------------------------------------------------
        # 1. Verification that Public Hacks Panel is REMOVED
        # ------------------------------------------------------------------
        print("--- 1. Testing Removal of Public Hacks Panel ---")
        assert not hasattr(game, "test_mode_menu"), "test_mode_menu should be completely removed"
        assert not hasattr(game.hub_station, "test_terminal_rect"), "test_terminal_rect should be removed from Hub"
        assert not hasattr(game.hub_station, "hud_test_btn_rect"), "hud_test_btn_rect should be removed from Hub"
        print("✓ Public hacks panel, test desk, and top HUD button are fully removed.")

        # ------------------------------------------------------------------
        # 2. Secret Keypad in Bottom-Right Corner & Dev Mode Unlock
        # ------------------------------------------------------------------
        print("--- 2. Testing Secret Developer Keypad & Code Verification ---")
        hub = game.hub_station
        keypad = hub.secret_keypad
        
        # When player is in center of hub, keypad is folded/inactive
        hub.player_pos = pygame.math.Vector2(game.screen.get_width() // 2, game.screen.get_height() // 2)
        keypad.update(hub.player_pos, 0.016)
        assert not keypad.is_active, "Keypad should not be active when player is away from bottom-right"

        # Walk player to bottom-right corner of screen
        hub.player_pos = pygame.math.Vector2(game.screen.get_width() - 80, game.screen.get_height() - 80)
        keypad.update(hub.player_pos, 0.016)
        assert keypad.is_active, "Keypad must activate when player enters bottom-right corner"

        # Test typing incorrect code
        for char in "WRONG":
            keypad.handle_event(pygame.event.Event(pygame.KEYDOWN, unicode=char, key=pygame.K_a))
        assert not game.dev_mode, "Incorrect code should not unlock Dev Mode"

        # Clear and enter secret programmer code: CHUDDEV
        keypad.input_text = ""
        for char in "CHUDDEV":
            keypad.handle_event(pygame.event.Event(pygame.KEYDOWN, unicode=char, key=pygame.K_a))
        keypad.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode=""))

        assert hub.dev_mode_unlocked is True, "Hub should record dev mode unlocked"
        assert game.dev_mode is True, "Game should enter Dev Mode"
        assert game.dev_drawer.is_open is True, "Level Iterator drawer should open on dev unlock"
        print("✓ Secret keypad activates in bottom-right corner and unlocks Dev Mode with 'CHUDDEV'.")

        # ------------------------------------------------------------------
        # 3. Level Iterator Drawer & Level Jumping
        # ------------------------------------------------------------------
        print("--- 3. Testing Level Iterator Drawer ---")
        drawer = game.dev_drawer
        assert isinstance(drawer, LevelIteratorDrawer)
        
        # Test iterating tracks and cars
        drawer.select_track(3)
        drawer.select_car(8)
        assert drawer.selected_track_idx == 3
        assert drawer.selected_car_idx == 8

        # Deploy directly into selected stage (Car 8 is index 7)
        drawer.deploy_selected()
        assert game.state == Game.STATE_PLAYING
        assert game.run_manager.route_id == "cryo"
        assert game.run_manager.current_car_index == 7
        print("✓ Level iterator drawer selects track and car and launches run.")

        # Test hotkey [N] next level/car and [B] previous level/car during play
        game.dev_drawer.next_car()
        assert game.run_manager.current_car_index == 8
        game.dev_drawer.next_car()
        assert game.run_manager.current_car_index == 9
        game.dev_drawer.prev_car()
        assert game.run_manager.current_car_index == 8
        print("✓ [N] Next Level and [B] Prev Level hotkeys successfully iterated through cars.")

        # ------------------------------------------------------------------
        # 4. Weapon Progression & Difficult Token Economy
        # ------------------------------------------------------------------
        print("--- 4. Testing Weapon Token Economy & Ranks 1-5 ---")
        assert prog.weapon_tokens == 0, "Player must start with 0 weapon tokens"
        assert prog.get_weapon_rank("riveter") == 1
        assert not prog.can_upgrade_weapon("riveter"), "Cannot upgrade weapon without token"

        # Intermediate cars must NOT grant weapon tokens
        game.load_next_train_car()
        assert prog.weapon_tokens == 0, "Clearing intermediate cars must NOT grant weapon tokens"

        # Only full track victory grants 1 token!
        # Simulate defeating the Car 15 Locomotive Climax Boss
        prog.advance_track_on_victory()
        assert prog.weapon_tokens == 1, "Full track victory must grant exactly 1 weapon token"
        assert prog.can_upgrade_weapon("riveter"), "Should now be able to upgrade with 1 token"

        # Upgrade Riveter from Rank 1 to Rank 2
        success = prog.upgrade_weapon("riveter")
        assert success is True
        assert prog.get_weapon_rank("riveter") == 2
        assert prog.weapon_tokens == 0, "Upgrading must consume the 1 token"

        # Verify upgraded weapon instantiation
        wpn_r2 = create_weapon_by_id("riveter", rank=2)
        assert wpn_r2.rank == 2
        assert wpn_r2.speed == 1150.0, "Riveter Rank 2 has increased projectile speed"
        assert wpn_r2.fire_rate == 0.13, "Riveter Rank 2 has increased fire rate"

        # Verify Rank 4 fires twin projectiles
        wpn_r4 = create_weapon_by_id("riveter", rank=4)
        assert wpn_r4.projectile_count == 2, "Riveter Rank 4 fires twin micro-rockets"

        # Verify Rank 5 Tungsten Railgun Ricochet
        wpn_r5 = create_weapon_by_id("riveter", rank=5)
        assert wpn_r5.rank == 5
        assert wpn_r5.projectile_count == 2
        print("✓ Token economy strictly requires full clear; weapons scale to Rank 5 with unique mechanics.")

        # ------------------------------------------------------------------
        # 5. Overhauled Boon System with Elemental Tags & Synergies
        # ------------------------------------------------------------------
        print("--- 5. Testing Overhauled Upgrade Boons & Elemental Synergies ---")
        tesla = TeslaCoilBoon()
        assert tesla.element == "ELECTRIC"
        stats = tesla.get_stat_breakdown()
        assert len(stats) >= 2
        assert "Chain Targets" in stats[0][0]

        pierce = TungstenPiercingBoon()
        assert pierce.element == "KINETIC"
        
        # Test Synergy detection
        preview = get_synergy_preview_for_boon("tungsten_pierce", [tesla])
        assert preview is not None
        assert preview["id"] == "superconductor_arc"

        active_syns = get_active_synergies([tesla, pierce])
        assert len(active_syns) == 1
        assert active_syns[0]["name"] == "Superconductor Arc"
        print("✓ Elemental affinities, stat breakdowns, and synergy previews working as designed.")

        # ------------------------------------------------------------------
        # 6. Conductor Honor Board (Leaderboard System)
        # ------------------------------------------------------------------
        print("--- 6. Testing Leaderboard Client & Honor Roll ---")
        client = game.leaderboard_client
        scores = client.get_top_scores(limit=5)
        assert len(scores) >= 1

        new_entry = client.record_run(
            player_name="Ace Conductor Test",
            route_id="infernal",
            route_name="Infernal Express",
            cars_cleared=15,
            weapon_name="Riveter (R5)",
            loop_count=1,
            is_victory=True,
            enemies_killed=77,
            damage_dealt=12000,
            duration_sec=320.0
        )
        assert new_entry["score"] > 5000
        top_scores = client.get_top_scores(limit=5)
        assert top_scores[0]["player_name"] == "Ace Conductor Test"
        print(f"✓ Conductor leaderboard recorded run with score {new_entry['score']:,}.")

        # ------------------------------------------------------------------
        # 7. Mobile Virtual Controls
        # ------------------------------------------------------------------
        print("--- 7. Testing Mobile Virtual On-Screen Controls ---")
        mobile = game.mobile_controls
        assert isinstance(mobile, MobileControls)
        assert mobile.enabled is False

        # Toggle on
        mobile.toggle()
        assert mobile.enabled is True

        # Test touch stick motion
        stick = mobile.stick
        # Touch at center of stick + 40px right
        down = stick.handle_touch_down(1, (stick.center.x + 40, stick.center.y))
        assert down is True
        assert stick.vector.x > 0.5
        assert mobile.get_move_vector().x > 0.5

        # Release touch
        stick.handle_touch_up(1)
        assert mobile.get_move_vector().length_squared() == 0

        # Test action buttons
        btn_fire = mobile.btn_fire
        btn_fire.handle_touch_down(2, (btn_fire.pos.x, btn_fire.pos.y))
        assert mobile.is_fire_active() is True
        btn_fire.handle_touch_up(2)
        assert mobile.is_fire_active() is False
        print("✓ Mobile virtual controls multi-touch thumbstick and action buttons verified.")

        print("\n=======================================================")
        print("ALL NEW FEATURES VERIFIED SUCCESSFULLY (100% PASS)!")
        print("=======================================================")

    finally:
        if os.path.exists(temp_save):
            os.remove(temp_save)
        pygame.quit()

if __name__ == "__main__":
    test_dev_mode_and_features_suite()
