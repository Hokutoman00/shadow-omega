"""
T1 Shadow War — FastAPI + SSE backend
Port: 8090

Endpoints:
  POST /universe/start        — Start/restart simulation
  POST /universe/stop         — Pause simulation
  GET  /universe/status       — Current status snapshot
  GET  /universe/stream       — SSE live event stream
  GET  /universe/{id}/ledger  — Budget/action history for one universe
  GET  /oracle/market         — List DarkMarketOracle available papers
"""
import asyncio
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from universe import UniverseOrchestrator
from oracle import list_market
from tda_analyzer import compute_barcode
from ledger import get_history
from ast_analyzer import analyze_source, generate_demo_planets, source_to_planets
from universe_init import build_universe_configs, verify_independence
from fossil_record import detect_convergence, get_store, SurvivorRecord
from reservoir import get_readout, get_compressor
from convergence_detector import get_detector
from sigma_monitor import get_monitor
from universe_cascade import get_cascade

# ── State ──────────────────────────────────────────────────────────────────
_orc: UniverseOrchestrator | None = None
_running = False
_subscribers: list[asyncio.Queue] = []
_TURN_INTERVAL = 0.4  # seconds between turns (fast for demo)


def _broadcast(event: dict) -> None:
    data = json.dumps(event, ensure_ascii=False)
    for q in _subscribers:
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            pass  # Drop event, keep subscriber alive


async def _run_loop() -> None:
    global _running
    detector = get_detector()
    monitor = get_monitor()
    cascade = get_cascade()

    while _running and _orc is not None:
        events = await _orc.run_turn()
        # Sample 1 successful battle event per turn (avoid flooding SSE queue)
        battles = [e for e in events if e.get("event_type") == "battle" and e.get("success")]
        if battles:
            _broadcast(battles[0])
        for e in events:
            if e.get("event_type") != "battle":
                _broadcast(e)

        status = _orc.status()
        turn = status["turn"]
        universe_states = status["universes"]

        # Mid-stage: record per-universe state for convergence + sigma
        for u in universe_states:
            uid = u["id"]
            avg_fit = u.get("mean_fitness", 0.0)
            u_agents = [a for a in _orc.agents if a.universe_id == uid]
            detector.record_turn(uid, u_agents, turn, avg_fit)
            monitor.update(uid, u.get("sigma", 1.0))
            cascade.record_win_rate(uid, u.get("defender_win_rate", 0.5))

        # Depth 1-5: independent convergence detection
        conv_events = detector.detect(turn)
        for ev in conv_events:
            _broadcast(ev)

        # Chain infection signal (Depth 4 ratchet complement)
        chain_events = monitor.check_chain_infection(universe_states)
        for ev in chain_events:
            _broadcast(ev)

        # Depth 6: universe death check
        death_events = cascade.check_deaths(turn)
        for ev in death_events:
            uid = ev["universe_id"]
            archetypes = get_store().all_archetypes()
            cascade.inherit_archetype(uid, archetypes)
            _broadcast(ev)
            # Auto-rebirth after 3 turns grace (handled next iteration)
            rebirth_ev = cascade.rebirth(uid, turn + 3)
            _broadcast(rebirth_ev)

        # Auto IB feedback: low sigma (attackers losing) → archetype rules may be FPs
        for u in universe_states:
            uid = u["id"]
            sigma = u.get("sigma", 1.0)
            if sigma < 0.7:
                fp_rate = round((0.7 - sigma) / 0.7, 4)
                get_compressor().apply_fp_feedback(uid, fp_rate)

        # Layer 5: coalition attack every 10 turns
        if turn % 10 == 0:
            for ev in _orc.coalition_attack(turn):
                _broadcast(ev)

        # Layer 4: TDA barcode every 10 turns
        if turn % 10 == 0:
            for uid in range(5):
                report = compute_barcode(uid, turn, _orc.agents)
                _broadcast({
                    "event_type": "tda_report",
                    "universe_id": uid,
                    "turn": turn,
                    "h0_components": report.h0_component_count,
                    "h1_cycles": report.h1_cycle_count,
                    "h0_persistence_max": report.h0_persistence_max,
                    "method": report.method,
                })

        # Status snapshot every 5 turns (includes sigma)
        if turn % 5 == 0:
            _broadcast({
                "event_type": "status_snapshot",
                **status,
                "sigma_report": monitor.sigma_report(),
                "cascade_status": cascade.status(),
            })

        await asyncio.sleep(_TURN_INTERVAL)


# ── App ────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Shadow War API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────────────────
@app.post("/universe/start")
async def start_universe(background_tasks=None):
    global _orc, _running
    if _running:
        return {"status": "already_running", "turn": _orc.turn if _orc else 0}
    _orc = UniverseOrchestrator(on_event=lambda e: None)  # handled in _run_loop with sampling
    _running = True
    asyncio.create_task(_run_loop())
    return {"status": "started", "universes": 5, "islands": 20, "agents_per_universe": 40}


@app.post("/universe/stop")
async def stop_universe():
    global _running
    _running = False
    return {"status": "stopped", "turn": _orc.turn if _orc else 0}


