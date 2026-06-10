import { useEffect, useState, useRef } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { Activity } from 'lucide-react';

export default function ASTGraphPanel({ simActive }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const fgRef = useRef();

  useEffect(() => {
    const N = 120;
    const nodes = [...Array(N).keys()].map(i => ({ 
      id: i, 
      val: Math.random() * 2,
      color: Math.random() > 0.9 ? 'rgba(248, 113, 113, 0.9)' : 'rgba(56, 189, 248, 0.3)' 
    }));
    const links = [...Array(N).keys()].filter(id => id).map(id => ({
      source: id,
      target: Math.round(Math.random() * (id - 1))
    }));
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setGraphData({ nodes, links });
  }, []);

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative', background: 'transparent' }}>
      <div style={{ position: 'absolute', top: 16, left: 16, zIndex: 10, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ color: 'var(--accent-blue)', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px' }} className="title-font">
          [ TARGET INGESTION ]
        </div>
        <div style={{ color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={16} /> AST Topological Structure
        </div>
        <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', marginTop: '4px' }} className="mono">
          STATUS: {simActive ? 'INJECTING TO MULTIVERSE...' : 'PARSED | 120 NODES'}
        </div>
      </div>
      
      {graphData.nodes.length > 0 && (
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          backgroundColor="rgba(0,0,0,0)"
          nodeColor={node => node.color}
          linkWidth={0.5}
          linkColor={() => 'rgba(255,255,255,0.05)'}
          width={300}
          height={600}
          enableNodeDrag={true}
          enableNavigationControls={true}
          showNavInfo={false}
        />
      )}
      
      {/* Scanning laser effect overlay */}
      {simActive && (
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, transparent 0%, rgba(56, 189, 248, 0.1) 50%, transparent 100%)', backgroundSize: '100% 200%', animation: 'scan 2s linear infinite', pointerEvents: 'none' }} />
      )}
      <style>{`
        @keyframes scan {
          0% { background-position: 0 -100%; }
          100% { background-position: 0 200%; }
        }
      `}</style>
    </div>
  );
}
