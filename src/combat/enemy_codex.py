"""Conductor's Field Log & Enemy Threat Index.

Registry of all standard, elite, mini-boss, and climax boss enemy types
across all 5 tracks, detailing their attack patterns, stats, tactical counters,
and animated preview factories.
"""
import pygame
import math
from typing import Dict, Any, List

from src.entities.enemies.types import TicketInspector, RangedSteward, BoilerImp, AutomatonShield
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem
from src.entities.enemies.miniboss import ChiefInspectorMiniBoss
from src.entities.enemies.boss import ConductorBoss
from src.entities.enemies.stage_bosses import (
    ScrapperForemanMiniBoss, VerminBroodEngineBoss,
    CyberDispatcherMiniBoss, TractionAICoreBoss,
    SubZeroWardenMiniBoss, CryoTurbineEngineBoss,
    AshPyromancerMiniBoss, IronLeviathanBoss
)

class DummyPreviewCamera:
    """Mock camera for rendering enemy sprites at fixed screen positions in UI modals."""
    def apply(self, pos: pygame.math.Vector2) -> tuple[int, int]:
        return (int(pos.x), int(pos.y))

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        return rect


ENEMY_CODEX_DATA: Dict[str, Dict[str, Any]] = {
    "ticket_inspector": {
        "id": "ticket_inspector",
        "name": "Ticket Inspector",
        "subtitle": "Frontline Passenger Enforcer",
        "category": "Standard",
        "stage": "Track 1: The Iron Express",
        "threat_stars": 2,
        "base_health": 78,
        "base_speed": 190.0,
        "attacks": [
            {
                "name": "Truncheon Lunge",
                "type": "Melee / Kinetic",
                "desc": "Telegraphs with a bright warning ring before bursting forward at 420 px/s with a heavy baton strike."
            },
            {
                "name": "Flocking Encirclement",
                "type": "Mobility",
                "desc": "Coordinates with adjacent stewards to surround and pinch the player into corners."
            }
        ],
        "tactics": "Time your block [SHIFT] during the windup ring to execute a Perfect Parry, counter-staggering them and opening an easy cleave window.",
        "lore": "Zealous corporate guards enforcing strict ticketing regulations through heavy industrial batons.",
        "factory": lambda x, y: TicketInspector(x, y)
    },
    "ranged_steward": {
        "id": "ranged_steward",
        "name": "Luggage Steward",
        "subtitle": "Pneumatic Needle Sharpshooter",
        "category": "Standard",
        "stage": "Track 1: The Iron Express",
        "threat_stars": 2,
        "base_health": 48,
        "base_speed": 130.0,
        "attacks": [
            {
                "name": "Pneumatic Needle Volley",
                "type": "Ranged / Piercing",
                "desc": "Fires high-velocity brass needles across carriage corridors with pinpoint accuracy."
            },
            {
                "name": "Kiting Reposition",
                "type": "Mobility",
                "desc": "Actively backs away from the player when approached within close-quarters melee reach."
            }
        ],
        "tactics": "Use directional dashing to close the distance through needle lanes, or block with [SHIFT] to deflect projectiles while advancing.",
        "lore": "Porters retrofitted with pneumatic luggage-tagging guns converted into lethal needle launchers.",
        "factory": lambda x, y: RangedSteward(x, y)
    },
    "boiler_imp": {
        "id": "boiler_imp",
        "name": "Scrap Boiler Imp",
        "subtitle": "Articulated Bipedal Runner",
        "category": "Standard",
        "stage": "Track 1: The Iron Express",
        "threat_stars": 3,
        "base_health": 42,
        "base_speed": 260.0,
        "attacks": [
            {
                "name": "Digitigrade Pincer Sprint",
                "type": "Melee / Slashing",
                "desc": "Accelerates on articulated talons directly toward the player, delivering dual scrap pincer strikes."
            },
            {
                "name": "Furnace Overheat",
                "type": "Passive / Enrage",
                "desc": "Glows with superheated boiler fire during sprint windups, resisting light knockback."
            }
        ],
        "tactics": "Swing Stoker's Cleaver in a wide frontal arc to interrupt their sprinting stride and apply hitstop before they reach you.",
        "lore": "Scavenger automatons assembled from discarded boiler scrap that scurry through ventilation ducts.",
        "factory": lambda x, y: BoilerImp(x, y)
    },
    "automaton_shield": {
        "id": "automaton_shield",
        "name": "Freight Warden Automaton",
        "subtitle": "Armored Bulwark Protector",
        "category": "Standard",
        "stage": "Track 1 & Track 3",
        "threat_stars": 3,
        "base_health": 95,
        "base_speed": 140.0,
        "attacks": [
            {
                "name": "Brass Bulwark Deflection",
                "type": "Defense",
                "desc": "Carries an impervious frontal shield deflecting all frontal projectile and bullet fire."
            },
            {
                "name": "Concussive Shield Bash",
                "type": "Melee / Knockback",
                "desc": "Bashes forward with tremendous force if the player enters close proximity, inflicting heavy pushback."
            }
        ],
        "tactics": "Dash through or flank behind the warden to target its vulnerable unarmored rear exhaust port.",
        "lore": "Heavy security automatons designed to safeguard precious freight cars against armed train hijackers.",
        "factory": lambda x, y: AutomatonShield(x, y)
    },
    "boiler_brute": {
        "id": "boiler_brute",
        "name": "Boiler Brute",
        "subtitle": "Armored Smelter Juggernaut",
        "category": "Elite",
        "stage": "Track 1 & Track 2",
        "threat_stars": 4,
        "base_health": 340,
        "base_speed": 115.0,
        "attacks": [
            {
                "name": "Seismic Deck Slam",
                "type": "Area / Shockwave",
                "desc": "Slams iron fists into the floor decking, radiating an expanding 320 px/s kinetic shockwave ring."
            },
            {
                "name": "Steam Vent Cleave",
                "type": "Melee / Steam",
                "desc": "Releases high-pressure steam bursts in an arc while delivering crushing hammer blows."
            }
        ],
        "tactics": "Dash directly through the shockwave ring using dash invulnerability frames; focus fire on glowing shoulder valves.",
        "lore": "Massive furnace stokers clad in boiler plating, mutated by prolonged exposure to superheated steam.",
        "factory": lambda x, y: BoilerBrute(x, y)
    },
    "furnace_golem": {
        "id": "furnace_golem",
        "name": "Furnace Golem",
        "subtitle": "Molten Slag Behemoth",
        "category": "Elite",
        "stage": "Track 5: The Infernal Boiler",
        "threat_stars": 4,
        "base_health": 340,
        "base_speed": 120.0,
        "attacks": [
            {
                "name": "Slag Eruption",
                "type": "Area / Fire",
                "desc": "Detonates burning shrapnel across the arena and leaves permanent hot coal hazard patches."
            },
            {
                "name": "Magma Fists",
                "type": "Melee / Burn",
                "desc": "Pounds the player with fiery fists inflicting lingering burn damage over time."
            }
        ],
        "tactics": "Keep moving across safe metal catwalks to avoid coal burn damage; utilize ranged weaponry or Tesla arcs.",
        "lore": "Living engines of molten slag forged inside the locomotive's bottomless volcanic firebox.",
        "factory": lambda x, y: FurnaceGolem(x, y)
    },
    "chief_inspector": {
        "id": "chief_inspector",
        "name": "Chief Ticket Inspector",
        "subtitle": "Senior Checkpoint Commander",
        "category": "Mini-Boss",
        "stage": "Track 1 (Car 5 Checkpoint)",
        "threat_stars": 4,
        "base_health": 680,
        "base_speed": 160.0,
        "attacks": [
            {
                "name": "Acoustic Sonic Whistle",
                "type": "Area / Cleanse",
                "desc": "Sounds an ear-splitting whistle creating an expanding shockwave that cleanses incoming player projectiles."
            },
            {
                "name": "Crossfire Flurry",
                "type": "Ranged / Multi-Angle",
                "desc": "Fires rapid fan volleys of razor-sharp brass ticket blades across the carriage."
            },
            {
                "name": "Phase 2 Enraged Rush",
                "type": "Melee / Trample",
                "desc": "Enters high-speed enraged rush below 50% HP, relentlessly trampling the player with +40% speed."
            }
        ],
        "tactics": "Hold your fire when the whistle windup begins; use timed parries [SHIFT] against his ticket flurries.",
        "lore": "The authoritarian master of passenger verification who enforces order with an iron ticket punch.",
        "factory": lambda x, y: ChiefInspectorMiniBoss(x, y)
    },
    "conductor": {
        "id": "conductor",
        "name": "The Conductor",
        "subtitle": "Locomotive Overlord",
        "category": "Climax Boss",
        "stage": "Track 1 (Car 15 Engine)",
        "threat_stars": 5,
        "base_health": 1320,
        "base_speed": 135.0,
        "attacks": [
            {
                "name": "Boiler Hammer Slam",
                "type": "Area / Shockwave",
                "desc": "Strikes the engine floor with colossal force, sending an arena-wide 340 px/s kinetic shockwave."
            },
            {
                "name": "Furnace Mortar Barrage",
                "type": "Area / Lingering Fire",
                "desc": "Lobs 3-4 burning slag mortars that burst into persistent fire hazard puddles."
            },
            {
                "name": "Locomotive Charge",
                "type": "Melee / Trample",
                "desc": "Locks onto the player with a red targeting laser and dashes at freight-train speed."
            }
        ],
        "tactics": "Dash through the expanding shockwave ring; stay clear of molten puddles and parry his hammer swings.",
        "lore": "The supreme master of The Iron Express who has merged his mechanical flesh directly into the locomotive boiler.",
        "factory": lambda x, y: ConductorBoss(x, y)
    },
    "scrapper_foreman": {
        "id": "scrapper_foreman",
        "name": "Scrapper Foreman",
        "subtitle": "Derelict Yardmaster",
        "category": "Mini-Boss",
        "stage": "Track 2 (Car 5 Smelter)",
        "threat_stars": 4,
        "base_health": 760,
        "base_speed": 160.0,
        "attacks": [
            {
                "name": "Dual Cleaver Whirlwind",
                "type": "Melee / 360° Slash",
                "desc": "Spins through the car brandishing dual industrial scrap cleavers, shredding everything in reach."
            },
            {
                "name": "Shrapnel Scatter Shot",
                "type": "Ranged / Shrapnel",
                "desc": "Fires a wide shotgun spread of jagged rusty scrap and iron bolts."
            }
        ],
        "tactics": "Back away during the whirlwind spin; burst down with Stoker's Cleaver once he enters dizzy recovery.",
        "lore": "Brutal foreman commanding the derelict salvage crews, wielding cleavers forged from railway track.",
        "factory": lambda x, y: ScrapperForemanMiniBoss(x, y)
    },
    "vermin_brood_engine": {
        "id": "vermin_brood_engine",
        "name": "The Vermin Brood Engine",
        "subtitle": "Biomechanical Pestilence Core",
        "category": "Climax Boss",
        "stage": "Track 2 (Car 15 Engine)",
        "threat_stars": 5,
        "base_health": 1480,
        "base_speed": 120.0,
        "attacks": [
            {
                "name": "Toxic Soot Vents",
                "type": "Area / Corrosive",
                "desc": "Vents thick plumes of corrosive soot across the deck that inflict lingering poison damage."
            },
            {
                "name": "Vermin Swarm Deployment",
                "type": "Summoning",
                "desc": "Spawns continuous swarms of scurrying scrap rats that bite and harass the player."
            },
            {
                "name": "Piston Tail Thrash",
                "type": "Melee / Knockback",
                "desc": "Sweeps a massive iron piston tail across the rear quadrant dealing severe damage."
            }
        ],
        "tactics": "Use wide-cleaving weapons to cull rat swarms quickly; do not stay inside corrosive soot clouds.",
        "lore": "A horrific fusion of overgrown rodents and rotting steam engines nesting deep inside derelict freight trains.",
        "factory": lambda x, y: VerminBroodEngineBoss(x, y)
    },
    "cyber_dispatcher": {
        "id": "cyber_dispatcher",
        "name": "Cyber Dispatcher",
        "subtitle": "Automated Transit Controller",
        "category": "Mini-Boss",
        "stage": "Track 3 (Car 5 Terminal)",
        "threat_stars": 4,
        "base_health": 720,
        "base_speed": 185.0,
        "attacks": [
            {
                "name": "Subterranean Laser Grid",
                "type": "Hazard / Beam",
                "desc": "Projects crisscrossing digital laser grids that slice through the car with minimal telegraph time."
            },
            {
                "name": "Pulse Volley Overdrive",
                "type": "Ranged / Electric",
                "desc": "Rapidly fires alternating high-voltage energy spheres in concentrated bursts."
            }
        ],
        "tactics": "Observe floor conduit lights before lasers activate; execute short dashes through beam gaps.",
        "lore": "An automated transit officer armed with digital grid projectors, obsessed with scheduling perfection.",
        "factory": lambda x, y: CyberDispatcherMiniBoss(x, y)
    },
    "traction_ai_core": {
        "id": "traction_ai_core",
        "name": "Traction AI Core",
        "subtitle": "Sentient Rail Computer",
        "category": "Climax Boss",
        "stage": "Track 3 (Car 15 Engine)",
        "threat_stars": 5,
        "base_health": 1550,
        "base_speed": 135.0,
        "attacks": [
            {
                "name": "Orbiting Laser Pylons",
                "type": "Continuous / Beam",
                "desc": "Spins 4 synchronized laser beams radiating outwards in a deadly rotating pinwheel pattern."
            },
            {
                "name": "EMP Pulse Shockwave",
                "type": "Area / Disruption",
                "desc": "Releases high-frequency electromagnetic pulses that knock back the player and disable dashing."
            },
            {
                "name": "Focused Rail Beam",
                "type": "Piercing / Laser",
                "desc": "Charges a massive central cannon that bisects the entire car length."
            }
        ],
        "tactics": "Circle in tandem with the rotating laser pinwheel; deploy Super Abilities during core cooling cycles.",
        "lore": "The rogue mainframe governing the underground transit network, having declared all biological life redundant.",
        "factory": lambda x, y: TractionAICoreBoss(x, y)
    },
    "sub_zero_warden": {
        "id": "sub_zero_warden",
        "name": "Sub-Zero Warden",
        "subtitle": "Cryo-Storage Jailer",
        "category": "Mini-Boss",
        "stage": "Track 4 (Car 5 Freezer)",
        "threat_stars": 4,
        "base_health": 780,
        "base_speed": 165.0,
        "attacks": [
            {
                "name": "Frost Hammer Quake",
                "type": "Area / Slowing",
                "desc": "Slams a solid-ice hammer creating freezing frost patches that drastically reduce player traction."
            },
            {
                "name": "Icicle Shard Burst",
                "type": "Ranged / Piercing",
                "desc": "Fires a 5-way spread of razor icicles that splinter into smaller shards upon wall contact."
            }
        ],
        "tactics": "Counteract ice slide drift by countering movement vectors; use fire/steam boons for bonus damage.",
        "lore": "A cryo-guard encased in frozen armor, preserving high-value cargo in perpetual absolute zero.",
        "factory": lambda x, y: SubZeroWardenMiniBoss(x, y)
    },
    "cryo_turbine_engine": {
        "id": "cryo_turbine_engine",
        "name": "The Cryo-Turbine Engine",
        "subtitle": "Blizzard Vortex Generator",
        "category": "Climax Boss",
        "stage": "Track 4 (Car 15 Engine)",
        "threat_stars": 5,
        "base_health": 1650,
        "base_speed": 125.0,
        "attacks": [
            {
                "name": "Howling Blizzard Vortex",
                "type": "Hazard / Wind",
                "desc": "Spins giant frosted turbine blades, generating violent headwinds that drag the player into hazard blades."
            },
            {
                "name": "Falling Stalactite Salvo",
                "type": "Area / Overhead",
                "desc": "Vibrates the carriage roof, causing dozens of massive icicle stalactites to crash onto marked floor zones."
            },
            {
                "name": "Permafrost Jet",
                "type": "Continuous / Frost",
                "desc": "Channels a freezing liquid nitrogen spray that freezes the deck and extinguishes projectiles."
            }
        ],
        "tactics": "Watch floor shadow circles to dodge falling stalactites; fire heavy weapons directly into turbine exhaust.",
        "lore": "A monstrous cooling turbine built to withstand Siberian blizzards, generating its own localized sub-zero microclimate.",
        "factory": lambda x, y: CryoTurbineEngineBoss(x, y)
    },
    "ash_pyromancer": {
        "id": "ash_pyromancer",
        "name": "Ash Pyromancer",
        "subtitle": "Volcanic Slag Priest",
        "category": "Mini-Boss",
        "stage": "Track 5 (Car 5 Crucible)",
        "threat_stars": 4,
        "base_health": 740,
        "base_speed": 175.0,
        "attacks": [
            {
                "name": "Flame Pillar Eruption",
                "type": "Area / Geyser",
                "desc": "Summons geysers of roaring flame that erupt through the iron deck grating."
            },
            {
                "name": "Molten Fireball Arc",
                "type": "Ranged / Fire",
                "desc": "Hurls sweeping arcs of magma balls that leave burning trails along their path."
            }
        ],
        "tactics": "Stay off glowing red grating fissures; dash through fireball rings to reach and strike the pyromancer.",
        "lore": "Fanatical engineer who treats the train's infernal boiler as an altar for molten destruction.",
        "factory": lambda x, y: AshPyromancerMiniBoss(x, y)
    },
    "iron_leviathan": {
        "id": "iron_leviathan",
        "name": "The Iron Leviathan",
        "subtitle": "Volcanic Apex Locomotive",
        "category": "Climax Boss",
        "stage": "Track 5 (Car 15 Engine)",
        "threat_stars": 5,
        "base_health": 1950,
        "base_speed": 140.0,
        "attacks": [
            {
                "name": "Dual Flamethrower Cannons",
                "type": "Continuous / Fire Sweep",
                "desc": "Sweeps dual front-mounted industrial flamethrowers across the entire width of the carriage."
            },
            {
                "name": "Volcanic Slag Mortars",
                "type": "Area / Cataclysm",
                "desc": "Bombards the arena with 6 molten slag shells that detonate in devastating explosive chain reactions."
            },
            {
                "name": "Locomotive Overdrive Ram",
                "type": "Melee / Trample",
                "desc": "Channels 100% steam pressure to surge forward with unstoppable momentum, crushing obstacles."
            }
        ],
        "tactics": "Stay along the perimeter walls during central flamethrower sweeps; unleash all fully charged Super Abilities.",
        "lore": "The ultimate steam locomotive juggernaut, armored with impenetrable forged tungsten and fueled by molten rock.",
        "factory": lambda x, y: IronLeviathanBoss(x, y)
    }
}


