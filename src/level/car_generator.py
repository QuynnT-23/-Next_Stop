"""Train car progression manager, enemy wave spawning, and route themes."""
import pygame
import random
from src.level.train_car import TrainCar
from src.entities.enemies.types import TicketInspector, RangedSteward, BoilerImp, AutomatonShield
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem
from src.entities.enemies.boss import ConductorBoss
from src.entities.enemies.miniboss import ChiefInspectorMiniBoss
from src.entities.enemies.stage_bosses import (
    ScrapperForemanMiniBoss, VerminBroodEngineBoss,
    CyberDispatcherMiniBoss, TractionAICoreBoss,
    SubZeroWardenMiniBoss, CryoTurbineEngineBoss,
    AshPyromancerMiniBoss, IronLeviathanBoss
)

TRAIN_ROUTES = {
    "steam": {
        "name": "The Iron Express",
        "description": "Runaway steam locomotive. Fight car-by-car through Victorian coaches to the furnace.",
        "theme": "steam",
        "cars": [
            {"type": "caboose", "name": "Rear Caboose"},
            {"type": "passenger", "name": "First-Class Coach"},
            {"type": "dining", "name": "Lounge & Dining Car"},
            {"type": "cold_storage", "name": "Refrigerated Meat Locker"},
            {"type": "inspection", "name": "Ticket Checkpoint (Mini-Boss)"},
            {"type": "cargo", "name": "Freight Cargo Hold"},
            {"type": "passenger", "name": "Sleeper Cabin Corridor"},
            {"type": "observation", "name": "Observation Skylight Deck"},
            {"type": "armory", "name": "Munitions & Security Bay"},
            {"type": "inspection_gauntlet", "name": "Central Enforcer Bay (Mini-Boss 2)"},
            {"type": "cargo", "name": "High-Explosives Cargo Hold"},
            {"type": "dining", "name": "Grand Ballroom Car"},
            {"type": "furnace_tender", "name": "The Coal Tender Catwalks"},
            {"type": "armory", "name": "Furnace Ante-Chamber"},
            {"type": "engine", "name": "The Locomotive Furnace (Final Boss)"},
        ]
    },
    "derelict": {
        "name": "The Derelict Freight",
        "description": "Abandoned, rusted junk train swarming with vermin mice and scavengers.",
        "theme": "derelict",
        "cars": [
            {"type": "caboose", "name": "Rusted Tail Caboose"},
            {"type": "cargo", "name": "Scrapyard Freight"},
            {"type": "passenger", "name": "Rotting Timber Coach"},
            {"type": "cargo", "name": "Flooded Bilge Hold"},
            {"type": "inspection", "name": "Dismantling Yard (Mini-Boss)"},
            {"type": "armory", "name": "Junk Crusher Bay"},
            {"type": "cold_storage", "name": "Rusted Freezer Compartment"},
            {"type": "cargo", "name": "Vermin Nest Freight"},
            {"type": "armory", "name": "Abandoned Munitions"},
            {"type": "inspection_gauntlet", "name": "Smelter Chute (Mini-Boss 2)"},
            {"type": "cargo", "name": "Toxic Waste Hold"},
            {"type": "observation", "name": "Wind-Swept Skeleton Deck"},
            {"type": "furnace_tender", "name": "Oil-Slicked Catwalks"},
            {"type": "armory", "name": "Brood Threshold"},
            {"type": "engine", "name": "The Vermin Brood Engine (Final Boss)"},
        ]
    },
    "subway": {
        "name": "The Neo-Subway",
        "description": "High-speed subterranean cyber transit rigged with high-voltage laser gates.",
        "theme": "subway",
        "cars": [
            {"type": "caboose", "name": "Subway Tail Car"},
            {"type": "passenger", "name": "Commuter Coach"},
            {"type": "cargo", "name": "Transit Cargo Hold"},
            {"type": "cold_storage", "name": "Cryo Battery Compartment"},
            {"type": "inspection", "name": "Security Turnstile Checkpoint (Mini-Boss)"},
            {"type": "armory", "name": "Maglev Capacitor Bay"},
            {"type": "passenger", "name": "High-Speed Express Deck"},
            {"type": "observation", "name": "Subterranean Observation Deck"},
            {"type": "cargo", "name": "Cyber Munitions Vault"},
            {"type": "inspection_gauntlet", "name": "Central Matrix Terminal (Mini-Boss 2)"},
            {"type": "armory", "name": "Laser Grid Security Bay"},
            {"type": "cold_storage", "name": "Overclocked Transformer"},
            {"type": "furnace_tender", "name": "Neon Rail Catwalks"},
            {"type": "armory", "name": "AI Core Threshold"},
            {"type": "engine", "name": "Traction AI Core (Final Boss)"},
        ]
    },
    "cryo": {
        "name": "The Glacier Line",
        "description": "Sub-zero mountain express encased in black ice, howling blizzards, and frost.",
        "theme": "cryo",
        "cars": [
            {"type": "caboose", "name": "Frostbitten Caboose"},
            {"type": "passenger", "name": "Frozen Coach"},
            {"type": "dining", "name": "Glacial Dining Hall"},
            {"type": "cold_storage", "name": "Deep Freezer Lockers"},
            {"type": "inspection", "name": "Sub-Zero Checkpoint (Mini-Boss)"},
            {"type": "cargo", "name": "Iced Freight Hold"},
            {"type": "passenger", "name": "Crystallized Sleeper Car"},
            {"type": "observation", "name": "Blizzard Skylight Deck"},
            {"type": "armory", "name": "Cryo-Munitions Vault"},
            {"type": "inspection_gauntlet", "name": "Frost Citadel (Mini-Boss 2)"},
            {"type": "cargo", "name": "Nitrogen Pipeline Car"},
            {"type": "cold_storage", "name": "Frozen Valve Compartment"},
            {"type": "furnace_tender", "name": "Ice Spire Catwalks"},
            {"type": "armory", "name": "Turbine Chamber Entrance"},
            {"type": "engine", "name": "The Cryo-Turbine Engine (Final Boss)"},
        ]
    },
    "infernal": {
        "name": "The Infernal Boiler",
        "description": "Apocalyptic volcanic juggernaut riding over rivers of boiling magma.",
        "theme": "infernal",
        "cars": [
            {"type": "caboose", "name": "Smoldering Caboose"},
            {"type": "passenger", "name": "Charred Coach"},
            {"type": "dining", "name": "Molten Dining Room"},
            {"type": "cargo", "name": "Brimstone Cargo Hold"},
            {"type": "inspection", "name": "Pyre Checkpoint (Mini-Boss)"},
            {"type": "armory", "name": "Magma Slag Hold"},
            {"type": "passenger", "name": "Obsidian Chamber"},
            {"type": "observation", "name": "Eruption Skylight Deck"},
            {"type": "armory", "name": "Munitions Smelter"},
            {"type": "inspection_gauntlet", "name": "Volcanic Forge (Mini-Boss 2)"},
            {"type": "cargo", "name": "Geyser Conduits"},
            {"type": "furnace_tender", "name": "Lava River Catwalks"},
            {"type": "furnace_tender", "name": "Inferno Tender Catwalks"},
            {"type": "armory", "name": "The Maw of Steel"},
            {"type": "engine", "name": "The Iron Leviathan (Final Boss)"},
        ]
    }
}

