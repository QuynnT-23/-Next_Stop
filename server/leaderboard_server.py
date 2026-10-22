"""Next Stop: Conductor Leaderboard Backend Server.
Provides a lightweight REST API for global / multiplayer leaderboard tracking.
Usage:
    uvicorn server.leaderboard_server:app --host 0.0.0.0 --port 8000
    or
    python -m server.leaderboard_server
"""
import os
import json
import sqlite3
import time
from typing import Optional, List, Dict, Any

try:
    from fastapi import FastAPI, Query, HTTPException
    from pydantic import BaseModel
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

DB_PATH = os.path.join(os.path.dirname(__file__), "leaderboard.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id TEXT PRIMARY KEY,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            route_id TEXT NOT NULL,
            route_name TEXT NOT NULL,
            cars_cleared INTEGER NOT NULL,
            weapon_name TEXT NOT NULL,
            loop_count INTEGER NOT NULL,
            is_victory BOOLEAN NOT NULL,
            enemies_killed INTEGER NOT NULL,
            timestamp INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

if HAS_FASTAPI:
    app = FastAPI(title="Next Stop Leaderboard API", version="1.0.0")

    class RunSubmission(BaseModel):
        id: Optional[str] = None
        player_name: str
        score: int
        route_id: str
        route_name: str
        cars_cleared: int
        weapon_name: str
        loop_count: int = 0
        is_victory: bool = False
        enemies_killed: int = 0
        timestamp: Optional[int] = None

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "Next Stop Conductor Leaderboard", "timestamp": int(time.time())}

    @app.get("/api/leaderboard")
    def get_leaderboard(limit: int = Query(20, ge=1, le=100), route_id: Optional[str] = None):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if route_id and route_id != "all":
            cursor.execute(
                "SELECT * FROM leaderboard WHERE route_id = ? ORDER BY score DESC LIMIT ?",
                (route_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM leaderboard ORDER BY score DESC LIMIT ?",
                (limit,)
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {"scores": rows, "count": len(rows)}

    @app.post("/api/leaderboard")
    def post_score(run: RunSubmission):
        run_id = run.id or f"srv_{int(time.time() * 1000)}"
        ts = run.timestamp or int(time.time())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO leaderboard
            (id, player_name, score, route_id, route_name, cars_cleared, weapon_name, loop_count, is_victory, enemies_killed, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, run.player_name[:24], run.score, run.route_id, run.route_name,
            run.cars_cleared, run.weapon_name, run.loop_count, run.is_victory,
            run.enemies_killed, ts
        ))
        conn.commit()
        conn.close()
        return {"status": "success", "id": run_id}

if __name__ == "__main__":
    if HAS_FASTAPI:
        uvicorn.run("server.leaderboard_server:app", host="0.0.0.0", port=8000, reload=True)
    else:
        print("FastAPI / uvicorn not installed. Please install fastapi and uvicorn to run the live backend server.")