def get_codex_id_from_enemy(enemy_obj) -> str:
    """Returns the unique codex identifier for any enemy entity instance."""
    cls_name = enemy_obj.__class__.__name__
    mapping = {
        "TicketInspector": "ticket_inspector",
        "RangedSteward": "ranged_steward",
        "BoilerImp": "boiler_imp",
        "AutomatonShield": "automaton_shield",
        "BoilerBrute": "boiler_brute",
        "FurnaceGolem": "furnace_golem",
        "ChiefInspectorMiniBoss": "chief_inspector",
        "ConductorBoss": "conductor",
        "ScrapperForemanMiniBoss": "scrapper_foreman",
        "VerminBroodEngineBoss": "vermin_brood_engine",
        "CyberDispatcherMiniBoss": "cyber_dispatcher",
        "TractionAICoreBoss": "traction_ai_core",
        "SubZeroWardenMiniBoss": "sub_zero_warden",
        "CryoTurbineEngineBoss": "cryo_turbine_engine",
        "AshPyromancerMiniBoss": "ash_pyromancer",
        "IronLeviathanBoss": "iron_leviathan",
    }
    return mapping.get(cls_name, "ticket_inspector")


def get_all_codex_entries() -> List[Dict[str, Any]]:
    """Returns an ordered list of all enemy codex definitions."""
    return list(ENEMY_CODEX_DATA.values())
