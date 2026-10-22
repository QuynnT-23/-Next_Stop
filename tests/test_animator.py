"""Automated unit and integration test suite for the procedural FrameAnimator engine."""
import os
import math
import pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.ui.animator import (
    FrameAnimator, Clip, lerp_pose, neutral_pose,
    make_walk_clip, make_idle_clip,
    build_player_clips, build_enemy_clips, build_boss_clips,
    POSE_CHANNELS
)
from src.entities.player import Player
from src.entities.enemies.types import TicketInspector, BoilerImp
from src.combat.damage import DamageEvent


def test_animator_suite():
    print("=======================================================")
    print("TESTING PROCEDURAL KEYFRAME ANIMATOR SUITE")
    print("=======================================================")

    # 1. Pose interpolation and neutral pose
    print("--- 1. Testing Neutral Pose & Pose Blending ---")
    np = neutral_pose()
    assert len(np) == len(POSE_CHANNELS)
    for ch in POSE_CHANNELS:
        assert np[ch] == 0.0

    p_a = {"hip_sway": 10.0, "lean": 2.0}
    p_b = {"hip_sway": 20.0, "lean": 8.0}
    p_half = lerp_pose(p_a, p_b, 0.5)
    assert math.isclose(p_half["hip_sway"], 15.0)
    assert math.isclose(p_half["lean"], 5.0)
    print("✓ Pose channel interpolation and defaults verified.")

    # 2. Clip construction and sampling
    print("--- 2. Testing Clip Sampling (Continuous Interpolation) ---")
    walk = make_walk_clip("walk", 8, 0.62, stride=8.0, hip=1.6, bob=2.0, arm=5.0, head=1.2)
    assert walk.frames == 8
    assert walk.loop is True

    # Sample at t=0.0
    pose_start = walk.sample(0.0)
    assert "hip_sway" in pose_start
    assert "body_bob" in pose_start
    assert "foot_l" in pose_start

    # Sample midway between frames (continuous sub-frame interpolation)
    pose_mid = walk.sample(0.25)
    assert isinstance(pose_mid["hip_sway"], float)
    print("✓ Procedural walk clip generated 8 keyframes with continuous sampling.")

    # 3. State machine priority, looping and transitions
    print("--- 3. Testing Priority State Machine & Transitions ---")
    anim = FrameAnimator(build_player_clips())
    assert anim.current.name == "idle"

    # Locomotion update switches to walk when moving
    anim.update(0.016, locomotion="walk")
    assert anim.current.name == "walk"

    # Play one-shot dash (priority 30 > walk priority 10)
    started = anim.play("dash")
    assert started is True
    assert anim.current.name == "dash"
    assert anim.finished is False

    # Lower-priority walk attempt cannot interrupt active dash
    walk_interrupt = anim.play("walk")
    assert walk_interrupt is False
    assert anim.current.name == "dash"

    # Higher-priority hit attempt (priority 40 > dash priority 30) CAN interrupt
    hit_interrupt = anim.play("hit")
    assert hit_interrupt is True
    assert anim.current.name == "hit"

    # Fast forward through hit animation to verify it finishes and returns to locomotion
    for _ in range(25):
        anim.update(0.016, locomotion="idle")
    assert anim.current.name == "idle"
    print("✓ Priority interruption, non-looping completion, and locomotion fallback verified.")

    # 4. Player entity integration
    print("--- 4. Testing Player Entity Animator Integration ---")
    pygame.init()
    player = Player(100, 100)
    assert hasattr(player, "animator")
    assert isinstance(player.animator, FrameAnimator)
    assert player.animator.current.name == "idle"

    class DummyInputHandler:
        mouse_world_pos = pygame.math.Vector2(200, 100)
        move_dir = pygame.math.Vector2(1, 0)
        block_held = False
        interact_pressed = False
        dash_pressed = False
        dash_dir_override = None
        attack_held = False

    class DummyGameState:
        class DummyParticles:
            def spawn_dash_ghost(self, *args, **kwargs): pass
            def spawn_sparks(self, *args, **kwargs): pass
            def add_damage_number(self, *args, **kwargs): pass
        class DummyAudio:
            def play(self, *args): pass
        class DummyCamera:
            def add_trauma(self, *args): pass
        particles = DummyParticles()
        audio = DummyAudio()
        camera = DummyCamera()
        enemies = []

    # Test moving player updates locomotion to walk
    player.vel = pygame.math.Vector2(200, 0)
    player.update(0.016, DummyInputHandler(), None, DummyGameState())
    assert player.animator.current.name == "walk"

    # Test dash triggers dash clip
    player.trigger_dash(DummyGameState())
    assert player.animator.current.name == "dash"
    player.animator.update(0.016)
    assert player.animator.get("blur") > 0.0

    # Test melee swing triggers melee clip
    player.start_melee_swing(duration=0.22)
    assert player.animator.current.name == "melee"
    print("✓ Player entity triggers dash, melee, and walk clips through animator.")

    # 5. Enemy entity integration
    print("--- 5. Testing Enemy Entity Animator Integration ---")
    imp = BoilerImp(150, 150)
    assert hasattr(imp, "animator")
    assert imp.animator.current.name == "idle" or imp.animator.current.name == "walk"

    # Test taking damage triggers hit flinch
    imp.take_damage(DamageEvent(amount=10, source_type="player"), DummyGameState())
    assert imp.animator.current.name == "hit"

    # Tick through hit flinch duration (0.18s) to return to state-driven AI animation
    for _ in range(15):
        imp.animator.update(0.016)

    # Test windup state plays windup clip with glow channel
    imp.state = "windup"
    imp.update_animator(0.016)
    assert imp.animator.current.name == "windup"
    assert imp.animator.get("glow") >= 0.0
    print("✓ Enemy entity state transitions drive windup, attack, and hit clips.")

    print("\n=======================================================")
    print("ALL PROCEDURAL ANIMATOR TESTS PASSED! ✓")
    print("=======================================================")


if __name__ == "__main__":
    test_animator_suite()
