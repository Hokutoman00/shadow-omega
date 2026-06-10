import { useEffect, useState } from 'react';
import { FileCode2, DownloadCloud } from 'lucide-react';

export default function ArchetypeOutputPanel({ latestConvergence }) {
  const [ruleContent, setRuleContent] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (latestConvergence && latestConvergence.strategy_fp) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(true);
      // Fetch the ESLint rule representation of the archetype
      fetch(`http://localhost:8090/fossil/archetypes?fp=${latestConvergence.strategy_fp}`)
        .then(res => res.json())
        .then(data => {
          setRuleContent(data.rule || `// Auto-generated archetype rule for FP: ${latestConvergence.strategy_fp}\nmodule.exports = {\n  create(context) {\n    return {\n      // AST visitor logic here...\n    };\n  }\n};`);
          setLoading(false);
        })
        .catch(err => {
          console.error('Failed to fetch archetype', err);
          // Mock output if backend endpoint isn't fully ready
          setRuleContent(`// Fossil Fallback: ${latestConvergence.strategy_fp}\nmodule.exports = {\n  meta: {\n    type: "problem",\n    docs: {\n      description: "Converged strategy rule",\n    }\n  },\n  create(context) {\n    return {\n      CallExpression(node) {\n        // Enforce converged behavior\n      }\n    };\n  }\n};`);
          setLoading(false);
        });
    }
  }, [latestConvergence]);

  return (
    <div style={{ flex: '0 0 320px', borderLeft: '1px solid #1a1a2e', background: '#020205', padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h2 className="title-font" style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <FileCode2 size={16} color="var(--accent-gold)" />
        ARCHETYPE EXPORT
      </h2>

      {!latestConvergence ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#333', fontSize: '0.8rem', textAlign: 'center' }}>
          WAITING FOR<br/>CONVERGENCE EVENT
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between' }}>
            <span>Target: ESLint Plugin</span>
            <span style={{ color: 'var(--accent-gold)' }}>FP:{latestConvergence.strategy_fp.substring(0,8)}</span>
          </div>
          
          <div style={{ flex: 1, background: '#05050a', border: '1px solid #222', borderRadius: '4px', padding: '0.5rem', overflowY: 'auto' }}>
            {loading ? (
              <div className="pulse-glow" style={{ color: 'var(--accent-blue)', fontSize: '0.8rem', textAlign: 'center', marginTop: '2rem' }}>
                Extracting from fossil record...
              </div>
            ) : (
              <pre className="mono" style={{ margin: 0, fontSize: '0.7rem', color: '#a5d6ff', whiteSpace: 'pre-wrap' }}>
                {ruleContent}
              </pre>
            )}
          </div>
          
          <button style={{ 
            marginTop: '1rem', background: '#111', color: 'var(--text-main)', border: '1px solid #333', 
            padding: '0.5rem', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            fontSize: '0.8rem', transition: 'all 0.2s'
          }}
          onMouseOver={e => e.currentTarget.style.background = '#222'}
          onMouseOut={e => e.currentTarget.style.background = '#111'}
          >
            <DownloadCloud size={14} /> EXPORT RULE.JS
          </button>
        </div>
      )}
    </div>
  );
}