STAGE_DIFFICULTY_CONFIG = {
    "steam": {
        "budget_mult": 1.0,
        "hp_mult": 1.0,
        "speed_mult": 1.0,
        "damage_mult": 1.0,
        "attack_rate_mult": 1.0,
        "base_elite_chance": 0.15,
    },
    "derelict": {
        "budget_mult": 1.25,
        "hp_mult": 1.25,
        "speed_mult": 1.08,
        "damage_mult": 1.15,
        "attack_rate_mult": 1.10,
        "base_elite_chance": 0.25,
    },
    "subway": {
        "budget_mult": 1.50,
        "hp_mult": 1.50,
        "speed_mult": 1.15,
        "damage_mult": 1.30,
        "attack_rate_mult": 1.20,
        "base_elite_chance": 0.35,
    },
    "cryo": {
        "budget_mult": 1.85,
        "hp_mult": 1.80,
        "speed_mult": 1.22,
        "damage_mult": 1.45,
        "attack_rate_mult": 1.30,
        "base_elite_chance": 0.45,
    },
    "infernal": {
        "budget_mult": 2.25,
        "hp_mult": 2.20,
        "speed_mult": 1.30,
        "damage_mult": 1.65,
        "attack_rate_mult": 1.40,
        "base_elite_chance": 0.55,
    },
}

