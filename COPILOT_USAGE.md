# GitHub Copilot Usage Record

Shadow-Omega includes Copilot-facing MCP configuration so the auditor can be used from GitHub Copilot workflows.

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
- `generate_convergence_certificate` - returns attack-surface map, universe votes, confidence, and ESLint rule skeleton.
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
    "get_multiverse_status",
    "get_shadow_omega_brief"
  ],
  "brief_ok": true,
  "audit_response_ok": true,
  "certificate_ok": true,
  "closed_loop_ok": true
}
```

This confirms the server works through the real MCP stdio protocol. The audit call returns structured output even when the backend is not running, so Copilot receives a recoverable backend-availability message instead of a crashed tool.

## Verified Copilot CLI Recognition

Command:

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

Command:

```powershell
gh copilot -p "Use the configured workspace MCP server named shadow-omega-auditor..." --allow-all-tools --output-format text --stream off
```

Observed result:

- Copilot CLI executed with no file changes.
- Current non-interactive Copilot CLI preview did not expose custom workspace MCP tools as callable agent functions in this environment, even though `mcp list/get` recognized the server.
- The repository therefore includes `verify_mcp_server.py` as the judge-repeatable protocol proof, plus `.vscode/mcp.json` for VS Code Copilot Agent Mode where workspace MCP servers are expected to be surfaced in the editor workflow.

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
