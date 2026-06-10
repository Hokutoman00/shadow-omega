import { Activity } from 'lucide-react';

export default function SigmaGaugePanel({ sigmaReport }) {
  // Default values if no report yet
  const report = sigmaReport && sigmaReport.length === 5 
    ? sigmaReport 
    : Array.from({ length: 5 }, (_, i) => ({
        universe_id: i,
        sigma: 1.0,
        label: "stable",
      }));

  const getColor = (label) => {
    switch (label) {
      case 'edge_of_chaos': return '#4ade80'; // Green
      case 'chaotic': return '#f87171';       // Red
      case 'stable': return '#38bdf8';        // Blue
      default: return '#666';
    }
  };

  return (
    <div style={{ flex: '0 0 320px', borderRight: '1px solid #1a1a2e', background: '#020205', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h2 className="title-font" style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Activity size={16} color="var(--accent-blue)" />
        SIGMA (σ) MONITOR
      </h2>
      
      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1.5rem', lineHeight: '1.4' }}>
        Unified σ-theory. Edge of Chaos: |σ-1| &lt; 0.08. Target σ=1.0 maximizes evolutionary adaptability.
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {report.map((u) => {
          const color = getColor(u.label);
          // Scale σ for the bar. Assuming range roughly 0.5 to 1.5. 
          // 1.0 is middle (50%). 
          const fillPercentage = Math.max(0, Math.min(100, ((u.sigma - 0.5) / 1.0) * 100));

          return (
            <div key={u.universe_id} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                <span className="mono" style={{ color: 'var(--text-main)', fontWeight: 'bold' }}>U{u.universe_id}</span>
                <span className="mono" style={{ color: color }}>σ={u.sigma.toFixed(3)} [{u.label.toUpperCase()}]</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: '#111', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
                {/* Target marker at sigma=1.0 (50%) */}
                <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '2px', background: '#fff', zIndex: 10, opacity: 0.5 }} />
                
                <div style={{ 
                  height: '100%', 
                  width: `${fillPercentage}%`, 
                  background: color, 
                  transition: 'all 0.3s ease-out' 
                }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