@app.post("/universe/reset")
async def reset_universe():
    global _orc, _running
    _running = False
    await asyncio.sleep(0.1)
    _orc = None
    get_detector().reset()
    return {"status": "reset"}


@app.get("/universe/status")
async def get_status():
    if _orc is None:
        return {"status": "idle", "turn": 0}
    return {"status": "running" if _running else "paused", **_orc.status()}


@app.get("/universe/stream")
async def stream_events(request: Request) -> EventSourceResponse:
    queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
    _subscribers.append(queue)

    async def generator() -> AsyncGenerator[str, None]:
        try:
            yield json.dumps({"event_type": "connected", "message": "Shadow War SSE connected"})
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield data
                except asyncio.TimeoutError:
                    yield json.dumps({"event_type": "heartbeat"})
        finally:
            try:
                _subscribers.remove(queue)
            except ValueError:
                pass

    return EventSourceResponse(generator())


@app.get("/universe/{universe_id}/ledger")
async def get_ledger(universe_id: int, limit: int = 50):
    history = get_history(universe_id, limit)
    budget_info = {}
    if _orc:
        for agent in _orc.agents:
            if agent.universe_id == universe_id:
                budget_info[agent.id] = round(agent.fitness, 4)
    return {"universe_id": universe_id, "history": history, "agent_fitness": budget_info}


@app.get("/oracle/market")
async def oracle_market():
    return {"papers": list_market()}


@app.get("/health")
async def health():
    return {"ok": True, "running": _running, "turn": _orc.turn if _orc else 0}


# ── Pre-stage endpoints ────────────────────────────────────────────────────────

@app.get("/analysis/planets/{universe_id}")
async def get_demo_planets(universe_id: int, n: int = 20):
    """デモ用合成惑星を生成して返す (前段階: 直交初期化済み座標)。"""
    planets = generate_demo_planets(universe_id, n)
    return {"universe_id": universe_id, "planets": planets}


@app.post("/analysis/source")
async def analyze_code_source(payload: dict):
    """
    Python ソースコードを受け取り脆弱性メトリクスを返す。
    Body: {"source": "<python source>", "universe_id": 0, "file_tag": "src"}
    """
    source = payload.get("source", "")
    uid = int(payload.get("universe_id", 0))
    file_tag = str(payload.get("file_tag", "src"))
    metrics = analyze_source(source)
    planets = source_to_planets(source, uid, file_tag)
    return {"metrics": metrics, "planets": planets}


@app.get("/universe/configs")
async def get_universe_configs():
    """5宇宙の直交初期化済み設定を返す (独立性監査付き)。"""
    configs = build_universe_configs()
    audit = verify_independence(configs)
    return {
        "configs": [c._asdict() for c in configs],
        "independence_audit": audit,
    }


# ── Post-stage endpoints ───────────────────────────────────────────────────────

@app.post("/fossil/convergence")
async def fossil_convergence(payload: dict):
    """
    SurvivorRecord リストから収束イベントを検出し ArchetypeRule を返す。
    Body: {"survivors": [...SurvivorRecord], "turn": 42}
    """
    raw = payload.get("survivors", [])
    turn = int(payload.get("turn", 0))
    survivors: list[SurvivorRecord] = [SurvivorRecord(**r) for r in raw]
    events = detect_convergence(survivors, turn)
    store = get_store()
    rules = []
    for ev in events:
        strategy = next(
            (s["strategy_json"] for s in survivors if s["universe_id"] == ev["converged_universes"][0]),
            {},
        )
        rule = store.to_archetype_rule(ev, strategy)
        rules.append(rule)
    return {"events": events, "archetype_rules": rules}


@app.get("/fossil/archetypes")
async def list_archetypes():
    """化石記録に蓄積された全アーキタイプを返す。"""
    return {"archetypes": get_store().all_archetypes()}


@app.post("/feedback/fp")
async def apply_fp_feedback(payload: dict):
    """
    FP フィードバックを受け取り IB β パラメータを更新する。
    Body: {"universe_id": 0, "fp_rate": 0.35}
    """
    uid = int(payload.get("universe_id", 0))
    fp_rate = float(payload.get("fp_rate", 0.0))
    comp = get_compressor()
    comp.apply_fp_feedback(uid, fp_rate)
    return {"universe_id": uid, "fp_rate": fp_rate, "new_beta": comp.get_beta(uid)}


@app.get("/sigma/report")
async def sigma_report():
    """全宇宙のσサマリーを返す。"""
    return {"sigma_report": get_monitor().sigma_report()}


@app.get("/convergence/history")
async def convergence_history():
    """収束検出器の現在のラチェットシグナルと収束済み FP を返す。"""
    d = get_detector()
    return {
        "ratchet_signal": d.get_ratchet_signal(),
        "confirmed_archetype_count": len(d._ratchet_fps),
    }


@app.get("/cascade/status")
async def cascade_status():
    """宇宙の死・免疫記憶のステータスを返す。"""
    return {"cascade": get_cascade().status()}


