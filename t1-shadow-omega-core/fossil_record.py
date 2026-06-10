"""
Post-stage: 化石記録 + 収束確信度スコア

SurvivorRecord を受け取り、宇宙をまたいで独立収束を検出する。
同一 strategy_id (または類似ハッシュ) が複数宇宙で同ターンに出現 → ArchetypeRule を生成する。
"""
import hashlib
import json
import math
import sqlite3
import datetime
from typing import TypedDict, Optional


class SurvivorRecord(TypedDict):
    strategy_json: dict
    universe_id: int
    survival_turns: int
    fitness: float


class ConvergenceEvent(TypedDict):
    strategy_id: str
    converged_universes: list[int]
    turn: int
    confidence: float


class ArchetypeRule(TypedDict):
    rule_id: str
    confidence: float
    severity: str           # "medium" | "high" | "critical"
    fossil_generations: int
    eslint_code: str


# ── Strategy fingerprint ──────────────────────────────────────────────────────

def _strategy_id(strategy: dict) -> str:
    """戦略の主要キーから不変ハッシュを生成する。"""
    keys = sorted(strategy.keys())
    sig = "|".join(f"{k}:{strategy[k]}" for k in keys)
    return hashlib.md5(sig.encode()).hexdigest()[:12]


def _similarity(a: dict, b: dict) -> float:
    """Jaccard 類似度 (キー集合ベース)。"""
    sa, sb = set(a.keys()), set(b.keys())
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


# ── Convergence detection ─────────────────────────────────────────────────────

def detect_convergence(
    survivors: list[SurvivorRecord],
    turn: int,
    sim_threshold: float = 0.75,
    min_universes: int = 3,
) -> list[ConvergenceEvent]:
    """
    同一ターン内の survivor 群から、複数宇宙で独立出現した戦略を検出する。
    min_universes 個以上の宇宙で類似戦略が出現すれば ConvergenceEvent を返す。
    """
    if not survivors:
        return []

    groups: list[list[SurvivorRecord]] = []
    used = [False] * len(survivors)

    for i, s in enumerate(survivors):
        if used[i]:
            continue
        group = [s]
        used[i] = True
        for j, t in enumerate(survivors):
            if used[j]:
                continue
            if t["universe_id"] != s["universe_id"] and _similarity(s["strategy_json"], t["strategy_json"]) >= sim_threshold:
                group.append(t)
                used[j] = True
        if len(group) >= min_universes:
            groups.append(group)

    events: list[ConvergenceEvent] = []
    for group in groups:
        universe_ids = [r["universe_id"] for r in group]
        n = len(universe_ids)
        confidence = round(1.0 - (1.0 / 5) ** (n - 1), 4)
        strategy_id = _strategy_id(group[0]["strategy_json"])
        events.append(ConvergenceEvent(
            strategy_id=strategy_id,
            converged_universes=sorted(universe_ids),
            turn=turn,
            confidence=confidence,
        ))
    return events


# ── Severity tagging ──────────────────────────────────────────────────────────

def _severity(turn: int) -> str:
    if turn <= 20:
        return "medium"
    elif turn <= 60:
        return "high"
    return "critical"


# ── Fossil store ──────────────────────────────────────────────────────────────

class FossilStore:
    """
    化石記録を in-memory dict に保持する。
    key = strategy_id, value = {strategy_json, appearances: [{turn, universes, confidence}]}
    """

    def __init__(self) -> None:
        self._fossils: dict[str, dict] = {}

    def record(self, event: ConvergenceEvent, strategy_json: dict) -> int:
        """
        収束イベントを記録する。同一 strategy_id の再出現は世代数を増やす。
        Returns: fossil_generations (この戦略が何世代生存したか)
        """
        sid = event["strategy_id"]
        if sid not in self._fossils:
            self._fossils[sid] = {"strategy_json": strategy_json, "appearances": []}
        self._fossils[sid]["appearances"].append({
            "turn": event["turn"],
            "universes": event["converged_universes"],
            "confidence": event["confidence"],
        })
        return len(self._fossils[sid]["appearances"])

    def to_archetype_rule(self, event: ConvergenceEvent, strategy_json: dict) -> ArchetypeRule:
        """収束イベントから ESLint 互換の ArchetypeRule を生成する。"""
        fossil_gen = self.record(event, strategy_json)
        sev = _severity(event["turn"])
        rule_id = f"shadow-omega/{event['strategy_id']}"
        eslint_code = (
            f"// [shadow-omega] {rule_id}\n"
            f"// confidence: {int(event['confidence'] * 100)}% "
            f"({len(event['converged_universes'])}/5 universes)\n"
            f"// severity: {sev} | turn: {event['turn']} | fossil_gen: {fossil_gen}"
        )
        return ArchetypeRule(
            rule_id=rule_id,
            confidence=event["confidence"],
            severity=sev,
            fossil_generations=fossil_gen,
            eslint_code=eslint_code,
        )

    def obsolescence_prediction(self, strategy_id: str) -> Optional[str]:
        """
        化石世代数から防衛戦略の陳腐化予測を返す。
        3世代以上陳腐化 → "UPGRADE PRIORITY" 警告。
        """
        fossil = self._fossils.get(strategy_id)
        if not fossil:
            return None
        gen = len(fossil["appearances"])
        if gen >= 3:
            return f"UPGRADE PRIORITY: strategy {strategy_id} deprecated in {gen} generations. Defense lifespan is short."
        if gen == 2:
            return f"WATCH: strategy {strategy_id} seen in 2 generations. Monitor for obsolescence."
        return None

    def all_archetypes(self) -> list[dict]:
        """記録済み全アーキタイプを辞書リストで返す。"""
        out = []
        for sid, data in self._fossils.items():
            last = data["appearances"][-1]
            out.append({
                "strategy_id": sid,
                "fossil_generations": len(data["appearances"]),
                "last_turn": last["turn"],
                "last_confidence": last["confidence"],
                "last_universes": last["universes"],
            })
        return out


# ── Module-level singleton ────────────────────────────────────────────────────

_store = FossilStore()


def get_store() -> FossilStore:
    return _store