TRACK_MODIFIERS = {
    "steam": [
        {"id": "overclocked_boiler", "name": "Overclocked Boiler", "desc": "Enemies gain +20% move speed and +15% attack cadence.", "speed_bonus": 0.20, "rate_bonus": 0.15},
        {"id": "dense_steam", "name": "Dense Steam Haze", "desc": "Steam obscures cabin visibility; enemies gain +12% armor plating.", "armor_bonus": 0.12}
    ],
    "derelict": [
        {"id": "vermin_frenzy", "name": "Vermin Swarm Frenzy", "desc": "Mice scurry in packs; enemies explode into scrap shrapnel on defeat.", "shrapnel": True},
        {"id": "rust_corrosion", "name": "Corrosive Sludge", "desc": "Health restoration reduced by 25%; enemies have +15% base damage.", "damage_bonus": 0.15}
    ],
    "subway": [
        {"id": "high_voltage", "name": "High-Voltage Overdrive", "desc": "Laser gates pulse rapidly; Automaton shields bash twice as hard.", "laser_mult": 1.4},
        {"id": "neural_burst", "name": "Neural Overclock", "desc": "Ranged Stewards fire an extra bullet per burst volley.", "burst_extra": 1}
    ],
    "cryo": [
        {"id": "permafrost", "name": "Black Ice Friction", "desc": "Increased ice slide drift; enemies resist knockback.", "permafrost": True},
        {"id": "blizzard_gale", "name": "Sub-Zero Gale", "desc": "Freezing winds buffet platforms; enemies gain +25% maximum HP.", "hp_bonus": 0.25}
    ],
    "infernal": [
        {"id": "magma_eruption", "name": "Volcanic Magma Surge", "desc": "Hot coals deal 2x burn damage; slain enemies leave magma pools.", "magma_death": True},
        {"id": "molten_juggernauts", "name": "Molten Juggernauts", "desc": "Brutes and Golems gain +35% health and expanded shockwaves.", "golem_hp": 0.35}
    ]
}

