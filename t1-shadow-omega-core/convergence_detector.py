"""
Mid-stage: Independent Convergence Detection (Depths 1-5)

Depth 1: Same strategy in 3+ universes at same turn = universality proof
Depth 2: Convergence timing → severity tag (≤20=medium, 21-60=high, >60=critical)
Depth 3: Direction convergence via cosine_similarity(fitness_gradient) > 0.8
          (10-20 turns early warning before endpoint convergence)
Depth 4: Ratchet — convergence event sends weak directional signal to all universes
Depth 5: Confidence = 1.0 - (1/N)^(n-1)  [exact p-value: P(coincidence) = (1/N)^(k-1)]
"""
import hashlib
import json
import math
from collections import deque
from typing import Optional


# ── Strategy fingerprinting ────────────────────────────────────────────────────

def _fingerprint(strategy: dict) -> str:
    # Exclude DNA-fixed keys that vary by universe (not emergent behavior)
    # and mutation noise (_n*) and oracle keys
    _EXCLUDE = {"defense_weight", "oracle_boost", "attack_style"}
    keys = sorted(
        k for k in strategy
        if not k.startswith("oracle") and not k.startswith("_n") and k not in _EXCLUDE
    )
    # Quantize floats to 1 decimal; sort lists so shuffled order doesn't break match
    def _q(v):
        if isinstance(v, float):
            return round(v, 1)
        if isinstance(v, list):
            return sorted(str(x) for x in v)
        return v
    sig = "|".join(f"{k}:{_q(strategy[k])}" for k in keys)
    return hashlib.md5(sig.encode()).hexdigest()[:10]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)


# ── Convergence Detector ───────────────────────────────────────────────────────

class ConvergenceDetector:
    """
    Per-turn strategy + fitness tracking across all universes.
    Called from main._run_loop every turn.
    """

    DIRECTION_WINDOW = 10   # turns to compute fitness gradient
    MAX_HISTORY = 200       # cap in-memory history per universe

    def __init__(self, n_universes: int = 5) -> None:
        self.n_universes = n_universes
        # universe_id → deque of (turn, {fp: str, strategy: dict, fitness: float})
        self._history: dict[int, deque] = {i: deque(maxlen=self.MAX_HISTORY) for i in range(n_universes)}
        # universe_id → deque of avg_fitness values (for gradient)
        self._fitness_series: dict[int, deque] = {i: deque(maxlen=self.DIRECTION_WINDOW + 2) for i in range(n_universes)}
        # Ratchet state: set of fingerprints already confirmed as universal
        self._ratchet_fps: set[str] = set()
        # Ratchet signal: broadcasted to all universes after convergence
        self._ratchet_signal: Optional[dict] = None

    def record_turn(self, universe_id: int, agents: list, turn: int, avg_fitness: float) -> None:
        """
        Record defender strategies per universe/turn.
        Defense patterns that independently converge across universes
        represent universally-exploitable vulnerabilities.
        """
        fps = {}
        for a in agents:
            if a.universe_id == universe_id and a.role == "defender":
                fp = _fingerprint(a.strategy)
                fps[fp] = a.strategy
        self._history[universe_id].append({"turn": turn, "fps": fps, "avg_fitness": avg_fitness})
        self._fitness_series[universe_id].append(avg_fitness)

    def _fitness_gradient(self, universe_id: int) -> list[float]:
        """Returns the fitness delta series for direction convergence check."""
        series = list(self._fitness_series[universe_id])
        if len(series) < 2:
            return [0.0]
        return [series[i + 1] - series[i] for i in range(len(series) - 1)]

    def detect(self, turn: int) -> list[dict]:
        """
        Run all depths and return list of convergence events to broadcast.
        """
        events = []

        # Depth 1 + 5: endpoint convergence across universes
        fp_to_universes: dict[str, list[int]] = {}
        for uid, hist in self._history.items():
            if not hist:
                continue
            latest = hist[-1]
            if latest["turn"] != turn:
                continue
            for fp in latest["fps"]:
                fp_to_universes.setdefault(fp, []).append(uid)

        for fp, universes in fp_to_universes.items():
            n = len(universes)
            if n < 3:
                continue

            # Depth 2: severity by turn timing
            if turn <= 20:
                severity = "medium"
            elif turn <= 60:
                severity = "high"
            else:
                severity = "critical"

            # Depth 5: confidence
            confidence = round(1.0 - (1.0 / self.n_universes) ** (n - 1), 4)

            # Depth 4: ratchet
            is_new = fp not in self._ratchet_fps
            if is_new:
                self._ratchet_fps.add(fp)
                # sample strategy from first converging universe
                sample_strat = self._history[universes[0]][-1]["fps"].get(fp, {})
                self._ratchet_signal = {"fp": fp, "strategy": sample_strat}

            events.append({
                "event_type": "convergence",
                "depth": 1,
                "strategy_fp": fp,
                "converged_universes": sorted(universes),
                "turn": turn,
                "confidence": confidence,
                "severity": severity,
                "is_new_archetype": is_new,
                "ratchet_active": bool(self._ratchet_signal),
            })

        # Depth 3: direction convergence (early warning)
        gradients = {uid: self._fitness_gradient(uid) for uid in range(self.n_universes)}
        min_len = min(len(g) for g in gradients.values())
        if min_len >= 3:
            aligned_pairs = []
            for i in range(self.n_universes):
                for j in range(i + 1, self.n_universes):
                    g_i = gradients[i][-min_len:]
                    g_j = gradients[j][-min_len:]
                    sim = _cosine(g_i, g_j)
                    if sim > 0.8:
                        aligned_pairs.append((i, j, round(sim, 4)))
            if len(aligned_pairs) >= 2:
                all_universes = sorted({u for pair in aligned_pairs for u in pair[:2]})
                events.append({
                    "event_type": "direction_convergence",
                    "depth": 3,
                    "aligned_universes": all_universes,
                    "turn": turn,
                    "note": "fitness gradient aligned — endpoint convergence expected in 10-20 turns",
                    "max_cosine": max(p[2] for p in aligned_pairs),
                })

        return events

    def get_ratchet_signal(self) -> Optional[dict]:
        return self._ratchet_signal

    def reset(self) -> None:
        """Clear all state — call when simulation restarts."""
        self._history = {i: deque(maxlen=self.MAX_HISTORY) for i in range(self.n_universes)}
        self._fitness_series = {i: deque(maxlen=self.DIRECTION_WINDOW + 2) for i in range(self.n_universes)}
        self._ratchet_fps = set()
        self._ratchet_signal = None


# Module-level singleton
_detector = ConvergenceDetector(n_universes=5)


def get_detector() -> ConvergenceDetector:
    return _detector
