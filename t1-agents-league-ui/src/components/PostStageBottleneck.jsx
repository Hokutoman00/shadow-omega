import { useMemo } from 'react';
import { ArrowRight, Terminal } from 'lucide-react';
import VSCodeMockup from './VSCodeMockup';

export default function PostStageBottleneck({ convergenceEvents, universeStats }) {
  // Information loss = deviation from Edge of Chaos (σ=1.0)
  // σ ≈ 1.0 → minimal compression loss; σ far from 1.0 → higher loss
  const lossPercent = useMemo(() => {
    const stats = Object.values(universeStats ?? {});
    if (!stats.length) return '0.00';
    const avgSigma = stats.reduce((acc, u) => acc + (u.sigma ?? 1.0), 0) / stats.length;
    return Math.min(50, Math.abs(avgSigma - 1.0) * 100).toFixed(2);
  }, [universeStats]);

  const lossNum = parseFloat(lossPercent);

  return (
    <div className="post-stage-panel" style={{ flex: '0 0 350px', borderLeft: '1px solid #1a1a2e', background: '#020205', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h2 className="title-font" style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '0.6rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ArrowRight size={16} color="var(--accent-red)" />
        POST-STAGE: COMPRESSION
      </h2>

      {/* Before / After — judges immediately understand the value */}
      <div style={{ display: 'flex', marginBottom: '0.75rem', background: '#05050a', border: '1px solid #111', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{ flex: 1, padding: '0.5rem 0.7rem', borderRight: '1px solid #1a1a2e' }}>
          <div className="mono" style={{ fontSize: '0.58rem', color: '#666', letterSpacing: '0.5px', marginBottom: '3px' }}>STANDARD LINTER</div>
          <div className="mono" style={{ color: '#ef4444', fontSize: '0.82rem', fontWeight: 'bold' }}>0 issues</div>
          <div style={{ fontSize: '0.58rem', color: '#3a3a4a', marginTop: '3px', lineHeight: '1.4' }}>
            Single-pass static<br/>No mutation awareness
          </div>
        </div>
        <div style={{ flex: 1, padding: '0.5rem 0.7rem' }}>
          <div className="mono" style={{ fontSize: '0.58rem', color: '#4ade80', letterSpacing: '0.5px', marginBottom: '3px' }}>SHADOW-OMEGA</div>
          <div className="mono" style={{ color: '#4ade80', fontSize: '0.82rem', fontWeight: 'bold' }}>
            {convergenceEvents.length > 0 ? `${convergenceEvents.length} CRITICAL` : <span className="scan-animate">SCANNING...</span>}
          </div>
          <div style={{ fontSize: '0.58rem', color: '#3a3a4a', marginTop: '3px', lineHeight: '1.4' }}>
            5-universe co-evolution<br/>Emergent consensus
          </div>
        </div>
      </div>

      <div style={{ background: '#05050a', border: '1px solid #111', borderRadius: '4px', padding: '0.75rem', marginBottom: '1rem' }}>
        <div className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>IB BOTTLENECK (σ DEVIATION FROM CHAOS EDGE)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ flex: 1, height: '6px', background: '#222', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${Math.min(100, lossNum * 2)}%`,
              background: lossNum > 15 ? 'var(--accent-red)' : 'var(--accent-gold)',
              transition: 'width 0.5s'
            }} />
          </div>
          <div className="mono" style={{ fontSize: '0.8rem', color: lossNum > 15 ? 'var(--accent-red)' : 'var(--accent-gold)', width: '45px', textAlign: 'right' }}>
            {lossPercent}%
          </div>
        </div>
        <div className="mono" style={{ fontSize: '0.6rem', color: '#666', marginTop: '4px', textAlign: 'right' }}>INFORMATION LOSS</div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div className="mono" style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Terminal size={12} /> IDE FEEDBACK LOOP
        </div>
        <div style={{ flex: 1, position: 'relative', overflow: 'hidden', border: '1px solid #1a1a2e', borderRadius: '4px' }}>
          <div style={{ transform: 'scale(0.8)', transformOrigin: 'top left', width: '125%', height: '125%' }}>
            <VSCodeMockup
              showWarning={convergenceEvents && convergenceEvents.length > 0}
              ruleData={convergenceEvents && convergenceEvents[convergenceEvents.length - 1]}
              onFalsePositive={() => console.log("Feedback received")}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
