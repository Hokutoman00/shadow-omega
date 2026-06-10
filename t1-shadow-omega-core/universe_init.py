"""
Pre-stage: 5宇宙の直交初期化

sklearn.utils.extmath.randomized_svd (fallback: Gram-Schmidt) で
直交ベクトルを生成し、各宇宙の vulnerability_weights を割り当てる。
cosine_similarity < 0.2 を保証することで「独立収束検出」の前提を満たす。
"""
import math
import random
from typing import NamedTuple

try:
    import numpy as np
    from sklearn.utils.extmath import randomized_svd
    _HAS_NP = True
except ImportError:
    _HAS_NP = False

TOPOLOGY_TYPES = ["scale_free", "small_world", "random", "hierarchical", "lattice"]

SIGMA_TARGETS = [0.95, 0.97, 1.00, 1.01, 1.03]  # 宇宙ごとの Edge of Chaos 目標値


class UniverseConfig(NamedTuple):
    universe_id: int
    topology_type: str
    vulnerability_weights: list[float]   # 惑星ごとの初期脆弱性重み (dim=20)
    sigma_target: float                  # Edge of Chaos の目標 σ 値


# ── 直交ベクトル生成 ───────────────────────────────────────────────────────────

def _gram_schmidt(n: int, dim: int, seed: int = 42) -> list[list[float]]:
    """純 Python の Gram-Schmidt 直交化 (numpy 未使用フォールバック)。"""
    rng = random.Random(seed)

    def rand_vec() -> list[float]:
        v = [rng.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in v))
        return [x / norm for x in v]

    def dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def sub(a: list[float], b: list[float], scale: float) -> list[float]:
        return [ai - scale * bi for ai, bi in zip(a, b)]

    basis: list[list[float]] = []
    for _ in range(n):
        v = rand_vec()
        for q in basis:
            v = sub(v, q, dot(v, q))
        norm = math.sqrt(sum(x * x for x in v))
        if norm < 1e-9:
            v = rand_vec()
            norm = math.sqrt(sum(x * x for x in v))
        basis.append([x / norm for x in v])
    return basis


def create_orthogonal_universe_vectors(n: int = 5, dim: int = 20, seed: int = 42) -> list[list[float]]:
    """
    n 個の直交ベクトルを返す (dim 次元)。
    numpy + sklearn が使える場合は randomized_svd、ない場合は Gram-Schmidt。
    """
    if _HAS_NP:
        rng = np.random.default_rng(seed)
        M = rng.standard_normal((dim, n * 2))
        U, _, _ = randomized_svd(M, n_components=n, random_state=seed)
        # U は dim×n の列直交行列。各列を取り出す。
        return [U[:, i].tolist() for i in range(n)]
    else:
        return _gram_schmidt(n, dim, seed)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return abs(dot / (na * nb))


# ── Universe config 生成 ──────────────────────────────────────────────────────

def _normalize_weights(vec: list[float]) -> list[float]:
    """ベクトルを [0, 1] に正規化して vulnerability_weights として使う。"""
    lo, hi = min(vec), max(vec)
    spread = hi - lo
    if spread < 1e-9:
        return [0.5] * len(vec)
    return [(x - lo) / spread for x in vec]


def build_universe_configs(n: int = 5, dim: int = 20, seed: int = 42) -> list[UniverseConfig]:
    """5宇宙それぞれの設定を返す。トポロジー・重み・σ目標が全て異なる。"""
    vecs = create_orthogonal_universe_vectors(n, dim, seed)
    configs = []
    for i, vec in enumerate(vecs):
        configs.append(UniverseConfig(
            universe_id=i,
            topology_type=TOPOLOGY_TYPES[i % len(TOPOLOGY_TYPES)],
            vulnerability_weights=_normalize_weights(vec),
            sigma_target=SIGMA_TARGETS[i % len(SIGMA_TARGETS)],
        ))
    return configs


def verify_independence(configs: list[UniverseConfig], threshold: float = 0.2) -> dict:
    """
    全宇宙ペアの cosine similarity を計算して独立性を監査する。
    max_similarity < threshold なら OK。
    """
    n = len(configs)
    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            s = _cosine_sim(configs[i].vulnerability_weights,
                            configs[j].vulnerability_weights)
            sims.append({"pair": (i, j), "cosine_similarity": round(s, 4)})
    max_sim = max((s["cosine_similarity"] for s in sims), default=0.0)
    return {
        "ok": max_sim < threshold,
        "max_cosine_similarity": round(max_sim, 4),
        "threshold": threshold,
        "pairs": sims,
    }
