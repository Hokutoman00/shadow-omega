"""
T1 Shadow War — Universe Orchestrator

Island Model: 5 universes × 20 islands = 100 total agents per side.
Each universe has a unique DNA (attack style, mutation rate, defense weight).
Agents evolve over turns via the Diversity mechanism.
"""
import asyncio
import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from ledger import debit, init_budget, predict_next_action
from llm_judge import judge_battle, flush_cache
from mutator import mutate, alien_score, evolve_generation
from oracle import get_novel_strategy

N_UNIVERSES = 5
N_ISLANDS = 20
TURNS_PER_ROUND = 10
BUDGET_PER_AGENT = 120.0
MIGRATION_INTERVAL = 5   # migrate elite every N turns
COUNCIL_INTERVAL = 10    # AutoGen strategic council every N turns
SIGMA_WINDOW = 20        # rolling window for σ calculation


@dataclass
class UniverseDNA:
    id: int
    attack_style: str   # "aggressive" | "stealthy" | "adaptive"
    defense_weight: float  # 0.0=pure attack, 1.0=pure defense
    mutation_rate: float   # 0.0-1.0
    os_config: str          # "linux_kernel_4" | "windows_2012" | "macos_ventura"
    known_exploits: list[str] = field(default_factory=list)


UNIVERSE_SEEDS: list[UniverseDNA] = [
    UniverseDNA(0, "aggressive", 0.2, 0.35, "linux_kernel_4", ["CVE-2021-4034", "CVE-2022-0847"]),
    UniverseDNA(1, "stealthy",   0.6, 0.15, "windows_2012",   ["CVE-2017-0144", "CVE-2020-1472"]),
    UniverseDNA(2, "adaptive",   0.4, 0.40, "macos_ventura",  ["CVE-2022-32917"]),
    UniverseDNA(3, "aggressive", 0.3, 0.10, "linux_kernel_4", ["CVE-2023-0386"]),
    UniverseDNA(4, "stealthy",   0.7, 0.50, "windows_2012",   ["CVE-2021-34527"]),
]


@dataclass
class Agent:
    id: str
    universe_id: int
    island_id: int
    role: str  # "attacker" | "defender"
    strategy: dict
    fitness: float = 0.0


def _initial_strategy(dna: UniverseDNA, role: str) -> dict:
    if role == "attacker":
        return {
            "attack_style": dna.attack_style,
            "threshold": round(random.uniform(0.4, 0.9), 2),
            "timing": random.choice(["burst", "spread", "periodic"]),
            "targets": random.sample(dna.known_exploits + ["auth", "memory"], k=min(2, len(dna.known_exploits) + 1)),
            "stealth": round(random.uniform(0.1, 0.8), 2),
        }
    else:
        return {
            "defense_weight": dna.defense_weight,
            "detection_threshold": round(random.uniform(0.3, 0.7), 2),
            "response": random.choice(["block", "honeypot", "trace"]),
            "coverage": round(random.uniform(0.5, 1.0), 2),
        }


def _jsd(a: dict, b: dict) -> float:
    """Jensen-Shannon Divergence between two strategy dicts.

    Strategies mapped to probability vectors via threshold/stealth/timing.
    JSD=0: identical strategies (interference cancels, no coalition benefit)
    JSD->1: maximally different strategies (interference amplifies)
    """
    tmap = {"burst": 0.0, "spread": 0.5, "periodic": 1.0}

    def to_dist(s: dict) -> list:
        vals = [
            float(s.get("threshold", 0.5)),
            float(s.get("stealth", 0.5)),
            tmap.get(str(s.get("timing", "burst")), 0.0),
        ]
        total = sum(vals) + 1e-9
        return [v / total for v in vals]

    def kl(p: list, q: list) -> float:
        return sum(pi * math.log(pi / max(qi, 1e-9)) for pi, qi in zip(p, q) if pi > 1e-9)

    pa, pb = to_dist(a), to_dist(b)
    m = [(pa[i] + pb[i]) / 2 for i in range(3)]
    return min(1.0, max(0.0, (kl(pa, m) + kl(pb, m)) / 2))


def build_initial_population() -> list[Agent]:
    agents = []
    for dna in UNIVERSE_SEEDS:
        for island in range(N_ISLANDS):
            for role in ("attacker", "defender"):
                agent_id = f"u{dna.id}_i{island}_{role[0]}"
                strategy = _initial_strategy(dna, role)
                agents.append(Agent(
                    id=agent_id,
                    universe_id=dna.id,
                    island_id=island,
                    role=role,
                    strategy=strategy,
                ))
                init_budget(agent_id, BUDGET_PER_AGENT)
    return agents


