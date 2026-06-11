# Shadow-Omega Judge Fixtures

Use `risky-transfer.js` to exercise the deterministic convergence certificate path:

```powershell
python t1-shadow-omega-core/verify_mcp_server.py
```

The fixture is intentionally small. It contains a check-then-write value transfer with split balance mutations and no transaction boundary. Shadow-Omega should produce a certifiable convergence certificate and a closed-loop mitigation demo for this pattern.

Expected summary:

```json
{
  "status": "converged",
  "finding": "non_atomic_value_transfer",
  "converged_universes": 3,
  "confidence": 0.96,
  "closed_loop_result": "mitigated",
  "after_patch_status": "not_converged"
}
```
