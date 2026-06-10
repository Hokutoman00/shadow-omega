"""
Pre-stage: AST → Shannon Entropy → Planet Coordinates

Python built-in ast module でソースコードを解析し、
コールグラフのエントロピー・脆弱性スコア・トポロジー型を計算する。
"""
import ast
import math
import random
import json
import hashlib
from typing import TypedDict

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False


class PlanetInit(TypedDict):
    planet_id: str
    universe_id: int
    vulnerability_score: float
    entropy: float
    topology_type: str
    node_count: int
    edge_count: int


# ── AST parsing ────────────────────────────────────────────────────────────────

def _extract_call_graph(source: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Python ソースから関数名ノードと呼び出しエッジを抽出する。"""
    nodes: list[str] = []
    edges: list[tuple[str, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return nodes, edges

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes.append(node.name)
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        edges.append((node.name, child.func.id))
                    elif isinstance(child.func, ast.Attribute):
                        edges.append((node.name, child.func.attr))
    return nodes, edges


# ── Metrics ────────────────────────────────────────────────────────────────────

def _shannon_entropy(degree_seq: list[int]) -> float:
    """次数分布のシャノンエントロピー H = -Σ p(k) log2 p(k)"""
    total = sum(degree_seq)
    if total == 0:
        return 0.0
    return -sum(
        (d / total) * math.log2(d / total)
        for d in degree_seq if d > 0
    )


def _detect_topology(degree_seq: list[int]) -> str:
    """次数分布のヒューリスティックからトポロジー型を判定する。"""
    if len(degree_seq) < 3:
        return "random"
    max_d = max(degree_seq)
    mean_d = sum(degree_seq) / len(degree_seq)
    ratio = max_d / max(mean_d, 1.0)
    if ratio > 5.0:
        return "scale_free"       # ハブ支配
    elif ratio > 2.5:
        return "small_world"      # 中程度クラスタリング
    elif mean_d > 3.0:
        return "hierarchical"     # 多層クラスタ
    elif max_d <= 4:
        return "lattice"          # 格子型
    else:
        return "random"


def analyze_source(source: str) -> dict:
    """
    Python ソースを解析して脆弱性メトリクスを返す。
    Returns: {entropy, vulnerability_score, topology_type, node_count, edge_count}
    """
    nodes, edges = _extract_call_graph(source)

    if not nodes:
        return dict(entropy=0.0, vulnerability_score=0.1,
                    topology_type="random", node_count=0, edge_count=0)

    if _HAS_NX:
        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        G.add_edges_from([(u, v) for u, v in edges if u in G and v in G])
        degree_seq = [d for _, d in G.degree()]
    else:
        deg: dict[str, int] = {n: 0 for n in nodes}
        for _, dst in edges:
            if dst in deg:
                deg[dst] += 1
        degree_seq = list(deg.values())

    raw_entropy = _shannon_entropy(degree_seq)
    max_entropy = math.log2(max(len(nodes), 2))
    norm_entropy = round(min(raw_entropy / max(max_entropy, 1.0), 1.0), 4)

    topology = _detect_topology(degree_seq)
    edge_density = len(edges) / max(len(nodes) ** 2, 1)
    vuln_score = round(min(1.0, norm_entropy * 0.6 + edge_density * 0.4), 4)

    return dict(
        entropy=norm_entropy,
        vulnerability_score=vuln_score,
        topology_type=topology,
        node_count=len(nodes),
        edge_count=len(edges),
    )


# ── Planet generation ──────────────────────────────────────────────────────────

def source_to_planets(source: str, universe_id: int, file_tag: str = "src") -> list[PlanetInit]:
    """
    ソースコードを PlanetInit リストに変換する。
    トップレベルの関数/クラスを惑星1つとして扱う。
    """
    planets: list[PlanetInit] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return planets

    top_nodes = [n for n in ast.iter_child_nodes(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]

    if not top_nodes:
        m = analyze_source(source)
        return [PlanetInit(planet_id=f"{file_tag}_0", universe_id=universe_id, **m)]

    for i, node in enumerate(top_nodes):
        seg = ast.get_source_segment(source, node) or ""
        m = analyze_source(seg)
        planets.append(PlanetInit(
            planet_id=f"{file_tag}_{i}",
            universe_id=universe_id,
            **m,
        ))
    return planets


def generate_demo_planets(universe_id: int, n: int = 20) -> list[PlanetInit]:
    """
    実ソースがない場合のデモ用合成惑星を生成する。
    同じ universe_id は常に同じ惑星配置を返す（シード固定）。
    """
    rng = random.Random(universe_id * 1337 + 42)
    topologies = ["scale_free", "small_world", "random", "hierarchical", "lattice"]
    planets = []
    for i in range(n):
        entropy = round(rng.uniform(0.2, 0.95), 4)
        vuln = round(min(1.0, entropy * rng.uniform(0.5, 1.2)), 4)
        planets.append(PlanetInit(
            planet_id=f"u{universe_id}_p{i}",
            universe_id=universe_id,
            vulnerability_score=vuln,
            entropy=entropy,
            topology_type=rng.choice(topologies),
            node_count=rng.randint(3, 30),
            edge_count=rng.randint(2, 50),
        ))
    return planets
