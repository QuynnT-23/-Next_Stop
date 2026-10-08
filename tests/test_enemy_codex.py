"""Test suite for Conductor's Field Log & Enemy Threat Index.

Verifies:
1. All 16 enemy archetypes registered in ENEMY_CODEX_DATA with complete attributes and attacks.
2. Enemy instantiation factories and preview rendering via DummyPreviewCamera.
3. ProgressionManager encounter recording and persistence.
4. Game loop automatic encounter recording when enemies spawn.
5. HubStation Dispatch Archives interaction, category filtering, keyboard navigation, and modal rendering.
"""
import os
import pygame
import tempfile
import json

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.combat.enemy_codex import (
    ENEMY_CODEX_DATA,
    DummyPreviewCamera,
    get_codex_id_from_enemy,
    get_all_codex_entries
)
from src.core.progression import ProgressionManager
from src.core.game import Game
from src.ui.hub_station import HubStation


def test_codex_registry_completeness():
    """Verify that all 16 enemies are registered with complete metadata and attack patterns."""
    print("--- 1. Testing Codex Registry Completeness ---")
    entries = get_all_codex_entries()
    assert len(entries) == 16, f"Expected 16 enemy codex entries, found {len(entries)}"

    expected_ids = {
        # Standard / Elite
        "ticket_inspector", "ranged_steward", "boiler_imp", "automaton_shield", "boiler_brute", "furnace_golem",
        # Mini-Bosses
        "chief_inspector", "scrapper_foreman", "cyber_dispatcher", "sub_zero_warden", "ash_pyromancer",
        # Climax Bosses
        "conductor", "vermin_brood_engine", "traction_ai_core", "cryo_turbine_engine", "iron_leviathan"
    }

    found_ids = set(ENEMY_CODEX_DATA.keys())
    assert found_ids == expected_ids, f"Mismatch in codex entries! Missing: {expected_ids - found_ids}"

    valid_categories = {"Standard", "Elite", "Mini-Boss", "Climax Boss"}

    for eid, data in ENEMY_CODEX_DATA.items():
        assert data["id"] == eid, f"Entry {eid} has mismatched id field"
        assert len(data["name"]) > 0, f"Entry {eid} has empty name"
        assert len(data["subtitle"]) > 0, f"Entry {eid} has empty subtitle"
        assert data["category"] in valid_categories, f"Entry {eid} has invalid category {data['category']}"
        assert data["threat_stars"] in (1, 2, 3, 4, 5), f"Entry {eid} has invalid threat_stars {data['threat_stars']}"
        assert data["base_health"] > 0, f"Entry {eid} has non-positive health"
        assert data["base_speed"] > 0, f"Entry {eid} has non-positive speed"
        assert len(data["attacks"]) >= 1, f"Entry {eid} must have at least one attack pattern"
        for atk in data["attacks"]:
            assert "name" in atk and len(atk["name"]) > 0
            assert "type" in atk and len(atk["type"]) > 0
            assert "desc" in atk and len(atk["desc"]) > 0
        assert len(data["tactics"]) > 0, f"Entry {eid} must have tactical guidance"
        assert len(data["lore"]) > 0, f"Entry {eid} must have lore text"
        assert callable(data["factory"]), f"Entry {eid} factory must be callable"

    print(f"✓ All 16 enemy entries verified with complete metadata and attack patterns.")


def test_codex_factories_and_preview_rendering():
    """Verify all 16 enemy factories instantiate valid objects and render via DummyPreviewCamera."""
    print("--- 2. Testing Enemy Factories & Live Preview Rendering ---")
    pygame.init()
    surface = pygame.Surface((1280, 720))
    camera = DummyPreviewCamera()

    for eid, data in ENEMY_CODEX_DATA.items():
        enemy = data["factory"](400, 300)
        assert enemy is not None, f"Factory for {eid} returned None"
        resolved_id = get_codex_id_from_enemy(enemy)
        assert resolved_id == eid, f"Expected resolved id '{eid}', got '{resolved_id}' for {enemy.__class__.__name__}"

        # Set preview attributes and draw with DummyPreviewCamera
        enemy.pos = pygame.math.Vector2(400, 300)
        enemy.walk_distance = 50.0
        enemy.facing_angle = 1.57
        enemy.flash_timer = 0.0
        enemy.state = "chase"
        enemy.state_timer = 1.0
        enemy.draw(surface, camera)

    print("✓ All 16 enemy factories instantiate and render cleanly with DummyPreviewCamera.")


