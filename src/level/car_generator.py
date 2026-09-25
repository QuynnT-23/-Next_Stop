"""Train car progression manager, enemy wave spawning, and route themes."""
import pygame
import random
from src.level.train_car import TrainCar
from src.entities.enemies.types import TicketInspector, RangedSteward, BoilerImp, AutomatonShield
from src.entities.enemies.brute import BoilerBrute, FurnaceGolem
from src.entities.enemies.boss import ConductorBoss

TRAIN_ROUTES = {
    "steam": {
        "name": "The Iron Express",
        "description": "Runaway steam locomotive. Fight car-by-car to the furnace engine.",
        "cars": [
            {"type": "caboose", "name": "Rear Caboose"},
            {"type": "passenger", "name": "First-Class Coach"},
            {"type": "dining", "name": "Lounge & Dining Car"},
            {"type": "cold_storage", "name": "Refrigerated Meat Locker"},
            {"type": "inspection", "name": "Ticket Inspection Checkpoint"},
            {"type": "cargo", "name": "Freight & Explosive Cargo Hold"},
            {"type": "observation", "name": "Observation Skylight Deck"},
            {"type": "armory", "name": "Munitions & Security Bay"},
            {"type": "furnace_tender", "name": "The Coal Tender Catwalks"},
            {"type": "engine", "name": "The Locomotive Furnace"},
        ]
    },
    "subway": {
        "name": "The Neo-Subway",
        "description": "High-speed cyber transit. Breaching subterranean security cars.",
        "cars": [
            {"type": "caboose", "name": "Subway Tail Car"},
            {"type": "passenger", "name": "Commuter Coach"},
            {"type": "cold_storage", "name": "Cryo Maintenance"},
            {"type": "cargo", "name": "Transit Freight"},
            {"type": "armory", "name": "Security Compartment"},
            {"type": "engine", "name": "Subway Traction Core"},
        ]
    }
}

class RunManager:
    """Controls progression through train cars and enemy generation."""
    def __init__(self, route_id: str = "steam"):
        self.route_id = route_id
        self.route_data = TRAIN_ROUTES[route_id]
        self.current_car_index = 0
        self.total_cars = len(self.route_data["cars"])

    def get_current_car_info(self) -> dict:
        return self.route_data["cars"][self.current_car_index]

    def is_final_car(self) -> bool:
        return self.current_car_index >= self.total_cars - 1

    def create_current_car(self) -> TrainCar:
        car_info = self.get_current_car_info()
        return TrainCar(
            car_index=self.current_car_index,
            car_type=car_info["type"],
            theme=self.route_id
        )

    def spawn_enemies_for_car(self, car: TrainCar) -> list:
        """Spawn enemy waves tailored to the specific car and difficulty curve."""
        enemies = []
        car_info = self.get_current_car_info()
        car_type = car_info["type"]
        idx = self.current_car_index
        
        # Min spawn X coordinate: Car 1 (caboose) has tighter spawn so action starts immediately
        min_x = 450 if idx == 0 else 550
        max_x = 1350 if idx == 0 else (car.width - 250)
        min_y = car.top_wall_y + 60
        max_y = car.bottom_wall_y - 60

        if car_type == "inspection":
            # Mid-Run Mini-Boss Encounter: The Chief Ticket Inspector!
            from src.entities.enemies.miniboss import ChiefInspectorMiniBoss
            miniboss = ChiefInspectorMiniBoss(car.width - 450, (car.top_wall_y + car.bottom_wall_y) // 2)
            enemies.append(miniboss)
            # Escort guards
            enemies.append(TicketInspector(car.width - 650, car.top_wall_y + 80))
            enemies.append(TicketInspector(car.width - 650, car.bottom_wall_y - 80))
            return enemies

        if car_type == "engine":
            # Locomotive Boss Encounter!
            boss = ConductorBoss(car.width - 450, (car.top_wall_y + car.bottom_wall_y) // 2)
            enemies.append(boss)
            return enemies

        # Helper to find valid spawn location not overlapping obstacles or barrels
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

        # Dynamic Encounter Themes
        themes = ["balanced_patrol"]
        if idx >= 1:
            themes.append("ambush_swarm")
            themes.append("artillery_barrage")
        if idx >= 3:
            themes.append("heavy_fortification")
            themes.append("elite_patrol")
        if idx >= 5:
            themes.append("furnace_surge")

        selected_theme = random.choice(themes)
        # Scaled point budget
        budget = 6.0 + (idx * 2.8) + random.uniform(-1.0, 2.5)
        
        # Enemy tier costs and constructors
        enemy_catalog = [
            ("imp", BoilerImp, 1.5, 0),
            ("inspector", TicketInspector, 2.0, 0),
            ("steward", RangedSteward, 3.0, 1),
            ("shield", AutomatonShield, 3.8, 2),
            ("brute", BoilerBrute, 6.0, 4),
            ("golem", FurnaceGolem, 6.5, 6),
        ]

        # Filter by car unlock level
        unlocked = [item for item in enemy_catalog if idx >= item[3]]

        # Theme-weighted selection
        weights = []
        for code, cls, cost, min_idx in unlocked:
            w = 1.0
            if selected_theme == "ambush_swarm":
                if code in ["imp", "inspector"]:
                    w = 3.5
            elif selected_theme == "artillery_barrage":
                if code in ["steward", "shield"]:
                    w = 3.0
            elif selected_theme == "heavy_fortification":
                if code in ["shield", "brute"]:
                    w = 3.5
            elif selected_theme == "furnace_surge":
                if code in ["golem", "imp"]:
                    w = 3.5
            elif selected_theme == "elite_patrol":
                if code in ["brute", "shield", "inspector"]:
                    w = 2.5
            weights.append(w)

        # Spend budget
        rem_budget = budget
        attempts = 0
        while rem_budget >= 1.5 and attempts < 40:
            attempts += 1
            # Pick enemy based on weights
            chosen = random.choices(unlocked, weights=weights, k=1)[0]
            code, cls, cost, _ = chosen
            if cost <= rem_budget + 0.5:
                x, y = get_valid_pos()
                enemy_inst = cls(x, y)
                
                # Elite variant chance
                elite_threshold = 0.35 if selected_theme == "elite_patrol" else (0.18 if idx >= 2 else 0.0)
                if random.random() < elite_threshold and code not in ["imp"]:
                    enemy_inst.make_elite()

                enemies.append(enemy_inst)
                rem_budget -= cost

        # Ensure minimum encounter presence
        if len(enemies) < 3:
            for _ in range(3 - len(enemies)):
                x, y = get_valid_pos()
                enemies.append(TicketInspector(x, y))

        return enemies

    def advance_to_next_car(self) -> bool:
        """Advance index. Returns True if next car exists, False if run won."""
        self.current_car_index += 1
        return self.current_car_index < self.total_cars
