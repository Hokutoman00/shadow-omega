# Screenshots

The screenshots below show Shadow-Ω running live. To reproduce locally:

```bash
cd t1-shadow-omega-core && uvicorn main:app --port 8090
cd t1-agents-league-ui && npm run dev
# open http://localhost:5173 → click INITIATE MULTIVERSE
```

## UI Panels

| Panel | Description |
|-------|-------------|
| **Pre-Stage** (left) | 3D force graph of AST entropy planets — attack surface nodes pulse during scan |
| **Mid-Stage** (center) | 5-universe ledger — attacker/defender fitness, σ (chaos coefficient), TDA barcodes per universe |
| **Dark Market** (center) | Real-time mutation trade feed — strategy DNA evolving each turn |
| **Convergence Banner** (overlay) | Full-width alert when 3+ universes independently converge on the same attack fingerprint |
| **Post-Stage** (right) | Information Bottleneck loss gauge + VSCode mockup with live ESLint rule feedback |

## Demo Video

See the full simulation in action: *(YouTube link — added after recording)*

## Architecture Diagram

See [README.md](../t1-shadow-omega-core/README.md#architecture) for the full Mermaid architecture diagram showing how Microsoft AutoGen v0.4, Azure AI Foundry, and the physics simulation layer interact.
