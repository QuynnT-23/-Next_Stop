"""Automated verification suite for the in-game Test Mode & Dev Console."""
import os
import pygame
from src.core.game import Game
from src.core.progression import ProgressionManager, ALL_STAGES, PERK_DEFINITIONS
from src.combat.weapons import RivetGun, TeslaArcCaster
from src.combat.damage import DamageEvent
from src.entities.enemies.stage_bosses import IronLeviathanBoss, AshPyromancerMiniBoss
from src.ui.test_mode_menu import TestModeMenu

def test_test_mode_suite():
    print("=======================================================")
    print("TESTING IN-GAME TEST MODE & DEV CONSOLE SUITE")
    print("=======================================================")
    pygame.init()
    temp_save = "test_dev_mode_save.json"
    if os.path.exists(temp_save):
        os.remove(temp_save)

    prog = ProgressionManager(save_path=temp_save)
    game = Game(headless=True, progression=prog)

    try:
        # ------------------------------------------------------------------
        # 1. Test Mode Toggle & Hub Integration
        # ------------------------------------------------------------------
        print("--- 1. Testing Test Mode Toggle & Hub Station Integration ---")
        assert game.test_mode_active is False
        assert isinstance(game.test_mode_menu, TestModeMenu)

        # Toggle via helper
        game.toggle_test_mode()
        assert game.test_mode_active is True
        game.toggle_test_mode()
        assert game.test_mode_active is False

        # Toggle via F1 key in handle_events
        f1_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1)
        pygame.event.post(f1_event)
        game.handle_events()
        assert game.test_mode_active is True, "Pressing F1 must activate Test Mode"

        # Close via ESC key
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        pygame.event.post(esc_event)
        game.handle_events()
        assert game.test_mode_active is False, "Pressing ESC inside Test Mode must close it"

        # Test Hub Terminal Desk interaction
        game.hub_station.player_pos = pygame.math.Vector2(game.hub_station.test_terminal_rect.center)
        e_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        game.hub_station.handle_input([e_event])
        assert game.hub_station.request_test_mode is True, "Interacting near Test Terminal desk must set request_test_mode"
        
        # Test handle_events picking up request_test_mode
        game.handle_events()
        assert game.test_mode_active is True
        game.toggle_test_mode()
        assert game.test_mode_active is False

        # Test clicking top HUD button
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=game.hub_station.hud_test_btn_rect.center)
        game.hub_station.handle_input([click_event])
        assert game.hub_station.request_test_mode is True, "Clicking top HUD test button must set request_test_mode"
        print("✓ Test Mode toggle via F1, terminal desk interaction, and HUD button verified.")

        # ------------------------------------------------------------------
        # 2. Conductor Level & Scrap Currency Steppers
        # ------------------------------------------------------------------
        print("--- 2. Testing Progression & Scrap Adjustment ---")
        prog.set_level(15)
        assert prog.level == 15
        assert prog.xp == 0

        prog.set_scrap(750)
        assert prog.scrap == 750

        # Max all perks
        prog.max_all_perks()
        for perk_id, data in PERK_DEFINITIONS.items():
            assert prog.perks[perk_id] == data["max_rank"]
        print("✓ Conductor level set (15), scrap set (750), and perks maxed verified.")

        # Reset perks
        prog.reset_all_perks()
        for perk_id in PERK_DEFINITIONS:
            assert prog.perks[perk_id] == 0
        print("✓ Conductor perks reset verified.")

        # ------------------------------------------------------------------
        # 3. Direct Stage & Car Warp Deployment
        # ------------------------------------------------------------------
        print("--- 3. Testing Direct Stage & Car Deployment ---")
        # Deploy straight into Track 5 (The Infernal Boiler), Car 15 (The Iron Leviathan final boss!)
        game.deploy_to_stage_and_car("infernal", 14, TeslaArcCaster(), loop_count=1)
        assert game.state == Game.STATE_PLAYING
        assert game.run_manager.route_id == "infernal"
        assert game.run_manager.current_car_index == 14
        assert game.run_manager.is_final_car() is True
        assert len(game.enemies) > 0
        assert isinstance(game.enemies[0], IronLeviathanBoss), "Car 15 of Infernal Boiler must spawn The Iron Leviathan"
        assert isinstance(game.player.weapon, TeslaArcCaster)
        print("✓ Direct deployment straight to Track 5, Car 15 (The Iron Leviathan) verified.")

        # In-Run Warp to Car 5 (Ash Pyromancer Mini-Boss Checkpoint)
        game.warp_to_car(4)
        assert game.run_manager.current_car_index == 4
        assert any(isinstance(e, AshPyromancerMiniBoss) for e in game.enemies), "Car 5 must spawn Ash Pyromancer"
        print("✓ In-run warping directly to Car 5 Mini-Boss verified.")

        # ------------------------------------------------------------------
        # 4. In-Run Combat Cheats (God Mode, Kill Foes, Refill Stats, Boon Draft)
        # ------------------------------------------------------------------
        print("--- 4. Testing Combat Testing Cheats ---")
        # God Mode
        assert game.player.god_mode is False
        game.player.god_mode = True
        init_hp = game.player.health
        # Hit player with massive damage
        game.player.take_damage(DamageEvent(80, source_type="enemy"), game)
        assert game.player.health == init_hp, "God Mode must block all incoming damage"

        # Turn God Mode off and take damage
        game.player.god_mode = False
        game.player.take_damage(DamageEvent(30, source_type="enemy"), game)
        assert game.player.health < init_hp, "Normal damage must apply when God Mode is OFF"

        # Refill stats
        game.player.super_charge = 15.0
        game.player.refill_stats()
        assert game.player.health == game.player.max_health
        assert game.player.super_charge == game.player.max_super_charge
        print("✓ God Mode invincibility and stat refill verified.")

        # Kill All Enemies
        assert any(e.is_alive() for e in game.enemies)
        game.kill_all_enemies()
        assert all(not e.is_alive() for e in game.enemies), "Kill all foes must eliminate every active enemy"
        print("✓ Instant enemy elimination cheat verified.")

        # Trigger Boon Draft
        game.trigger_boon_draft()
        assert game.state == Game.STATE_BOON_DRAFT, "trigger_boon_draft must open UpgradeMenu on demand"
        print("✓ On-demand Boon Draft cheat verified.")

        # ------------------------------------------------------------------
        # 5. Reset to Fresh Save Utility
        # ------------------------------------------------------------------
        print("--- 5. Testing Fresh Save Reset Utility ---")
        prog.set_level(30)
        prog.set_scrap(5000)
        prog.loop_count = 3
        prog.current_track_idx = 4
        assert prog.level == 30

        prog.reset_to_fresh()
        assert prog.level == 1
        assert prog.xp == 0
        assert prog.scrap == 0
        assert prog.current_track_idx == 0
        assert prog.loop_count == 0
        assert prog.unlocked_stages == ["steam"]
        assert all(v == 0 for v in prog.perks.values())
        print("✓ Fresh Save Reset restored all progression to pristine Level 1 defaults.")

        # ------------------------------------------------------------------
        # 6. Test Console Modal Rendering
        # ------------------------------------------------------------------
        print("--- 6. Testing Test Console Modal Rendering ---")
        surf = pygame.Surface((1280, 720))
        game.test_mode_menu.open()
        game.test_mode_menu.update(0.016)
        game.test_mode_menu.draw(surf)
        print("✓ Test Mode modal frame rendered cleanly without errors.")

        print("\n=======================================================")
        print("ALL TEST MODE & DEV CONSOLE TESTS PASSED! ✓")
        print("=======================================================")

    finally:
        if os.path.exists(temp_save):
            os.remove(temp_save)

if __name__ == "__main__":
    test_test_mode_suite()
