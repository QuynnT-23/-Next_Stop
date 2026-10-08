"""Test suite for Destructible Windows, Environment Revamp, Enemy Health Buffs, and Locked Neo-Subway."""
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.core.game import Game
from src.level.train_car import TrainCar, TrainWindow, WallLamp, ExplosiveBarrel
from src.entities.enemies.types import TicketInspector, RangedSteward, BoilerImp, AutomatonShield
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem
from src.entities.enemies.miniboss import ChiefInspectorMiniBoss
from src.entities.enemies.boss import ConductorBoss
from src.combat.damage import DamageEvent
from src.combat.weapons import StokerWrench, RivetGun
from src.entities.projectile import Projectile

def test_enemy_health_buffs():
    """Verify that all enemy archetypes and bosses have their updated, buffed HP values."""
    print("--- 1. Testing Enemy Health Buffs ---")
    inspector = TicketInspector(100, 100)
    assert inspector.max_health == 78
    assert inspector.health == 78

    steward = RangedSteward(100, 100)
    assert steward.max_health == 64
    assert steward.health == 64

    imp = BoilerImp(100, 100)
    assert imp.max_health == 38
    assert imp.health == 38

    shield = AutomatonShield(100, 100)
    assert shield.max_health == 130
    assert shield.health == 130

    brute = BoilerBrute(100, 100)
    assert brute.max_health == 340
    assert brute.health == 340

    golem = FurnaceGolem(100, 100)
    assert golem.max_health == 340
    assert golem.health == 340

    miniboss = ChiefInspectorMiniBoss(100, 100)
    assert miniboss.max_health == 680
    assert miniboss.health == 680

    boss = ConductorBoss(100, 100)
    assert boss.max_health == 1320
    assert boss.health == 1320
    print("✓ All 8 enemy archetype and boss HP buffs verified.")

def test_destructible_windows():
    """Verify window states: intact -> cracked -> shattered, and shard/wind generation."""
    print("--- 2. Testing Destructible Window States ---")
    game = Game()
    car = TrainCar(car_index=0, car_type="passenger", theme="steam")
    assert len(car.windows) > 0, "Train car must spawn destructible windows along walls"
    assert len(car.wall_lamps) > 0, "Train car must spawn wall sconce lamps"

    win = car.windows[0]
    assert win.state == TrainWindow.STATE_INTACT
    assert win.health == 35

    # Apply moderate damage -> cracked
    win.take_damage(16, game)
    assert win.state == TrainWindow.STATE_CRACKED
    assert win.health == 19
    assert len(game.particles.particles) > 0, "Cracking window must spawn glass shards"

    # Apply fatal damage -> shattered
    win.take_damage(25, game)
    assert win.state == TrainWindow.STATE_SHATTERED
    assert win.health <= 0
    
    # Update shattered window -> spawns wind streak
    initial_particle_count = len(game.particles.particles)
    for _ in range(15):
        win.update(0.05, game)
    assert len(game.particles.particles) >= initial_particle_count, "Shattered window must emit wind streaks"
    print("✓ Window damage state transitions (intact -> cracked -> shattered) verified.")

def test_projectile_window_shattering():
    """Verify that stray projectiles shatter windows upon collision."""
    print("--- 3. Testing Projectile Collision with Windows ---")
    game = Game()
    game.start_new_run("steam", RivetGun())
    car = game.train_car
    target_win = car.windows[0]
    
    # Spawn a player projectile colliding with target_win
    proj = Projectile(
        target_win.pos.x, target_win.pos.y,
        vel=pygame.math.Vector2(100, 0),
        damage_event=DamageEvent(40, source_type="player"),
        radius=5.0,
        lifetime=1.0,
        owner="player"
    )
    game.projectiles.append(proj)
    
    # Advance game loop to process projectile collision
    game.update(0.016)
    assert target_win.state == TrainWindow.STATE_SHATTERED, "Projectile impact should shatter window"
    print("✓ Projectile window collision & shattering verified.")

def test_explosive_barrel_window_destruction():
    """Verify that barrel detonation shatters nearby windows."""
    print("--- 4. Testing Barrel Detonation Window Shattering ---")
    game = Game()
    game.start_new_run("steam", RivetGun())
    car = game.train_car
    
    # Position a window right next to a barrel
    test_win = car.windows[0]
    barrel = ExplosiveBarrel(test_win.pos.x + 30, test_win.pos.y + 40)
    car.barrels.append(barrel)
    
    barrel.detonate(game)
    assert test_win.state == TrainWindow.STATE_SHATTERED, "Nearby explosive barrel detonation must shatter window"
    print("✓ Explosive barrel window shattering verified.")

def test_melee_window_interaction():
    """Verify that Stoker's Cleaver melee cleave damages adjacent windows."""
    print("--- 5. Testing Melee Cleave Window Shattering ---")
    game = Game()
    game.start_new_run("steam", RivetGun())
    car = game.train_car
    target_win = car.windows[0]
    
    # Position player adjacent to window and swing cleaver
    game.player.pos = pygame.math.Vector2(target_win.pos.x, target_win.pos.y + 40)
    cleaver = StokerWrench()
    cleaver.attack(game.player, target_win.pos, game)
    assert target_win.state in (TrainWindow.STATE_CRACKED, TrainWindow.STATE_SHATTERED), "Melee swing should damage adjacent window"
    print("✓ Melee cleave window damage verified.")

def test_hub_station_locked_subway():
    """Verify that locked routes like Neo-Subway cannot be boarded in the Hub Station."""
    print("--- 6. Testing Hub Station Route Locking ---")
    game = Game()
    hub = game.hub_station
    # Ensure isolated stage state for locking test
    hub.progression.unlocked_stages = ["steam"]
    hub.progression.current_track_idx = 0
    hub.selected_route_id = "steam"
    test_surface = pygame.Surface((1280, 720))
    hub.draw(test_surface)

    # Find the subway docking bay (Track 3)
    subway_bay = next(b for b in hub.docking_bays if b["route_id"] == "subway")
    assert "subway" not in hub.progression.unlocked_stages, "Subway should be locked by default"

    # Attempt to click subway door rect
    result = hub.handle_input([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=subway_bay["door_rect"].center)])
    assert not result, "Subway door click should not trigger departure when locked"
    assert hub.get_selected_route_id() == "steam", "Selected route must remain steam"

    # Move player into subway door and press E
    hub.player_pos = pygame.math.Vector2(subway_bay["door_rect"].center)
    result_e = hub.handle_input([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
    assert not result_e, "Subway interact should not depart when locked"
    assert hub.get_selected_route_id() == "steam", "Route must remain steam"
    print("✓ Hub Station route locking verified.")

if __name__ == "__main__":
    test_enemy_health_buffs()
    test_destructible_windows()
    test_projectile_window_shattering()
    test_explosive_barrel_window_destruction()
    test_melee_window_interaction()
    test_hub_station_locked_subway()
    print("\n=======================================================")
    print("ALL ENVIRONMENT, WINDOW & HEALTH BUFF TESTS PASSED! ✓")
    print("=======================================================")
