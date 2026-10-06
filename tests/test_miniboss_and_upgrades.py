"""Test suite verifying Car 5 Mini-Boss defeat, Boon Pedestal activation,
UpgradeMenu rendering across all rarities (especially Legendary), and Car 6 transition.
"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from src.core.game import Game
from src.combat.boons import (
    StaticDynamoBoon, StokerSiphonBoon, MoltenCoreBoon,
    CombustionEngineBoon, TungstenPiercingBoon, get_random_boon_choices
)
from src.entities.enemies.miniboss import ChiefInspectorMiniBoss

def test_miniboss_defeat_and_upgrade_draft():
    print("=== Testing Mini-Boss Defeat, Upgrade Drafting & Legendary Rendering ===")
    pygame.init()
    game = Game(headless=True)
    game.start_new_run("steam", None)
    
    # 1. Advance to Car 5 (Index 4: Inspection Car)
    print("--- 1. Advancing to Car 5 (Ticket Inspection Checkpoint) ---")
    while game.run_manager.current_car_index < 4:
        game.run_manager.current_car_index += 1
    
    game.train_car = game.run_manager.create_current_car()
    assert game.train_car.car_type == "inspection", f"Expected 'inspection', got '{game.train_car.car_type}'"
    game.enemies = game.run_manager.spawn_enemies_for_car(game.train_car)
    
    # Verify Chief Ticket Inspector is present
    miniboss = next((e for e in game.enemies if isinstance(e, ChiefInspectorMiniBoss)), None)
    assert miniboss is not None, "ChiefInspectorMiniBoss must spawn in inspection car"
    assert miniboss.is_miniboss is True
    print(f"✓ Chief Ticket Inspector spawned with {miniboss.health} HP and {len(game.enemies)} total enemies.")

    # 2. Defeat the Mini-Boss and all enemies
    print("--- 2. Defeating Mini-Boss and verifying exit unlock ---")
    for enemy in game.enemies:
        enemy.health = 0
    
    # Update game loop to trigger car cleared logic
    game.update(0.016)
    assert len(game.enemies) == 0, "All enemies should be dead and removed"
    assert game.train_car.exit_unlocked is True, "Exit door must be unlocked"
    assert game.train_car.boon_pedestal_active is True, "Boon pedestal must become active"
    print("✓ Mini-boss defeated: Exit unlocked and boon pedestal active.")

    # 3. Approach Boon Pedestal & Trigger Upgrade Menu
    print("--- 3. Testing Upgrade Pedestal Interaction ---")
    game.player.pos = pygame.math.Vector2(game.train_car.boon_pedestal_pos)
    game.update(0.016)
    assert game.state == game.STATE_BOON_DRAFT, f"Expected STATE_BOON_DRAFT, got {game.state}"
    print("✓ Walking onto pedestal transitions game to STATE_BOON_DRAFT.")

    # 4. Test UpgradeMenu Rendering with all rarities (Common, Rare, Epic, LEGENDARY)
    print("--- 4. Testing UpgradeMenu rendering with Legendary boons (Regression Test for NameError) ---")
    legendary_boon = StokerSiphonBoon()
    assert legendary_boon.rarity == "Legendary", "StokerSiphonBoon must be Legendary"
    epic_boon = CombustionEngineBoon()
    common_boon = TungstenPiercingBoon()

    test_choices = [legendary_boon, epic_boon, common_boon]
    game.upgrade_menu.open(test_choices, owned_ids=set(), existing_boons=game.player.boons)

    # Render multiple frames to exercise the math.sin pulsing animation on the Legendary card
    test_surface = pygame.Surface((1280, 720))
    for _ in range(5):
        game.upgrade_menu.draw(test_surface)
        game.render()
    print("✓ Successfully rendered UpgradeMenu with Legendary, Epic, and Common cards without NameError!")

    # Also test with StaticDynamoBoon rolled as Legendary
    legendary_boon_2 = StaticDynamoBoon(rarity="Legendary")
    assert legendary_boon_2.rarity == "Legendary"
    game.upgrade_menu.open([legendary_boon_2, legendary_boon, epic_boon], owned_ids=set(), existing_boons=game.player.boons)
    for _ in range(5):
        game.upgrade_menu.draw(test_surface)
        game.render()
    print("✓ Successfully rendered UpgradeMenu with multiple Legendary cards.")

    # 5. Select a Boon
    print("--- 5. Selecting a Boon and returning to PLAYING state ---")
    game.player.add_boon(legendary_boon)
    game.train_car.boon_claimed = True
    game.state = game.STATE_PLAYING
    assert any(b.id == legendary_boon.id for b in game.player.boons), "Player should now have Legendary boon"
    print(f"✓ Player acquired: {legendary_boon.name} ({legendary_boon.rarity})")

    # 6. Walk through Exit Door to Car 6 (Freight Cargo Hold)
    print("--- 6. Transitioning to Car 6 (Freight & Cargo Hold) ---")
    game.player.pos = pygame.math.Vector2(game.train_car.width - 40, (game.train_car.top_wall_y + game.train_car.bottom_wall_y) // 2)
    game.update(0.016)
    
    assert game.run_manager.current_car_index == 5, f"Expected car index 5, got {game.run_manager.current_car_index}"
    car_info = game.run_manager.get_current_car_info()
    assert car_info["type"] == "cargo", f"Expected cargo car, got {car_info['type']}"
    assert len(game.enemies) > 0, "Car 6 must have spawned enemies"
    print(f"✓ Successfully transitioned to Car 6 ({car_info['name']}) with {len(game.enemies)} enemies!")

    # Render a frame in Car 6 to ensure full pipeline stability
    game.render()
    print("✓ Car 6 rendered flawlessly!")
    print("ALL MINI-BOSS AND UPGRADE TESTS PASSED!")

if __name__ == "__main__":
    test_miniboss_defeat_and_upgrade_draft()