def test_progression_encounter_tracking():
    """Verify ProgressionManager records encounters and persists them across save/load."""
    print("--- 3. Testing ProgressionManager Encounter Tracking & Save/Load ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        prog = ProgressionManager(save_path=temp_path)
        assert "ticket_inspector" in prog.encountered_enemies
        assert "ranged_steward" in prog.encountered_enemies
        assert "boiler_imp" in prog.encountered_enemies
        assert "scrapper_foreman" not in prog.encountered_enemies

        # Record a new enemy
        newly_added = prog.record_enemy_encounter("scrapper_foreman")
        assert newly_added is True, "Expected True when recording a new enemy"
        assert "scrapper_foreman" in prog.encountered_enemies

        # Duplicate recording should return False
        dup_added = prog.record_enemy_encounter("scrapper_foreman")
        assert dup_added is False, "Expected False for already encountered enemy"

        # Check persistence by reloading
        prog2 = ProgressionManager(save_path=temp_path)
        assert "scrapper_foreman" in prog2.encountered_enemies
        assert "iron_leviathan" not in prog2.encountered_enemies
        print("✓ ProgressionManager encounter recording and persistence confirmed.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


from src.combat.weapons import StokerWrench


def test_game_automatic_encounter_recording():
    """Verify that Game records spawned enemies into progression encountered_enemies."""
    print("--- 4. Testing Automatic In-Game Encounter Registration ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        prog = ProgressionManager(save_path=temp_path)
        game = Game(headless=True)
        game.progression = prog
        game.start_new_run("steam", StokerWrench())

        # In Track 1, start_new_run spawns enemies in Car 1
        assert len(game.enemies) > 0, "Car 1 should spawn enemies"
        for enemy in game.enemies:
            cid = get_codex_id_from_enemy(enemy)
            assert cid in prog.encountered_enemies, f"Spawned enemy {cid} should be recorded in progression"

        print("✓ Game loop automatically registers newly encountered enemy archetypes.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_hub_station_codex_interaction_and_modal():
    """Verify HubStation Dispatch Archives desk, modal toggle, navigation, filtering, and badging."""
    print("--- 5. Testing HubStation Dispatch Archives UI & Interactions ---")
    pygame.init()
    surface = pygame.Surface((1280, 720))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        prog = ProgressionManager(save_path=temp_path)
        # Ensure only default 3 enemies are encountered
        prog.encountered_enemies = ["ticket_inspector", "ranged_steward", "boiler_imp"]
        prog.save()

        hub = HubStation(prog)
        assert hub.show_codex is False
        assert hub.codex_rect is not None
        assert hub.codex_rect.width == 160 and hub.codex_rect.height == 120

        # Toggle modal with [B] key
        b_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)
        hub.handle_input([b_event])
        assert hub.show_codex is True, "Pressing [B] should open the enemy codex"

        # Test Category Filtering
        assert hub.codex_category_filter == "ALL"
        assert len(hub._get_filtered_codex_entries()) == 16

        # Switch to Mini-Boss category via key '3'
        num3_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)
        hub.handle_input([num3_event])
        assert hub.codex_category_filter == "Mini-Boss"
        filtered_minis = hub._get_filtered_codex_entries()
        assert len(filtered_minis) == 5
        assert all(entry["category"] == "Mini-Boss" for entry in filtered_minis)

        # Switch to Climax Boss category via key '4'
        num4_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_4)
        hub.handle_input([num4_event])
        assert hub.codex_category_filter == "Climax Boss"
        filtered_bosses = hub._get_filtered_codex_entries()
        assert len(filtered_bosses) == 5
        assert all(entry["category"] == "Climax Boss" for entry in filtered_bosses)

        # Switch to Standard via key '2'
        num2_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)
        hub.handle_input([num2_event])
        assert hub.codex_category_filter == "Standard"
        filtered_std = hub._get_filtered_codex_entries()
        assert len(filtered_std) == 6

        # Switch back to ALL via key '1'
        num1_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)
        hub.handle_input([num1_event])
        assert hub.codex_category_filter == "ALL"

        # Test Selection Navigation (DOWN key)
        initial_selected = hub.selected_codex_id
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        hub.handle_input([down_event])
        assert hub.selected_codex_id != initial_selected, "Pressing DOWN should change selected enemy"

        # Test Modal Drawing (both encountered and unseen enemies)
        # 1. Selected is encountered (e.g. ticket_inspector)
        hub.selected_codex_id = "ticket_inspector"
        hub.draw(surface)

        # 2. Selected is unseen (e.g. iron_leviathan)
        hub.selected_codex_id = "iron_leviathan"
        assert "iron_leviathan" not in prog.encountered_enemies
        hub.draw(surface)

        # Test Close with ESC
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        hub.handle_input([esc_event])
        assert hub.show_codex is False, "Pressing ESC should close the codex modal"

        # Test Desk Proximity and Interaction with [E]
        hub.player_pos = pygame.math.Vector2(hub.codex_rect.centerx, hub.codex_rect.centery)
        e_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        hub.handle_input([e_event])
        assert hub.show_codex is True, "Pressing [E] at the Dispatch Archives desk should open codex"

        print("✓ HubStation Dispatch Archives modal, navigation, filtering, and badging verified.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    test_codex_registry_completeness()
    test_codex_factories_and_preview_rendering()
    test_progression_encounter_tracking()
    test_game_automatic_encounter_recording()
    test_hub_station_codex_interaction_and_modal()
    print("\n=======================================================")
    print("ALL 5 ENEMY CODEX TESTS COMPLETED SUCCESSFULLY!")
    print("=======================================================")
