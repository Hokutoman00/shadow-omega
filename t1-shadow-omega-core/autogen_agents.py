"""
Shadow-Ω AutoGen Agent Layer — Microsoft AI Foundry Integration

Architecture:
  UniverseAgentCouncil:  per-universe 2-agent strategic council (Attacker + Defender).
    Runs every COUNCIL_INTERVAL turns. Proposes evolved strategy direction.
    Output is fed into physics simulation as directional parameters for the next N turns.

  ConvergenceOrchestratorAgent: cross-universe semantic convergence analysis.
    Runs after each council round. LLM-powered semantic reasoning supplements
    the hash-based ConvergenceDetector.

Model backend: GitHub Models or Azure AI Foundry (gpt-4o-mini) via Microsoft AI.
Fallback: deterministic physics-based strategy evolution when credentials are absent.

Required env vars (optional — falls back to physics if absent):
  Priority 1 — Azure AI Foundry:
    AZURE_OPENAI_ENDPOINT  — https://<resource>.openai.azure.com
    AZURE_OPENAI_KEY       — Azure OpenAI API key
    AZURE_OPENAI_DEPLOYMENT — deployment name (default: gpt-4o-mini)
  Priority 2 — GitHub Models (free with any GitHub account):
    GITHUB_TOKEN           — GitHub personal access token
    GITHUB_MODEL           — model name (default: openai/gpt-4o-mini)
    GITHUB_MODELS_BASE_URL — endpoint (default: https://models.github.ai/inference)
"""
import hashlib
import json
import os
import random
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────

COUNCIL_INTERVAL = 10  # run AutoGen councils every N simulation turns

_DNA_PERSONAS = {
    "aggressive": (
        "You are a high-tempo secure-code risk reviewer. Favor quickly surfacing "
        "high-impact risk hypotheses so the defender can close them early."
    ),
    "stealthy": (
        "You are a low-noise secure-code risk reviewer. Prioritize subtle logic paths "
        "that need careful defensive review over obvious failures."
    ),
    "adaptive": (
        "You are an adaptive secure-code risk reviewer. Analyze defender behavior "
        "patterns and select risk hypotheses that reveal blind spots."
    ),
}

_DEFAULT_ATTACK = {
    "attack_style": "LATERAL",
    "stealth": 0.5,
    "timing": "ADAPTIVE",
    "threshold": 0.6,
}
_DEFAULT_DEFENSE = {
    "defense_weight": 0.6,
    "coverage": 0.5,
    "detection_threshold": 0.5,
    "adaptive_response": "PATCH",
}

_DNA_MAP = {0: "aggressive", 1: "stealthy", 2: "adaptive", 3: "aggressive", 4: "stealthy"}


# ── Azure AI Foundry client factory ──────────────────────────────────────────

def _github_model_info(model: str) -> dict:
    """AutoGen 0.7 requires model_info for provider/model GitHub Models IDs."""
    from autogen_core.models import ModelFamily

    family = ModelFamily.GPT_41 if "gpt-4.1" in model else ModelFamily.GPT_4O
    return {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": family,
        "structured_output": True,
    }


def _make_azure_client():
    """Create AutoGen model client. Priority 1: Azure AI Foundry. Priority 2: GitHub Models."""
    # Priority 1: Azure AI Foundry
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    key = os.getenv("AZURE_OPENAI_KEY", "").strip()
    if endpoint and key:
        try:
            from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            return AzureOpenAIChatCompletionClient(
                azure_deployment=deployment,
                model=deployment,
                api_version="2025-01-01-preview",
                azure_endpoint=endpoint,
                api_key=key,
            )
        except Exception:
            pass

    # Priority 2: GitHub Models (free, Microsoft AI infrastructure)
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    if gh_token:
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            model = os.getenv("GITHUB_MODEL", "openai/gpt-4o-mini")
            base_url = os.getenv(
                "GITHUB_MODELS_BASE_URL",
                "https://models.github.ai/inference",
            )
            return OpenAIChatCompletionClient(
                model=model,
                base_url=base_url,
                api_key=gh_token,
                model_info=_github_model_info(model),
            )
        except Exception:
            pass

    return None


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class StrategyOutput:
    """Result of one AutoGen council round."""
    attack: dict
    defense: dict
    fingerprint: str
    reasoning: str
    llm_driven: bool


# ── Per-universe council ──────────────────────────────────────────────────────