@app.post("/reservoir/compress")
async def reservoir_compress(payload: dict):
    """
    ArchetypeRule リストを IB 圧縮して返す (CWE 予測 + β フィルタリング)。
    Body: {"archetype_rules": [...], "universe_id": 0, "universe_states": [...]}
    """
    rules = payload.get("archetype_rules", [])
    uid = int(payload.get("universe_id", 0))
    states = payload.get("universe_states", [])
    readout = get_readout()
    compressor = get_compressor()
    compressed = compressor.compress(rules, uid, readout, states)
    return {"compressed_rules": compressed, "beta": compressor.get_beta(uid)}


# ── AutoGen Agent Endpoints ───────────────────────────────────────────────────

@app.get("/agents/status")
async def agents_status():
    """Return per-universe council status and orchestrator initialization state."""
    from autogen_agents import _councils, _orchestrator, agents_available, agents_config
    return {
        "available": agents_available(),
        "config": agents_config(),
        "councils": {
            uid: {
                "dna": c.dna_trait,
                "available": c.available,
                "last_strategy": c._last_strategy.fingerprint if c._last_strategy else None,
            }
            for uid, c in _councils.items()
        },
    }


@app.get("/agents/config")
async def agents_config_endpoint():
    """Return Azure AI Foundry + AutoGen configuration."""
    from autogen_agents import agents_config
    return agents_config()


# ── Demo UI ───────────────────────────────────────────────────────────────────
_DEMO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shadow War — Multiverse Simulation</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0a0a0f; color: #e0e0e0;
       font-family: 'JetBrains Mono','Courier New',monospace;
       font-size: 12px; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

/* ── Header ─────────────────────────────────────────── */
#hdr { display: flex; align-items: center; justify-content: space-between;
       padding: 7px 16px; border-bottom: 1px solid #1e1e2e; flex-shrink: 0; }
