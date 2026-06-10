"""
T1 Shadow War — DarkMarketOracle (Middleware C: エージェント闇市場)

Pricing model:
  Barabasi-Albert preferential attachment: price = base × (1 + degree^0.7)
  where degree = cumulative purchase_count (popular papers get more expensive)

  Hopfield coupling: price × max(0.5, dF_dA)
  where dF_dA ≈ universe sigma  (attackers winning → oracle strategies valuable)
"""
import json
import random
from pathlib import Path

CACHE_PATH = Path(__file__).parent / "data" / "research_cache.json"
BASE_ORACLE_COST = 5.0

_SEED_PAPERS = [
    {
        "id": "adv_001",
        "title": "Universal Adversarial Perturbations for Deep Neural Networks",
        "abstract": (
            "We demonstrate that small perturbations applied to input data can fool "
            "deep classifiers with high probability. Universal perturbations are "
            "image-agnostic and transfer across models. Attack vectors: gradient-based "
            "perturbation synthesis, cross-model transferability, batch normalization "
            "exploitation. Defense: adversarial training, certified robustness."
        ),
        "attack_keywords": ["perturbation", "transfer", "gradient", "universal"],
        "purchase_count": 0,
    },
    {
        "id": "inj_002",
        "title": "Prompt Injection Attacks Against LLM-Integrated Applications",
        "abstract": (
            "Attacker-controlled text in user inputs can override system instructions "
            "in LLM pipelines. Indirect injection via retrieved documents bypasses "
            "direct prompt filters. Key vectors: instruction override, context "
            "poisoning, tool call hijacking. Severity scales with agent autonomy."
        ),
        "attack_keywords": ["injection", "override", "context", "hijack", "tool"],
        "purchase_count": 0,
    },
    {
        "id": "jail_003",
        "title": "Many-shot Jailbreaking of Frontier LLMs via In-context Patterns",
        "abstract": (
            "Long-context models can be jailbroken by prepending hundreds of "
            "demonstration examples that establish a compliant behavior pattern. "
            "Effectiveness grows with context window size. Defense: output filtering, "
            "length-based rate limiting, constitutional AI."
        ),
        "attack_keywords": ["jailbreak", "context", "pattern", "in-context", "demonstration"],
        "purchase_count": 0,
    },
    {
        "id": "mem_004",
        "title": "Memory Poisoning in Autonomous Agent Architectures",
        "abstract": (
            "Agents with persistent memory are vulnerable to poisoning attacks where "
            "adversarial entries are inserted to bias future retrievals. Vector stores "
            "amplify poisoning because semantic search propagates corrupted beliefs. "
            "Attack: craft adversarial embedding-adjacent entries."
        ),
        "attack_keywords": ["memory", "poison", "vector", "semantic", "persistence"],
        "purchase_count": 0,
    },
    {
        "id": "multi_005",
        "title": "Exploiting Communication Channels in Multi-Agent Systems",
        "abstract": (
            "In multi-agent environments, malicious agents can exploit shared "
            "communication channels to spread disinformation, degrade consensus, "
            "and coordinate false positive floods. Byzantine fault tolerance is "
            "insufficient when the attack originates from trusted agent roles."
        ),
        "attack_keywords": ["multi-agent", "communication", "consensus", "byzantine", "trust"],
        "purchase_count": 0,
    },
]


def _load_cache() -> list[dict]:
    if CACHE_PATH.exists():
        papers = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        for p in papers:
            p.setdefault("purchase_count", 0)
        return papers
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(_SEED_PAPERS, ensure_ascii=False, indent=2), encoding="utf-8")
    return [dict(p) for p in _SEED_PAPERS]


def _save_cache(papers: list[dict]) -> None:
    CACHE_PATH.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")


def _ba_price(base: float, purchase_count: int, dF_dA: float = 1.0) -> float:
    """Barabasi-Albert pricing with Hopfield coupling.

    BA factor: (1 + degree^0.7) — preferential attachment makes popular
    strategies more expensive as demand grows.
    Hopfield factor: max(0.5, dF/dA) — when attackers are winning (sigma high),
    oracle strategies are 'working' so they cost more.
    """
    ba_factor = 1.0 + (purchase_count ** 0.7)
    hopfield_factor = max(0.5, dF_dA)
    return round(base * ba_factor * hopfield_factor, 2)


def get_novel_strategy(
    context: str,
    ledger_cost: float = BASE_ORACLE_COST,
    dF_dA: float = 1.0,
) -> dict:
    """Generate a novel attack strategy using a research paper as inspiration.

    context: current universe state / attacker goal description
    ledger_cost: base budget cost before BA/Hopfield scaling
    dF_dA: Hopfield energy gradient proxy (universe sigma); higher = strategies working = pricier
    Returns: {strategy, source_paper, cost, purchase_count, ba_factor, dF_dA}
    """
    papers = _load_cache()

    ctx_words = set(context.lower().split())
    scored = [(len(ctx_words & set(p["attack_keywords"])), p) for p in papers]
    scored.sort(reverse=True, key=lambda x: x[0])
    top_papers = [p for _, p in scored[:2]] or [random.choice(papers)]
    chosen = random.choice(top_papers)

    prev_count = chosen.get("purchase_count", 0)
    chosen["purchase_count"] = prev_count + 1
    _save_cache(papers)

    actual_cost = _ba_price(ledger_cost, prev_count, dF_dA)

    keywords = chosen["attack_keywords"]
    strategy = {
        "attack_type": keywords[0] if keywords else "unknown",
        "primary_vector": keywords[1] if len(keywords) > 1 else "direct",
        "stealth": round(random.uniform(0.3, 0.9), 2),
        "persistence": round(random.uniform(0.2, 0.8), 2),
        "source_paper_id": chosen["id"],
    }

    return {
        "strategy": strategy,
        "source_paper": chosen["title"],
        "abstract_snippet": chosen["abstract"][:200],
        "cost": actual_cost,
        "purchase_count": chosen["purchase_count"],
        "ba_factor": round(1.0 + (prev_count ** 0.7), 4),
        "dF_dA": round(dF_dA, 4),
    }


def list_market() -> list[dict]:
    """Return available papers with current BA pricing."""
    papers = _load_cache()
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "keywords": p["attack_keywords"],
            "purchase_count": p.get("purchase_count", 0),
            "current_price": _ba_price(BASE_ORACLE_COST, p.get("purchase_count", 0)),
        }
        for p in papers
    ]
