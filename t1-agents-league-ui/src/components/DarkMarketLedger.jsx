import { useState, useEffect } from 'react';
import { Database, ShieldAlert } from 'lucide-react';

function TdaBarcode({ tda }) {
  const h0 = Math.min(tda?.h0 ?? 0, 12);
  const h1 = Math.min(tda?.h1 ?? 0, 8);
  const total = 20;
  return (
    <div style={{ display: 'flex', gap: '2px', height: '12px', alignItems: 'center' }}>
      {Array.from({ length: total }, (_, i) => {
        const isH0 = i < h0;
        const isH1 = i >= h0 && i < h0 + h1;
        return (
          <div key={i} style={{
            width: '2px',
            height: isH0 ? '12px' : isH1 ? '7px' : '3px',
            background: isH0 ? 'var(--accent-blue)' : isH1 ? 'var(--accent-gold)' : '#222'
          }} />
        );
      })}
    </div>
  );
}

export default function DarkMarketLedger({ simActive, convergenceEvents, universeStats, tdaData, coalitionAttack, deadUniverses, dirConvEvent, chainInfection }) {
  const [activeCoalition, setActiveCoalition] = useState(null);

  const universes = [
    { id: 0, dna: 'AGGRESSIVE', color: '#f87171' },
    { id: 1, dna: 'STEALTHY', color: '#38bdf8' },
    { id: 2, dna: 'ADAPTIVE', color: '#fbbf24' },
    { id: 3, dna: 'AGGRESSIVE', color: '#a78bfa' },
    { id: 4, dna: 'STEALTHY', color: '#4ade80' },
  ];

  // coalition_attack SSE event
  useEffect(() => {
    if (!coalitionAttack) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setActiveCoalition({
      type: 'coalition_attack',
      universes: [coalitionAttack.universe_id],
      jsd_ab: coalitionAttack.jsd_ab,
      jsd_bc: coalitionAttack.jsd_bc,
      fitness_boost: coalitionAttack.fitness_boost,
      multiplier: coalitionAttack.coalition_multiplier,
    });
    const t = setTimeout(() => setActiveCoalition(null), 4000);
    return () => clearTimeout(t);
  }, [coalitionAttack]);

  // convergence event
  useEffect(() => {
    if (!convergenceEvents || convergenceEvents.length === 0) return;
    const ev = convergenceEvents[convergenceEvents.length - 1];
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setActiveCoalition({
      type: 'convergence',
      universes: ev.universes,
      confidence: ev.confidence,
    });
    const t = setTimeout(() => setActiveCoalition(null), 4000);
    return () => clearTimeout(t);
  }, [convergenceEvents]);

  const isDead = (uid) => deadUniverses && deadUniverses.includes(uid);
  const inCoalition = (uid) => activeCoalition && activeCoalition.universes.includes(uid);

  const championId = Object.values(universeStats).length > 0
    ? Object.values(universeStats).reduce((prev, curr) =>
        (curr.avg_attacker_fitness ?? -999) > (prev.avg_attacker_fitness ?? -999) ? curr : prev
      ).id
    : null;

  return (
    <div className="dark-market-panel" style={{ flex: 1, background: '#020205', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h2 className="title-font" style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '0.5rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Database size={16} color="var(--accent-gold)" />
          MID-STAGE: DARKMARKET & COALITION
        </div>
        <span className="mono" style={{ fontSize: '0.52rem', color: '#444', fontWeight: 'normal', letterSpacing: '0.5px' }}>5 UNIVERSES · INDEPENDENT EVOLUTION</span>
      </h2>

      {/* Ledger Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
        <div style={{ display: 'flex', padding: '0 0.5rem', color: 'var(--text-dim)', fontSize: '0.65rem', fontWeight: 'bold', borderBottom: '1px dashed #333', paddingBottom: '4px' }}>
          <div style={{ width: '80px' }}>UNIVERSE</div>
          <div style={{ width: '100px' }}>DNA TRAIT</div>
          <div style={{ width: '120px' }}>ATK / DEF</div>
          <div style={{ width: '80px' }}>σ (CHAOS)</div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '6px' }}>
            TDA
            <span style={{ color: '#38bdf8', fontSize: '0.55rem' }}>H₀=clusters</span>
            <span style={{ color: '#fbbf24', fontSize: '0.55rem' }}>H₁=loops</span>
          </div>
        </div>

        {universes.map((u) => {
          const stats = universeStats[u.id];
          const tda = tdaData[u.id];
          const dead = isDead(u.id);
          const coalition = inCoalition(u.id);
          const fitness = stats?.avg_attacker_fitness ?? null;
          const defFitness = stats?.avg_defender_fitness ?? null;
          const sigma = stats?.sigma ?? null;
          const isChampion = !dead && fitness !== null && u.id === championId;
          const sigmaColor = sigma !== null
            ? (Math.abs(sigma - 1.0) < 0.05 ? '#4ade80' : Math.abs(sigma - 1.0) < 0.2 ? '#fbbf24' : '#f87171')
            : '#444';

          return (
            <div key={u.id} style={{
              display: 'flex',
              padding: '0.5rem',
              background: dead ? 'rgba(100,0,0,0.3)' : coalition ? 'rgba(239,68,68,0.2)' : isChampion ? 'rgba(251,191,36,0.04)' : '#05050a',
              border: `1px solid ${dead ? '#7f1d1d' : coalition ? 'var(--accent-red)' : '#111'}`,
              boxShadow: isChampion ? 'inset 3px 0 0 var(--accent-gold)' : 'none',
              alignItems: 'center',
              borderRadius: '4px',
              transition: 'all 0.3s',
              opacity: dead ? 0.5 : 1,
            }}>
              <div className="mono" style={{ width: '80px', color: dead ? '#666' : u.color, fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '3px' }}>
                {dead && <span>☠ </span>}
                {isChampion && <span style={{ color: '#fbbf24', fontSize: '0.6rem' }}>★</span>}
                U#{u.id}
              </div>
              <div className="mono" style={{ width: '100px', color: 'var(--text-main)', fontSize: '0.7rem' }}>[{u.dna}]</div>
              <div className="mono" style={{ width: '120px', lineHeight: '1.3' }}>
                <div style={{ color: fitness !== null ? '#4ade80' : '#333', fontSize: '0.75rem' }}>
                  {fitness !== null
                    ? `▲ ${fitness.toFixed(3)}`
                    : (simActive ? <span className="scan-animate">⋯</span> : <span style={{ color: '#2a2a2a' }}>—</span>)
                  }
                </div>
                {defFitness !== null && (
                  <div style={{ color: '#f87171', fontSize: '0.6rem', opacity: 0.75 }}>▼ {defFitness.toFixed(3)}</div>
                )}
              </div>
              <div className="mono" style={{ width: '80px', color: sigmaColor, fontSize: '0.75rem', lineHeight: '1.1' }}>
                {sigma !== null ? (
                  <>
                    {sigma.toFixed(3)}
                    <div style={{ fontSize: '0.5rem', opacity: 0.7 }}>
                      {Math.abs(sigma - 1.0) < 0.05 ? 'EDGE' : sigma > 1.0 ? 'CHAOTIC' : 'STABLE'}
                    </div>
                  </>
                ) : (simActive ? <span className="scan-animate">⋯</span> : '—')}
              </div>
              <div style={{ flex: 1 }}><TdaBarcode tda={tda} /></div>
            </div>
          );
        })}
      </div>

      {/* Convergence History — last 5 events */}
      {convergenceEvents && convergenceEvents.length > 0 && (
        <div style={{ marginTop: '8px', background: '#05050a', border: '1px solid #111', borderRadius: '4px', padding: '0.4rem 0.6rem' }}>
          <div className="mono" style={{ fontSize: '0.55rem', color: '#444', letterSpacing: '0.5px', marginBottom: '4px' }}>CONVERGENCE LOG</div>
          {convergenceEvents.slice(-5).reverse().map((ev, i) => (
            <div key={i} className="mono" style={{ fontSize: '0.6rem', color: i === 0 ? '#f87171' : '#555', display: 'flex', gap: '8px', marginBottom: '2px' }}>
              <span style={{ color: '#333' }}>#{convergenceEvents.length - i}</span>
              <span>U[{ev.universes?.join(',')}]</span>
              <span style={{ color: '#38bdf8' }}>{((ev.confidence ?? 0) * 100).toFixed(0)}%</span>
              {ev.severity && <span style={{ color: ev.severity === 'critical' ? '#f87171' : '#fbbf24' }}>{ev.severity.toUpperCase()}</span>}
              {ev.is_new_archetype && <span style={{ color: '#ff9900' }}>NEW</span>}
            </div>
          ))}
        </div>
      )}

      {/* Direction Convergence + Chain Infection strip */}
      {(dirConvEvent || chainInfection) && (
        <div style={{ display: 'flex', gap: '8px', marginTop: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
          {dirConvEvent && (
            <div className="mono" style={{ fontSize: '0.65rem', padding: '3px 8px', background: 'rgba(248,113,113,0.1)', border: '1px solid #f87171', borderRadius: '3px', color: '#f87171' }}>
              DIR-CONV depth={dirConvEvent.depth} · cos={dirConvEvent.max_cosine?.toFixed(3)} · U[{dirConvEvent.aligned_universes?.join(',')}]
            </div>
          )}
          {chainInfection && (
            <div className="mono" style={{ fontSize: '0.65rem', padding: '3px 8px', background: 'rgba(251,191,36,0.1)', border: '1px solid #fbbf24', borderRadius: '3px', color: '#fbbf24' }}>
              CHAIN-INF U{chainInfection.source_universe}→[{chainInfection.target_universes?.join(',')}] σ={chainInfection.sigma_source} nudge={chainInfection.nudge_strength}
            </div>
          )}
        </div>
      )}

      {/* Coalition / Convergence Panel */}
      <div style={{
        marginTop: '1rem',
        height: '120px',
        border: '1px dashed #333',
        borderRadius: '8px',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: activeCoalition ? 'rgba(239,68,68,0.1)' : 'transparent',
        transition: 'all 0.3s',
      }}>
        {activeCoalition ? (
          <>
            <div className="title-font glow-text-red" style={{ fontSize: '1.1rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={20} />
              {activeCoalition.type === 'coalition_attack' ? 'COALITION ATTACK EXECUTED' : 'SMART CONTRACT COALITION'}
            </div>
            <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-main)', textAlign: 'center' }}>
              {activeCoalition.type === 'coalition_attack' ? (
                <>JSD(ab)={activeCoalition.jsd_ab?.toFixed(3)} JSD(bc)={activeCoalition.jsd_bc?.toFixed(3)} × {activeCoalition.multiplier?.toFixed(3)} → +{activeCoalition.fitness_boost?.toFixed(3)} boost<br /></>
              ) : (
                <>Convergence purity: {((activeCoalition.confidence ?? 0) * 100).toFixed(1)}%<br /></>
              )}
              Pool: <span style={{ color: 'var(--accent-gold)' }}>[ {activeCoalition.universes.map(id => `U#${id}`).join(', ')} ]</span><br />
              <span style={{ color: '#4ade80' }}>Payload confirmed → compression phase.</span>
            </div>
          </>
        ) : (
          <div className="mono" style={{ color: '#555', fontSize: '0.8rem' }}>AWAITING COALITION EVENT...</div>
        )}
      </div>
    </div>
  );
}
