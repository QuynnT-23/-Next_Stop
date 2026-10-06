"""Player meta-progression, Conductor licensing, permanent upgrades, and persistent save data."""
import os
import json

SAVE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "save_data.json")

PERK_DEFINITIONS = {
    "iron_constitution": {
        "name": "Iron Constitution",
        "desc": "Increases base maximum Health by +20 HP per tier.",
        "max_rank": 5,
        "base_cost": 50,
        "cost_mult": 1.6,
        "effect_per_rank": 20,
        "stat": "max_hp"
    },
    "boiler_pressure": {
        "name": "Boiler Pressure",
        "desc": "Increases dash recovery speed by +15% per tier.",
        "max_rank": 4,
        "base_cost": 60,
        "cost_mult": 1.7,
        "effect_per_rank": 0.15,
        "stat": "dash_recovery"
    },
    "stokers_greed": {
        "name": "Scrap Magnet",
        "desc": "Increases Scrap Metal drops and rewards by +25% per tier.",
        "max_rank": 5,
        "base_cost": 40,
        "cost_mult": 1.5,
        "effect_per_rank": 0.25,
        "stat": "scrap_mult"
    },
    "precision_tuning": {
        "name": "Precision Tuning",
        "desc": "Increases base Critical Strike chance by +4% per tier.",
        "max_rank": 5,
        "base_cost": 75,
        "cost_mult": 1.8,
        "effect_per_rank": 0.04,
        "stat": "crit_chance"
    },
    "emergency_reroll": {
        "name": "Blueprint Archive",
        "desc": "Grants +1 Boon draft reroll per run.",
        "max_rank": 3,
        "base_cost": 120,
        "cost_mult": 2.2,
        "effect_per_rank": 1,
        "stat": "rerolls"
    }
}

ALL_STAGES = ["steam", "derelict", "subway", "cryo", "infernal"]

