# Next Stop (2026): Locomotive Oblivion 🚂💥

A fast-paced, top-down runaway train action roguelite dungeon crawler inspired by **Hades** and **Archero**, built with **Python 3.13** and **Pygame-CE** (Community Edition).

Created as an educational and playable pair-programming project demonstrating real-world Computer Science and Game Engineering patterns.

---

## 🎮 How to Play

### Launching the Game
Activate the virtual environment and start the game:
```bash
source .venv/bin/activate
python3 main.py
```

### Controls
| Input | Action |
| :--- | :--- |
| **W, A, S, D** or **Arrow Keys** | Move in 8 directions (with smooth momentum & friction) |
| **Double-Tap W, A, S, or D** | **Instant Directional Dash** (High-speed burst with i-frames) |
| **Spacebar** / **Left Mouse Click** | **Attack** (Fire ranged rivet/plasma or swing melee wrench) |
| **Mouse Cursor** | Aim weapon (360° precision) |
| **Left Shift** / **Right Mouse Click** | Alternate Dash shortcut |
| **E** | Interact (Claim Boon Pedestal, open bulkhead doors) |
| **1, 2, 3, 4** | Select starter weapon at Hub, or draft Boons [1-3] |
| **Q / E** or **< / >** | Switch train routes at Grand Central Hub |
| **Escape / P** | Pause game |
| **R** | Return to Grand Central Station after Victory or Run Over |

---

## 🧭 Gameplay Overview

1. **Grand Central Station (Hub Menu)**:
   - **Choose Route**:
     - *The Iron Express*: Classical steam locomotive with brass coaches, velvet dining cars, refrigerated meat lockers, and roaring boilers.
     - *The Neo-Subway*: High-speed cyber metro with tiled corridors, neon lights, and tighter choke points.
   - **Choose Starter Weapon**:
     - *Pneumatic Riveter*: Rapid-fire nailgun with pinpoint accuracy.
     - *Stoker's Heavy Cleaver*: Sweeping melee arc that deals massive damage and repels foes.
     - *Coal Scattergun*: 5-pellet blunderbuss shotgun with devastating close-range burst.
     - *Tesla Arc Caster*: High-voltage electric plasma spheres that pierce foes.

2. **Fighting Through Dynamic Cars**:
   - Each car possesses unique environmental gameplay:
     - *Passenger Coach*: Narrow aisles and tactical seating cover.
     - *Dining Car*: Breakable tables dropping snacks.
     - *Cold Storage Car*: Freezing temperatures with reduced friction ice-sliding!
     - *Cargo Hold*: Explosive red fuel barrels that can be shot to obliterate swarms, and breakable supply crates.
     - *Armory*: Scalding steam floor vents that can be used against enemies.
   - Defeat enemy waves to unlock the bulkhead door.

3. **Boon Leveling & Evolution System (Hades style)**:
   - Boons now stack and level up from **Tier 1 ➔ Tier 2 ➔ Tier 3 (Evolved)**!
   - Step onto the golden pedestal to draft new boons or level up existing ones:
     - **Tesla Discharge** (Chain lightning ➔ Stuns ➔ Death shockwave)
     - **Boiler Jet Dash** (Burning steam ➔ Lingering cloud ➔ Backblast explosion & +1 Dash Charge)
     - **Molten Fuel** (Burn DoT ➔ Burning puddles ➔ +35% damage vulnerability)
     - **Cryo Condenser** (Chill slow ➔ Deep frost ➔ Freeze enemies solid)
     - **Tungsten Rounds** (Pierce +1 ➔ Pierce +2 ➔ Ricochet bouncing bullets)
     - **Kinetic Repulsor** (Defensive blast ➔ Armor i-frames ➔ Destroys incoming enemy bullets)
     - **Stoker's Feast** (Life steal on kills ➔ Higher heal ➔ Bloodlust speed boost)
     - **Bearing Lubricant** (Movement speed ➔ Faster dash recharge ➔ Enemy slow-mo on dash)
     - **Boiler Rupture** (Shrapnel explosions on kill ➔ Huge radius ➔ Chain reactions)