#hdr h1 { color: #ef4444; font-size: 0.8rem; letter-spacing: 3px; font-weight: 700; }
#hdr-meta { display: flex; align-items: center; gap: 10px; font-size: 0.68rem; }
#turn-disp  { color: #e0e0e0; }
#champ-disp { color: #ef4444; }
.cnt-chip { color: #555; }
.cnt-chip b { color: #888; }
#status-disp { color: #333; }

/* ── Controls ───────────────────────────────────────── */
#ctrl { display: flex; align-items: center; gap: 6px;
        padding: 5px 16px; border-bottom: 1px solid #111; flex-shrink: 0; }
button { background: #111; border: 1px solid #2a2a3e; color: #888; padding: 3px 11px;
         cursor: pointer; font-size: 0.7rem; border-radius: 2px; font-family: inherit;
         letter-spacing: 1px; transition: border-color 0.15s, color 0.15s; }
button:hover { border-color: #ef4444; color: #ef4444; }
button.on  { border-color: #22c55e; color: #22c55e; }
button.act { border-color: #ef4444; color: #ef4444; }
.ctrl-sep { width: 1px; height: 14px; background: #1e1e2e; }
select { background: #111; border: 1px solid #2a2a3e; color: #888; padding: 2px 5px;
         font-family: inherit; font-size: 0.68rem; border-radius: 2px; }
input[type=range] { width: 68px; accent-color: #ef4444; }

/* ── Convergence banner ─────────────────────────────── */
#conv-ban { display: none; margin: 5px 16px; padding: 7px 13px;
            border: 1px solid #ef4444; background: rgba(239,68,68,0.06);
            border-radius: 2px; flex-shrink: 0; }
#conv-ban.high   { border-color: #f59e0b; background: rgba(245,158,11,0.06); }
#conv-ban.medium { border-color: #60a5fa; background: rgba(96,165,250,0.06); }
#conv-title  { font-size: 0.76rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 2px; }
#conv-detail { font-size: 0.65rem; color: #999; }

/* ── Main 2-col layout ──────────────────────────────── */
#main { display: grid; grid-template-columns: 1fr 218px; flex: 1; overflow: hidden; }

/* ── Left panel ─────────────────────────────────────── */
#left { display: flex; flex-direction: column; overflow: hidden; border-right: 1px solid #111; }

/* Grid */
#grid-sec { padding: 7px 13px 3px; flex-shrink: 0; }
.urow { display: flex; align-items: center; gap: 4px; margin-bottom: 2px; }
.rlabel { width: 52px; font-size: 0.6rem; color: #555; flex-shrink: 0; line-height: 1.3; }
.rlabel b { color: #888; font-weight: 700; }
.cells { display: grid; grid-template-columns: repeat(20, 1fr); gap: 2px; flex: 1; }
.cell { aspect-ratio: 1; background: #14142a; border-radius: 1px;
        transition: background 0.6s ease-out; min-height: 10px; }
.cell.atk-ok { background: #ef4444; transition: background 0.05s; }
.cell.atk-no { background: #1e293b; transition: background 0.05s; }
.cell.migr   { background: #3b82f6; transition: background 0.05s; }
.cell.coal   { background: #f59e0b; transition: background 0.05s; }
.urow.dead .cell  { opacity: 0.1 !important; }
.urow.dead .rlabel { color: #2a2a2a; }
@keyframes rebirthFlash {
  0%,20%,40%,60%,80% { opacity: .2; }
  10%,30%,50%,70%,90%,100% { opacity: 1; }
}
.urow.reb { animation: rebirthFlash 0.8s ease-out forwards; }

/* Fitness scoreboard */
#fit-board { padding: 4px 13px 5px; border-top: 1px solid #0d0d1a; flex-shrink: 0; }
.fb-title { font-size: 0.55rem; color: #333; letter-spacing: 2px; margin-bottom: 3px; }
.fb-rows { display: flex; gap: 6px; }
.fb-col { flex: 1; }
.fb-row { display: flex; align-items: center; gap: 3px; margin-bottom: 1px; }
.fb-lbl { font-size: 0.58rem; color: #444; width: 16px; flex-shrink: 0; }
.fb-bar-wrap { flex: 1; height: 4px; background: #0f0f1a; border-radius: 1px; overflow: hidden; }
.fb-bar-a { height: 100%; width: 0%; background: #ef4444; border-radius: 1px; transition: width 0.5s; }
.fb-bar-d { height: 100%; width: 0%; background: #3b82f6; border-radius: 1px; transition: width 0.5s; }
.fb-val { font-size: 0.55rem; color: #444; width: 26px; text-align: right; flex-shrink: 0; }

/* Log filter */
#log-filter { display: flex; gap: 3px; padding: 4px 13px; flex-shrink: 0; border-top: 1px solid #0d0d1a; }
.flt { background: none; border: 1px solid #1a1a2e; color: #444; padding: 1px 7px;
       font-size: 0.6rem; letter-spacing: 1px; cursor: pointer;
       border-radius: 1px; font-family: inherit; transition: border-color 0.15s, color 0.15s; }
.flt:hover { color: #888; border-color: #333; }
.flt.on { border-color: #ef4444; color: #ef4444; }

/* FP panel */
#fp-pan { padding: 4px 13px; display: flex; align-items: center; gap: 6px;
          flex-shrink: 0; border-top: 1px solid #0d0d1a; font-size: 0.65rem; color: #444; }
#fp-val-disp { width: 28px; color: #888; }

/* Log */
#log { flex: 1; overflow-y: auto; padding: 5px 13px; font-size: 0.66rem; line-height: 1.6; }
.le { padding: 1px 0; border-bottom: 1px solid #0c0c18; }
.le.bat  { color: #22c55e; }
.le.batf { color: #ef4444; opacity: 0.65; }
.le.mig  { color: #3b82f6; }
.le.stat { color: #f59e0b; }
.le.conv { color: #ef4444; font-weight: 700; }
.le.dir  { color: #a78bfa; }
.le.dead { color: #ef4444; opacity: 0.55; }
.le.reb  { color: #22c55e; }
.le.coal { color: #f59e0b; }
.le.chn  { color: #a78bfa; opacity: 0.75; }
.le.tda  { color: #38bdf8; opacity: 0.65; }
.le.hidden { display: none; }

/* ── Right panel ────────────────────────────────────── */
#right { display: flex; flex-direction: column; overflow: hidden; }
.ptitle { font-size: 0.58rem; color: #333; letter-spacing: 2px; margin-bottom: 6px; }

/* Sigma panel with sparkline */
#sig-pan { padding: 8px 10px; border-bottom: 1px solid #111; flex-shrink: 0; }
.srow { display: flex; align-items: center; gap: 4px; margin-bottom: 5px; }
.slbl  { width: 20px; font-size: 0.6rem; color: #555; flex-shrink: 0; }
.sbar-wrap { width: 52px; height: 10px; background: #0f0f1a; border-radius: 1px; overflow: hidden; flex-shrink: 0; }
.sbar  { height: 100%; width: 50%; transition: width 0.4s, background 0.4s;
         background: #3b82f6; border-radius: 1px; }
.sbar.edge { background: #22c55e; }
.sbar.chao { background: #ef4444; }
.sval  { width: 28px; font-size: 0.58rem; color: #666; text-align: right; flex-shrink: 0; }
.spark { flex: 1; font-size: 0.55rem; letter-spacing: 0; line-height: 1; color: #3b82f6;
         white-space: nowrap; overflow: hidden; }

/* TDA panel */
#tda-pan { padding: 8px 10px; border-bottom: 1px solid #111; flex-shrink: 0; }
.trow { display: flex; justify-content: space-between; font-size: 0.6rem; margin-bottom: 3px; }
.trow .tl  { color: #555; }
.trow .th0 { color: #60a5fa; }
.trow .th1 { color: #a78bfa; }
.trow .tst { font-size: 0.54rem; color: #444; }
@keyframes blink { 50% { opacity: .2; } }
.tst.cvg { color: #ef4444; animation: blink 1s infinite; }
.pan-note { font-size: 0.52rem; color: #2a2a3e; margin-bottom: 4px; line-height: 1.5; }
.pan-note .g { color: #22c55e; } .pan-note .r { color: #ef4444; }
.pan-note .b { color: #3b82f6; } .pan-note .y { color: #f59e0b; }

/* Coalition panel */
#coal-pan { padding: 8px 10px; flex: 1; overflow-y: auto; }
.coal-entry { font-size: 0.6rem; color: #f59e0b; border-bottom: 1px solid #0e0e18;
              padding: 2px 0; line-height: 1.5; }
</style>
</head>
<body>

<div id="hdr">
  <h1>SHADOW WAR // MULTIVERSE SIMULATION</h1>
  <div id="hdr-meta">
    <span id="turn-disp">T:0</span>
    <span id="champ-disp" title="Universe with highest average attacker fitness — most dangerous evolution">CHAMPION: —</span>
    <span class="cnt-chip" title="Convergence events: identical defense strategy appeared independently in 3+ universes">CONV:<b id="cnt-conv">0</b></span>
    <span class="cnt-chip" title="New Archetypes: first-ever convergence of this strategy fingerprint (★ novel threat)">ARCH:<b id="cnt-arch">0</b></span>
    <span class="cnt-chip" title="Coalition attacks: top-3 diverse attackers synergized (fires when strategy divergence JSD>0.15)">COAL:<b id="cnt-coal">0</b></span>
    <span id="status-disp">IDLE</span>
  </div>
</div>

<div id="ctrl">
  <button id="btn-start" onclick="startSim()">START</button>
  <button onclick="stopSim()">PAUSE</button>
  <button onclick="resetSim()">RESET</button>
  <div class="ctrl-sep"></div>
  <span style="font-size:0.65rem;color:#444" title="False Positive Rate — fraction of threat alerts that are incorrect (0=no FP, 1=all alerts wrong)">FP rate:</span>
  <select id="fp-uid">
    <option value="0">U0</option><option value="1">U1</option>
    <option value="2">U2</option><option value="3">U3</option>
    <option value="4">U4</option>
  </select>
  <input type="range" id="fp-rate" min="0" max="100" value="30"
         oninput="document.getElementById('fp-val-disp').textContent=(this.value/100).toFixed(2)">
  <span id="fp-val-disp" style="font-size:0.65rem;color:#888;width:28px">0.30</span>
  <button onclick="sendFP()">SEND FP</button>
</div>

<div id="conv-ban">
  <div id="conv-title">CONVERGENCE</div>
  <div id="conv-detail"></div>
</div>

<div id="main">
  <div id="left">
    <div id="grid-sec"></div>

    <div id="fit-board">
      <div class="fb-title">FITNESS  <span style="color:#ef4444">ATK▌</span><span style="color:#3b82f6">DEF</span>  (bright label = winning side)</div>
      <div class="fb-rows" id="fb-rows"></div>
    </div>

    <div id="log-filter">
      <button class="flt on"  id="flt-all"  onclick="setFilter('all')">ALL</button>
      <button class="flt"     id="flt-conv" onclick="setFilter('conv')">CONV</button>
      <button class="flt"     id="flt-coal" onclick="setFilter('coal')">COAL</button>
      <button class="flt"     id="flt-tda"  onclick="setFilter('tda')">TDA</button>
      <button class="flt"     id="flt-dead" onclick="setFilter('dead')">DEAD</button>
      <button class="flt"     id="flt-bat"  onclick="setFilter('bat')">BATTLE</button>
    </div>

    <div id="log"></div>
  </div>

  <div id="right">
    <div id="sig-pan">
      <div class="ptitle">σ BRANCHING RATIO</div>
      <div class="pan-note"><span class="g">■</span> EDGE σ≈1.0 balanced &nbsp;<span class="r">■</span> CHAO σ&gt;1.08 attackers winning &nbsp;<span class="b">■</span> STBL σ&lt;0.92 defenders winning</div>
      <div id="sig-bars"></div>
    </div>
    <div id="tda-pan">
      <div class="ptitle">TDA BARCODE</div>
      <div class="pan-note">H₀ = connected strategy clusters &nbsp; H₁ = strategy loops<br><span class="r">H₀=1 → all universes converged to one strategy</span></div>
      <div id="tda-rows"></div>
    </div>
    <div id="coal-pan">
      <div class="ptitle">COALITION WAR</div>
      <div class="pan-note"><span class="y">■</span> JSD = strategy divergence (0=identical → 1=opposite)<br>High JSD = diverse tactics → stronger multiplier boost</div>
      <div id="coal-log"></div>
    </div>
  </div>
</div>

<script>
const API = 'http://localhost:8090';
let es = null;
let _logFilter = 'all';

// State
const _counts  = {conv: 0, arch: 0, coal: 0};
const _sigHist = {0:[], 1:[], 2:[], 3:[], 4:[]};  // σ history per universe (max 24)
const _fitness = {0:{a:0,d:0}, 1:{a:0,d:0}, 2:{a:0,d:0}, 3:{a:0,d:0}, 4:{a:0,d:0}};

const SPARK_CHARS = '▁▂▃▄▅▆▇█';
const OS_MAP  = {0:'linux', 1:'win', 2:'macos', 3:'linux', 4:'win'};
const STY_MAP = {0:'aggr',  1:'stlth', 2:'adpt', 3:'aggr', 4:'stlth'};

// ── Build 5×20 island grid ────────────────────────────
const gs = document.getElementById('grid-sec');
for (let u = 0; u < 5; u++) {
  const row = document.createElement('div');
  row.className = 'urow'; row.id = 'urow-' + u;
  const lbl = document.createElement('div');
  lbl.className = 'rlabel';
  lbl.innerHTML = '<b>U' + u + '</b> ' + OS_MAP[u] + '<br>' + STY_MAP[u];
  row.appendChild(lbl);
  const cells = document.createElement('div');
  cells.className = 'cells';
  for (let i = 0; i < 20; i++) {
    const c = document.createElement('div');
    c.className = 'cell'; c.id = 'c-u' + u + '-i' + i;
    c.title = 'U' + u + ' Island ' + i + ' — attacker vs defender battle site\nred=attack hit  blue=migration  amber=coalition';
    cells.appendChild(c);
  }
  row.appendChild(cells);
  gs.appendChild(row);
}

// ── Build fitness scoreboard ──────────────────────────
const fbr = document.getElementById('fb-rows');
for (let u = 0; u < 5; u++) {
  const col = document.createElement('div');
  col.className = 'fb-col';
  col.innerHTML =
    '<div class="fb-row"><span class="fb-lbl" id="fbla-' + u + '" title="Attacker avg fitness — higher = attack evolving faster">U' + u + 'A</span>' +
      '<div class="fb-bar-wrap"><div class="fb-bar-a" id="fba-' + u + '"></div></div>' +
      '<span class="fb-val" id="fbav-' + u + '">—</span></div>' +
    '<div class="fb-row"><span class="fb-lbl" id="fbld-' + u + '" title="Defender avg fitness — higher = defense holding">U' + u + 'D</span>' +
      '<div class="fb-bar-wrap"><div class="fb-bar-d" id="fbd-' + u + '"></div></div>' +
      '<span class="fb-val" id="fbdv-' + u + '">—</span></div>';
  fbr.appendChild(col);
}

// ── Build σ gauge rows ────────────────────────────────
const sb = document.getElementById('sig-bars');
for (let u = 0; u < 5; u++) {
  sb.innerHTML +=
    '<div class="srow">' +
      '<span class="slbl">U' + u + '</span>' +
      '<div class="sbar-wrap"><div class="sbar" id="sbar-' + u + '" style="width:50%"></div></div>' +
      '<span class="sval" id="sval-' + u + '">1.00</span>' +
      '<span class="spark" id="spark-' + u + '">▄▄▄▄▄▄▄▄</span>' +
    '</div>';
}

// ── Build TDA rows ────────────────────────────────────
const tr = document.getElementById('tda-rows');
for (let u = 0; u < 5; u++) {
  tr.innerHTML +=
    '<div class="trow">' +
      '<span class="tl">U' + u + '</span>' +
      '<span class="th0" id="th0-' + u + '">H₀:—</span>' +
      '<span class="th1" id="th1-' + u + '">H₁:—</span>' +
      '<span class="tst" id="tst-' + u + '">—</span>' +
    '</div>';
}

// ── Helpers ───────────────────────────────────────────
function flash(cell, cls, ms) {
  if (!cell) return;
  cell.classList.add(cls);
  setTimeout(() => cell.classList.remove(cls), ms || 350);
}

function setCount(key, n) {
  _counts[key] = n;
  document.getElementById('cnt-' + key).textContent = n;
}

function incCount(key) { setCount(key, _counts[key] + 1); }

function addLog(txt, cls) {
  const log = document.getElementById('log');
  const d = document.createElement('div');
  const visible = _logFilter === 'all' || cls === _logFilter || (cls||'').startsWith(_logFilter);
  d.className = 'le ' + (cls||'') + (visible ? '' : ' hidden');
  d.dataset.cls = cls || '';
  d.textContent = '[' + new Date().toLocaleTimeString('en', {hour12: false}) + '] ' + txt;
  log.prepend(d);
  while (log.children.length > 500) log.removeChild(log.lastChild);
}

function setFilter(f) {
  _logFilter = f;
  document.querySelectorAll('.flt').forEach(b => b.classList.remove('on'));
  document.getElementById('flt-' + f).classList.add('on');
  document.querySelectorAll('.le').forEach(el => {
    const c = el.dataset.cls || '';
    el.classList.toggle('hidden', f !== 'all' && c !== f && !c.startsWith(f));
  });
}

// σ sparkline: map value to block char + color class
function _sigBlock(s) {
  const idx = Math.min(7, Math.max(0, Math.round((s - 0.5) / 0.125)));
  return SPARK_CHARS[idx];
}
function _sigColor(s) {
  if (Math.abs(s - 1.0) < 0.08) return '#22c55e';
  if (s > 1.08) return '#ef4444';
  return '#3b82f6';
}

function updateSigma(report) {
  (report || []).forEach(r => {
    const u = r.universe_id, s = r.sigma;
    const bar  = document.getElementById('sbar-'  + u);
    const val  = document.getElementById('sval-'  + u);
    const spk  = document.getElementById('spark-' + u);
    if (!bar) return;

    // bar width: σ range [0.5, 1.5] → [0%, 100%]
    bar.style.width = Math.min(100, Math.max(0, (s - 0.5) * 100)) + '%';
    val.textContent = s.toFixed(2);
    const edge = Math.abs(s - 1.0) < 0.08, chao = s > 1.08;
    bar.className = 'sbar ' + (edge ? 'edge' : chao ? 'chao' : '');

    // sparkline history
    _sigHist[u].push(s);
    if (_sigHist[u].length > 24) _sigHist[u].shift();
    if (spk) {
      // render colored spans per step
      spk.innerHTML = _sigHist[u].map(v => {
        const ch = _sigBlock(v);
        const col = _sigColor(v);
        return '<span style="color:' + col + '">' + ch + '</span>';
      }).join('');
    }
  });
}

function updateFitness(universes) {
  if (!universes) return;
  universes.forEach(u => {
    const uid = u.id;
    const af = u.avg_attacker_fitness || 0;
    const df = u.avg_defender_fitness || 0;
    _fitness[uid] = {a: af, d: df};
    const maxF = Math.max(Math.abs(af), Math.abs(df), 1);
    const barA = document.getElementById('fba-'  + uid);
    const barD = document.getElementById('fbd-'  + uid);
    const valA = document.getElementById('fbav-' + uid);
    const valD = document.getElementById('fbdv-' + uid);
    if (barA) barA.style.width = Math.min(100, (Math.abs(af) / maxF) * 100) + '%';
    if (barD) barD.style.width = Math.min(100, (Math.abs(df) / maxF) * 100) + '%';
    if (valA) valA.textContent = af.toFixed(1);
    if (valD) valD.textContent = df.toFixed(1);
    const lblA = document.getElementById('fbla-' + uid);
    const lblD = document.getElementById('fbld-' + uid);
    if (lblA) lblA.style.color = af > df ? '#ef4444' : '#2a2a3a';
    if (lblD) lblD.style.color = df > af ? '#3b82f6' : '#2a2a3a';
  });
}

function showConv(data) {
  const b = document.getElementById('conv-ban');
  const sev = (data.severity || 'medium').toLowerCase();
  b.className = sev === 'critical' ? '' : sev;
  b.style.display = 'block';
  document.getElementById('conv-title').textContent =
    'CONVERGENCE  U[' + data.converged_universes.join(',') + ']  ' +
    Math.round((data.confidence || 0) * 100) + '%  ' + sev.toUpperCase() +
    (data.is_new_archetype ? '  ★NEW ARCHETYPE' : '') +
    (data.ratchet_active   ? '  ★RATCHET — directional signal now propagating to all universes' : '');
  document.getElementById('conv-detail').textContent =
    'fp=' + (data.strategy_fp || '').substring(0, 12) + '  T=' + data.turn +
    (data.ratchet_active ? '  ratchet=ON' : '');
  setTimeout(() => { b.style.display = 'none'; }, 9000);
}

// ── SSE ───────────────────────────────────────────────
function connectSSE() {
  if (es) es.close();
  es = new EventSource(API + '/universe/stream');
  es.onmessage = e => {
    let data; try { data = JSON.parse(e.data); } catch { return; }
    const et = data.event_type;

    if (et === 'battle') {
      const cell = document.getElementById('c-u' + data.universe_id + '-i' + data.island_id);
      flash(cell, data.success ? 'atk-ok' : 'atk-no', data.success ? 500 : 300);
      if (data.success)
        addLog('U' + data.universe_id + ' I' + data.island_id + ' T' + data.turn +
               ': ' + data.attack_style + ' HIT  Δ' + data.fitness_delta +
               (data.alien_score ? '  alien=' + data.alien_score : ''), 'bat');

    } else if (et === 'migration') {
      flash(document.getElementById('c-u' + data.universe_id + '-i' + data.to_island), 'migr', 700);

    } else if (et === 'status_snapshot') {
      document.getElementById('turn-disp').textContent = 'T:' + data.turn;
      document.getElementById('champ-disp').textContent = 'CHAMPION U' + data.champion_universe + ' (highest ATK)';
      document.getElementById('status-disp').textContent = 'RUNNING';
      if (data.sigma_report)  updateSigma(data.sigma_report);
      if (data.universes)     updateFitness(data.universes);

    } else if (et === 'convergence') {
      incCount('conv');
      if (data.is_new_archetype) incCount('arch');
      showConv(data);
      addLog('CONVERGENCE  U[' + data.converged_universes + ']  ' +
             Math.round((data.confidence || 0) * 100) + '%  ' +
             (data.severity || '').toUpperCase() +
             (data.is_new_archetype ? '  ★NEW-ARCHETYPE' : ''), 'conv');

    } else if (et === 'direction_convergence') {
      addLog('DIR-CONV ⚠  U[' + data.aligned_universes + ']  cos=' +
             (data.max_cosine || 0).toFixed(3) +
             '  early warning — endpoint convergence expected in 10-20 turns', 'dir');

    } else if (et === 'chain_infection') {
      addLog('CHAIN  U' + data.source_universe + '→[' + data.target_universes +
             ']  σ=' + data.sigma_source, 'chn');

    } else if (et === 'universe_death') {
      const row = document.getElementById('urow-' + data.universe_id);
      if (row) row.classList.add('dead');
      addLog('DEAD  U' + data.universe_id + '  T' + data.turn +
             '  consec=' + data.consecutive_low_turns, 'dead');

    } else if (et === 'universe_rebirth') {
      const row = document.getElementById('urow-' + data.universe_id);
      if (row) { row.classList.remove('dead'); row.classList.add('reb');
                 setTimeout(() => row.classList.remove('reb'), 900); }
      addLog('REBIRTH  U' + data.universe_id + '  T' + data.turn +
             '  archetypes=' + data.inherited_archetypes, 'reb');

    } else if (et === 'coalition_attack') {
      incCount('coal');
      (data.agent_ids || []).forEach(id => {
        const m = id.match(/u(\d+)_i(\d+)/);
        if (m) flash(document.getElementById('c-u' + m[1] + '-i' + m[2]), 'coal', 700);
      });
      const cl = document.getElementById('coal-log');
      const ce = document.createElement('div');
      ce.className = 'coal-entry';
      ce.textContent = 'T' + data.turn + ' U' + data.universe_id +
                       ' ×' + data.coalition_multiplier +
                       ' JSD=' + data.jsd_ab.toFixed(2) + '/' + data.jsd_bc.toFixed(2) +
                       ' +' + data.fitness_boost;
      cl.prepend(ce);
      while (cl.children.length > 30) cl.removeChild(cl.lastChild);
      addLog('COAL  U' + data.universe_id + ' ×' + data.coalition_multiplier +
             ' boost=' + data.fitness_boost, 'coal');

    } else if (et === 'tda_report') {
      const u   = data.universe_id;
      const h0e = document.getElementById('th0-' + u);
      const h1e = document.getElementById('th1-' + u);
      const ste = document.getElementById('tst-' + u);
      if (h0e) h0e.textContent = 'H₀:' + data.h0_components;
      if (h1e) h1e.textContent = 'H₁:' + data.h1_cycles;
      if (ste) {
        const cvg = data.h0_components <= 1;
        ste.textContent = cvg ? 'CONVERGING' : 'p=' + (data.h0_persistence_max || 0).toFixed(2);
        ste.className = 'tst' + (cvg ? ' cvg' : '');
      }
      if (data.h0_components <= 1)
        addLog('TDA  U' + data.universe_id + ' H₀=' + data.h0_components +
               ' CONVERGING  H₁=' + data.h1_cycles, 'tda');
    }
  };
  es.onerror = () => {
    addLog('SSE disconnected', 'batf');
    document.getElementById('status-disp').textContent = 'DISC';
  };
}

// ── API calls ─────────────────────────────────────────
async function sendFP() {
  const uid  = parseInt(document.getElementById('fp-uid').value);
  const rate = parseFloat(document.getElementById('fp-rate').value) / 100;
  const r = await fetch(API + '/feedback/fp', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({universe_id: uid, fp_rate: rate})
  });
  const d = await r.json();
  addLog('FP  U' + uid + '  rate=' + rate.toFixed(2) + '  β=' + d.new_beta, 'stat');
}

async function startSim() {
  const r = await fetch(API + '/universe/start', {method: 'POST'});
  const d = await r.json();
  document.getElementById('btn-start').classList.add('on');
  document.getElementById('status-disp').textContent = 'RUNNING';
  addLog('STARTED  ' + d.universes + 'U × ' + d.islands + 'I × ' + d.agents_per_universe + 'A', 'stat');
  connectSSE();
}

async function stopSim() {
  document.getElementById('btn-start').classList.remove('on');
  document.getElementById('status-disp').textContent = 'PAUSED';
  await fetch(API + '/universe/stop', {method: 'POST'});
}

async function resetSim() {
  if (es) { es.close(); es = null; }
  document.getElementById('btn-start').classList.remove('on');
  document.getElementById('status-disp').textContent = 'IDLE';
  await fetch(API + '/universe/reset', {method: 'POST'});

  document.getElementById('log').innerHTML      = '';
  document.getElementById('coal-log').innerHTML = '';
  document.getElementById('turn-disp').textContent  = 'T:0';
  document.getElementById('champ-disp').textContent = 'CHAMPION: —';
  document.getElementById('conv-ban').style.display = 'none';
  setCount('conv', 0); setCount('arch', 0); setCount('coal', 0);
  setFilter('all');

  document.querySelectorAll('.cell').forEach(c => { c.className = 'cell'; });
  document.querySelectorAll('.urow').forEach(r => r.classList.remove('dead', 'reb'));

  for (let u = 0; u < 5; u++) {
    _sigHist[u].length = 0;
    const b = document.getElementById('sbar-'  + u); if (b) { b.style.width = '50%'; b.className = 'sbar'; }
    const sp = document.getElementById('spark-' + u); if (sp) sp.textContent = '▄▄▄▄▄▄▄▄';
    document.getElementById('sval-' + u).textContent = '1.00';
    const h0 = document.getElementById('th0-' + u); if (h0) h0.textContent = 'H₀:—';
    const h1 = document.getElementById('th1-' + u); if (h1) h1.textContent = 'H₁:—';
    const st = document.getElementById('tst-' + u); if (st) { st.textContent = '—'; st.className = 'tst'; }
    const ba = document.getElementById('fba-'  + u); if (ba) ba.style.width = '0%';
    const bd = document.getElementById('fbd-'  + u); if (bd) bd.style.width = '0%';
    document.getElementById('fbav-' + u).textContent = '—';
    document.getElementById('fbdv-' + u).textContent = '—';
  }
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return _DEMO_HTML


if __name__ == "__main__":
    import uvicorn
    print("Shadow War starting on http://localhost:8090")
    uvicorn.run(app, host="0.0.0.0", port=8090)
