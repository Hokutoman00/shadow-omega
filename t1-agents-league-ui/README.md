# Shadow-Ω Frontend — Multiverse Dashboard

React 18 + Vite 6 dashboard that renders the live state of all 5 adversarial universes streamed from the backend over Server-Sent Events.

## Run

```bash
npm install
npm run dev
# → http://localhost:5173 → click INITIATE MULTIVERSE
```

Requires the backend running on port 8090 (`cd ../t1-shadow-omega-core && uvicorn main:app --port 8090`).

## Panels

| Component | Role |
|-----------|------|
| `ASTGraphPanel` | Pre-Stage — 3D force-directed graph of AST entropy planets (react-force-graph-3d / Three.js) |
| `MultiverseGrid` / `MultiverseDisplay` | Mid-Stage — per-universe ledger: ATK/DEF fitness, σ chaos coefficient, TDA H₀/H₁ barcodes |
| `DarkMarketLedger` / `DarkMarketTicker` | Real-time mutation trade feed between agent islands |
| `SigmaGaugePanel` | Edge-of-chaos monitor (target σ ≈ 1.0) |
| `ConvergenceBanner` | LIVE THREAT alert when 3+ universes converge on the same strategy fingerprint |
| `PostStageBottleneck` | Information Bottleneck loss gauge |
| `ArchetypeOutputPanel` | Fossil Record archetypes + exported ESLint rule skeletons |
| `VSCodeMockup` | Editor mockup showing the generated ESLint rule firing on the vulnerable source |

## Stack

React 18, Vite 6, Framer Motion, react-force-graph-3d (Three.js). State is driven entirely by the SSE event stream — no client-side simulation.
