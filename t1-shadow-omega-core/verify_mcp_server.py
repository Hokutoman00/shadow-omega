"""
Smoke-test the Shadow-Omega MCP server through the real MCP stdio protocol.

This intentionally works even when the FastAPI backend is not running: tool
discovery must succeed, and the audit tool must return a structured backend
availability error instead of crashing.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parent


async def main() -> None:
    server = StdioServerParameters(
        command="python",
        args=[str(ROOT / "mcp_server.py")],
        env={"SHADOW_OMEGA_BACKEND_URL": "http://localhost:8090"},
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = sorted(tool.name for tool in tools.tools)

            expected = {
                "get_shadow_omega_brief",
                "audit_code",
                "generate_convergence_certificate",
                "run_closed_loop_demo",
                "get_multiverse_status",
                "export_eslint_rules",
                "ground_finding_in_knowledge_base",
                "get_knowledge_provenance",
            }
            missing = expected.difference(names)
            if missing:
                raise SystemExit(f"Missing MCP tools: {sorted(missing)}")

            brief = await session.call_tool("get_shadow_omega_brief", {})
            audit = await session.call_tool(
                "audit_code",
                {
                    "source_code": (
                        "function transfer(user, target, amount) { "
                        "if (user.balance >= amount) { target.balance += amount; "
                        "user.balance -= amount; } }"
                    )
                },
            )
            certificate = await session.call_tool(
                "generate_convergence_certificate",
                {
                    "source_code": (
                        "function transfer(user, target, amount) { "
                        "if (user.balance >= amount) { target.balance += amount; "
                        "user.balance -= amount; } }"
                    )
                },
            )
            loop = await session.call_tool(
                "run_closed_loop_demo",
                {
                    "source_code": (
                        "function transfer(user, target, amount) { "
                        "if (user.balance >= amount) { target.balance += amount; "
                        "user.balance -= amount; } }"
                    )
                },
            )
            grounding = await session.call_tool(
                "ground_finding_in_knowledge_base",
                {"finding": "non_atomic_value_transfer"},
            )
            provenance = await session.call_tool("get_knowledge_provenance", {})

            grounding_payload = json.loads(grounding.content[0].text)
            provenance_payload = json.loads(provenance.content[0].text)

            print(
                json.dumps(
                    {
                        "server": "shadow-omega-auditor",
                        "tools": names,
                        "brief_ok": bool(brief.content),
                        "audit_response_ok": bool(audit.content),
                        "certificate_ok": bool(certificate.content),
                        "closed_loop_ok": bool(loop.content),
                        "grounding_ok": bool(grounding_payload.get("citations")),
                        "grounding_provenance": grounding_payload.get("provenance"),
                        "knowledge_path": provenance_payload.get("active_path"),
                    },
                    indent=2,
                )
            )


if __name__ == "__main__":
    asyncio.run(main())
