"""Automated test suite verifying Chud Studios branding, Lil' Chud splash screen, and WebAssembly compatibility."""
import os
import sys
import asyncio

# Set headless dummy drivers for SDL
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from src.config import TITLE, SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.game import Game
from src.core.sound import SoundManager
from src.ui.splash_screen import SplashScreen, SmokePuff

def test_splash_screen_unit():
    print("--- 1. Testing SplashScreen Unit Lifecycle & Lil' Chud Mascot ---")
    pygame.init()
    sound_mgr = SoundManager()
    splash = SplashScreen(sound_mgr)
    
    assert not splash.finished
    assert splash.duration == 3.2
    assert splash.click_squish == 0.0
    
    # 1. Update timer and verify boing and whistle sound cues trigger
    for _ in range(10):
        splash.update(0.03)  # Reaches 0.3s
    assert splash.played_boing, "Boing sound should trigger at timer >= 0.2s"
    
    for _ in range(30):
        splash.update(0.03)  # Reaches 1.2s
    assert splash.played_whistle, "Whistle sound should trigger at timer >= 1.0s"
    
    # 2. Smoke puffs should generate between 0.4s and 2.8s
    assert len(splash.smoke_puffs) > 0, "Smoke puffs should be actively spawned from smokestack"
    
    # 3. Render Lil' Chud to headless surface
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    splash.draw(surf)
    print("✓ Lil' Chud mascot and banner rendered cleanly to surface.")
    
    # 4. Interactive skip via Space key
    space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    result = splash.handle_input([space_event])
    assert result is True
    assert splash.finished is True
    print("✓ Splash screen skip interaction verified.")

def test_sound_effects_synthesis():
    print("--- 2. Testing Procedural Sound Synthesis for Chud Studios ---")
    sound_mgr = SoundManager()
    assert 'boing' in sound_mgr.sounds, "SoundManager must contain 'boing' sound effect"
    assert 'whistle' in sound_mgr.sounds, "SoundManager must contain 'whistle' sound effect"
    
    # Test playing without exceptions
    sound_mgr.play('boing')
    sound_mgr.play('whistle')
    print("✓ Cartoon 'boing' and 'whistle' sound synthesis verified.")

def test_game_states_and_headless_bypass():
    print("--- 3. Testing Game Headless Bypass & Splash Startup Flow ---")
    # Headless game should bypass splash straight to HUB
    game_headless = Game(headless=True)
    assert game_headless.state == Game.STATE_HUB, "Headless game must default to STATE_HUB for CI test suites"
    
    # Non-headless game should default to STATE_SPLASH
    game_normal = Game(headless=False)
    assert game_normal.state == Game.STATE_SPLASH, "Normal game must start on STATE_SPLASH"
    
    # Simulate splash screen completion in game_normal
    game_normal.splash_screen.finish()
    game_normal.update(0.1)
    assert game_normal.state == Game.STATE_HUB, "Game must transition to STATE_HUB once splash screen finishes"
    print("✓ Headless bypass and splash-to-hub transition verified.")

def test_branding_constants_and_hub_plaque():
    print("--- 4. Testing Studio Branding & Hub Station Plaque ---")
    assert "Chud Studios" in TITLE, f"Window title '{TITLE}' must mention Chud Studios"
    
    game = Game(headless=True)
    hub_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    game.hub_station.draw(hub_surf)
    print(f"✓ Window Title verified: '{TITLE}'")
    print("✓ Grand Central Terminal Chud Studios brass production plaque rendered.")

def test_async_webassembly_loop():
    print("--- 5. Testing Async WebAssembly Game Loop (run_async) ---")
    game = Game(headless=True)
    
    async def run_briefly():
        # Stop game after 2 frames
        async def stop_soon():
            await asyncio.sleep(0.01)
            game.running = False
            
        asyncio.create_task(stop_soon())
        await game.run_async()
        
    asyncio.run(run_briefly())
    assert game.running is False
    print("✓ Dual-mode run_async() coroutine executed smoothly without blocking.")

if __name__ == "__main__":
    test_splash_screen_unit()
    test_sound_effects_synthesis()
    test_game_states_and_headless_bypass()
    test_branding_constants_and_hub_plaque()
    test_async_webassembly_loop()
    print("\n=======================================================")
    print("ALL CHUD STUDIOS & WEBASSEMBLY TESTS PASSED! ✓")
    print("=======================================================")