class UniverseAgentCouncil:
    """
    AutoGen 2-agent strategic council for one Shadow-Ω universe.

    One dialogue round per call: AttackerAgent proposes a strategy, DefenderAgent
    counters. The resulting strategy parameters are applied to the top agents in the
    physics simulation as directional guidance for the next COUNCIL_INTERVAL turns.
    """

    def __init__(self, universe_id: int, dna_trait: str) -> None:
        self.universe_id = universe_id
        self.dna_trait = dna_trait.lower()
        self._client = _make_azure_client()
        self.available = self._client is not None
        self._last_strategy: Optional[StrategyOutput] = None

        if self.available:
            from autogen_agentchat.agents import AssistantAgent
            persona = _DNA_PERSONAS.get(self.dna_trait, _DNA_PERSONAS["adaptive"])

            self.attacker = AssistantAgent(
                name=f"attacker_u{universe_id}",
                model_client=self._client,
                system_message=(
                    f"You are a secure-code risk reviewer in simulation universe {universe_id} "
                    f"(DNA trait: {dna_trait.upper()}).\n"
                    f"{persona}\n\n"
                    "Given the current simulation state, propose the next defensive risk hypothesis.\n\n"
                    "Respond ONLY with a single-line JSON object — no markdown, no prose:\n"
                    '{"attack_style": "ACCESS_PATH|INPUT_ABUSE|STATE_RACE|SUPPLY_CHAIN|UNKNOWN_RISK", '
                    '"stealth": 0.0-1.0, "timing": "BURST|SLOW_BURN|ADAPTIVE", "threshold": 0.0-1.0}\n\n'
                    "stealth=0.0 means obvious risk signal; stealth=1.0 means subtle risk signal. "
                    "threshold is defensive-review trigger sensitivity."
                ),
            )

            self.defender = AssistantAgent(
                name=f"defender_u{universe_id}",
                model_client=self._client,
                system_message=(
                    f"You are a security defender in simulation universe {universe_id}.\n"
                    "Evolve a defense strategy that minimizes residual risk "
                    "against the reviewer proposed risk hypothesis.\n\n"
                    "Respond ONLY with a single-line JSON object — no markdown, no prose:\n"
                    '{"defense_weight": 0.0-1.0, "coverage": 0.0-1.0, '
                    '"detection_threshold": 0.0-1.0, '
                    '"adaptive_response": "PATCH|HONEYPOT|ISOLATION|DECEPTION"}\n\n'
                    "High coverage = broad but shallow detection. "
                    "Low coverage + high detection_threshold = deep targeted inspection."
                ),
            )

    async def run_council(self, state: dict) -> StrategyOutput:
        """
        Run one council round: attacker proposes, defender counters.

        Args:
            state: {turn, avg_attacker_fitness, avg_defender_fitness, sigma}
        Returns:
            StrategyOutput with evolved strategies, fingerprint, reasoning.
        """
        if not self.available:
            return self._physics_fallback(state)

        try:
            from autogen_agentchat.messages import TextMessage
            try:
                from autogen_core import CancellationToken
            except ImportError:
                from autogen_agentchat.base import CancellationToken

            state_summary = (
                f"Turn={state.get('turn', 0)} | "
                f"ATK_fitness={state.get('avg_attacker_fitness', 0.0):.3f} | "
                f"DEF_fitness={state.get('avg_defender_fitness', 0.0):.3f} | "
                f"σ={state.get('sigma', 1.0):.3f} | "
                f"DNA={self.dna_trait.upper()}"
            )

            # Round 1: risk reviewer proposes hypothesis
            atk_resp = await self.attacker.on_messages(
                [TextMessage(
                    content=f"Current simulation state: {state_summary}. Propose your evolved defensive risk hypothesis.",
                    source="user",
                )],
                cancellation_token=CancellationToken(),
            )
            atk_text = atk_resp.chat_message.content.strip()

            # Round 2: defender counters
            def_resp = await self.defender.on_messages(
                [TextMessage(
                    content=(
                        f"Risk hypothesis: {atk_text}\n"
                        f"State: {state_summary}\n"
                        "Counter with your optimal defense configuration."
                    ),
                    source="user",
                )],
                cancellation_token=CancellationToken(),
            )
            def_text = def_resp.chat_message.content.strip()

            attack = self._extract_json(atk_text, _DEFAULT_ATTACK)
            defense = self._extract_json(def_text, _DEFAULT_DEFENSE)

            fp_raw = json.dumps({"attack": attack, "dna": self.dna_trait}, sort_keys=True)
            fingerprint = hashlib.sha256(fp_raw.encode()).hexdigest()[:12]

            result = StrategyOutput(
                attack=attack,
                defense=defense,
                fingerprint=fingerprint,
                reasoning=atk_text[:140],
                llm_driven=True,
            )
            self._last_strategy = result
            return result

        except Exception:
            return self._physics_fallback(state)

    def _extract_json(self, text: str, default: dict) -> dict:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return dict(default)

    def _physics_fallback(self, state: dict) -> StrategyOutput:
        """State-aware deterministic fallback when Azure OpenAI is unavailable."""
        styles_by_dna = {
            "aggressive": ["EXPLOIT", "ZERO_DAY", "LATERAL"],
            "stealthy":   ["SUPPLY_CHAIN", "PHISHING", "LATERAL"],
            "adaptive":   ["LATERAL", "PHISHING", "EXPLOIT"],
        }
        style = random.choice(styles_by_dna.get(self.dna_trait, ["LATERAL"]))
        sigma = state.get("sigma", 1.0)
        atk_fitness = state.get("avg_attacker_fitness", 0.0)

        stealth = min(0.9, max(0.1, 0.5 + (1.0 - sigma) * 0.3))
        threshold = min(0.95, max(0.2, 0.6 + atk_fitness * 0.01))

        attack = {
            "attack_style": style,
            "stealth": round(stealth, 3),
            "timing": "ADAPTIVE" if self.dna_trait == "adaptive" else random.choice(["BURST", "SLOW_BURN"]),
            "threshold": round(threshold, 3),
        }
        defense = {
            "defense_weight": round(random.uniform(0.4, 0.8), 3),
            "coverage": round(random.uniform(0.3, 0.8), 3),
            "detection_threshold": round(1.0 - stealth * 0.6, 3),
            "adaptive_response": random.choice(["PATCH", "HONEYPOT", "ISOLATION", "DECEPTION"]),
        }
        fp_raw = json.dumps({"attack": attack, "dna": self.dna_trait}, sort_keys=True)
        fingerprint = hashlib.sha256(fp_raw.encode()).hexdigest()[:12]

        return StrategyOutput(
            attack=attack,
            defense=defense,
            fingerprint=fingerprint,
            reasoning="physics-fallback",
            llm_driven=False,
        )


