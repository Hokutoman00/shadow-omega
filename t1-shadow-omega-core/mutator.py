"""
T1 Shadow War — StrategyMutator (Middleware B: エイリアンコード)

Mutates attack/defense strategy JSON to produce "alien" variants that are
structurally different but semantically similar. Makes strategies harder to
pattern-match by defenders.
"""
import copy
import json
import random


def _jaccard(a: dict, b: dict) -> float:
    """Jaccard similarity on key sets."""
    ka, kb = set(a.keys()), set(b.keys())
    if not ka and not kb:
        return 1.0
    return len(ka & kb) / len(ka | kb)


def mutate(strategy: dict, intensity: float = 0.3) -> dict:
    """
    Mutate a strategy dict:
      - Numeric values: perturb by ±intensity * value
      - Add dummy keys (obfuscation noise)
      - Shuffle list elements

    Returns mutated copy.
    """
    if not isinstance(strategy, dict):
        return strategy

    mutated = copy.deepcopy(strategy)
    for key in list(mutated.keys()):
        val = mutated[key]
        if isinstance(val, (int, float)):
            delta = val * intensity * random.uniform(-1.0, 1.0)
            mutated[key] = round(val + delta, 4)
        elif isinstance(val, list):
            if random.random() < intensity:
                random.shuffle(mutated[key])
        elif isinstance(val, str) and random.random() < intensity * 0.5:
            mutated[key] = val[::-1] if len(val) <= 8 else val  # short string obfuscation

    # Inject dummy keys
    noise_count = max(1, int(len(strategy) * intensity))
    for i in range(noise_count):
        noise_key = f"_n{random.randint(100, 999)}"
        mutated[noise_key] = round(random.random(), 4)

    return mutated


def alien_score(original: dict, mutated: dict) -> float:
    """
    How 'alien' is the mutated strategy vs original?
    1.0 = completely alien, 0.0 = identical.
    """
    # Key set divergence
    key_sim = _jaccard(original, mutated)

    # Value divergence (for common numeric keys)
    common_keys = set(original.keys()) & set(mutated.keys())
    value_diff = 0.0
    num_keys = 0
    for k in common_keys:
        if isinstance(original[k], (int, float)) and isinstance(mutated[k], (int, float)):
            orig_v = original[k]
            if orig_v != 0:
                value_diff += abs(mutated[k] - orig_v) / abs(orig_v)
            num_keys += 1

    avg_value_diff = value_diff / max(num_keys, 1)
    return round(min(1.0, (1 - key_sim) * 0.5 + avg_value_diff * 0.5), 4)


def evolve_generation(population: list[dict], top_k: int = 3, intensity: float = 0.25) -> list[dict]:
    """
    Produce next generation: keep top_k elite unchanged, mutate the rest.
    population: list of dicts with "strategy" and "fitness" keys.
    """
    if not population:
        return []
    sorted_pop = sorted(population, key=lambda x: x.get("fitness", 0), reverse=True)
    elite = sorted_pop[:top_k]
    offspring = []
    for ind in sorted_pop[top_k:]:
        parent = random.choice(elite)["strategy"]
        child_strategy = mutate(parent, intensity)
        offspring.append({"strategy": child_strategy, "fitness": 0.0})
    return elite + offspring
