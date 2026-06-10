"""
Mid-stage Layer 4: Topological Data Analysis (TDA)

H0 barcode: persistent connected components of strategy space
  - H0 count high = diverse clusters (universes independent)
  - H0 -> 1 = all strategies converging to single cluster
H1 barcode: persistent loops in strategy space
  - H1 count > 0 = cyclic attack-defense alternation patterns

Uses ripser if available, falls back to Union-Find approximation.
"""
import math
from typing import NamedTuple

try:
    from ripser import ripser as _ripser
    import numpy as _np
    _HAS_RIPSER = True
except ImportError:
    _HAS_RIPSER = False


class TDAReport(NamedTuple):
    universe_id: int
    turn: int
    h0_persistence_max: float
    h0_component_count: int
    h1_cycle_count: int
    barcode_h0: list
    barcode_h1: list
    method: str


def _strategy_to_vector(s: dict) -> list:
    timing_map = {"burst": 0.0, "spread": 0.5, "periodic": 1.0}
    return [
        float(s.get("threshold", 0.5)),
        float(s.get("stealth", 0.5)),
        timing_map.get(str(s.get("timing", "burst")), 0.0),
        float(s.get("defense_weight", 0.5)),
        float(s.get("coverage", 0.5)),
        float(s.get("detection_threshold", 0.5)),
    ]


def _euclid(a: list, b: list) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _approx_h0(points: list) -> list:
    """Vietoris-Rips H0 approximation via Union-Find on sorted edge list."""
    n = len(points)
    parent = list(range(n))
    birth = [0.0] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges = sorted(
        [(i, j, _euclid(points[i], points[j])) for i in range(n) for j in range(i + 1, n)],
        key=lambda e: e[2],
    )
    barcode = []
    for i, j, d in edges:
        pi, pj = find(i), find(j)
        if pi != pj:
            later = max(pi, pj, key=lambda c: birth[c])
            barcode.append((birth[later], d))
            parent[pi] = parent[pj] = min(pi, pj, key=lambda c: birth[c])
    for s in set(find(i) for i in range(n)):
        barcode.append((birth[s], float("inf")))
    return barcode


def compute_barcode(universe_id: int, turn: int, agents: list) -> TDAReport:
    """Compute TDA barcode for all attackers in a given universe."""
    attackers = [a for a in agents if a.universe_id == universe_id and a.role == "attacker"]
    if len(attackers) < 3:
        return TDAReport(universe_id, turn, 0.0, len(attackers), 0, [], [], "approx")

    points = [_strategy_to_vector(a.strategy) for a in attackers]

    if _HAS_RIPSER:
        pc = _np.array(points, dtype=float)
        dgms = _ripser(pc, maxdim=1)["dgms"]
        h0_raw = [(float(b), float(d)) for b, d in dgms[0] if not math.isinf(d)]
        h1_raw = [(float(b), float(d)) for b, d in dgms[1] if not math.isinf(d)]
        method = "ripser"
    else:
        raw = _approx_h0(points)
        h0_raw = [(b, d) for b, d in raw if not math.isinf(d)]
        h1_raw = []
        method = "approx"

    noise = 0.05
    h0_p = [(b, d) for b, d in h0_raw if (d - b) > noise]
    h1_p = [(b, d) for b, d in h1_raw if (d - b) > noise]
    h0_max = max((d - b for b, d in h0_p), default=0.0)

    return TDAReport(
        universe_id=universe_id,
        turn=turn,
        h0_persistence_max=round(h0_max, 4),
        h0_component_count=len(h0_p),
        h1_cycle_count=len(h1_p),
        barcode_h0=[(round(b, 3), round(d, 3)) for b, d in h0_p[:10]],
        barcode_h1=[(round(b, 3), round(d, 3)) for b, d in h1_p[:5]],
        method=method,
    )
