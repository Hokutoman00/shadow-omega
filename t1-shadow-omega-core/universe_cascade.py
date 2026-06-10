"""
Mid-stage: 宇宙の死 + 免疫記憶 (Universe Death & Immune Memory)

Depth 6: 死亡条件 defender_win_rate < 0.1 が DEATH_THRESHOLD ターン継続
Depth 7: 化石記録 → 陳腐化予測 (fossil_record と連携)
Depth 8: 免疫記憶を引き継いで宇宙を再生

死亡した宇宙は archetype strategies を引き継ぎ、
新しい初期戦略として再生する。
"""
from collections import deque
from typing import Optional


DEATH_THRESHOLD = 10        # defender_win_rate < 0.1 がこのターン数続いたら死
WEAK_WIN_RATE_THRESHOLD = 0.1


class UniverseCascade:
    """
    宇宙の生死を管理するクラス。
    main._run_loop から毎ターン呼び出される。
    """

    def __init__(self, n_universes: int = 5, death_threshold: int = DEATH_THRESHOLD) -> None:
        self.n_universes = n_universes
        self.death_threshold = death_threshold

        # universe_id → deque of defender_win_rate (recent turns)
        self._win_rate_history: dict[int, deque] = {
            i: deque(maxlen=death_threshold + 5) for i in range(n_universes)
        }
        # universe_id → list of inherited archetype strategies (免疫記憶)
        self._immune_memory: dict[int, list[dict]] = {i: [] for i in range(n_universes)}
        # universe_id → death count (何回死んだか = fossil_generations)
        self._death_count: dict[int, int] = {i: 0 for i in range(n_universes)}
        # universe_id → is_alive
        self._alive: dict[int, bool] = {i: True for i in range(n_universes)}

    def record_win_rate(self, universe_id: int, defender_win_rate: float) -> None:
        self._win_rate_history[universe_id].append(defender_win_rate)

    def _consecutive_low(self, universe_id: int) -> int:
        """直近で defender_win_rate < threshold が続いたターン数を返す。"""
        history = list(self._win_rate_history[universe_id])
        count = 0
        for rate in reversed(history):
            if rate < WEAK_WIN_RATE_THRESHOLD:
                count += 1
            else:
                break
        return count

    def check_deaths(self, turn: int) -> list[dict]:
        """
        死亡条件を満たした宇宙のリストを返す。
        呼び出し側は該当宇宙の reset を実行する。
        """
        events = []
        for uid in range(self.n_universes):
            if not self._alive[uid]:
                continue
            consecutive = self._consecutive_low(uid)
            if consecutive >= self.death_threshold:
                self._alive[uid] = False
                self._death_count[uid] += 1
                events.append({
                    "event_type": "universe_death",
                    "universe_id": uid,
                    "turn": turn,
                    "death_count": self._death_count[uid],
                    "consecutive_low_turns": consecutive,
                    "immune_memory_size": len(self._immune_memory[uid]),
                    "note": f"U{uid} collapsed after {consecutive} turns of defender_win_rate < {WEAK_WIN_RATE_THRESHOLD}",
                })
        return events

    def inherit_archetype(self, universe_id: int, archetypes: list[dict]) -> None:
        """
        死亡時に収束済みアーキタイプ戦略を免疫記憶として保存する。
        archetypes: ArchetypeRule リスト (fossil_record から取得)
        """
        for a in archetypes:
            if a not in self._immune_memory[universe_id]:
                self._immune_memory[universe_id].append(a)
        # 最大20個に制限
        self._immune_memory[universe_id] = self._immune_memory[universe_id][-20:]

    def rebirth(self, universe_id: int, turn: int) -> dict:
        """
        死亡した宇宙を免疫記憶付きで再生する。
        Returns: rebirth イベント (main から broadcast)
        """
        self._alive[universe_id] = True
        self._win_rate_history[universe_id].clear()
        memory = self._immune_memory[universe_id]
        return {
            "event_type": "universe_rebirth",
            "universe_id": universe_id,
            "turn": turn,
            "death_count": self._death_count[universe_id],
            "inherited_archetypes": len(memory),
            "memory_rule_ids": [m.get("rule_id", "?") for m in memory[:5]],
            "note": f"U{universe_id} reborn with {len(memory)} immune archetypes",
        }

    def is_alive(self, universe_id: int) -> bool:
        return self._alive.get(universe_id, True)

    def get_immune_memory(self, universe_id: int) -> list[dict]:
        return list(self._immune_memory[universe_id])

    def status(self) -> list[dict]:
        return [
            {
                "universe_id": uid,
                "alive": self._alive[uid],
                "death_count": self._death_count[uid],
                "consecutive_low": self._consecutive_low(uid),
                "immune_memory_size": len(self._immune_memory[uid]),
            }
            for uid in range(self.n_universes)
        ]


# Module-level singleton
_cascade = UniverseCascade(n_universes=5)


def get_cascade() -> UniverseCascade:
    return _cascade
