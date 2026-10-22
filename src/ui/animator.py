"""Procedural keyframe animation engine for Next Stop (2026).

Drives multi-frame skeletal *poses* for the player, enemies, and bosses without
any sprite sheets. A pose is just a dict of named float channels (hip sway, arm
swing, head bob, lean...). The sprite renderer reads those channels and offsets
the limbs it already draws procedurally.

Design notes
------------
* Pure Python, no pygame import: fully unit-testable headless and WebAssembly-safe.
* A ``Clip`` is authored as N evenly spaced keyframes (e.g. an 8-frame walk), but
  is sampled *continuously* with smooth interpolation, so motion is crisp at any
  display frame rate (60/120/144 FPS) instead of snapping between 8 poses.
* ``FrameAnimator`` is a small priority state machine with cross-fade blending:
  one-shot clips (hit, melee, dash, attack) interrupt looping ones (walk, idle).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

Pose = Dict[str, float]

# Every channel a renderer may read. Missing channels default to 0.0.
POSE_CHANNELS = (
    "hip_sway",      # horizontal torso shift (px, perpendicular to facing)
    "body_bob",      # vertical torso bob (px, +down)
    "head_bob",      # extra head vertical offset (px)
    "arm_l",         # left arm swing (px along facing)
    "arm_r",         # right arm swing (px along facing)
    "foot_l",        # left foot stride offset (px along facing)
    "foot_r",        # right foot stride offset (px along facing)
    "weapon_bob",    # weapon vertical offset (px)
    "lean",          # forward lean (px along facing)
    "squash",        # scale factor delta: +stretch / -squash (e.g. 0.08)
    "twist",         # torso rotation (radians)
    "blur",          # 0..1 motion-blur / streak intensity
    "glow",          # 0..1 aura / telegraph intensity
)


def _smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def _cosine(t: float) -> float:
    return 0.5 - 0.5 * math.cos(t * math.pi)


def lerp_pose(a: Pose, b: Pose, t: float) -> Pose:
    """Linearly blend two poses channel by channel."""
    out: Pose = {}
    for key in set(a) | set(b):
        va = a.get(key, 0.0)
        vb = b.get(key, 0.0)
        out[key] = va + (vb - va) * t
    return out


def neutral_pose() -> Pose:
    return {ch: 0.0 for ch in POSE_CHANNELS}


@dataclass
class Clip:
    """A named animation authored as evenly spaced keyframes.

    ``frames`` is the authored keyframe count. ``duration`` is the full clip
    length in seconds. Looping clips wrap the last frame back to the first.
    """
    name: str
    keyframes: List[Pose]
    duration: float
    loop: bool = True
    priority: int = 0          # higher interrupts lower
    blend_in: float = 0.08     # seconds to cross-fade into this clip

    @property
    def frames(self) -> int:
        return len(self.keyframes)

    def sample(self, t: float) -> Pose:
        """Sample the pose at normalized time ``t`` (0..1 for one pass)."""
        n = len(self.keyframes)
        if n == 0:
            return neutral_pose()
        if n == 1:
            return dict(self.keyframes[0])
        if self.loop:
            t = t % 1.0
            f = t * n
            i = int(f) % n
            j = (i + 1) % n
        else:
            t = max(0.0, min(1.0, t))
            f = t * (n - 1)
            i = min(int(f), n - 2)
            j = i + 1
        frac = f - int(f) if self.loop else f - i
        return lerp_pose(self.keyframes[i], self.keyframes[j], _cosine(frac))


# --------------------------------------------------------------------------- #
# Clip construction helpers
# --------------------------------------------------------------------------- #

def _cycle(frames: int, fn) -> List[Pose]:
    """Build ``frames`` keyframes by evaluating fn(phase) at even phases (0..2pi)."""
    return [fn(2.0 * math.pi * k / frames) for k in range(frames)]


def make_walk_clip(name: str, frames: int, duration: float, *, stride: float,
                   hip: float, bob: float, arm: float, head: float,
                   weapon: float = 0.0, lean: float = 0.0, priority: int = 10) -> Clip:
    """Procedural walk cycle: opposing arm/leg swing, double-time bob."""
    def pose(ph: float) -> Pose:
        s = math.sin(ph)
        return {
            "hip_sway": math.sin(ph) * hip,
            "body_bob": -abs(math.sin(ph)) * bob,      # lowest at foot plant
            "head_bob": -abs(math.sin(ph + 0.6)) * head,
            "foot_l": s * stride,
            "foot_r": -s * stride,
            "arm_l": -s * arm,
            "arm_r": s * arm,
            "weapon_bob": math.sin(ph * 2.0) * weapon,
            "lean": lean,
            "twist": s * 0.06,
        }
    return Clip(name, _cycle(frames, pose), duration, loop=True, priority=priority)


def make_idle_clip(name: str, frames: int, duration: float, *, breathe: float,
                   sway: float = 0.5, glow: float = 0.0, priority: int = 0) -> Clip:
    def pose(ph: float) -> Pose:
        return {
            "body_bob": math.sin(ph) * breathe,
            "head_bob": math.sin(ph - 0.5) * breathe * 0.6,
            "hip_sway": math.cos(ph) * sway,
            "arm_l": math.sin(ph) * 0.8,
            "arm_r": -math.sin(ph) * 0.8,
            "glow": (0.5 + 0.5 * math.sin(ph)) * glow,
        }
    return Clip(name, _cycle(frames, pose), duration, loop=True, priority=priority)


# --------------------------------------------------------------------------- #
# Clip libraries
# --------------------------------------------------------------------------- #

def build_player_clips() -> Dict[str, Clip]:
    """Player: 8f walk, 4f idle, 6f dash, 4f melee swing, 4f hit reaction."""
    walk = make_walk_clip("walk", 8, 0.62, stride=8.0, hip=1.6, bob=2.0,
                          arm=5.0, head=1.2, weapon=1.0, lean=2.0)
    idle = make_idle_clip("idle", 4, 2.4, breathe=1.5, sway=0.8)

    dash = Clip("dash", [
        {"lean": 1.0, "squash": 0.00, "blur": 0.0, "body_bob": 0.0},
        {"lean": 5.0, "squash": 0.10, "blur": 0.6, "body_bob": 1.0, "arm_l": -6, "arm_r": -6},
        {"lean": 8.0, "squash": 0.16, "blur": 1.0, "body_bob": 2.0, "arm_l": -8, "arm_r": -8,
         "foot_l": 7, "foot_r": -7},
        {"lean": 8.0, "squash": 0.16, "blur": 1.0, "body_bob": 2.0, "arm_l": -8, "arm_r": -8,
         "foot_l": -7, "foot_r": 7},
        {"lean": 5.0, "squash": 0.08, "blur": 0.5, "body_bob": 1.0},
        {"lean": 1.5, "squash": -0.04, "blur": 0.1, "body_bob": -0.5},
    ], duration=0.22, loop=False, priority=30, blend_in=0.02)

    melee = Clip("melee", [
        {"twist": -0.35, "lean": -3.0, "arm_r": -6, "weapon_bob": -2},      # wind-up
        {"twist": 0.05, "lean": 4.0, "arm_r": 8, "weapon_bob": 1, "blur": 0.6},  # strike
        {"twist": 0.40, "lean": 6.0, "arm_r": 10, "weapon_bob": 2, "blur": 0.9},  # follow-through
        {"twist": 0.10, "lean": 1.0, "arm_r": 2, "weapon_bob": 0},          # recover
    ], duration=0.22, loop=False, priority=20, blend_in=0.015)

    hit = Clip("hit", [
        {"lean": -6.0, "squash": -0.10, "body_bob": 2.0, "head_bob": 3.0, "twist": -0.15},
        {"lean": -4.0, "squash": -0.06, "body_bob": 1.5, "head_bob": 2.0, "twist": 0.10},
        {"lean": -2.0, "squash": -0.02, "body_bob": 0.5, "head_bob": 1.0},
        {"lean": 0.0},
    ], duration=0.28, loop=False, priority=40, blend_in=0.01)

    return {c.name: c for c in (walk, idle, dash, melee, hit)}


def build_enemy_clips() -> Dict[str, Clip]:
    """Enemies: 6f walk, 4f windup telegraph, 3f attack burst, 4f hit flinch."""
    walk = make_walk_clip("walk", 6, 0.70, stride=6.0, hip=1.4, bob=1.6,
                          arm=4.0, head=1.0, lean=1.0)
    idle = make_idle_clip("idle", 4, 2.0, breathe=1.2, sway=0.6)

    windup = Clip("windup", [
        {"lean": -2.0, "squash": -0.04, "glow": 0.2, "arm_r": -4},
        {"lean": -4.0, "squash": -0.08, "glow": 0.5, "arm_r": -7},
        {"lean": -5.0, "squash": -0.10, "glow": 0.8, "arm_r": -9, "body_bob": 1.0},
        {"lean": -5.0, "squash": -0.10, "glow": 1.0, "arm_r": -10, "body_bob": 1.5},
    ], duration=0.45, loop=False, priority=20, blend_in=0.04)

    attack = Clip("attack", [
        {"lean": 4.0, "squash": 0.10, "glow": 1.0, "arm_r": 9, "blur": 0.7},
        {"lean": 8.0, "squash": 0.16, "glow": 0.8, "arm_r": 12, "blur": 1.0},
        {"lean": 3.0, "squash": 0.02, "glow": 0.3, "arm_r": 4, "blur": 0.3},
    ], duration=0.18, loop=False, priority=25, blend_in=0.01)

    hit = Clip("hit", [
        {"lean": -4.0, "squash": -0.08, "twist": -0.12},
        {"lean": -2.0, "squash": -0.03, "twist": 0.06},
        {"lean": 0.0},
    ], duration=0.18, loop=False, priority=40, blend_in=0.01)

    return {c.name: c for c in (walk, idle, windup, attack, hit)}


def build_boss_clips() -> Dict[str, Clip]:
    """Bosses: continuous idle sway plus a phase-2 rage aura pulse."""
    idle = make_idle_clip("idle", 6, 3.0, breathe=2.0, sway=1.4)
    rage = make_idle_clip("rage", 6, 0.9, breathe=2.6, sway=2.0, glow=1.0, priority=5)
    return {"idle": idle, "rage": rage}


# --------------------------------------------------------------------------- #
# The animator
# --------------------------------------------------------------------------- #

@dataclass
class FrameAnimator:
    """Plays clips, blends between them, and exposes the current ``pose``.

    Typical use (player)::

        anim = FrameAnimator(build_player_clips())
        anim.update(dt, locomotion="walk" if moving else "idle", speed_scale=speed/base)
        if dashed:  anim.play("dash")
        pose = anim.pose
    """
    clips: Dict[str, Clip]
    default: str = "idle"

    current: Optional[Clip] = field(default=None, init=False)
    _time: float = field(default=0.0, init=False)         # seconds into current clip
    _prev_pose: Pose = field(default_factory=neutral_pose, init=False)
    _blend_t: float = field(default=1.0, init=False)      # 0 -> just switched, 1 -> done
    _blend_dur: float = field(default=0.0, init=False)
    pose: Pose = field(default_factory=neutral_pose, init=False)
    finished: bool = field(default=False, init=False)

    def __post_init__(self):
        if self.default in self.clips:
            self.current = self.clips[self.default]
            self.pose = self.current.sample(0.0)

    # -- control ----------------------------------------------------------- #
    def play(self, name: str, *, force: bool = False) -> bool:
        """Start a clip. Lower-priority requests never interrupt a running one-shot
        unless ``force`` is set. Returns True if the clip actually started."""
        clip = self.clips.get(name)
        if clip is None:
            return False
        cur = self.current
        if cur is clip and clip.loop:
            return False
        if (cur is not None and not self.finished and not cur.loop
                and clip.priority < cur.priority and not force):
            return False
        self._switch(clip)
        return True

    def _switch(self, clip: Clip):
        self._prev_pose = dict(self.pose)
        self._blend_dur = clip.blend_in
        self._blend_t = 0.0 if clip.blend_in > 0 else 1.0
        self.current = clip
        self._time = 0.0
        self.finished = False

    def is_playing(self, name: str) -> bool:
        return (self.current is not None and self.current.name == name
                and not self.finished)

    # -- per-frame --------------------------------------------------------- #
    def update(self, dt: float, locomotion: Optional[str] = None,
               speed_scale: float = 1.0) -> Pose:
        """Advance time. ``locomotion`` names the looping clip to fall back to
        once any one-shot has finished (e.g. "walk" or "idle")."""
        if self.current is None:
            return self.pose

        clip = self.current
        self._time += dt * max(0.0, speed_scale if clip.loop else 1.0)

        if not clip.loop and self._time >= clip.duration:
            self.finished = True
            self._time = clip.duration

        # Return to locomotion once a one-shot ends (or switch walk <-> idle).
        if locomotion and locomotion in self.clips:
            if self.finished:
                self._switch(self.clips[locomotion])
                clip = self.current
            elif clip.loop and clip.name != locomotion:
                # Looping clips are locomotion-level: swap freely (walk <-> idle).
                self._switch(self.clips[locomotion])
                clip = self.current

        t = (self._time / clip.duration) if clip.duration > 0 else 1.0
        target = clip.sample(t)

        if self._blend_t < 1.0:
            self._blend_t = min(1.0, self._blend_t + (dt / self._blend_dur if self._blend_dur > 0 else 1.0))
            target = lerp_pose(self._prev_pose, target, _smoothstep(self._blend_t))

        self.pose = target
        return self.pose

    # -- convenience ------------------------------------------------------- #
    def get(self, channel: str) -> float:
        return self.pose.get(channel, 0.0)
