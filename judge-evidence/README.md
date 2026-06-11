# Judge Evidence

This folder contains sanitized evidence for the Shadow-Omega Creative Apps submission.

## Files

- `copilot-cli-mcp-evidence.json` - sanitized Copilot CLI MCP evidence. It records MCP server loading and tool calls without raw model reasoning logs.
- `convergence-trace-risky-transfer.json` - five-universe deterministic trace for the risky transfer fixture.
- `certificate-risky-transfer.json` - MCP certificate output derived from the trace.
- `closed-loop-risky-transfer.json` - discover -> patch -> re-audit loop proof.
- `github-models-council-transcript.json` - AutoGen council transcript/config evidence. If credentials are available while generating, it records `llm_driven: true`; otherwise it records the fallback reason.

Regenerate:

```powershell
python t1-shadow-omega-core/generate_judge_evidence.py
```

For live GitHub Models council evidence, provide `GITHUB_TOKEN` in the environment before running the script.
