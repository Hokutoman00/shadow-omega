# GitHub Copilot Usage Record

Shadow-Omega includes Copilot-facing MCP configuration so the auditor can be used from GitHub Copilot workflows.

Final Copilot convergence certificate demo: https://youtu.be/HMq6hyqLzb8

## MCP Configuration

| Target | File | Purpose |
| --- | --- | --- |
| Copilot CLI | `.mcp.json` | Workspace MCP server discovered by `gh copilot -- mcp list/get` |
| GitHub MCP workspace fallback | `.github/mcp.json` | Same server config for GitHub-oriented workspace loaders |
| VS Code Copilot | `.vscode/mcp.json` | VS Code MCP server definition for Copilot Agent Mode |

Server:

- Name: `shadow-omega-auditor`
- Transport: stdio
- Command: `python t1-shadow-omega-core/mcp_server.py`
- Backend URL: `http://localhost:8090`

## Tools Exposed

- `get_shadow_omega_brief` - explains the creative developer workflow.
- `audit_code` - sends selected source code to the Shadow-Omega backend for AST entropy and multiverse audit analysis.
- `generate_convergence_certificate` - returns attack-surface map, trace-derived universe votes, confidence, and ESLint rule skeleton.
- `run_closed_loop_demo` - demonstrates discover -> patch -> re-audit -> rule-export.
- `get_multiverse_status` - returns current universe, sigma, convergence, and cascade state.
- `export_eslint_rules` - exports converged vulnerability archetypes as ESLint rule skeletons.

## Verified MCP Protocol Use

Command:

```powershell
python t1-shadow-omega-core/verify_mcp_server.py
```

Observed result:

```json
{
  "server": "shadow-omega-auditor",
  "tools": [
    "audit_code",
    "export_eslint_rules",
    "generate_convergence_certificate",
    "get_multiverse_status",
    "get_shadow_omega_brief",
    "run_closed_loop_demo"
  ],
  "brief_ok": true,
  "audit_response_ok": true,
  "certificate_ok": true,
  "closed_loop_ok": true
}
```

This confirms the server works through the real MCP stdio protocol. The audit call returns structured output even when the backend is not running, so Copilot receives a recoverable backend-availability message instead of a crashed tool.

## Verified Copilot CLI Recognition

Recognition command:

```powershell
gh copilot -- mcp get shadow-omega-auditor --json
```

Observed result:

```json
{
  "shadow-omega-auditor": {
    "tools": ["*"],
    "type": "local",
    "command": "python",
    "args": ["t1-shadow-omega-core/mcp_server.py"],
    "env": {
      "SHADOW_OMEGA_BACKEND_URL": "http://localhost:8090"
    },
    "source": "workspace",
    "sourcePath": "C:\\tmp\\shadow-omega-release\\.mcp.json"
  }
}
```

Non-interactive Copilot CLI tool-call command shape:

```powershell
gh copilot -- --additional-mcp-config "@<mcp-wrapper.json>" `
  --allow-tool='shadow-omega-auditor' `
  -p "Use the shadow-omega-auditor MCP server..."
```

Observed result:

- Passing `.mcp.json` directly is not enough for the current CLI; `--additional-mcp-config` expects a top-level `mcpServers` wrapper.
- With that wrapper, Copilot CLI loaded `shadow-omega-auditor` as a connected stdio MCP server.
- Copilot CLI issued real tool requests to `get_shadow_omega_brief`, `generate_convergence_certificate`, and `run_closed_loop_demo`.
- The certificate run returned `status=converged`, `finding=non_atomic_value_transfer`, `converged_universes=3`, `closed_loop_result=mitigated`, and `after_patch_status=not_converged`.
- Raw JSONL logs are not committed because they contain model reasoning events. Sanitized tool-call evidence is committed in `judge-evidence/copilot-cli-mcp-evidence.json`.

Minimal wrapper:

```json
{
  "mcpServers": {
    "shadow-omega-auditor": {
      "type": "local",
      "command": "python",
      "args": ["t1-shadow-omega-core/mcp_server.py"],
      "env": {"SHADOW_OMEGA_BACKEND_URL": "http://localhost:8090"},
      "tools": ["*"]
    }
  }
}
```

## VS Code / GitHub Copilot Agent Mode Flow

1. Open this repository in VS Code.
2. Ensure GitHub Copilot is enabled.
3. Start the backend:

   ```powershell
   cd t1-shadow-omega-core
   uvicorn main:app --port 8090 --reload
   ```

4. Ask Copilot Agent Mode:

   ```text
   Use the shadow-omega-auditor MCP server on this selected JavaScript function.
   First generate a convergence certificate, then run the closed-loop demo.
   Apply the guarded patch only if the after-patch certificate is not_converged.
   ```

5. Copilot can call the MCP tools while the developer remains inside the editor.

## Creative Apps Fit

The Creative Apps track asks for innovative applications built with GitHub Copilot and welcomes MCP server integrations. Shadow-Omega turns Copilot into a multiverse security design partner: the developer selects code, Copilot calls the MCP auditor, and the result becomes a certificate, a guarded patch, a re-audit result, and a practical lint-rule draft.

## Judge Evidence Bundle

`judge-evidence/` contains the score-focused evidence added after final review:

- `copilot-cli-mcp-evidence.json` - sanitized proof of Copilot CLI loading and calling the MCP server.
- `convergence-trace-risky-transfer.json` - five-universe trace for the risky transfer fixture.
- `certificate-risky-transfer.json` - `simulation_trace_hybrid` certificate whose votes include `trace_turn`, `strategy_fingerprint`, fitness, sigma, and observed source lines.
- `closed-loop-risky-transfer.json` - patch and after-patch re-audit proof.
- `github-models-council-transcript.json` - AutoGen council evidence from GitHub Models via `https://models.github.ai/inference`, with credential values omitted.
