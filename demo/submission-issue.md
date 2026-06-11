<!-- GitHub Issue: microsoft/agentsleague
     Title: Project: [Creative Apps] - Shadow-Omega: Copilot Multiverse Code Auditor
     Label: Creative Apps -->

### Track

Creative Apps (GitHub Copilot + MCP)

### Project Name

Shadow-Omega: Copilot Multiverse Code Auditor

### GitHub Username

Hokutoman00

### Repository URL

https://github.com/Hokutoman00/shadow-omega

### Project Description

Shadow-Ω turns GitHub Copilot into a multiverse security design partner. A developer selects risky source code in VS Code or Copilot CLI, Copilot calls the `shadow-omega-auditor` MCP server, and Shadow-Ω runs the snippet through 5 independent adversarial universes before crystallizing converged attack patterns into ESLint rule drafts.

**The problem:** Copilot can write, explain, and refactor code, but developers still need a creative way to ask: "What would a future adversary discover in this code if several attacker models evolved independently?"

**Shadow-Ω answers:** "What if Copilot could consult 5 isolated adversarial universes before the bug ever shipped?"

**How it works:**

1. **Copilot MCP layer** - `.mcp.json`, `.github/mcp.json`, and `.vscode/mcp.json` expose `shadow-omega-auditor` to GitHub Copilot workflows
2. **Pre-stage** - AST entropy mapping identifies high-risk attack surface nodes, visualized as a 3D force-directed planet graph
3. **Mid-stage** - 5 parallel universes run 20 islands of attacker/defender agents each, evolving independently through mutation, fitness selection, and Dark Market strategy trading
4. **Strategic layer** - Microsoft AutoGen v0.4 fires an agent council every 10 turns through Azure AI Foundry or GitHub Models, with deterministic physics fallback for zero-credential demos
5. **Post-stage** - When 3+ universes converge on the same strategy fingerprint, a LIVE THREAT event fires and the Fossil Record exports an ESLint rule skeleton
6. **Closed-loop safety** - Copilot can request a convergence certificate, apply a guarded patch, re-audit the patched code, and preserve the pattern as a reusable lint rule

**Key innovation:** Copilot is no longer only a code generator. Through MCP, it becomes the front door to an interactive adversarial simulation that discovers new lint-rule ideas by multiverse consensus, then verifies that the proposed fix breaks convergence.

### Demo Video or Screenshots

- Architecture demo (2:17): https://youtu.be/i37Xn0-GrPk
- Copilot convergence certificate demo (1:51): https://youtu.be/HMq6hyqLzb8

### Primary Programming Language

Python / TypeScript

### Key Technologies Used

- **GitHub Copilot CLI / VS Code Copilot Agent Mode**
- **Model Context Protocol** Python server (`mcp.server.fastmcp.FastMCP`)
- Workspace MCP configs: `.mcp.json`, `.github/mcp.json`, `.vscode/mcp.json`
- **Microsoft AutoGen v0.4** (`autogen-agentchat`, `autogen-ext[openai]`)
- **Azure AI Foundry** priority path and **GitHub Models** fallback path
- Python 3.11 + FastAPI + Server-Sent Events (port 8090)
- React 18 + Vite + Framer Motion + react-force-graph-3d (Three.js)
- TDA persistence diagrams, reservoir computing, sigma edge-of-chaos monitor

### Submission Type

Individual

### Team Members

- @Hokutoman00 - Full Stack AI / Security Systems Developer

### Submission Requirements

- [x] My project meets the track-specific challenge requirements
- [x] My repository includes a comprehensive README.md with setup instructions
- [x] My code does not contain hardcoded API keys or secrets
- [x] I have included demo materials (video or screenshots)
- [x] My project is my own work with proper attribution for any third-party code
- [x] I agree to the [Code of Conduct](https://github.com/microsoft/agentsleague/blob/main/CODE_OF_CONDUCT.md)
- [x] I have read and agree to the [Disclaimer](https://github.com/microsoft/agentsleague/blob/main/DISCLAIMER.md)
- [x] My submission does NOT contain any confidential, proprietary, or sensitive information
- [x] I confirm I have the rights to submit this content and grant the necessary licenses

### Quick Setup Summary

```bash
# Copilot MCP verification
gh copilot -- mcp get shadow-omega-auditor --json
python t1-shadow-omega-core/verify_mcp_server.py

# Backend (FastAPI SSE server)
cd t1-shadow-omega-core
pip install -r requirements.txt
uvicorn main:app --port 8090 --reload

# Frontend (React dashboard)
cd ../t1-agents-league-ui
npm install && npm run dev
# -> http://localhost:5173 -> click INITIATE MULTIVERSE
```

No credentials required - runs fully in physics-fallback mode. For AI features, copy `.env.example` and fill either the GitHub Models values or the Azure AI Foundry values described there.

Copilot usage record: https://github.com/Hokutoman00/shadow-omega/blob/main/COPILOT_USAGE.md

Judge evidence bundle: https://github.com/Hokutoman00/shadow-omega/tree/main/judge-evidence

### Technical Highlights

- **Copilot-native MCP workflow**: GitHub Copilot CLI can discover `shadow-omega-auditor`, load it through `--additional-mcp-config`, and call the MCP tools non-interactively; sanitized evidence is committed
- **Judge-repeatable verification**: `verify_mcp_server.py` uses the real MCP stdio protocol to list tools and call `audit_code`
- **Convergence Certificate**: `generate_convergence_certificate` returns attack-surface map, trace-derived universe votes, confidence, strategy fingerprint, and ESLint rule skeleton
- **GitHub Models council evidence**: AutoGen council transcript generated through the current `https://models.github.ai/inference` endpoint with credential values omitted
- **Closed-loop demo**: `run_closed_loop_demo` shows discover -> guarded patch -> re-audit -> reusable rule
- **Creative developer experience**: The app combines editor-native Copilot interaction with a cinematic 3D dashboard, live universes, threat banners, and ESLint archetype output
- **Two-layer architecture**: AutoGen councils run every 10 turns while the physics simulation runs at 0.4s/turn across 200 agents
- **5-universe independence**: A vulnerability discovered by 3+ independently evolved universes has survived diverse evolutionary pressure
- **Fossil Record**: Converged strategies become named archetypes with ESLint rule skeletons

### Challenges & Learnings

**Challenge:** A spectacular creative simulation is not enough if it lives outside the developer workflow.

**Solution:** Ship Shadow-Ω as a Copilot MCP server so Copilot can call the auditor from VS Code or Copilot CLI while the developer stays in context.

**Challenge:** Running LLM inference at 200-agent simulation speed is too expensive for a real-time demo.

**Solution:** Use a two-layer architecture. AutoGen councils fire every 10 turns as strategic epoch signals while the fast physics layer evolves every turn.

**Challenge:** Making vulnerability convergence meaningful rather than decorative.

**Solution:** Require 3+ independently seeded universes to converge on the same strategy fingerprint before exporting a rule.

### Contact Information

hokutoman00@gmail.com

### Country/Region

Japan
