import { useEffect, useState } from 'react';
import { AlertTriangle, Fingerprint } from 'lucide-react';

export default function ConvergenceBanner({ convergenceEvent }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (convergenceEvent) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setVisible(true);
      const timer = setTimeout(() => setVisible(false), 8000); // Hide after 8s
      return () => clearTimeout(timer);
    }
  }, [convergenceEvent]);

  if (!visible || !convergenceEvent) return null;

  const { converged_universes, confidence, severity, strategy_fp, is_new_archetype } = convergenceEvent;
  
  // severity colors
  const severityColor = severity === 'critical' ? 'var(--accent-red)' : severity === 'high' ? 'var(--accent-gold)' : 'var(--accent-blue)';
  
  return (
    <div style={{
      position: 'absolute',
      top: '80px',
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: 1000,
      background: `rgba(20, 5, 5, 0.95)`,
      border: `2px solid ${severityColor}`,
      borderRadius: '8px',
      padding: '1.5rem',
      boxShadow: `0 0 30px ${severityColor}40`,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minWidth: '600px',
      animation: 'pulse-glow 2s infinite'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '0.5rem' }}>
        <AlertTriangle size={32} color={severityColor} />
        <h2 className="title-font glow-text-red" style={{ margin: 0, fontSize: '1.5rem', letterSpacing: '2px' }}>
          STRATEGY CONVERGENCE DETECTED
        </h2>
      </div>
      
      <div className="mono" style={{ fontSize: '1.1rem', color: '#fff', textAlign: 'center', lineHeight: '1.5' }}>
        U[{converged_universes.join(',')}] 同時収束 — confidence {(confidence * 100).toFixed(1)}% / severity <span style={{color: severityColor}}>{severity.toUpperCase()}</span>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem', padding: '0.5rem 1rem', background: '#000', borderRadius: '4px', border: '1px solid #333' }}>
        <Fingerprint size={16} color="var(--accent-gold)" />
        <span className="mono" style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>fp={strategy_fp}</span>
        {is_new_archetype && (
          <span className="mono pulse-glow" style={{ fontSize: '0.8rem', background: 'var(--accent-red)', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontWeight: 'bold' }}>
            NEW ARCHETYPE
          </span>
        )}
      </div>
    </div>
  );
}
