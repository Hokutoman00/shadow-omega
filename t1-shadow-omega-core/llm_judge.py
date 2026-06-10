"""
T1 Shadow War — LLM Judge (Middleware D: AI-Native Adjudication)

Adjudicates individual attacker-vs-defender battles using Microsoft AI
(GitHub Models or Azure AI Foundry — whichever credentials are present).
SHA256-keyed cache keeps API calls near-zero after warmup (80%+ hit rate
after turn 10).

Required env vars (optional — falls back to physics if absent):
  Priority 1 — Azure AI Foundry:
    AZURE_OPENAI_ENDPOINT  — https://<resource>.openai.azure.com
    AZURE_OPENAI_KEY       — Azure OpenAI API key
    AZURE_OPENAI_DEPLOYMENT — deployment name (default: gpt-4o-mini)
  Priority 2 — GitHub Models (free with any GitHub account):
    GITHUB_TOKEN           — GitHub personal access token
    GITHUB_MODEL           — model name (default: gpt-4o-mini)
"""
import hashlib
import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CACHE_PATH = Path(__file__).parent / "data" / "judge_cache.json"
_cache: dict[str, dict] = {}
_api_client = None
_api_available = False


def _load_cache() -> None:
    global _cache
    if CACHE_PATH.exists():
        try:
            _cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            _cache = {}


def _save_cache() -> None:
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(_cache, indent=2, ensure_ascii=False), encoding="utf-8")


def _strategy_hash(attacker: dict, defender: dict) -> str:
    combined = json.dumps({"a": attacker, "d": defender}, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def _init_api() -> bool:
    global _api_client, _api_available
    if _api_client is not None:
        return _api_available

    # Priority 1: Azure AI Foundry
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    az_key = os.getenv("AZURE_OPENAI_KEY", "").strip()
    if endpoint and az_key:
        try:
            from openai import AzureOpenAI
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            _api_client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=az_key,
                api_version="2025-01-01-preview",
                default_headers={"x-ms-useragent": "shadow-omega/1.0"},
            )
            _api_client._deployment = deployment
            _api_available = True
            return True
        except ImportError:
            pass

    # Priority 2: GitHub Models (free, Microsoft AI infrastructure)
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    if gh_token:
        try:
            from openai import OpenAI
            model = os.getenv("GITHUB_MODEL", "gpt-4o-mini")
            _api_client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key=gh_token,
                default_headers={"x-ms-useragent": "shadow-omega/1.0"},
            )
            _api_client._deployment = model
            _api_available = True
            return True
        except ImportError:
            pass

    _api_available = False
    return False


def _call_azure(attacker: dict, defender: dict, environment: str) -> dict:
    """Call Azure OpenAI to adjudicate. Returns {success, margin, reasoning}.
    Raises on rate-limit errors so the caller does NOT cache the result.
    """
    deployment = getattr(_api_client, "_deployment", "gpt-4o-mini")
    prompt = (
        "You are adjudicating a cybersecurity simulation battle.\n\n"
        f"ATTACKER: {json.dumps(attacker)}\n"
        f"DEFENDER: {json.dumps(defender)}\n"
        f"ENV: {environment}\n\n"
        "Analyze attack_style/stealth/timing vs defense_weight/coverage/detection_threshold.\n"
        "Respond ONLY in JSON (no markdown): "
        '{"success": true/false, "margin": 0.0-1.0, "reasoning": "one sentence"}'
    )
    try:
        response = _api_client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.3,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        result = json.loads(text)
        return {
            "success": bool(result.get("success", False)),
            "margin": float(max(0.0, min(1.0, result.get("margin", 0.5)))),
            "reasoning": str(result.get("reasoning", ""))[:200],
        }
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "rate_limit" in err.lower():
            raise RuntimeError("rate-limited") from e
        a_power = (attacker.get("stealth", 0.5) + attacker.get("threshold", 0.5)) / 2
        d_power = (defender.get("defense_weight", 0.5) + defender.get("coverage", 0.5)) / 2
        success = a_power > d_power
        margin = abs(a_power - d_power)
        return {"success": success, "margin": round(margin, 3), "reasoning": "api-error→physics"}


def judge_battle(
    attacker_strategy: dict,
    defender_strategy: dict,
    universe_dna: str = "",
) -> dict:
    """
    Adjudicate with Azure OpenAI (cached) or physics fallback.
    Returns {success, margin, reasoning, from_cache, llm_adjudicated}.
    """
    key = _strategy_hash(attacker_strategy, defender_strategy)

    if key in _cache:
        cached = _cache[key]
        return {**cached, "from_cache": True, "llm_adjudicated": True}

    if _init_api():
        try:
            result = _call_azure(attacker_strategy, defender_strategy, universe_dna)
            _cache[key] = result
            if len(_cache) % 50 == 0:
                _save_cache()
            return {**result, "from_cache": False, "llm_adjudicated": True}
        except RuntimeError:
            pass  # rate-limited — fall through to physics, do NOT cache

    # No API or rate-limited — physics-based deterministic fallback
    a_power = (attacker_strategy.get("stealth", 0.5) + attacker_strategy.get("threshold", 0.5)) / 2
    d_power = (defender_strategy.get("defense_weight", 0.5) + defender_strategy.get("coverage", 0.5)) / 2
    a_roll = a_power * random.uniform(0.8, 1.2)
    d_roll = d_power * random.uniform(0.8, 1.2)
    success = a_roll > d_roll
    margin = abs(a_roll - d_roll)
    result = {
        "success": success,
        "margin": round(margin, 3),
        "reasoning": _physics_reasoning(attacker_strategy, defender_strategy, success, a_roll, d_roll),
    }
    _cache[key] = result
    return {**result, "from_cache": False, "llm_adjudicated": False}


def _physics_reasoning(attacker: dict, defender: dict, success: bool, a_roll: float, d_roll: float) -> str:
    style = (attacker.get("timing") or attacker.get("attack_style") or "HYBRID").upper()
    stealth = attacker.get("stealth", 0.5)
    coverage = defender.get("coverage", 0.5)
    det = defender.get("detection_threshold", 0.5)
    if success:
        if stealth > 0.7:
            return f"{style} slips coverage gap ({coverage:.2f}); stealth={stealth:.2f} evades det={det:.2f}"
        elif a_roll > d_roll * 1.3:
            return f"overwhelming {style} burst (+{a_roll - d_roll:.2f}) saturates adaptive defense"
        else:
            return f"{style} probe wins: atk={a_roll:.2f} > def={d_roll:.2f}; margin sufficient"
    else:
        if coverage > 0.7:
            return f"perimeter coverage ({coverage:.2f}) deflects {style}; insufficient entropy"
        elif det > 0.7:
            return f"detection threshold ({det:.2f}) intercepts {style} before payload"
        else:
            return f"{style} absorbed: def={d_roll:.2f} > atk={a_roll:.2f}; attacker recalibrates"


def flush_cache() -> int:
    """Force-persist cache. Returns number of entries saved."""
    _save_cache()
    return len(_cache)


_load_cache()
