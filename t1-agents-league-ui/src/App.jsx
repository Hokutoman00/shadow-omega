import { useState, useEffect, useRef } from 'react';
import './App.css';
import { ShieldAlert } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PreStagePanel from './components/PreStagePanel';
import DarkMarketLedger from './components/DarkMarketLedger';
import PostStageBottleneck from './components/PostStageBottleneck';

function HeroMetric({ label, value, color, desc }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
      <span className="title-font" style={{ fontSize: '1.5rem', color, fontWeight: 'bold', lineHeight: '1', minWidth: '1.8rem' }}>
        {value}
      </span>
      <div>
        <div className="mono" style={{ fontSize: '0.58rem', color, letterSpacing: '1px' }}>{label}</div>
        <div className="mono" style={{ fontSize: '0.52rem', color: '#555' }}>{desc}</div>
      </div>
    </div>
  );
}

function App() {
  const [simActive, setSimActive] = useState(false);
  const [battleEvents, setBattleEvents] = useState([]);
  const [convergenceEvents, setConvergenceEvents] = useState([]);
  const [deadUniverses, setDeadUniverses] = useState([]);
  const [universeStats, setUniverseStats] = useState({});
  const [tdaData, setTdaData] = useState({});
  const [coalitionAttack, setCoalitionAttack] = useState(null);
  const [sigmaReport, setSigmaReport] = useState(null);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [dirConvEvent, setDirConvEvent] = useState(null);
  const [chainInfection, setChainInfection] = useState(null);
  const migSkip = useRef(0);
  const [liveAlert, setLiveAlert] = useState(null);
  const liveAlertTimerRef = useRef(null);

  const [backendConfig, setBackendConfig] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8090/agents/config')
      .then(r => r.json())
      .then(setBackendConfig)
      .catch(() => {});
  }, []);

  const aiLabel = backendConfig?.active_backend === 'azure_ai_foundry'
    ? 'AZURE AI FOUNDRY'
    : backendConfig?.active_backend === 'github_models'
    ? 'GITHUB MODELS'
    : 'PHYSICS ENGINE';
  const aiColor = backendConfig?.active_backend === 'physics_fallback' ? '#888' : '#4ade80';

  const noveltyCount = new Set(convergenceEvents.map(e => e.strategy_fp).filter(Boolean)).size;
  const consensusCount = convergenceEvents.length;

  // Auto-detect if simulation is already running when page loads
  useEffect(() => {
    fetch('http://localhost:8090/universe/status')
      .then(r => r.json())
      .then(data => { if (data.status === 'running') setSimActive(true); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const evtSource = new EventSource('http://localhost:8090/universe/stream');
    let convCount = 0;

    evtSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        const et = data.event_type;

        if (et === 'connected') {
          // don't auto-enable — let handleInitiate set simActive
        } else if (et === 'battle' && data.success) {
          if (data.turn) setCurrentTurn(data.turn);
          setBattleEvents(prev => [...prev.slice(-49), {
            id: `${data.turn}-${data.universe_id}-${data.island_id}-${data.attack_style}`,
            turn: data.turn,
            universe_id: data.universe_id,
            island_id: data.island_id,
            attack_style: data.attack_style,
            fitness_delta: data.fitness_delta,
            reasoning: data.reasoning,
          }]);
        } else if (et === 'convergence') {
          convCount += 1;
          const ev = {
            universes: data.converged_universes,
            universe_id: data.converged_universes[0],
            confidence: data.confidence,
            fossil_generations: convCount,
            severity: data.severity,
            is_new_archetype: data.is_new_archetype,
            strategy_fp: data.strategy_fp,
          };
          setConvergenceEvents(prev => [...prev, ev]);
          setLiveAlert(ev);
          if (liveAlertTimerRef.current) clearTimeout(liveAlertTimerRef.current);
          liveAlertTimerRef.current = setTimeout(() => setLiveAlert(null), 7000);
        } else if (et === 'universe_death') {
          setDeadUniverses(prev => [...prev, data.universe_id]);
        } else if (et === 'status_snapshot') {
          if (data.universes) {
            const statsMap = {};
            data.universes.forEach(u => { statsMap[u.id] = u; });
            setUniverseStats(statsMap);
          }
          if (data.sigma_report) setSigmaReport(data.sigma_report);
        } else if (et === 'tda_report') {
          setTdaData(prev => ({
            ...prev,
            [data.universe_id]: {
              h0: data.h0_components,
              h1: data.h1_cycles,
              persistence: data.h0_persistence_max,
            }
          }));
        } else if (et === 'coalition_attack') {
          setCoalitionAttack(data);
        } else if (et === 'direction_convergence') {
          setDirConvEvent(data);
        } else if (et === 'chain_infection') {
          setChainInfection(data);
        } else if (et === 'universe_rebirth') {
          setDeadUniverses(prev => prev.filter(id => id !== data.universe_id));
        } else if (et === 'migration') {
          migSkip.current = (migSkip.current + 1) % 6;
          if (migSkip.current === 0) {
            setBattleEvents(prev => [...prev.slice(-79), {
              type: 'migration',
              id: `m-${data.universe_id}-${data.from_island}-${data.to_island}-${data.turn}`,
              turn: data.turn,
              universe_id: data.universe_id,
              from_island: data.from_island,
              to_island: data.to_island,
              fitness: data.fitness,
            }]);
          }
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    evtSource.onerror = (err) => {
      console.error("EventSource failed:", err);
    };

    return () => {
      evtSource.close();
    };
  }, []);

  const handleInitiate = async () => {
    const wasRunning = simActive;

    // Reset all local state immediately
    setBattleEvents([]);
    setConvergenceEvents([]);
    setDeadUniverses([]);
    setUniverseStats({});
    setTdaData({});
    setCoalitionAttack(null);
    setSigmaReport(null);
    setCurrentTurn(0);
    setDirConvEvent(null);
    setChainInfection(null);
    setSimActive(false);
    migSkip.current = 0;

    try {
      if (wasRunning) {
        await fetch('http://localhost:8090/universe/stop', { method: 'POST' });
        await new Promise(r => setTimeout(r, 150));
        await fetch('http://localhost:8090/universe/reset', { method: 'POST' });
        await new Promise(r => setTimeout(r, 100));
      }
      const res = await fetch('http://localhost:8090/universe/start', { method: 'POST' });
      if (res.ok) {
        setSimActive(true);
      }
    } catch (e) {
      console.error("Error starting simulation:", e);
    }
  };

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', background: '#000', color: '#fff', overflow: 'hidden' }}>

      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', background: '#0a0a0f', borderBottom: '1px solid #1a1a2e' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h1 className="title-font glow-text" style={{ fontSize: '1.25rem', margin: 0, letterSpacing: '2px' }}>
            MICROSOFT FOUNDRY: SHADOW-OMEGA
          </h1>
          <span className="mono" style={{ fontSize: '0.75rem', background: '#222', padding: '2px 8px', borderRadius: '12px', color: 'var(--accent-gold)' }}>v2.0.4-dev</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {simActive && currentTurn > 0 && (
            <div className="mono" style={{ fontSize: '0.7rem', color: '#555', display: 'flex', gap: '12px' }}>
              <span>T<span style={{ color: '#aaa' }}>{currentTurn}</span></span>
              {dirConvEvent && (
                <span style={{ color: '#f87171' }}>
                  DIR-CONV U[{dirConvEvent.aligned_universes?.join(',')}] cos={dirConvEvent.max_cosine?.toFixed(3)}
                </span>
              )}
              {chainInfection && (
                <span style={{ color: '#fbbf24' }}>
                  CHAIN-INF U{chainInfection.source_universe}→[{chainInfection.target_universes?.join(',')}] σ={chainInfection.sigma_source}
                </span>
              )}
            </div>
          )}
          <div className="mono" style={{ fontSize: '0.75rem', color: simActive ? aiColor : '#f87171', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: simActive ? aiColor : '#f87171' }} className={simActive ? "pulse-glow" : ""} />
            {simActive ? `${aiLabel}: ACTIVE` : 'SYSTEM STANDBY'}
          </div>
          <button
            onClick={handleInitiate}
            className="action-button title-font"
            style={{
              background: simActive ? '#1a1a2e' : 'var(--accent-blue)',
              color: simActive ? '#ef4444' : '#fff',
              border: simActive ? '1px solid #ef4444' : 'none',
              padding: '0.5rem 1.5rem',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
              letterSpacing: '1px'
            }}
          >
            {simActive ? 'RESTART MULTIVERSE' : 'INITIATE MULTIVERSE'}
          </button>
        </div>
      </header>

      {/* Metrics Hero Strip */}
      <div style={{ display: 'flex', alignItems: 'center', padding: '0 2rem', background: '#020205', borderBottom: '1px solid #111', height: '46px', flexShrink: 0, gap: '20px' }}>
        <HeroMetric label="NOVELTY" value={noveltyCount} color="#ff9900" desc="new archetypes" />
        <div style={{ width: '1px', height: '26px', background: '#1a1a2e' }} />
        <HeroMetric label="CONSENSUS" value={consensusCount} color="#38bdf8" desc="universes converged" />
        <div style={{ width: '1px', height: '26px', background: '#1a1a2e' }} />
        <HeroMetric label="ACTIONABILITY" value={convergenceEvents.filter(e => e.severity === 'critical' || e.severity === 'high').length} color="#4ade80" desc="critical rules generated" />
        <div style={{ flex: 1 }} />
        <div className="mono" style={{ fontSize: '0.6rem', color: '#3a3a4a', display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span style={{ color: '#555' }}>INPUT</span>
          <span>→</span>
          <span style={{ color: '#555' }}>EVOLUTION</span>
          <span>→</span>
          <span style={{ color: '#555' }}>OUTPUT</span>
        </div>
      </div>

      {/* Live Threat Discovered Banner — fires on convergence event */}
      <AnimatePresence>
        {liveAlert && (
          <motion.div
            key={consensusCount}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            style={{ overflow: 'hidden', flexShrink: 0, background: 'rgba(248,113,113,0.08)', borderBottom: '1px solid rgba(248,113,113,0.22)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.4rem 2rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <ShieldAlert size={15} color="#f87171" />
                <span className="title-font" style={{ color: '#f87171', fontSize: '0.78rem', letterSpacing: '1.5px' }}>
                  LIVE THREAT DISCOVERED
                </span>
                <span className="mono" style={{ color: '#888', fontSize: '0.63rem' }}>
                  {liveAlert.universes?.length ?? '?'} independent universes converged on same zero-day pattern
                </span>
              </div>
              <div className="mono" style={{ display: 'flex', gap: '14px', fontSize: '0.63rem', alignItems: 'center' }}>
                <span style={{ color: '#38bdf8' }}>CONFIDENCE: {((liveAlert.confidence ?? 0) * 100).toFixed(0)}%</span>
                {liveAlert.is_new_archetype && <span style={{ color: '#fbbf24' }}>★ NEW ARCHETYPE</span>}
                <span style={{ color: '#4ade80' }}>→ IDE RULE GENERATED</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main 3-Stage Layout */}
      <div className="main-panels" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <PreStagePanel simActive={simActive} battleEvents={battleEvents} />
        <DarkMarketLedger
          simActive={simActive}
          convergenceEvents={convergenceEvents}
          universeStats={universeStats}
          tdaData={tdaData}
          coalitionAttack={coalitionAttack}
          sigmaReport={sigmaReport}
          deadUniverses={deadUniverses}
          dirConvEvent={dirConvEvent}
          chainInfection={chainInfection}
        />
        <PostStageBottleneck
          simActive={simActive}
          convergenceEvents={convergenceEvents}
          universeStats={universeStats}
        />
      </div>

    </div>
  );
}

export default App;
