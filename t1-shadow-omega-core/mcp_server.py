"""
Model Context Protocol (MCP) server for Shadow-Omega multiverse code auditor.

Exposes the Shadow-Omega backend HTTP API (port 8090) to GitHub Copilot agent mode
in VS Code via three MCP tools:
  1. audit_code(source_code: str) - Analyze source code through multiverse simulation
  2. get_multiverse_status() - Current universe fitness / convergence state
  3. export_eslint_rules() - ESLint rule skeletons from fossil record

Uses Python stdlib (urllib.request) for HTTP communication.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any

from convergence_certificate import (
    build_closed_loop_demo,
    build_convergence_certificate,
    dumps as dumps_certificate,
)
from mcp.server.fastmcp import FastMCP

# ── Configuration ──────────────────────────────────────────────────────────
BACKEND_URL = os.environ.get("SHADOW_OMEGA_BACKEND_URL", "http://localhost:8090").rstrip("/")

# ── Server Setup ───────────────────────────────────────────────────────────
mcp = FastMCP("shadow-omega-auditor")


def _http_get(endpoint: str) -> dict[str, Any]:
    """
    Make a GET request to the Shadow-Omega backend.
    Returns parsed JSON response or error dict if backend unavailable.
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.URLError as e:
        return {
            "error": f"Shadow-Omega backend unavailable at {BACKEND_URL}: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {"error": f"Backend returned invalid JSON: {str(e)}"}
    except Exception as e:
        return {"error": f"HTTP request failed: {str(e)}"}


def _http_post(endpoint: str, payload: dict) -> dict[str, Any]:
    """
    Make a POST request to the Shadow-Omega backend.
    Returns parsed JSON response or error dict if backend unavailable.
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except urllib.error.URLError as e:
        return {
            "error": f"Shadow-Omega backend unavailable at {BACKEND_URL}: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {"error": f"Backend returned invalid JSON: {str(e)}"}
    except Exception as e:
        return {"error": f"HTTP request failed: {str(e)}"}


@mcp.tool()
def get_shadow_omega_brief() -> str:
    """
    Explain what Shadow-Omega exposes to GitHub Copilot.

    Use this first when Copilot needs to understand the creative workflow:
    developers ask Copilot to inspect risky code, Copilot passes snippets to
    Shadow-Omega, and Shadow-Omega returns multiverse-derived attack-surface
    signals plus exportable ESLint archetypes.

    Returns:
        JSON string describing the available workflow and backend URL
    """
    return json.dumps(
        {
            "name": "Shadow-Omega MCP Auditor",
            "backend_url": BACKEND_URL,
            "creative_apps_positioning": (
                "A GitHub Copilot creative developer tool: Copilot can call "
                "Shadow-Omega as an MCP server while the developer stays inside "
                "VS Code or Copilot CLI."
            ),
            "recommended_flow": [
                "Call audit_code(source_code) with the risky file or selected snippet.",
                "Call generate_convergence_certificate(source_code) to see which universes converged.",
                "Call run_closed_loop_demo(source_code) to get a patch and re-audit proof.",
                "Call get_multiverse_status() to inspect convergence, sigma, and cascade state.",
                "Call export_eslint_rules() to turn discovered archetypes into lint-rule drafts.",
            ],
            "requires_backend": "Start `uvicorn main:app --port 8090` before live audits.",
        },
        ensure_ascii=False,
    )


@mcp.tool()
def audit_code(source_code: str) -> str:
    """
    Analyze source code through the Shadow-Omega multiverse simulation.

    Sends the source code to the backend for AST entropy analysis and kicks off
    a multiverse audit run across 5 independent universes with attacker/defender
    agents. Returns metrics and attack surface analysis.

    Args:
        source_code: Python source code string to audit

    Returns:
        JSON string containing vulnerability metrics and attack surface planets
    """
    if not source_code or not source_code.strip():
        return json.dumps({"error": "source_code cannot be empty"})

    payload = {
        "source": source_code,
        "universe_id": 0,
        "file_tag": "copilot-audit",
        "requested_by": "github-copilot-mcp",
    }
    result = _http_post("/analysis/source", payload)

    if "error" in result:
        return json.dumps({"error": result["error"]})

    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def generate_convergence_certificate(source_code: str) -> str:
    """
    Generate a judge-repeatable convergence certificate for selected code.

    This trace-backed certificate makes Shadow-Omega's core claim inspectable:
    at least 3 independent adversarial universe profiles must converge on the
    same vulnerability family before the finding is treated as certifiable.

    Args:
        source_code: Source code string to certify

    Returns:
        JSON string containing attack-surface map, trace-derived universe votes,
        confidence, strategy fingerprint, and ESLint rule skeleton when converged
    """
    return dumps_certificate(build_convergence_certificate(source_code))


@mcp.tool()
def run_closed_loop_demo(source_code: str) -> str:
    """
    Demonstrate the Copilot safety loop: discover, patch, re-audit, rule-export.

    Args:
        source_code: Source code string to run through the closed-loop demo

    Returns:
        JSON string containing the initial convergence certificate, patch
        suggestion, after-patch certificate, and loop result
    """
    return dumps_certificate(build_closed_loop_demo(source_code))


@mcp.tool()
def get_multiverse_status() -> str:
    """
    Get current multiverse simulation status.

    Returns the real-time state of all 5 universes including:
    - Current turn number and simulation status
    - Per-universe fitness metrics (mean, attacker, defender)
    - Sigma (σ) chaos coefficient for each universe
    - Convergence events detected
    - Universe health and defender win rates

    Returns:
        JSON string containing full multiverse status snapshot
    """
    status = _http_get("/universe/status")

    if "error" in status:
        return json.dumps({"error": status["error"]})

    sigma_report = _http_get("/sigma/report")
    if "error" not in sigma_report:
        status["sigma_metrics"] = sigma_report.get("sigma_report", {})

    convergence = _http_get("/convergence/history")
    if "error" not in convergence:
        status["convergence_history"] = convergence

    cascade = _http_get("/cascade/status")
    if "error" not in cascade:
        status["cascade_info"] = cascade.get("cascade", {})

    return json.dumps(status, ensure_ascii=False)


@mcp.tool()
def export_eslint_rules() -> str:
    """
    Export crystallized ESLint rule skeletons from the fossil record.

    Retrieves all converged attack patterns discovered and persisted by the
    multiverse simulator. These rules represent emergent vulnerabilities that
    survived independent evolution across 5 parallel universes.

    Each archetype includes:
    - Rule name and severity
    - Strategy fingerprint (hash of convergence pattern)
    - Confidence score (1.0 - (1.0 / N)^(k-1))
    - CWE classification
    - Suggested ESLint implementation skeleton

    Returns:
        JSON string containing array of ESLint rule archetypes
    """
    archetypes_resp = _http_get("/fossil/archetypes")

    if "error" in archetypes_resp:
        return json.dumps({"error": archetypes_resp["error"]})

    archetypes = archetypes_resp.get("archetypes", [])

    if not archetypes:
        return json.dumps(
            {
                "status": "no_archetypes",
                "message": "No convergence events detected yet. "
                "Run a multiverse audit with audit_code() to discover vulnerabilities.",
                "archetypes": [],
            }
        )

    return json.dumps(
        {
            "status": "success",
            "archetype_count": len(archetypes),
            "archetypes": archetypes,
        },
        ensure_ascii=False,
    )


if __name__ == "__main__":
    # Run the MCP server on stdio transport
    mcp.run()
