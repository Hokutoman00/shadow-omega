"""
Post-stage: Reservoir Computing readout + Information Bottleneck compression

シミュレーション結果（200エージェントの状態）をリザバーとして扱い、
Ridge regression readout で CWE カテゴリを予測する。
IB パラメータ β を FP フィードバックで動的に調整する。
"""
import math
import hashlib
import json
from typing import Optional

try:
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    _HAS_SK = True
except ImportError:
    _HAS_SK = False


# ── Reservoir state ───────────────────────────────────────────────────────────

class ReservoirReadout:
    """
    シミュレーション宇宙群 = リザバー (学習しない)
    Ridge regression = 読み出し層 (唯一の学習器)

    X: (n_turns, n_features) — 各ターンの全宇宙・全エージェントの統計的特徴量
    y: (n_turns,) — 対応する CWE カテゴリ label (整数インデックス)
    """

    def __init__(self, alpha: float = 0.1) -> None:
        self.alpha = alpha
        self._fitted = False
        if _HAS_SK:
            self._model = Ridge(alpha=alpha)
            self._scaler = StandardScaler()
        else:
            self._model = None
            self._scaler = None

    def _fallback_predict(self, features: list[float]) -> int:
        """numpy/sklearn なしの最小フォールバック: 最大値インデックスを返す。"""
        return features.index(max(features)) if features else 0

    def extract_features(self, universe_states: list[dict]) -> list[float]:
        """
        universe_states: UniverseOrchestrator.status() のリスト (全宇宙)
        Returns: 固定長の特徴量ベクトル (16 次元)
        """
        n = max(len(universe_states), 1)
        fitnesses = [u.get("mean_fitness", 0.0) for u in universe_states]
        sigmas = [u.get("sigma", 1.0) for u in universe_states]
        def_rates = [u.get("defender_win_rate", 0.5) for u in universe_states]
        turns = [float(u.get("turn", 0)) for u in universe_states]

        mean_fitness = sum(fitnesses) / n
        std_fitness = math.sqrt(sum((f - mean_fitness) ** 2 for f in fitnesses) / n)
        mean_sigma = sum(sigmas) / n
        std_sigma = math.sqrt(sum((s - mean_sigma) ** 2 for s in sigmas) / n)
        mean_def = sum(def_rates) / n
        max_def = max(def_rates)
        min_def = min(def_rates)
        turn_avg = sum(turns) / n

        # σ = 1 からの距離 (Edge of Chaos 接近度)
        sigma_dist = abs(mean_sigma - 1.0)
        # 宇宙間の多様性 (分散)
        diversity = std_fitness + std_sigma

        return [
            mean_fitness, std_fitness,
            mean_sigma, std_sigma,
            mean_def, max_def, min_def,
            turn_avg,
            sigma_dist,
            diversity,
            float(n),
            sum(1 for s in sigmas if abs(s - 1.0) < 0.1) / n,  # chaos ratio
            max(fitnesses) - min(fitnesses),  # fitness spread
            sum(1 for d in def_rates if d > 0.6) / n,  # high-defense ratio
            sum(1 for d in def_rates if d < 0.1) / n,  # dying universe ratio
            mean_fitness * mean_def,  # interaction term
        ]

    def fit(self, X: list[list[float]], y: list[int]) -> None:
        """読み出し層を学習させる。"""
        if not X or not y:
            return
        if _HAS_SK:
            X_np = np.array(X)
            y_np = np.array(y)
            X_scaled = self._scaler.fit_transform(X_np)
            self._model.fit(X_scaled, y_np)
            self._fitted = True

    def predict(self, features: list[float]) -> int:
        """CWE カテゴリインデックスを予測する (0-indexed)。"""
        if not _HAS_SK or not self._fitted:
            return self._fallback_predict(features)
        X = np.array(features).reshape(1, -1)
        X_scaled = self._scaler.transform(X)
        return int(round(float(self._model.predict(X_scaled)[0])))


# ── Information Bottleneck compression ───────────────────────────────────────

CWE_CATEGORIES = [
    "CWE-79",    # XSS
    "CWE-89",    # SQL Injection
    "CWE-22",    # Path Traversal
    "CWE-502",   # Deserialization
    "CWE-287",   # Improper Authentication
    "CWE-200",   # Information Exposure
    "CWE-352",   # CSRF
    "CWE-476",   # NULL Pointer Dereference
]


class IBCompressor:
    """
    Information Bottleneck: X = simulation patterns, Y = CWE categories, Z = defense rules
    β パラメータで圧縮率を制御する。β が高い → より多くの情報を捨てる。
    FP フィードバックで universe ごとに β を動的に調整する。
    """

    def __init__(self, base_beta: float = 1.0) -> None:
        self._beta: dict[int, float] = {}  # universe_id → β
        self.base_beta = base_beta

    def get_beta(self, universe_id: int) -> float:
        return self._beta.get(universe_id, self.base_beta)

    def apply_fp_feedback(self, universe_id: int, fp_rate: float, threshold: float = 0.3) -> None:
        """
        fp_rate > threshold の宇宙の β を上げる (より強く圧縮)。
        具体的: β += 0.5 × (fp_rate - threshold) / (1 - threshold)
        """
        if fp_rate > threshold:
            delta = 0.5 * (fp_rate - threshold) / max(1.0 - threshold, 1e-9)
            current = self.get_beta(universe_id)
            self._beta[universe_id] = round(min(current + delta, 5.0), 4)

    def compress(
        self,
        archetype_rules: list[dict],
        universe_id: int,
        readout: ReservoirReadout,
        universe_states: list[dict],
    ) -> list[dict]:
        """
        archetype_rules をリザバー予測 CWE カテゴリで絞り込む。
        β が高いほど低 confidence ルールを捨てる。
        """
        beta = self.get_beta(universe_id)
        features = readout.extract_features(universe_states)
        cwe_idx = readout.predict(features)
        cwe_label = CWE_CATEGORIES[cwe_idx % len(CWE_CATEGORIES)]

        confidence_threshold = 0.15 + (beta - 1.0) * 0.1
        compressed = [
            r for r in archetype_rules
            if r.get("confidence", 0) >= confidence_threshold
        ]
        for r in compressed:
            r["predicted_cwe"] = cwe_label
            r["ib_beta"] = beta
        return compressed


# ── Module-level singletons ───────────────────────────────────────────────────

_readout = ReservoirReadout(alpha=0.1)
_compressor = IBCompressor(base_beta=1.0)


def get_readout() -> ReservoirReadout:
    return _readout


def get_compressor() -> IBCompressor:
    return _compressor
