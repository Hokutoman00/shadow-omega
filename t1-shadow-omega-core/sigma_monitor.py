"""
Mid-stage: σ統一理論モニター

σ = 1 が 4学問の合流点:
  - 複雑系: Lyapunov λ ≈ 0 (カオスの縁)
  - ネットワーク浸透理論: 浸透閾値 σ = 1
  - 神経科学 Neural Avalanche: 臨界分岐 σ = 1
  - Hopfield network: エネルギー極小 dE/dt = 0

このモジュールは各宇宙のσを追跡し、
σが目標値から外れた宇宙に「連鎖感染」シグナルを送る。
"""
import math
from collections import deque
from typing import Optional


SIGMA_TARGET_DEFAULT = 1.0
EDGE_OF_CHAOS_BAND = 0.08     # |σ - 1| < 0.08 = Edge of Chaos ゾーン
CHAIN_INFECTION_STRENGTH = 0.05  # 連鎖感染ナッジの強さ


class SigmaMonitor:
    """
    各宇宙のσ値を追跡する。
    σは battle win_rate から以下の式で算出:
      sigma = 0.5 + attacker_win_rate  (win_rate=0.5 → sigma=1.0)
    """

    HISTORY_LEN = 30

    def __init__(self, n_universes: int = 5) -> None:
        self.n_universes = n_universes
        self._sigma_history: dict[int, deque] = {
            i: deque(maxlen=self.HISTORY_LEN) for i in range(n_universes)
        }
        self._targets: dict[int, float] = {}

    def set_target(self, universe_id: int, sigma_target: float) -> None:
        self._targets[universe_id] = sigma_target

    def update(self, universe_id: int, sigma: float) -> None:
        self._sigma_history[universe_id].append(sigma)

    def current_sigma(self, universe_id: int) -> float:
        hist = self._sigma_history[universe_id]
        if not hist:
            return 1.0
        return hist[-1]

    def mean_sigma(self, universe_id: int, window: int = 10) -> float:
        hist = list(self._sigma_history[universe_id])[-window:]
        if not hist:
            return 1.0
        return sum(hist) / len(hist)

    def is_edge_of_chaos(self, universe_id: int) -> bool:
        return abs(self.mean_sigma(universe_id) - 1.0) < EDGE_OF_CHAOS_BAND

    def sigma_label(self, universe_id: int) -> str:
        s = self.mean_sigma(universe_id)
        if abs(s - 1.0) < EDGE_OF_CHAOS_BAND:
            return "edge_of_chaos"
        elif s > 1.0:
            return "chaotic"
        else:
            return "stable"

    def check_chain_infection(self, universe_states: list[dict]) -> list[dict]:
        """
        Edge of Chaos に到達した宇宙が他の宇宙に
        「この方向に何かある」という弱いシグナルを送る。
        Returns: chain_infection イベントのリスト
        """
        events = []
        for state in universe_states:
            uid = state.get("id", -1)
            sigma = state.get("sigma", 1.0)
            self.update(uid, sigma)

        for state in universe_states:
            uid = state.get("id", -1)
            if not self.is_edge_of_chaos(uid):
                continue
            # この宇宙が Edge of Chaos → 他の宇宙に nudge
            target_sigma = self._targets.get(uid, SIGMA_TARGET_DEFAULT)
            targets_away = [
                s["id"] for s in universe_states
                if s.get("id", -1) != uid
                and abs(s.get("sigma", 1.0) - 1.0) > EDGE_OF_CHAOS_BAND
            ]
            if targets_away:
                events.append({
                    "event_type": "chain_infection",
                    "source_universe": uid,
                    "target_universes": targets_away,
                    "sigma_source": round(self.current_sigma(uid), 4),
                    "nudge_strength": CHAIN_INFECTION_STRENGTH,
                    "note": f"U{uid} at edge_of_chaos (σ≈1) → weak signal to {targets_away}",
                })
        return events

    def sigma_report(self) -> list[dict]:
        """全宇宙の σ サマリーを返す。"""
        return [
            {
                "universe_id": uid,
                "sigma": round(self.current_sigma(uid), 4),
                "mean_sigma_10": round(self.mean_sigma(uid, 10), 4),
                "label": self.sigma_label(uid),
                "target": self._targets.get(uid, SIGMA_TARGET_DEFAULT),
            }
            for uid in range(self.n_universes)
        ]


# Module-level singleton
_monitor = SigmaMonitor(n_universes=5)


def get_monitor() -> SigmaMonitor:
    return _monitor
