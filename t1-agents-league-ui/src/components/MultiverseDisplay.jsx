import { useMemo, useState, useEffect } from 'react';
import { Activity, Skull, ShieldAlert, Cpu, Database, Link as LinkIcon } from 'lucide-react';

function ExecutionLane({ lane, simActive, sigma, isDead, isConverged, infections }) {
  // Generate fake active node data
  const [activeNode, setActiveNode] = useState('IDLE');
  const [entropy, setEntropy] = useState(0);

  useEffect(() => {
    if (!simActive || isDead) return;
    const interval = setInterval(() => {
      const nodes = ['CallExpression', 'FunctionDecl', 'BlockStatement', 'BinaryExpression', 'Identifier'];
      setActiveNode(nodes[Math.floor(Math.random() * nodes.length)]);
      setEntropy(Math.random() * 100);
    }, 400 + Math.random() * 600);
    return () => clearInterval(interval);
  }, [simActive, isDead]);

  const hasInfection = infections.some(inf => inf.to === lane.id || inf.from === lane.id);

  return (
    <div style={{
      flex: 1, 
      display: 'flex', 
      flexDirection: 'column', 
      background: isDead ? 'rgba(20,0,0,0.8)' : 'rgba(10,10,20,0.6)', 
      border: `1px solid ${isConverged ? '#fff' : (isDead ? '#ef4444' : lane.color)}`,
      borderRadius: '8px',
      position: 'relative',
      overflow: 'hidden',
      transition: 'all 0.3s'
    }}>
      {/* Scanning effect */}
      {simActive && !isDead && (
        <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(to bottom, transparent, ${lane.color}22, transparent)`, height: '200%', animation: 'scan-lane 2s linear infinite' }} />
      )}
      
      {/* Header */}
      <div style={{ padding: '0.5rem', borderBottom: `1px solid ${lane.color}44`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: `${lane.color}11` }}>
         <span className="title-font" style={{ color: isDead ? '#ef4444' : lane.color, fontSize: '0.8rem', fontWeight: 700 }}>SANDBOX U{lane.id}</span>
         {isDead ? <Skull size={14} color="#ef4444" /> : <Cpu size={14} color={lane.color} />}
      </div>

      {/* Status Body */}
      <div style={{ padding: '1rem 0.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', zIndex: 1 }}>
         <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
           STATUS: <span style={{ color: isDead ? '#ef4444' : (simActive ? '#4ade80' : 'var(--text-main)') }}>
             {isDead ? 'HALTED (CRASH)' : (simActive ? 'INFERRING' : 'STANDBY')}
           </span>
         </div>
         
         <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-main)' }}>
           σ: {(sigma || 0.5).toFixed(4)}
         </div>

         <div style={{ background: '#000', padding: '0.5rem', borderRadius: '4px', border: '1px solid #333' }}>
            <div className="mono" style={{ fontSize: '0.6rem', color: 'var(--text-dim)', marginBottom: '4px' }}>CURRENT_AST_TARGET</div>
            <div className="mono" style={{ fontSize: '0.75rem', color: lane.color, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {isDead ? 'NULL' : activeNode}
            </div>
         </div>

         {/* Data stream visualizer */}
         {!isDead && (
           <div style={{ height: '4px', background: '#222', borderRadius: '2px', overflow: 'hidden' }}>
             <div style={{ height: '100%', width: `${entropy}%`, background: lane.color, transition: 'width 0.2s' }} />
           </div>
         )}
      </div>

      {hasInfection && (
        <div style={{ position: 'absolute', bottom: '0', left: 0, right: 0, background: 'var(--accent-red)', color: '#000', fontSize: '0.7rem', textAlign: 'center', padding: '2px' }} className="mono bold pulse-glow">
          CHAIN INFECTION
        </div>
      )}
    </div>
  );
}

export default function MultiverseDisplay({ simActive, convergenceEvents, chainInfections, deadUniverses, sigmaData }) {
  const lanes = useMemo(() => [
    { id: 1, color: '#38bdf8' },
    { id: 2, color: '#fbbf24' },
    { id: 3, color: '#f87171' },
    { id: 4, color: '#a78bfa' },
    { id: 5, color: '#4ade80' },
  ], []);

  const activeConvergence = convergenceEvents && convergenceEvents.length > 0 ? convergenceEvents[convergenceEvents.length - 1] : null;
  const convergedIds = activeConvergence ? activeConvergence.universes : [];

  return (
    <div style={{ flex: 1, position: 'relative', background: '#020205', overflow: 'hidden', borderRadius: '12px', display: 'flex', flexDirection: 'column', border: '1px solid #1a1a2e' }}>
      {/* Background Orchestration Fabric Grid */}
      <div style={{ position: 'absolute', inset: 0, backgroundImage: 'linear-gradient(#1a1a2e 1px, transparent 1px), linear-gradient(90deg, #1a1a2e 1px, transparent 1px)', backgroundSize: '40px 40px', opacity: 0.4 }} />

      {/* HUD Overlays */}
      <div style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', zIndex: 10, borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(2,2,5,0.8)' }}>
        <div>
          <div style={{ color: 'var(--accent-gold)', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px' }} className="title-font">
            [ ORCHESTRATOR FABRIC ]
          </div>
          <div style={{ color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={16} /> Shadow-Omega Execution Lanes
          </div>
        </div>
        <div className="mono" style={{ color: simActive ? '#4ade80' : 'var(--text-dim)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={14} className={simActive ? "pulse-glow" : ""} /> {simActive ? 'ENGINE RUNNING' : 'SYSTEM IDLE'}
        </div>
      </div>

      {/* The 5 Execution Lanes */}
      <div style={{ display: 'flex', flex: 1, gap: '1rem', padding: '1.5rem', zIndex: 1 }}>
         {lanes.map(lane => (
           <ExecutionLane 
              key={lane.id}
              lane={lane}
              simActive={simActive}
              sigma={sigmaData ? sigmaData[lane.id] : 0.5}
              isDead={deadUniverses ? deadUniverses.includes(lane.id) : false}
              isConverged={convergedIds.includes(lane.id)}
              infections={chainInfections || []}
           />
         ))}
      </div>

      {/* Reconciliation Node (Convergence) */}
      <div style={{ 
          margin: '0 1.5rem 1.5rem 1.5rem', 
          padding: '1rem', 
          background: activeConvergence ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.02)', 
          border: activeConvergence ? '1px solid var(--accent-red)' : '1px dashed #333',
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1,
          transition: 'all 0.5s'
      }}>
          <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
             <LinkIcon size={12} /> RECONCILIATION NODE
          </div>
          
          {activeConvergence ? (
            <div style={{ textAlign: 'center' }}>
               <h3 className="title-font glow-text-red" style={{ margin: '0 0 0.5rem 0', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldAlert size={20} /> CRITICAL CONVERGENCE VERIFIED
               </h3>
               <div className="mono" style={{ fontSize: '0.85rem', color: '#fff' }}>
                  Converged Paths: <span style={{ color: 'var(--accent-gold)' }}>[ {activeConvergence.universes.map(id => `U${id}`).join(', ')} ]</span>
                  <span style={{ margin: '0 1rem', color: '#555' }}>|</span>
                  Confidence: <span style={{ color: '#4ade80' }}>{(activeConvergence.confidence * 100).toFixed(1)}%</span>
               </div>
            </div>
          ) : (
            <div className="mono" style={{ fontSize: '0.8rem', color: '#555' }}>Awaiting Independent Convergence...</div>
          )}
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan-lane {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(50%); }
        }
      `}} />
    </div>
  );
}