# ── Cross-universe convergence orchestrator ───────────────────────────────────

class ConvergenceOrchestratorAgent:
    """
    AutoGen-powered semantic convergence orchestrator.

    Monitors all 5 universe strategy councils and uses LLM reasoning to detect
    semantic convergence — strategies that are equivalent in intent even when
    their hash fingerprints differ. This supplements the physics ConvergenceDetector
    (hash-based) with genuine semantic understanding.
    """

    def __init__(self) -> None:
        self._client = _make_azure_client()
        self.available = self._client is not None

        if self.available:
            from autogen_agentchat.agents import AssistantAgent
            self.agent = AssistantAgent(
                name="convergence_orchestrator",
                model_client=self._client,
                system_message=(
                    "You are the cross-universe convergence orchestrator for Shadow-Ω.\n"
                    "You monitor 5 parallel defensive simulation universes and detect when they "
                    "independently converge on semantically equivalent risk hypotheses — "
                    "indicating a universal, fundamental vulnerability.\n\n"
                    "Analyze risk hypotheses from all 5 universes. Determine:\n"
                    "1. Are 3+ universes using semantically similar risk approaches?\n"
                    "   (Same intent counts even with different labels: "
                    "   ACCESS_PATH+subtle≈SUPPLY_CHAIN+subtle, INPUT_ABUSE+burst≈STATE_RACE+burst)\n"
                    "2. Confidence level (0.0-1.0)\n"
                    "3. Archetype name in UPPER_SNAKE (e.g. STEALTHY_EXFIL, BURST_ZERO_DAY)\n"
                    "4. Severity: low|medium|high|critical\n\n"
                    "Respond ONLY with JSON (no markdown):\n"
                    '{"converged": bool, "universe_ids": [list of int], "confidence": 0.0-1.0, '
                    '"archetype": "UPPER_SNAKE", "severity": "low|medium|high|critical", '
                    '"reasoning": "one sentence explaining the convergent pattern"}'
                ),
            )

    async def analyze_convergence(self, universe_strategies: list[dict]) -> Optional[dict]:
        """
        Analyze strategies from all 5 universes for semantic convergence.

        Args:
            universe_strategies: list of {universe_id, dna, fingerprint, attack}
        Returns:
            Convergence event dict if 3+ universes converge, else None.
        """
        if not self.available:
            return None

        try:
            from autogen_agentchat.messages import TextMessage
            try:
                from autogen_core import CancellationToken
            except ImportError:
                from autogen_agentchat.base import CancellationToken

            summary = json.dumps([
                {
                    "universe_id": s["universe_id"],
                    "dna": s["dna"],
                    "fingerprint": s["fingerprint"],
                    "risk_style": s["attack"].get("attack_style"),
                    "stealth": s["attack"].get("stealth"),
                    "timing": s["attack"].get("timing"),
                    "threshold": s["attack"].get("threshold"),
                }
                for s in universe_strategies
            ], indent=2)

            response = await self.agent.on_messages(
                [TextMessage(
                    content=f"Analyze these 5 universe risk hypotheses for convergence:\n{summary}",
                    source="user",
                )],
                cancellation_token=CancellationToken(),
            )

            result = self._extract_json(response.chat_message.content)
            if not result or not result.get("converged"):
                return None
            if len(result.get("universe_ids", [])) < 3:
                return None

            return {
                "event_type": "llm_convergence",
                "converged_universes": result["universe_ids"],
                "confidence": float(result.get("confidence", 0.5)),
                "severity": result.get("severity", "medium"),
                "strategy_fp": universe_strategies[0]["fingerprint"],
                "is_new_archetype": True,
                "archetype": result.get("archetype", "UNKNOWN"),
                "llm_reasoning": result.get("reasoning", ""),
                "source": "convergence_orchestrator_agent",
            }

        except Exception:
            return None

    def _extract_json(self, text: str) -> Optional[dict]:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return None


