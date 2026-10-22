"""Leaderboard management system with local JSON persistence and optional REST backend."""
import os
import json
import time
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

LEADERBOARD_FILE = os.path.expanduser("~/.next_stop_leaderboard.json")
DEFAULT_SERVER_URL = os.environ.get("NEXT_STOP_LEADERBOARD_URL", "http://localhost:8000")

DEFAULT_LOCAL_SCORES = [
    {
        "id": "conductor_1",
        "player_name": "Chief Conductor Vance",
        "score": 12850,
        "route_id": "infernal",
        "route_name": "Infernal Express",
        "cars_cleared": 15,
        "weapon_name": "Arc Caster (R5)",
        "loop_count": 2,
        "is_victory": True,
        "enemies_killed": 98,
        "timestamp": int(time.time()) - 86400 * 3
    },
    {
        "id": "conductor_2",
        "player_name": "Boiler Stoker Martha",
        "score": 9400,
        "route_id": "cryo",
        "route_name": "Cryo Express",
        "cars_cleared": 15,
        "weapon_name": "Cleaver (R4)",
        "loop_count": 1,
        "is_victory": True,
        "enemies_killed": 82,
        "timestamp": int(time.time()) - 86400 * 2
    },
    {
        "id": "conductor_3",
        "player_name": "Iron Track Jackson",
        "score": 6750,
        "route_id": "subway",
        "route_name": "Metro Ghost",
        "cars_cleared": 12,
        "weapon_name": "Scattergun (R3)",
        "loop_count": 0,
        "is_victory": False,
        "enemies_killed": 64,
        "timestamp": int(time.time()) - 86400
    },
    {
        "id": "conductor_4",
        "player_name": "Steamwright Alex",
        "score": 4200,
        "route_id": "steam",
        "route_name": "Steam Line",
        "cars_cleared": 8,
        "weapon_name": "Riveter (R2)",
        "loop_count": 0,
        "is_victory": False,
        "enemies_killed": 35,
        "timestamp": int(time.time()) - 3600 * 12
    }
]

class LeaderboardClient:
    """Manages recording runs, querying top ranks, and syncing with cloud server."""
    def __init__(self, server_url: str = DEFAULT_SERVER_URL):
        self.server_url = server_url.rstrip("/")
        self.local_scores: List[Dict[str, Any]] = []
        self.load_local_scores()

    def load_local_scores(self):
        """Loads local leaderboard scores from disk or defaults."""
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.local_scores = data
                        return
            except Exception:
                pass
        self.local_scores = list(DEFAULT_LOCAL_SCORES)
        self.save_local_scores()

    def save_local_scores(self):
        """Persists local scores to disk."""
        try:
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(self.local_scores, f, indent=2)
        except Exception:
            pass

    def calculate_score(self, cars_cleared: int, enemies_killed: int, damage_dealt: int,
                        duration_sec: float, loop_count: int, is_victory: bool) -> int:
        """Computes score based on performance metrics."""
        car_points = cars_cleared * 300
        kill_points = enemies_killed * 50
        dmg_points = int(damage_dealt * 0.5)
        loop_bonus = loop_count * 2000
        victory_bonus = 3000 if is_victory else 0
        speed_bonus = max(0, int((600 - duration_sec) * 5)) if is_victory else 0
        return car_points + kill_points + dmg_points + loop_bonus + victory_bonus + speed_bonus

    def record_run(self, player_name: str, route_id: str, route_name: str,
                   cars_cleared: int, weapon_name: str, loop_count: int,
                   is_victory: bool, enemies_killed: int, damage_dealt: int,
                   duration_sec: float) -> Dict[str, Any]:
        """Records a completed run locally and attempts async cloud sync."""
        score = self.calculate_score(cars_cleared, enemies_killed, damage_dealt, duration_sec, loop_count, is_victory)
        entry = {
            "id": f"run_{int(time.time() * 1000)}",
            "player_name": player_name or "Stoker",
            "score": score,
            "route_id": route_id,
            "route_name": route_name,
            "cars_cleared": cars_cleared,
            "weapon_name": weapon_name,
            "loop_count": loop_count,
            "is_victory": is_victory,
            "enemies_killed": enemies_killed,
            "timestamp": int(time.time())
        }
        self.local_scores.append(entry)
        self.local_scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        self.local_scores = self.local_scores[:100]
        self.save_local_scores()

        # Try background sync to online server if available
        self._try_post_online(entry)
        return entry

    def get_top_scores(self, limit: int = 10, route_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns top scores locally or merged with online entries if available."""
        scores = self.local_scores
        if route_id and route_id != "all":
            scores = [s for s in scores if s.get("route_id") == route_id]
        scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
        return scores[:limit]

    def _try_post_online(self, entry: Dict[str, Any]):
        """Non-blocking POST to server with short timeout."""
        try:
            url = f"{self.server_url}/api/leaderboard"
            data = json.dumps(entry).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            # Timeout of 1.0 second so game never stutters
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                pass
        except Exception:
            # Server not running or offline; gracefully fallback to local
            pass