class RunManager:
    """Controls progression through train cars, loop difficulty scaling, and enemy generation."""
    def __init__(self, route_id: str = "steam", loop_count: int = 0):
        self.route_id = route_id if route_id in TRAIN_ROUTES else "steam"
        self.route_data = TRAIN_ROUTES[self.route_id]
        self.loop_count = max(0, loop_count)
        self.current_car_index = 0
        self.total_cars = len(self.route_data["cars"])
        self.active_modifiers = TRACK_MODIFIERS.get(self.route_id, []) if self.loop_count >= 1 else []

    def get_loop_display(self) -> str:
        if self.loop_count <= 0:
            return ""
        if self.loop_count <= 3:
            return "+" * self.loop_count
        return f"+{self.loop_count}"

    def get_active_modifiers(self) -> list[dict]:
        return self.active_modifiers

    def get_current_car_info(self) -> dict:
        return self.route_data["cars"][self.current_car_index]

    def is_final_car(self) -> bool:
        return self.current_car_index >= self.total_cars - 1

    def create_current_car(self) -> TrainCar:
        car_info = self.get_current_car_info()
        return TrainCar(
            car_index=self.current_car_index,
            car_type=car_info["type"],
            theme=self.route_data.get("theme", self.route_id)
        )

    def spawn_enemies_for_car(self, car: TrainCar) -> list:
        """Spawn enemy waves tailored to the specific car, theme, boss roster, loop cycle, and modifiers."""
        enemies = []
        car_info = self.get_current_car_info()
        car_type = car_info["type"]
        idx = self.current_car_index
        mid_y = (car.top_wall_y + car.bottom_wall_y) // 2
        
        cfg = STAGE_DIFFICULTY_CONFIG.get(self.route_id, STAGE_DIFFICULTY_CONFIG["steam"])
        car_hp_scale = 1.0 + (idx * 0.025)
        car_dmg_scale = 1.0 + (idx * 0.020)
        car_speed_scale = 1.0 + (idx * 0.012)
        car_rate_scale = 1.0 + (idx * 0.015)

        # Loop difficulty enhancements (Track 1+, Track 2+, etc.)
        loop_hp = 1.0 + (self.loop_count * 0.35)
        loop_dmg = 1.0 + (self.loop_count * 0.25)
        loop_speed = 1.0 + (self.loop_count * 0.08)
        loop_rate = 1.0 + (self.loop_count * 0.10)

        # Integrate active modifiers
        for mod in self.active_modifiers:
            loop_speed += mod.get("speed_bonus", 0.0)
            loop_rate += mod.get("rate_bonus", 0.0)
            loop_dmg += mod.get("damage_bonus", 0.0)
            loop_hp += mod.get("hp_bonus", 0.0)

        hp_mult = cfg["hp_mult"] * car_hp_scale * loop_hp
        dmg_mult = cfg["damage_mult"] * car_dmg_scale * loop_dmg
        speed_mult = cfg["speed_mult"] * car_speed_scale * loop_speed
        rate_mult = cfg["attack_rate_mult"] * car_rate_scale * loop_rate

        # 1. Car 5: Mid-Run Mini-Boss 1
        if car_type == "inspection":
            if self.route_id == "steam":
                miniboss = ChiefInspectorMiniBoss(car.width - 450, mid_y)
                enemies.append(miniboss)
                enemies.append(TicketInspector(car.width - 650, car.top_wall_y + 80))
                enemies.append(TicketInspector(car.width - 650, car.bottom_wall_y - 80))
            elif self.route_id == "derelict":
                miniboss = ScrapperForemanMiniBoss(car.width - 450, mid_y)
                enemies.append(miniboss)
                enemies.append(BoilerImp(car.width - 650, car.top_wall_y + 80))
                enemies.append(BoilerImp(car.width - 650, car.bottom_wall_y - 80))
            elif self.route_id == "subway":
                miniboss = CyberDispatcherMiniBoss(car.width - 450, mid_y)
                enemies.append(miniboss)
                enemies.append(AutomatonShield(car.width - 650, mid_y))
            elif self.route_id == "cryo":
                miniboss = SubZeroWardenMiniBoss(car.width - 450, mid_y)
                enemies.append(miniboss)
                enemies.append(RangedSteward(car.width - 650, car.top_wall_y + 80))
                enemies.append(RangedSteward(car.width - 650, car.bottom_wall_y - 80))
            elif self.route_id == "infernal":
                miniboss = AshPyromancerMiniBoss(car.width - 450, mid_y)
                enemies.append(miniboss)
                enemies.append(BoilerImp(car.width - 650, car.top_wall_y + 80))
                enemies.append(BoilerImp(car.width - 650, car.bottom_wall_y - 80))
            
            for e in enemies:
                e.apply_difficulty_scaling(hp_mult, speed_mult, dmg_mult, rate_mult)
            return enemies

        # 2. Car 10: Mid-Run Mini-Boss 2 / Enforcer Gauntlet
        if car_type == "inspection_gauntlet":
            brute = BoilerBrute(car.width - 420, mid_y)
            brute.make_elite()
            enemies.append(brute)
            shield = AutomatonShield(car.width - 620, car.top_wall_y + 90)
            steward = RangedSteward(car.width - 620, car.bottom_wall_y - 90)
            enemies.append(shield)
            enemies.append(steward)
            for e in enemies:
                e.apply_difficulty_scaling(hp_mult, speed_mult, dmg_mult, rate_mult)
            return enemies

        # 3. Car 15: The Climax Final Boss
        if car_type == "engine":
            if self.route_id == "steam":
                boss = ConductorBoss(car.width - 450, mid_y)
            elif self.route_id == "derelict":
                boss = VerminBroodEngineBoss(car.width - 450, mid_y)
            elif self.route_id == "subway":
                boss = TractionAICoreBoss(car.width - 450, mid_y)
            elif self.route_id == "cryo":
                boss = CryoTurbineEngineBoss(car.width - 450, mid_y)
            elif self.route_id == "infernal":
                boss = IronLeviathanBoss(car.width - 450, mid_y)
            else:
                boss = ConductorBoss(car.width - 450, mid_y)
            boss.apply_difficulty_scaling(hp_mult, speed_mult, dmg_mult, rate_mult)
            enemies.append(boss)
            return enemies

        # Normal Car Wave Generation
        min_x = 450 if idx == 0 else 550
        max_x = 1350 if idx == 0 else (car.width - 250)
        min_y = car.top_wall_y + 60
        max_y = car.bottom_wall_y - 60

        def get_valid_pos():
            for _ in range(35):
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                valid = True
                for obs in car.obstacles:
                    if obs.inflate(40, 40).collidepoint(x, y):
                        valid = False
                        break
                for b in car.barrels:
                    if (b.pos - pygame.math.Vector2(x, y)).length() < 40:
                        valid = False
                        break
                if valid:
                    return x, y
            return random.uniform(min_x, max_x), random.uniform(min_y, max_y)

        # Point budget scales with car index, stage multiplier, and loop count (Track 1+, etc.)
        late_car_bonus = 5.0 if idx >= 10 else (2.5 if idx >= 5 else 0.0)
        loop_budget_bonus = self.loop_count * 4.0
        loop_budget_mult = 1.0 + (self.loop_count * 0.20)
        budget = ((7.0 + (idx * 2.2) + late_car_bonus + loop_budget_bonus) * cfg["budget_mult"] * loop_budget_mult) + random.uniform(-0.5, 1.5)
        elite_chance = min(0.85, cfg["base_elite_chance"] + (idx / 14.0) * 0.20 + (self.loop_count * 0.10))

        enemy_catalog = [
            ("imp", BoilerImp, 1.5, 0),
            ("inspector", TicketInspector, 2.0, 0),
            ("steward", RangedSteward, 3.0, 1),
            ("shield", AutomatonShield, 3.8, 2),
            ("brute", BoilerBrute, 6.0, 3),
            ("golem", FurnaceGolem, 6.5, 5),
        ]
        unlocked = [item for item in enemy_catalog if idx >= item[3]]
        rem_budget = budget
        attempts = 0
        while rem_budget >= 1.5 and attempts < 40:
            attempts += 1
            chosen = random.choice(unlocked)
            code, cls, cost, _ = chosen
            if cost <= rem_budget + 0.5:
                x, y = get_valid_pos()
                enemy_inst = cls(x, y)
                if random.random() < elite_chance and code not in ["imp"]:
                    enemy_inst.make_elite()
                enemy_inst.apply_difficulty_scaling(hp_mult, speed_mult, dmg_mult, rate_mult)
                enemies.append(enemy_inst)
                rem_budget -= cost

        if len(enemies) < 3:
            for _ in range(3 - len(enemies)):
                x, y = get_valid_pos()
                fallback_insp = TicketInspector(x, y)
                fallback_insp.apply_difficulty_scaling(hp_mult, speed_mult, dmg_mult, rate_mult)
                enemies.append(fallback_insp)

        return enemies

    def advance_to_next_car(self) -> bool:
        """Advance index. Returns True if next car exists, False if run won."""
        self.current_car_index += 1
        return self.current_car_index < self.total_cars
