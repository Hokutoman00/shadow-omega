# Shadow-Ω — Multiverse Code Auditor

**5 isolated universes of adversarial AI agents attack your code in parallel. When 3+ independently converge on the same vulnerability, it crystallizes into an ESLint rule.**

Built for **Microsoft Agents League 2026** — powered by Microsoft AutoGen v0.4 + Azure AI Foundry / GitHub Models.

🎬 **Demo video (2:17):** https://youtu.be/i37Xn0-GrPk

![Mid-Stage — 5-universe ledger](screenshots/02-midstage-universe-ledger.png)

## The Problem

ESLint, SonarQube, and Semgrep catch patterns that have **already occurred**. They cannot identify what a determined adversary — one that has never existed before — would discover tomorrow.

Shadow-Ω asks a different question: *"What would 5 independent adversarial AIs converge on as the most dangerous pattern in this codebase — if they evolved in isolation for 100 turns?"*

## How It Works

| Stage | What happens |
|-------|--------------|
| **Pre-Stage** | AST entropy mapping identifies high-risk attack-surface nodes, visualized as a 3D force-directed planet graph |
| **Mid-Stage** | 5 parallel universes (AGGRESSIVE / STEALTHY / ADAPTIVE), each running 20 islands of Attacker + Defender agents evolving via mutation, fitness selection, and Dark Market strategy trading |
| **Strategic Layer** | An AutoGen v0.4 agent council (Attacker + Defender + ConvergenceOrchestrator) fires every 10 turns via Azure AI Foundry (priority 1) or GitHub Models (priority 2). Council output propagates through the physics layer as epoch signals |
| **Post-Stage** | When 3+ universes independently converge on the same strategy fingerprint, a LIVE THREAT fires with confidence `1 − (1/N)^(k−1)`, and an ESLint rule skeleton is exported from the Fossil Record |

![Architecture — two-layer agent design](screenshots/05-architecture-two-layer.png)

A detailed Mermaid architecture diagram, agent design notes, and metrics live in [t1-shadow-omega-core/README.md](t1-shadow-omega-core/README.md).

## Quick Start

No credentials required — the system runs fully in physics-fallback mode out of the box.

```bash
# Backend (FastAPI + SSE, port 8090)
cd t1-shadow-omega-core
pip install -r requirements.txt
uvicorn main:app --port 8090 --reload

# Frontend (React dashboard)
cd t1-agents-league-ui
npm install && npm run dev
# → http://localhost:5173 → click INITIATE MULTIVERSE
```

To enable the AutoGen + LLM strategic layer, copy [t1-shadow-omega-core/.env.example](t1-shadow-omega-core/.env.example) to `.env` and fill either the GitHub Models values or the Azure AI Foundry values described there.

## GitHub Copilot + MCP Creative Workflow

Shadow-Ω also ships as a **GitHub Copilot MCP server** for the Agents League Creative Apps track. Copilot can call the auditor from VS Code or Copilot CLI while the developer stays inside the coding workflow.

```bash
# Confirm Copilot sees the workspace MCP server
gh copilot -- mcp get shadow-omega-auditor --json

# Smoke-test the actual MCP stdio protocol
python t1-shadow-omega-core/verify_mcp_server.py
```

The repository includes three MCP entry points:

- [.mcp.json](.mcp.json) — Copilot CLI workspace config
- [.github/mcp.json](.github/mcp.json) — GitHub workspace config fallback
- [.vscode/mcp.json](.vscode/mcp.json) — VS Code Copilot Agent Mode config

The server exposes `get_shadow_omega_brief`, `audit_code`, `get_multiverse_status`, and `export_eslint_rules`. Usage details and verification output live in [COPILOT_USAGE.md](COPILOT_USAGE.md).

## Repository Layout

```
t1-shadow-omega-core/   Python 3.11 backend — simulation engine, AutoGen council,
                        convergence detection, FastAPI SSE server
t1-agents-league-ui/    React 18 + Vite frontend — 3D AST graph, multiverse grid,
                        sigma gauges, Dark Market ledger, VSCode alert mockup
screenshots/            UI captures (see screenshots/README.md)
.mcp.json               Copilot CLI workspace MCP server config
.vscode/mcp.json        VS Code Copilot Agent Mode MCP server config
COPILOT_USAGE.md        Copilot / MCP usage and verification record
```

## Tech Stack

- **Microsoft AutoGen v0.4** (`autogen-agentchat`, `autogen-ext[openai]`) — strategic agent council
- **Azure AI Foundry** (priority 1) / **GitHub Models** (priority 2) / physics fallback (zero-credential)
- Python 3.11 + FastAPI + Server-Sent Events
- React 18 + Vite 6 + Framer Motion + react-force-graph-3d (Three.js)
- TDA persistence diagrams (H₀/H₁ barcodes), reservoir computing for universe-history compression

## Key Numbers

- 200 agents across 5 universes at 0.4 s/turn — LLM councils fire every 10 turns, making real-time demos affordable
- Convergence confidence at 3/5 universes: **97%+** (`1 − (1/5)²`)
- Edge-of-chaos control keeps each universe at σ ≈ 1.0 (Information Bottleneck loss < 0.30)

## License

[MIT](LICENSE) © 2026 HOKUTO TORIGOE