# ── Module-level singletons ───────────────────────────────────────────────────

_councils: dict[int, UniverseAgentCouncil] = {}
_orchestrator: Optional[ConvergenceOrchestratorAgent] = None


def get_council(universe_id: int) -> UniverseAgentCouncil:
    if universe_id not in _councils:
        _councils[universe_id] = UniverseAgentCouncil(universe_id, _DNA_MAP[universe_id])
    return _councils[universe_id]


def get_orchestrator() -> ConvergenceOrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ConvergenceOrchestratorAgent()
    return _orchestrator


def agents_available() -> bool:
    """True when any AI credentials are configured (Azure AI Foundry or GitHub Models)."""
    azure_ready = bool(
        os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
        and os.getenv("AZURE_OPENAI_KEY", "").strip()
    )
    github_ready = bool(os.getenv("GITHUB_TOKEN", "").strip())
    return azure_ready or github_ready


def agents_config() -> dict:
    """Return AutoGen + AI backend configuration status."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    gh_token = os.getenv("GITHUB_TOKEN", "")
    gh_model = os.getenv("GITHUB_MODEL", "openai/gpt-4o-mini")
    gh_base_url = os.getenv(
        "GITHUB_MODELS_BASE_URL",
        "https://models.github.ai/inference",
    )
    resource_name = ""
    if endpoint:
        resource_name = endpoint.replace("https://", "").split(".openai.azure.com")[0]

    azure_connected = bool(endpoint.strip() and os.getenv("AZURE_OPENAI_KEY", "").strip())
    github_connected = bool(gh_token.strip())

    if azure_connected:
        active_backend = "azure_ai_foundry"
        active_model = deployment
    elif github_connected:
        active_backend = "github_models"
        active_model = gh_model
    else:
        active_backend = "physics_fallback"
        active_model = "none"

    return {
        "azure_foundry_connected": azure_connected,
        "github_models_connected": github_connected,
        "active_backend": active_backend,
        "active_model": active_model,
        "resource_name": resource_name or "not_configured",
        "deployment": deployment,
        "github_models_base_url": gh_base_url,
        "framework": "Microsoft AutoGen v0.4",
        "councils_initialized": len(_councils),
        "orchestrator_initialized": _orchestrator is not None,
        "council_interval_turns": COUNCIL_INTERVAL,
        "fallback": "physics-deterministic",
    }
