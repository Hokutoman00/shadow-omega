"""
T1 Shadow War — PredictiveLedger (Middleware A: 未来予知)

Append-only SQLite ledger that:
  1. Records every agent action with its cost
  2. Enforces per-agent budget (forced surrender when exhausted)
  3. Predicts likely next moves using cosine similarity on action history
"""
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "ledger.db"


_db_conn: sqlite3.Connection | None = None


def _conn() -> sqlite3.Connection:
    global _db_conn
    if _db_conn is not None:
        return _db_conn
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            universe_id INTEGER NOT NULL,
            island_id INTEGER NOT NULL,
            turn INTEGER NOT NULL,
            action TEXT NOT NULL,
            cost REAL NOT NULL,
            outcome TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            agent_id TEXT PRIMARY KEY,
            initial REAL NOT NULL,
            spent REAL NOT NULL DEFAULT 0.0
        )
    """)
    conn.commit()
    _db_conn = conn
    return conn


def init_budget(agent_id: str, initial: float = 100.0) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO budgets (agent_id, initial, spent) VALUES (?,?,?)",
            (agent_id, initial, 0.0)
        )


def debit(agent_id: str, universe_id: int, island_id: int,
          turn: int, action: str, cost: float) -> dict:
    """Debit cost from agent's budget. Returns {allowed, remaining}."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT initial, spent FROM budgets WHERE agent_id=?", (agent_id,)
        ).fetchone()
        if row is None:
            init_budget(agent_id)
            initial, spent = 100.0, 0.0
        else:
            initial, spent = row
        remaining = initial - spent - cost
        allowed = remaining >= 0
        if allowed:
            conn.execute(
                "UPDATE budgets SET spent=? WHERE agent_id=?", (spent + cost, agent_id)
            )
            conn.execute(
                "INSERT INTO actions (agent_id,universe_id,island_id,turn,action,cost,created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (agent_id, universe_id, island_id, turn, action, cost,
                 datetime.now(timezone.utc).isoformat())
            )
        return {"allowed": allowed, "remaining": max(0.0, remaining), "forced_surrender": not allowed}


def get_budget(agent_id: str) -> dict:
    with _conn() as conn:
        row = conn.execute(
            "SELECT initial, spent FROM budgets WHERE agent_id=?", (agent_id,)
        ).fetchone()
        if row is None:
            return {"agent_id": agent_id, "remaining": 100.0, "spent": 0.0}
        initial, spent = row
        return {"agent_id": agent_id, "remaining": initial - spent, "spent": spent}


def predict_next_action(agent_id: str, current_action: str) -> str | None:
    """Find the most common action that followed current_action historically."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT action FROM actions WHERE agent_id=? ORDER BY id", (agent_id,)
        ).fetchall()
    history = [r[0] for r in rows]
    if len(history) < 2:
        return None
    successors: dict[str, dict[str, int]] = {}
    for i in range(len(history) - 1):
        prev, nxt = history[i], history[i + 1]
        successors.setdefault(prev, {})
        successors[prev][nxt] = successors[prev].get(nxt, 0) + 1
    if current_action not in successors:
        return None
    return max(successors[current_action], key=successors[current_action].get)


def get_history(universe_id: int, limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT agent_id, island_id, turn, action, cost, outcome, created_at "
            "FROM actions WHERE universe_id=? ORDER BY id DESC LIMIT ?",
            (universe_id, limit)
        ).fetchall()
    return [{"agent_id": r[0], "island_id": r[1], "turn": r[2],
             "action": r[3], "cost": r[4], "outcome": r[5], "created_at": r[6]}
            for r in rows]
