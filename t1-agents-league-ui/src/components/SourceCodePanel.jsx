import { Code } from 'lucide-react';

export default function SourceCodePanel({ simActive }) {
  const codeSnippet = `
function evaluateRisk(target) {
    if (target.sigma > 0.8) {
        // High entropy region detected
        let risk = calculateBaseRisk(target);
        if (target.connections > 10) {
            risk *= 1.5; // Chain infection vector
        }
        return triggerQuarantine(target, risk);
    }
    return proceedWithAnalysis(target);
}

// AST Traversal:
// -> FunctionDeclaration: evaluateRisk
// -> BlockStatement
// -> IfStatement: target.sigma > 0.8
// -> VariableDeclaration: risk
`;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-blue)', fontSize: '0.8rem', letterSpacing: '2px', fontWeight: 'bold' }}>
        <Code size={16} /> TARGET SOURCE_AST
      </div>
      
      <div style={{ flex: 1, background: 'rgba(0, 0, 0, 0.4)', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)', overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
        <div style={{ padding: '4px 8px', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.7rem', color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between' }}>
          <span>target_system.js</span>
          <span>{simActive ? 'ANALYZING...' : 'IDLE'}</span>
        </div>
        
        <div style={{ padding: '1rem', overflowY: 'auto', flex: 1, fontSize: '0.75rem', lineHeight: 1.6, position: 'relative' }}>
          {/* Scanning line effect */}
          {simActive && (
             <div className="scanner-line" style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'var(--accent-blue)', boxShadow: '0 0 10px var(--accent-blue)', zIndex: 10, animation: 'scan 2s linear infinite' }} />
          )}

          <pre style={{ margin: 0, fontFamily: 'monospace' }}>
            <code style={{ color: 'var(--text-bright)' }}>
{codeSnippet.split('\n').map((line, i) => (
  <div key={i} style={{ display: 'flex' }}>
    <span style={{ color: 'var(--text-dim)', width: '20px', userSelect: 'none', textAlign: 'right', marginRight: '1rem' }}>{i + 1}</span>
    <span style={{ 
      color: line.includes('//') ? 'var(--accent-green)' : 
             line.includes('if') || line.includes('return') || line.includes('function') ? 'var(--accent-gold)' : 
             'var(--text-bright)',
      textShadow: simActive && line.includes('target.sigma > 0.8') ? '0 0 5px var(--accent-gold)' : 'none'
    }}>{line}</span>
  </div>
))}
            </code>
          </pre>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scan {
          0% { top: 0; opacity: 1; }
          90% { top: 100%; opacity: 0; }
          100% { top: 100%; opacity: 0; }
        }
      `}} />
    </div>
  );
}