4. **The Locomotive Engine Boss**:
   - **The Conductor (Master of the Locomotive)**:
     - *Phase 1*: Wrench salvos, 360-degree steam rings, and summoned boiler imps.
     - *Phase 2 (Enraged Overclocked)*: Glowing crimson furnace aura, high-speed locomotive rush across the car with devastating shockwaves!

---

## 🛠️ Software Architecture (For CS Students)

This project was built following industry-standard Game Architecture and Object-Oriented Design Patterns:

```
Next_Stop_2026/
├── main.py                  # Entrypoint: initializes pygame and runs Game loop
├── src/
│   ├── config.py            # Global constants (dimensions, colors, layers, physics speeds)
│   ├── core/
│   │   ├── game.py          # Master Engine & Finite State Machine (HUB, PLAYING, UPGRADE, etc.)
│   │   ├── camera.py        # 2D camera with exponential lerp and trauma-based screen shake
│   │   ├── input_handler.py # Event aggregator normalizing keyboard and mouse input
│   │   └── sound.py         # Procedural waveform audio synthesizer (safe fallbacks)
│   ├── combat/
│   │   ├── weapons.py       # Weapon implementations (Riveter, Wrench, Scattergun, Tesla)
│   │   ├── boons.py         # Strategy/Observer pattern for synergies (hooks on hit/dash/kill)
│   │   └── damage.py        # Damage instances, critical strike rolls, and knockback
│   ├── entities/
│   │   ├── base.py          # Vector2 physics, circular collision, hitboxes, and i-frames
│   │   ├── player.py        # WASD physics, dash state machine with i-frames, weapon handling
│   │   ├── projectile.py    # Bullets with obstacle collision, pierce, and elemental tags
│   │   └── enemies/
│   │       ├── base_enemy.py# AI state machine (CHASE, WINDUP, ATTACK, COOLDOWN) + flocking
│   │       ├── types.py     # Inspector (melee), Steward (ranged), Imp (suicide), Warden (shield)
│   │       └── boss.py      # Conductor Boss with multi-phase transitions and telegraphs
│   ├── level/
│   │   ├── train_car.py     # Arena layout, tactical cover (seats/crates), track parallax
│   │   └── car_generator.py # Progression manager and wave composition scaling
│   └── ui/
│       ├── hud.py           # Health bar, dash stamina charges, car banner, boss bar
│       ├── upgrade_menu.py  # 3-card modal draft interface
│       └── particles.py     # Floating damage numbers (crits in gold) and particle emitters
└── tests/
    └── sanity_check.py      # Headless automated integration test suite
```

### Key CS Patterns Demonstrated:
1. **Delta Time Timestep (`dt`)**: Everything scales with `dt` to guarantee uniform physics regardless of whether the game runs at 30 FPS, 60 FPS, or 144 FPS.
2. **Finite State Machines (FSM)**:
   - High level: `Game` states (`HUB` $\rightarrow$ `PLAYING` $\rightarrow$ `BOON_DRAFT` $\rightarrow$ `VICTORY`).
   - Low level: `Enemy` AI states (`CHASE` $\rightarrow$ `WINDUP` with telegraph $\rightarrow$ `ATTACK` $\rightarrow$ `COOLDOWN`).
3. **Trauma-Based Camera Shake**: Uses a quadratic decay model ($shake = trauma^2$) popularized by Vlambeer for punchy game feel.
4. **Observer & Hook Pattern for Synergies**: Instead of writing complex `if` statements across the codebase, boons implement event hooks (`on_hit`, `on_dash`, `on_kill`, `on_take_damage`) that automatically fire.
5. **Flocking / Separation Forces**: Boids-inspired repulsive vector math prevents swarming enemies from overlapping onto a single pixel.
