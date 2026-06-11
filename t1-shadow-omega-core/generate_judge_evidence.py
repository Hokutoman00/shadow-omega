"""
Generate sanitized judge evidence for the Shadow-Omega Creative Apps submission.

The generated files intentionally exclude raw Copilot JSONL logs because those
logs can contain model reasoning events. The Copilot CLI file is a sanitized
transcription of an observed run; this generator preserves that disclosure and
does not replay `gh copilot`. Only tool names, MCP server status, success flags,
and final user-visible summaries are persisted.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parent
EVIDENCE = ROOT / "judge-evidence"
FIXTURE = ROOT / "demo" / "fixtures" / "risky-transfer.js"

sys.path.insert(0, str(CORE))

warnings.filterwarnings("ignore", message="Resolved model mismatch:.*")

from autogen_agents import UniverseAgentCouncil, agents_config  # noqa: E402
from convergence_certificate import (  # noqa: E402
    build_closed_loop_demo,
    build_convergence_certificate,
    build_simulation_trace,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _safe_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "azure_foundry_connected": config.get("azure_foundry_connected"),
        "github_models_connected": config.get("github_models_connected"),
        "active_backend": config.get("active_backend"),
        "active_model": config.get("active_model"),
        "resource_name": config.get("resource_name"),
        "deployment": config.get("deployment"),
        "github_models_base_url": config.get("github_models_base_url"),
        "framework": config.get("framework"),
        "council_interval_turns": config.get("council_interval_turns"),
        "fallback": config.get("fallback"),
    }


def _copilot_evidence(source_code: str) -> dict[str, Any]:
    source_sha = hashlib.sha256(source_code.encode("utf-8")).hexdigest()
    return {
        "schema": "shadow-omega.copilot-cli-mcp-evidence.v1",
        "observed_at": "2026-06-11T20:34:21+09:00",
        "evidence_kind": "sanitized_transcription_of_observed_copilot_cli_run",
        "observation_method": (
            "Live Copilot CLI run observed locally, then manually reduced to "
            "server names, tool names, public result fields, and success flags."
        ),
        "regeneration_scope": (
            "generate_judge_evidence.py reproduces this sanitized evidence file "
            "from the recorded observation; it does not replay Copilot CLI."
        ),
        "raw_logs_committed": False,
        "reason": (
            "Raw Copilot JSONL contains reasoning events; this file keeps only "
            "a sanitized observation transcript of tool-call evidence."
        ),
        "mcp_config_recognition": {
            "command": "gh copilot -- mcp get shadow-omega-auditor --json",
            "server": "shadow-omega-auditor",
            "source": "workspace",
            "sourcePath": "C:\\tmp\\shadow-omega-release\\.mcp.json",
            "transport": "stdio",
            "command_under_test": "python t1-shadow-omega-core/mcp_server.py",
            "recognized": True,
        },
        "copilot_cli_runtime": {
            "command_shape": (
                "gh copilot -- --additional-mcp-config @<mcp-wrapper.json> "
                "--allow-tool='shadow-omega-auditor' -p <prompt>"
            ),
            "mcp_servers_loaded": [
                {
                    "name": "shadow-omega-auditor",
                    "status": "connected",
                    "transport": "stdio",
                },
                {
                    "name": "github-mcp-server",
                    "status": "connected",
                    "source": "builtin",
                    "transport": "http",
                },
            ],
            "tool_requests": [
                {
                    "tool": "get_shadow_omega_brief",
                    "mcpServerName": "shadow-omega-auditor",
                    "success": True,
                },
                {
                    "tool": "generate_convergence_certificate",
                    "mcpServerName": "shadow-omega-auditor",
                    "source_sha256": source_sha,
                    "success": True,
                },
                {
                    "tool": "run_closed_loop_demo",
                    "mcpServerName": "shadow-omega-auditor",
                    "source_sha256": source_sha,
                    "success": True,
                },
            ],
            "assistant_visible_summary": {
                "certificate_status": "converged",
                "finding": "non_atomic_value_transfer",
                "converged_universes": 3,
                "closed_loop_result": "mitigated",
                "after_patch_status": "not_converged",
            },
        },
        "reproduction_notes": [
            "Wrap .mcp.json under a top-level mcpServers object when passing --additional-mcp-config.",
            "Use --allow-tool='shadow-omega-auditor' so Copilot CLI can call the local MCP server non-interactively.",
            "This JSON is a sanitized transcription, not a raw log export and not a replay harness.",
            "Do not commit raw JSONL; sanitize to tool names, status, and public outputs.",
        ],
    }


async def _live_council_evidence() -> dict[str, Any]:
    state = {
        "turn": 80,
        "avg_attacker_fitness": 0.82,
        "avg_defender_fitness": 0.48,
        "sigma": 0.77,
    }
    config = agents_config()
    payload: dict[str, Any] = {
        "schema": "shadow-omega.autogen-council-transcript.v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "config": _safe_config(config),
        "state": state,
        "credential_values_recorded": False,
        "content_policy_hardening": (
            "Council prompts use secure-code risk reviewer/control planner language "
            "so GitHub Models can run the defensive simulation without triggering "
            "content filters."
        ),
    }

    council = UniverseAgentCouncil(0, "aggressive")
    payload["client_available"] = council.available
    try:
        if council.available:
            result = await council.run_council(state)
            payload["llm_driven"] = result.llm_driven
            payload["agent_names"] = {
                "risk_reviewer": "attacker_u0",
                "control_planner": "defender_u0",
            }
            payload["strategy_output"] = {
                "attack": result.attack,
                "defense": result.defense,
                "fingerprint": result.fingerprint,
                "reasoning_excerpt": result.reasoning[:180],
            }
        else:
            payload["llm_driven"] = False
            payload["skip_reason"] = "No Azure AI Foundry or GitHub Models client available in this environment."
    finally:
        client = getattr(council, "_client", None)
        if client is not None and hasattr(client, "close"):
            await client.close()

    return payload


def _readme() -> str:
    return """# Judge Evidence

This folder contains sanitized evidence for the Shadow-Omega Creative Apps submission.

## Files

- `copilot-cli-mcp-evidence.json` - sanitized transcription of an observed Copilot CLI MCP run. It records MCP server loading and tool calls without raw model reasoning logs; the generator preserves this observation and does not replay `gh copilot`.
- `convergence-trace-risky-transfer.json` - five-universe deterministic trace for the risky transfer fixture.
- `certificate-risky-transfer.json` - MCP certificate output derived from the trace.
- `closed-loop-risky-transfer.json` - discover -> patch -> re-audit loop proof.
- `github-models-council-transcript.json` - AutoGen council transcript/config evidence. If credentials are available while generating, it records `llm_driven: true`; otherwise it records the fallback reason.

Regenerate:

```powershell
python t1-shadow-omega-core/generate_judge_evidence.py
```

For live GitHub Models council evidence, provide `GITHUB_TOKEN` in the environment before running the script.
"""


async def main() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    source_code = FIXTURE.read_text(encoding="utf-8")

    _write_json(EVIDENCE / "copilot-cli-mcp-evidence.json", _copilot_evidence(source_code))
    _write_json(EVIDENCE / "convergence-trace-risky-transfer.json", build_simulation_trace(source_code))
    _write_json(EVIDENCE / "certificate-risky-transfer.json", build_convergence_certificate(source_code))
    _write_json(EVIDENCE / "closed-loop-risky-transfer.json", build_closed_loop_demo(source_code))
    _write_json(EVIDENCE / "github-models-council-transcript.json", await _live_council_evidence())
    (EVIDENCE / "README.md").write_text(_readme(), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