class ProgressionManager:
    """Manages persistent Conductor XP, levels, scrap currency, single-track progression, and Loop+ cycles."""
    def __init__(self, save_path=None):
        self.save_path = save_path or SAVE_FILE
        self.level = 1
        self.xp = 0
        self.scrap = 0
        self.current_track_idx = 0  # 0: steam, 1: derelict, 2: subway, 3: cryo, 4: infernal
        self.loop_count = 0         # 0 = base game, 1 = Loop 1 (Track 1+), 2 = Loop 2 (Track 1++), etc.
        self.unlocked_stages = ["steam"]
        self.perks = {k: 0 for k in PERK_DEFINITIONS}
        self.total_runs = 0
        self.total_bosses_slain = 0
        self.load()

    def get_active_route_id(self) -> str:
        """Returns the ID of the single active available track."""
        return ALL_STAGES[self.current_track_idx]

    def get_loop_suffix(self) -> str:
        """Returns '+' notation for the current loop (e.g. '', '+', '++', '+3')."""
        if self.loop_count <= 0:
            return ""
        if self.loop_count <= 3:
            return "+" * self.loop_count
        return f"+{self.loop_count}"

    def get_track_display_name(self, track_ref) -> str:
        """Returns formatted track name e.g. 'TRACK 1', 'TRACK 1+', 'TRACK 2++'."""
        if isinstance(track_ref, str):
            idx = ALL_STAGES.index(track_ref) if track_ref in ALL_STAGES else 0
        else:
            idx = int(track_ref)
        suffix = self.get_loop_suffix()
        return f"TRACK {idx + 1}{suffix}"

    def get_track_state(self, track_ref) -> str:
        """Returns 'completed' (departed), 'active' (boardable), or 'locked' (upcoming)."""
        if isinstance(track_ref, str):
            idx = ALL_STAGES.index(track_ref) if track_ref in ALL_STAGES else 0
        else:
            idx = int(track_ref)
        if idx < self.current_track_idx:
            return "completed"
        elif idx == self.current_track_idx:
            return "active"
        else:
            return "locked"

    def advance_track_on_victory(self) -> dict:
        """Advances progression after defeating the Car 15 boss.
        
        Once beaten, the current track departs and becomes unboardable.
        The next track becomes the only active track.
        If Track 5 is beaten, cycle resets to Track 1+, advancing loop_count.
        """
        prev_idx = self.current_track_idx
        prev_route = ALL_STAGES[prev_idx]

        if self.current_track_idx < len(ALL_STAGES) - 1:
            self.current_track_idx += 1
            new_loop = False
        else:
            # Completed Track 5! Advance to next loop cycle (Track 1+)!
            self.current_track_idx = 0
            self.loop_count += 1
            new_loop = True

        self.unlocked_stages = [self.get_active_route_id()]
        self.save()
        return {
            "previous_track_idx": prev_idx,
            "previous_route": prev_route,
            "active_track_idx": self.current_track_idx,
            "active_route": self.get_active_route_id(),
            "loop_count": self.loop_count,
            "new_loop": new_loop,
            "display_name": self.get_track_display_name(self.current_track_idx)
        }

    def unlock_next_stage(self, completed_stage: str) -> str | None:
        """Backwards compatibility shim for advance_track_on_victory."""
        result = self.advance_track_on_victory()
        return result["active_route"]

    def get_xp_for_next_level(self) -> int:
        return int(100 * (self.level ** 1.35))

    def gain_xp(self, amount: int) -> bool:
        """Adds XP and handles level ups. Returns True if level up occurred."""
        self.xp += amount
        leveled_up = False
        while self.xp >= self.get_xp_for_next_level():
            self.xp -= self.get_xp_for_next_level()
            self.level += 1
            self.scrap += 25  # Bonus scrap on level up!
            leveled_up = True
        self.save()
        return leveled_up

    def gain_scrap(self, amount: int):
        mult = 1.0 + self.perks.get("stokers_greed", 0) * PERK_DEFINITIONS["stokers_greed"]["effect_per_rank"]
        self.scrap += int(amount * mult)
        self.save()

    def get_perk_cost(self, perk_id: str) -> int:
        data = PERK_DEFINITIONS[perk_id]
        cur_rank = self.perks.get(perk_id, 0)
        if cur_rank >= data["max_rank"]:
            return -1
        return int(data["base_cost"] * (data["cost_mult"] ** cur_rank))

    def can_afford_perk(self, perk_id: str) -> bool:
        cost = self.get_perk_cost(perk_id)
        return cost > 0 and self.scrap >= cost

    def purchase_perk(self, perk_id: str) -> bool:
        cost = self.get_perk_cost(perk_id)
        if cost > 0 and self.scrap >= cost:
            self.scrap -= cost
            self.perks[perk_id] = self.perks.get(perk_id, 0) + 1
            self.save()
            return True
        return False

    def apply_perks_to_player(self, player):
        """Applies purchased meta-upgrades to a fresh player instance."""
        bonus_hp = self.perks.get("iron_constitution", 0) * 20
        player.max_health += bonus_hp
        player.health += bonus_hp
        
        bonus_crit = self.perks.get("precision_tuning", 0) * 0.04
        if hasattr(player, "crit_bonus"):
            player.crit_bonus += bonus_crit
        else:
            player.crit_bonus = bonus_crit

        if hasattr(player, "dash_recovery_mult"):
            player.dash_recovery_mult += self.perks.get("boiler_pressure", 0) * 0.15
        else:
            player.dash_recovery_mult = 1.0 + self.perks.get("boiler_pressure", 0) * 0.15

    def save(self):
        data = {
            "level": self.level,
            "xp": self.xp,
            "scrap": self.scrap,
            "current_track_idx": self.current_track_idx,
            "loop_count": self.loop_count,
            "unlocked_stages": self.unlocked_stages,
            "perks": self.perks,
            "total_runs": self.total_runs,
            "total_bosses_slain": self.total_bosses_slain
        }
        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save progression: {e}")

    def load(self):
        if not os.path.exists(self.save_path) or os.path.getsize(self.save_path) == 0:
            return
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.level = data.get("level", 1)
            self.xp = data.get("xp", 0)
            self.scrap = data.get("scrap", 0)
            self.current_track_idx = data.get("current_track_idx", 0)
            self.loop_count = data.get("loop_count", 0)
            self.unlocked_stages = data.get("unlocked_stages", [self.get_active_route_id()])
            loaded_perks = data.get("perks", {})
            for k in PERK_DEFINITIONS:
                self.perks[k] = loaded_perks.get(k, 0)
            self.total_runs = data.get("total_runs", 0)
            self.total_bosses_slain = data.get("total_bosses_slain", 0)
        except Exception as e:
            print(f"Warning: Failed to load progression: {e}")
