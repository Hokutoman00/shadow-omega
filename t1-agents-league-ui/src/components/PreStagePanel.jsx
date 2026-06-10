import { useRef, useEffect } from 'react';
import { Network } from 'lucide-react';

export default function PreStagePanel({ simActive, battleEvents }) {
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [battleEvents]);

  const formatEntry = (ev) => {
    if (ev.type === 'migration') {
      return `[MUTATE] U${ev.universe_id} I${ev.from_island}→I${ev.to_island} fit=${ev.fitness?.toFixed(2) ?? '?'}`;
    }
    const hex = ((ev.turn * 31 + ev.universe_id * 17 + (ev.island_id ?? 0) * 7) % 16777215)
      .toString(16).padStart(6, '0');
    const delta = Math.abs(ev.fitness_delta ?? 0).toFixed(4);
    return `[AST::${ev.attack_style}] U${ev.universe_id}/I${ev.island_id} → H(G):${delta} → map(0x${hex})`;
  };

  return (
    <div className="pre-stage-panel" style={{ flex: '0 0 300px', borderRight: '1px solid #1a1a2e', background: '#020205', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h2 className="title-font" style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Network size={16} color="var(--accent-blue)" />
        PRE-STAGE: ENTROPY MAPPING
      </h2>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1rem', lineHeight: '1.4' }}>
        Extracting AST graph entropy (H(G)) from source noise and mapping vulnerable topological coordinates to the DarkMarket bulk space.
      </div>

      <div
        ref={logRef}
        className="mono"
        style={{ flex: 1, background: '#000', border: '1px solid #111', borderRadius: '4px', padding: '0.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}
      >
        {battleEvents && battleEvents.length > 0 ? (
          battleEvents.map(ev => (
            <div key={ev.id} style={{ marginBottom: '2px' }}>
              <div style={{ color: ev.type === 'migration' ? '#38bdf8' : '#4ade80', fontSize: '0.65rem' }}>
                {formatEntry(ev)}
              </div>
              {ev.reasoning && (
                <div style={{ color: '#2d6a4f', fontSize: '0.6rem', paddingLeft: '8px' }}>
                  └─ {ev.reasoning}
                </div>
              )}
            </div>
          ))
        ) : (
          <div style={{ color: '#555', fontSize: '0.7rem' }}>
            {simActive ? 'SCANNING SOURCE TOPOLOGY...' : 'AWAITING SOURCE INGESTION...'}
          </div>
        )}
      </div>
    </div>
  );
}
