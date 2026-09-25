"""Headless automated sanity and integration test suite."""
import os
import sys

# Ensure headless dummy video and audio for headless CI / testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from src.core.game import Game
from src.combat.weapons import RivetGun, StokerWrench, CoalScattergun, TeslaArcCaster
from src.combat.boons import (
    TeslaCoilBoon, SteamOverdriveDashBoon, TungstenPiercingBoon,
    KineticPlatingBoon, StokerSiphonBoon, LocomotiveGreaseBoon,
    ExplosiveShrapnelBoon, MoltenCoreBoon, CryoCondenserBoon,
    get_random_boon_choices
)
from src.combat.damage import DamageEvent
from src.entities.enemies.boss import ConductorBoss
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem, ShockwaveRing
from src.level.train_car import ExplosiveBarrel, SupplyCrate

def run_tests():
    print("--- 1. Initializing Pygame in Headless Mode ---")
    pygame.init()
    game = Game(headless=True)
    assert game.screen is not None
    assert game.state == Game.STATE_HUB
    print("✓ Game headless initialization passed.")

    print("--- 2. Testing Route & Weapon Selection (Hub State) ---")
    hub = game.hub_station
    test_surface = pygame.Surface((1280, 720))
    hub.draw(test_surface)  # Populate rects
    
    # Verify mouse clicks on route tabs (Subway is locked as special server event)
    assert len(hub.route_tab_rects) >= 2, "Hub should have route tab rects populated"
    subway_tab_center = hub.route_tab_rects[1].center
    hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=subway_tab_center)])
    assert hub.get_selected_route_id() == "steam", "Clicking locked route should remain on steam"
    
    iron_tab_center = hub.route_tab_rects[0].center
    hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=iron_tab_center)])
    assert hub.get_selected_route_id() == "steam", "Clicking first route tab should select steam"

    # Verify mouse clicks on weapon cards
    assert len(hub.weapon_card_rects) >= 4, "Hub should have 4 weapon card rects"
    card2_center = hub.weapon_card_rects[1].center
    hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=card2_center)])
    assert hub.selected_weapon_idx == 1, "Clicking weapon card 2 should select it"

    # Reset back to RivetGun (index 0)
    card1_center = hub.weapon_card_rects[0].center
    hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=card1_center)])
    assert hub.selected_weapon_idx == 0, "Clicking weapon card 1 should select RivetGun"

    # Verify mouse click on 'ALL ABOARD' button to launch run
    board_clicked = hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=hub.board_btn_rect.center)])
    assert board_clicked is True, "Clicking board button should return True"

    route_id = hub.get_selected_route_id()
    weapon = hub.get_selected_weapon()
    assert route_id == "steam"
    assert isinstance(weapon, RivetGun)
    game.start_new_run(route_id, weapon)
    assert game.state == Game.STATE_PLAYING
    assert game.player is not None
    assert game.player.health == 100
    assert len(game.enemies) > 0
    print(f"✓ Hub Station mouse navigation verified. Run started: Route '{route_id}', Weapon '{weapon.name}', {len(game.enemies)} enemies spawned.")

    print("--- 3. Testing Spacebar Attack & Double-Tap Directional Dashing ---")
    # Test Spacebar Attack
    space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    game.input_handler.process_events([space_event])
    assert game.input_handler.attack_pressed, "Spacebar must trigger attack_pressed"
    assert game.input_handler.attack_held, "Spacebar must trigger attack_held"
    
    # Test Double-Tap 'D' (Right) to Dash
    d_tap1 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)
    game.input_handler.process_events([d_tap1])
    assert not game.input_handler.dash_pressed, "First tap should not trigger dash"
    
    d_tap2 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d)
    game.input_handler.process_events([d_tap2])
    assert game.input_handler.dash_pressed, "Double-tapping 'D' within threshold must trigger dash"
    assert game.input_handler.dash_dir_override == pygame.math.Vector2(1, 0), "Double-tap 'D' must dash right"
    
    # Update game to process the double-tap dash
    game.update(0.016)
    assert game.player.is_dashing, "Player should enter dashing state from double-tap"
    print("✓ Spacebar attack and double-tap directional dashing verified.")

    print("--- 4. Testing Combat, Projectiles, and Damage Events ---")
    target_pos = game.enemies[0].pos
    game.input_handler.mouse_world_pos = target_pos
    game.input_handler.attack_held = True
    game.input_handler.attack_pressed = True
    game.update(0.016)
    assert len(game.projectiles) > 0, "Weapon attack should spawn projectiles"
    print(f"✓ Weapon fired: {len(game.projectiles)} active projectiles.")

    # Direct damage test
    first_enemy = game.enemies[0]
    initial_enemy_hp = first_enemy.health
    dmg_event = DamageEvent(20, source_type="player", damage_type="normal", is_crit=True)
    first_enemy.take_damage(dmg_event, game)
    assert first_enemy.health < initial_enemy_hp, "Enemy health should decrement on damage"
    assert len(game.particles.damage_numbers) > 0, "Damage number popup should spawn"
    print(f"✓ Combat damage: enemy HP reduced from {initial_enemy_hp} to {first_enemy.health}")

    print("--- 5. Testing Boon Leveling, Stacking & Evolutions ---")
    tesla = TeslaCoilBoon()
    assert tesla.level == 1
    assert tesla.chain_count == 2
    
    # Add to player
    game.player.add_boon(tesla)
    assert len(game.player.boons) == 1
    
    # Upgrade to Level 2
    tesla_upgrade_card = TeslaCoilBoon()
    game.player.add_boon(tesla_upgrade_card)
    assert tesla.level == 2, "Adding duplicate boon must increment existing level"
    assert tesla.chain_count == 4, "Level 2 Tesla must chain to 4 targets"
    
    # Upgrade to Level 3 (Evolution)
    game.player.add_boon(TeslaCoilBoon())
    assert tesla.level == 3
    assert tesla.chain_count == 6
    assert tesla.is_max_level()
    print("✓ Boon leveling up to Tier 3 Evolution verified.")

    print("--- 6. Testing Brute Enemy (BoilerBrute) & Expanding Shockwaves ---")
    brute = BoilerBrute(400, 300)
    initial_brute_hp = brute.health
    assert initial_brute_hp == 250
    # Test armor reduction
    brute.take_damage(DamageEvent(100, source_type="player"), game)
    assert brute.health == 250 - 80, "Brute 20% passive armor should reduce 100 dmg to 80"
    
    # Test Shockwave
    shockwave = ShockwaveRing(400, 300, max_radius=200, speed=300, damage=20)
    game.shockwaves.append(shockwave)
    assert len(game.shockwaves) > 0
    game.update(0.016)
    assert shockwave.radius > 20.0
    print("✓ BoilerBrute armor and expanding shockwave verified.")

    print("--- 7. Testing Interactive Props, Crates & Timed Overcharge Boost ---")
    barrel = ExplosiveBarrel(500, 300)
    game.train_car.barrels.append(barrel)
    # Shoot barrel
    barrel.take_damage(DamageEvent(10, source_type="player"), game)
    assert barrel.is_dead, "Barrel must detonate on hit"
    print("✓ Explosive barrel detonation verified.")

    # Test Supply Crate Overcharge timed buff
    orig_fire_rate = game.player.weapon.fire_rate
    from src.level.train_car import PickupItem
    pickup = PickupItem(game.player.pos.x, game.player.pos.y, item_type="overcharge")
    pickup.update(game.player, game)
    assert game.player.attack_boost_timer == 8.0, "Overcharge pickup must grant 8.0s duration"
    assert game.player.weapon.get_effective_fire_rate(game.player) < orig_fire_rate, "Boosted fire rate should be faster"
    assert game.player.weapon.fire_rate == orig_fire_rate, "Base fire rate must not be permanently modified"
    # Test cap
    game.player.apply_attack_boost(8.0)
    assert game.player.attack_boost_timer == 12.0, "Boost timer must cap at 12.0s"
    # Test expiration
    game.input_handler.attack_held = False
    game.input_handler.attack_pressed = False
    game.input_handler.move_dir = pygame.math.Vector2(0, 0)
    game.player.vel = pygame.math.Vector2(0, 0)
    game.player.pos = pygame.math.Vector2(100, 360)
    for _ in range(125):
        game.player.update(0.1, game.input_handler, game.train_car, game)
    game.player.pos = pygame.math.Vector2(100, 360)
    game.player.vel = pygame.math.Vector2(0, 0)
    assert game.player.attack_boost_timer == 0.0, "Timer must expire back to 0.0"
    assert game.player.weapon.get_effective_fire_rate(game.player) == orig_fire_rate, "Weapon stats must revert after timer"
    print("✓ Timed Overcharge attack boost, stacking cap, and expiration verified.")

    print("--- 8. Testing Cold Storage Car & Reduced Friction ---")
    cold_car = game.run_manager.create_current_car()
    cold_car.car_type = "cold_storage"
    game.train_car = cold_car
    game.update(0.016)
    assert game.player.friction == 350.0, "Cold storage car must reduce friction for ice drift"
    print("✓ Cold Storage car ice drift friction verified.")

    print("--- 9. Testing Car Progression & Room Cleared State ---")
    for enemy in game.enemies:
        enemy.health = 0
        enemy.die(game)
    game.update(0.016)
    assert len(game.enemies) == 0
    assert game.train_car.exit_unlocked, "Train car exit door should unlock when all enemies die"
    assert game.train_car.boon_pedestal_active, "Boon pedestal should activate"

    # Test walking to the exit door trigger
    old_car_idx = game.run_manager.current_car_index
    door_mid_y = (game.train_car.top_wall_y + game.train_car.bottom_wall_y) // 2
    game.player.pos = pygame.math.Vector2(game.train_car.width - 90, door_mid_y)
    assert game.train_car.can_player_exit(game.player.pos, game.player.radius)
    game.update(0.016)
    assert game.run_manager.current_car_index == old_car_idx + 1
    assert len(game.enemies) > 0
    print(f"✓ Walking into doorway advanced to Car {game.run_manager.current_car_index + 1}: {game.run_manager.get_current_car_info()['name']}")

    print("--- 10. Testing Full 10-Car Route Progression, Mini-Boss & Hazards ---")
    # Start Iron Express
    game.start_new_run("steam", RivetGun())
    assert game.run_manager.total_cars == 10, "The Iron Express must now have 10 cars"

    for car_idx in range(10):
        car_info = game.run_manager.get_current_car_info()
        print(f"  Testing Car {car_idx + 1}/10: {car_info['name']} ({car_info['type']})")
        assert len(game.enemies) > 0

        # Car 5: Check Chief Ticket Inspector Mini-Boss
        if car_idx == 4:
            from src.entities.enemies.miniboss import ChiefInspectorMiniBoss
            miniboss = next((e for e in game.enemies if isinstance(e, ChiefInspectorMiniBoss)), None)
            assert miniboss is not None, "Car 5 must spawn ChiefInspectorMiniBoss"
            assert miniboss.health == 520
            # Test Phase 2 transition (accounting for 25% passive armor)
            miniboss.take_damage(DamageEvent(360, source_type="player"), game)
            assert miniboss.phase == 2, "Chief Inspector must enter Phase 2 at < 50% HP"
            print("    ✓ Chief Ticket Inspector Mini-Boss verified (Phase 2 enrage active).")

        # Car 7: Check Observation Deck Headwinds
        if car_idx == 6:
            orig_px = game.player.pos.x
            game.update(0.1)
            assert game.player.pos.x < orig_px, "Observation Deck must apply leftward headwind force"
            print("    ✓ Observation Deck aerodynamic headwinds verified.")

        # Car 9: Check Furnace Tender Hot Coals
        if car_idx == 8:
            assert len(game.train_car.hot_coals) > 0, "Furnace Tender must have hot coals"
            game.player.pos = pygame.math.Vector2(game.train_car.hot_coals[0].centerx, game.train_car.hot_coals[0].centery)
            orig_hp = game.player.health
            game.update(0.1)
            assert game.player.health < orig_hp, "Stepping on hot coals must deal fire damage"
            print("    ✓ Furnace Tender hot coal hazard damage verified.")

        # If not final car, clear enemies and advance
        if car_idx < 9:
            for enemy in game.enemies:
                enemy.health = 0
                enemy.die(game)
            game.update(0.016)
            assert game.train_car.exit_unlocked
            game.load_next_train_car()

    print("--- 11. Testing Locomotive Final Boss Defeat & Instant Victory Sequence ---")
    assert game.run_manager.is_final_car(), "Must be in final Locomotive Engine car"
    boss = game.enemies[0]
    assert isinstance(boss, ConductorBoss), "Final car must spawn ConductorBoss"
    
    # Kill the boss
    boss.health = 0
    boss.die(game)
    assert not game.train_car.exit_unlocked, "Engine room must NEVER unlock an exit door"
    assert not game.train_car.boon_pedestal_active, "Engine room must NEVER spawn a boon pedestal"

    # Update for transition timer duration (1.2s)
    for _ in range(80):
        game.update(0.02)
    assert game.state == Game.STATE_VICTORY, "Game must transition to STATE_VICTORY after Conductor defeat"
    # Verify victory overlay rendering executes cleanly
    game.render()
    print("✓ Boss defeat triggered immediate dramatic Victory sequence and overlay rendered cleanly.")

    print("--- 12. Testing Victory Return-to-Station Loop ---")
    # Press Space to return to station hub
    space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    game.handle_events_custom = True
    # Test Space event
    game.input_handler.process_events([])
    game.state in (Game.STATE_VICTORY,)
    # Simulate event directly in game.handle_events queue or mock event
    pygame.event.post(space_event)
    game.handle_events()
    assert game.state == Game.STATE_HUB, "Pressing Space on Victory screen must return to Hub Station"
    print("✓ Victory loop successfully returned player to Grand Central Terminal Hub!")

    print("--- 13. Testing Frame Rendering Across States ---")
    for _ in range(10):
        game.update(0.016)
        game.render()
    print("✓ Frame rendering executed without exceptions.")

    print("\n===========================================")
    print("ALL 13 SANITY & INTEGRATION SUITES PASSED! ✓")
    print("===========================================")

if __name__ == "__main__":
    run_tests()