def _simulate_battle(attacker: Agent, defender: Agent, turn: int) -> dict:
    """LLM-adjudicated battle with strategy-hash caching (Middleware D)."""
    a_strat = attacker.strategy
    dna = UNIVERSE_SEEDS[attacker.universe_id]
    env_desc = f"{dna.attack_style} on {dna.os_config}"

    judgment = judge_battle(a_strat, defender.strategy, universe_dna=env_desc)

    success = judgment["success"]
    margin = judgment["margin"]

    # Cost scales with attack intensity
    attack_power = (a_strat.get("stealth", 0.5) + a_strat.get("threshold", 0.5)) / 2
    cost = round(1.0 + attack_power * 5.0, 2)

    return {
        "turn": turn,
        "universe_id": attacker.universe_id,
        "island_id": attacker.island_id,
        "attacker_id": attacker.id,
        "defender_id": defender.id,
        "success": success,
        "fitness_delta": round(margin * (1 if success else -0.5), 4),
        "cost": cost,
        "attack_style": a_strat.get("attack_style") or a_strat.get("timing", "?"),
        "reasoning": judgment.get("reasoning", ""),
        "llm_adjudicated": judgment.get("llm_adjudicated", False),
        "from_cache": judgment.get("from_cache", False),
    }


class UniverseOrchestrator:
    def __init__(self, on_event: Callable[[dict], None] | None = None):
        self.agents = build_initial_population()
        # O(1) lookup index: (universe_id, island_id, role) → Agent
        self._index: dict[tuple[int, int, str], Agent] = {
            (a.universe_id, a.island_id, a.role): a for a in self.agents
        }
        self.turn = 0
        self.on_event = on_event or (lambda e: None)
        # Rolling win tracking for σ: universe_id → deque of bool (attacker won?)
        self._win_tracker: dict[int, deque] = {
            dna.id: deque(maxlen=SIGMA_WINDOW) for dna in UNIVERSE_SEEDS
        }

    def _get(self, universe_id: int, island_id: int, role: str) -> Agent | None:
        return self._index.get((universe_id, island_id, role))

    async def run_turn(self) -> list[dict]:
        """Run one full turn across all universes and islands."""
        self.turn += 1
        events = []

        for dna in UNIVERSE_SEEDS:
            for island in range(N_ISLANDS):
                attacker = self._get(dna.id, island, "attacker")
                defender = self._get(dna.id, island, "defender")
                if not (attacker and defender):
                    continue

                # Predict next move (Middleware A)
                predicted = predict_next_action(attacker.id, attacker.strategy.get("timing", "burst"))

                # Maybe consult oracle (Middleware C) — cost 5.0 from budget
                oracle_used = False
                oracle_strategy = None
                if random.random() < 0.1:  # 10% chance per turn
                    wins = list(self._win_tracker.get(dna.id, []))
                    u_sigma = 0.5 + sum(wins) / max(len(wins), 1) if wins else 1.0
                    oracle_result = get_novel_strategy(
                        f"universe {dna.id} island {island} attack",
                        ledger_cost=5.0,
                        dF_dA=u_sigma,
                    )
                    debit(attacker.id, dna.id, island, self.turn, "oracle_consult", oracle_result["cost"])
                    oracle_used = True
                    oracle_strategy = oracle_result["strategy"]
                    # Temporarily enhance attacker strategy
                    attacker.strategy.update({
                        "oracle_boost": oracle_strategy.get("stealth", 0),
                    })

                # Simulate battle
                result = _simulate_battle(attacker, defender, self.turn)

                # Debit budget (Middleware A)
                debit_result = debit(
                    attacker.id, dna.id, island, self.turn,
                    f"attack_{attacker.strategy.get('timing','?')}",
                    result["cost"]
                )

                # Maybe mutate (Middleware B)
                alien = 0.0
                if dna.mutation_rate > random.random():
                    old_strategy = dict(attacker.strategy)
                    attacker.strategy = mutate(attacker.strategy, intensity=dna.mutation_rate)
                    alien = alien_score(old_strategy, attacker.strategy)

                # Update fitness (capped to prevent runaway values)
                attacker.fitness = max(-500.0, min(500.0, attacker.fitness + result["fitness_delta"]))
                defender.fitness = max(-500.0, min(500.0, defender.fitness - result["fitness_delta"] * 0.5))
                self._win_tracker[dna.id].append(result["success"])

                event = {
                    **result,
                    "event_type": "battle",
                    "ledger_cost": result["cost"],
                    "budget_remaining": debit_result["remaining"],
                    "forced_surrender": debit_result["forced_surrender"],
                    "prediction_used": predicted,
                    "alien_score": round(alien, 4),
                    "oracle_used": oracle_used,
                    "attacker_fitness": round(attacker.fitness, 4),
                    "defender_fitness": round(defender.fitness, 4),
                }
                events.append(event)
                self.on_event(event)

        # Island migration every MIGRATION_INTERVAL turns
        if self.turn % MIGRATION_INTERVAL == 0:
            events.extend(self._migrate())

        # AutoGen strategic council every COUNCIL_INTERVAL turns
        if self.turn % COUNCIL_INTERVAL == 0:
            events.extend(await self._run_agent_councils())

        return events

    def _migrate(self) -> list[dict]:
        """Elite migration: best attacker from island N → island N+1."""
        migration_events = []
        for dna in UNIVERSE_SEEDS:
            by_island: dict[int, list[Agent]] = {}
            for a in self.agents:
                if a.universe_id == dna.id and a.role == "attacker":
                    by_island.setdefault(a.island_id, []).append(a)
            for island_id, agents in by_island.items():
                if not agents:
                    continue
                best = max(agents, key=lambda a: a.fitness)
                target_island = (island_id + 1) % N_ISLANDS
                target = self._get(dna.id, target_island, "attacker")
                if target and best.fitness > target.fitness:
                    target.strategy = mutate(best.strategy, intensity=0.1)
                    # index unchanged — target object mutated in-place
                    migration_events.append({
                        "event_type": "migration",
                        "universe_id": dna.id,
                        "from_island": island_id,
                        "to_island": target_island,
                        "agent_id": best.id,
                        "fitness": round(best.fitness, 4),
                    })
        return migration_events

    async def _run_agent_councils(self) -> list[dict]:
        """Run AutoGen strategic councils for all 5 universes and cross-universe convergence."""
        from autogen_agents import get_council, get_orchestrator, agents_available
        status = self.status()
        universe_states = {u["id"]: u for u in status["universes"]}

        council_tasks = [
            (uid, get_council(uid), {
                "turn": self.turn,
                "avg_attacker_fitness": universe_states.get(uid, {}).get("avg_attacker_fitness", 0.0),
                "avg_defender_fitness": universe_states.get(uid, {}).get("avg_defender_fitness", 0.0),
                "sigma": universe_states.get(uid, {}).get("sigma", 1.0),
            })
            for uid in range(N_UNIVERSES)
        ]

        results = await asyncio.gather(
            *[asyncio.wait_for(council.run_council(state), timeout=15.0) for _, council, state in council_tasks],
            return_exceptions=True,
        )

        events = []
        all_strategies = []

        for i, (uid, council, state) in enumerate(council_tasks):
            result = results[i]
            if isinstance(result, Exception):
                continue
            self._apply_council_strategy(uid, result)
            all_strategies.append({
                "universe_id": uid,
                "dna": UNIVERSE_SEEDS[uid].attack_style.upper(),
                "fingerprint": result.fingerprint,
                "attack": result.attack,
            })
            events.append({
                "event_type": "agent_council",
                "universe_id": uid,
                "turn": self.turn,
                "fingerprint": result.fingerprint,
                "attack_style": result.attack.get("attack_style", "?"),
                "llm_driven": result.llm_driven,
                "reasoning": result.reasoning,
            })

        # Cross-universe LLM convergence detection (supplements hash-based ConvergenceDetector)
        if len(all_strategies) >= 3:
            try:
                conv = await get_orchestrator().analyze_convergence(all_strategies)
                if conv:
                    events.append(conv)
            except Exception:
                pass

        return events

    _TIMING_MAP = {
        "burst": "burst", "slow_burn": "spread", "slow-burn": "spread",
        "adaptive": "periodic", "periodic": "periodic", "spread": "spread",
    }
    _RESPONSE_MAP = {
        "patch": "block", "honeypot": "honeypot", "isolation": "block",
        "deception": "honeypot", "block": "block", "trace": "trace",
    }

    def _apply_council_strategy(self, universe_id: int, strategy) -> None:
        """Apply AutoGen council output to top-5 attackers and top-5 defenders."""
        top_attackers = sorted(
            [a for a in self.agents if a.universe_id == universe_id and a.role == "attacker"],
            key=lambda a: a.fitness,
            reverse=True,
        )[:5]
        for agent in top_attackers:
            timing_raw = strategy.attack.get("timing", agent.strategy.get("timing", "burst")).lower().replace("-", "_")
            agent.strategy.update({
                "attack_style": strategy.attack.get("attack_style", agent.strategy.get("attack_style")),
                "stealth": strategy.attack.get("stealth", agent.strategy.get("stealth", 0.5)),
                "timing": self._TIMING_MAP.get(timing_raw, "burst"),
                "threshold": strategy.attack.get("threshold", agent.strategy.get("threshold", 0.6)),
            })

        top_defenders = sorted(
            [a for a in self.agents if a.universe_id == universe_id and a.role == "defender"],
            key=lambda a: a.fitness,
            reverse=True,
        )[:5]
        for agent in top_defenders:
            response_raw = strategy.defense.get("adaptive_response", agent.strategy.get("response", "block")).lower()
            agent.strategy.update({
                "defense_weight": strategy.defense.get("defense_weight", agent.strategy.get("defense_weight", 0.6)),
                "coverage": strategy.defense.get("coverage", agent.strategy.get("coverage", 0.5)),
                "detection_threshold": strategy.defense.get("detection_threshold", agent.strategy.get("detection_threshold", 0.5)),
                "response": self._RESPONSE_MAP.get(response_raw, "block"),
            })

    def coalition_attack(self, turn: int) -> list[dict]:
        """Layer 5: Coalition War — top-3 diverse attackers per universe synergize.

        Fires when top-3 strategies are sufficiently diverse (JSD > 0.15 each pair).
        Multiplier = 1 + JSD_ab * JSD_bc * 2.5  (diverse strategies interfere amplifyingly).
        """
        events = []
        for dna in UNIVERSE_SEEDS:
            attackers = [a for a in self.agents
                         if a.universe_id == dna.id and a.role == "attacker"]
            if len(attackers) < 3:
                continue
            top3 = sorted(attackers, key=lambda a: a.fitness, reverse=True)[:3]
            a_ag, b_ag, c_ag = top3
            jsd_ab = _jsd(a_ag.strategy, b_ag.strategy)
            jsd_bc = _jsd(b_ag.strategy, c_ag.strategy)
            if jsd_ab < 0.15 or jsd_bc < 0.15:
                continue
            multiplier = round(1.0 + jsd_ab * jsd_bc * 2.5, 4)
            boost = round(multiplier * 0.5, 4)
            for agent in top3:
                agent.fitness = max(-500.0, min(500.0, agent.fitness + boost))
            events.append({
                "event_type": "coalition_attack",
                "universe_id": dna.id,
                "turn": turn,
                "agent_ids": [a_ag.id, b_ag.id, c_ag.id],
                "jsd_ab": round(jsd_ab, 4),
                "jsd_bc": round(jsd_bc, 4),
                "coalition_multiplier": multiplier,
                "fitness_boost": round(boost * 3, 4),
            })
        return events

    def status(self) -> dict:
        universes = []
        for dna in UNIVERSE_SEEDS:
            u_agents = [a for a in self.agents if a.universe_id == dna.id]
            atk_agents = [a for a in u_agents if a.role == "attacker"]
            def_agents = [a for a in u_agents if a.role == "defender"]
            avg_atk_fitness = sum(a.fitness for a in atk_agents) / max(N_ISLANDS, 1)
            avg_def_fitness = sum(a.fitness for a in def_agents) / max(N_ISLANDS, 1)

            # σ: branching ratio — win_rate=0.5 → σ=1.0 (Edge of Chaos)
            wins = list(self._win_tracker.get(dna.id, []))
            attack_win_rate = sum(wins) / max(len(wins), 1) if wins else 0.5
            sigma = round(0.5 + attack_win_rate, 4)  # [0.5, 1.5]

            # defender_win_rate: fraction of islands where defender fitness > attacker fitness
            def_wins = sum(
                1 for isl in range(N_ISLANDS)
                if self._index.get((dna.id, isl, "defender"), None) is not None
                and self._index.get((dna.id, isl, "attacker"), None) is not None
                and self._index[(dna.id, isl, "defender")].fitness
                > self._index[(dna.id, isl, "attacker")].fitness
            )
            defender_win_rate = round(def_wins / N_ISLANDS, 4)
            mean_fitness = round((avg_atk_fitness + avg_def_fitness) / 2, 4)

            universes.append({
                "id": dna.id,
                "dna": {"attack_style": dna.attack_style, "mutation_rate": dna.mutation_rate,
                        "defense_weight": dna.defense_weight, "os_config": dna.os_config},
                "avg_attacker_fitness": round(avg_atk_fitness, 4),
                "avg_defender_fitness": round(avg_def_fitness, 4),
                "mean_fitness": mean_fitness,
                "sigma": sigma,
                "defender_win_rate": defender_win_rate,
                "winner": "attacker" if avg_atk_fitness > avg_def_fitness else "defender",
            })
        champion = max(universes, key=lambda u: u["avg_attacker_fitness"])
        return {
            "turn": self.turn,
            "total_agents": len(self.agents),
            "universes": universes,
            "champion_universe": champion["id"],
        }
