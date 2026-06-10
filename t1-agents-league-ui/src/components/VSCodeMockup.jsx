import React from 'react';
import { ShieldAlert, Terminal as TermIcon, Code2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function VSCodeMockup({ showWarning, ruleData, onFalsePositive }) {
  const codeSnippet = `function authenticateUser(req, res) {
  const { username, password } = req.body;
  
  // Normal DB check
  const user = db.query('SELECT * FROM users WHERE username = ?', [username]);
  
  if (user && user.password === hash(password)) {
    // Issue token
    const token = jwt.sign({ id: user.id }, SECRET);
    return res.json({ token });
  }
  return res.status(401).send("Unauthorized");
}`;

  const [fpSent, setFpSent] = React.useState(false);

  const handleFalsePositive = () => {
      setFpSent(true);
      if (onFalsePositive) onFalsePositive(ruleData);
      setTimeout(() => setFpSent(false), 3000);
  };

  return (
    <div style={{ width: '100%', height: '100%', background: '#0d1117', display: 'flex', flexDirection: 'column', fontFamily: "'JetBrains Mono', Consolas, monospace", fontSize: '13px', position: 'relative' }}>
      
      {/* VS Code Header */}
      <div style={{ height: '36px', background: '#010409', display: 'flex', alignItems: 'center', padding: '0 12px', gap: '8px', borderBottom: '1px solid #30363d' }}>
        <div style={{ display: 'flex', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }} />
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }} />
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }} />
        </div>
        <div style={{ color: '#8b949e', fontSize: '12px', marginLeft: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
           <Code2 size={14} /> auth.js - Shadow-Omega Linter
        </div>
      </div>

      {/* Editor Body */}
      <div style={{ flex: 1, padding: '16px', color: '#c9d1d9', position: 'relative', overflow: 'hidden' }}>
        <pre style={{ margin: 0, lineHeight: '1.6' }}>
          {codeSnippet.split('\n').map((line, idx) => {
            const isTargetLine = idx === 4; 
            return (
              <div key={idx} style={{ position: 'relative', display: 'flex' }}>
                <span style={{ color: '#484f58', minWidth: '30px', userSelect: 'none', textAlign: 'right', marginRight: '16px' }}>{idx + 1}</span>
                <span style={{ 
                  color: isTargetLine && showWarning && !fpSent ? '#f85149' : 'inherit', 
                  textDecoration: isTargetLine && showWarning && !fpSent ? 'underline wavy #f85149' : 'none',
                  background: isTargetLine && showWarning && !fpSent ? 'rgba(248,81,73,0.1)' : 'transparent',
                  display: 'inline-block',
                  width: '100%'
                }}>
                  {line}
                </span>
              </div>
            );
          })}
        </pre>

        {/* Warning Tooltip */}
        <AnimatePresence>
          {showWarning && ruleData && !fpSent && (
            <motion.div 
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 20, stiffness: 300 }}
              style={{ position: 'absolute', top: '100px', left: '40px', background: '#161b22', border: '1px solid #f85149', borderRadius: '8px', padding: '16px', width: '340px', boxShadow: '0 8px 32px rgba(0,0,0,0.6), 0 0 20px rgba(248,81,73,0.2)', zIndex: 100 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f85149', marginBottom: '12px', fontWeight: 'bold', fontSize: '14px' }}>
                <ShieldAlert size={18} /> [Shadow-Omega Critical]
              </div>
              <div style={{ color: '#c9d1d9', fontSize: '12px', lineHeight: '1.5' }}>
                AST topology from universe U#{ruleData.universe_id} collapse matched emergent zero-day pattern.<br/><br/>
                <span style={{ color: '#58a6ff' }}>Confidence: {((ruleData.confidence ?? 0) * 100).toFixed(0)}% (independent convergence verified)</span><br/>
                <span style={{ color: '#d2a8ff' }}>Fossil generations: {ruleData.fossil_generations} (mutation active)</span>
                {ruleData.severity && (
                  <><br/><span style={{ color: ruleData.severity === 'critical' ? '#f85149' : ruleData.severity === 'high' ? '#fbbf24' : '#4ade80' }}>
                    Severity: {ruleData.severity.toUpperCase()}
                  </span></>
                )}
                {ruleData.is_new_archetype && (
                  <><br/><span style={{ color: '#ff9900', fontWeight: 'bold' }}>⚡ NEW ARCHETYPE DETECTED</span></>
                )}
              </div>
              <div style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
                <button onClick={() => { const el = document.createElement('div'); el.style.cssText='position:fixed;top:12px;right:12px;background:#238636;color:#fff;padding:8px 16px;border-radius:6px;font-family:monospace;font-size:12px;z-index:9999;'; el.textContent='✓ ESLint rule injected'; document.body.appendChild(el); setTimeout(()=>el.remove(),2500); }} style={{ background: '#238636', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 600, flex: 1 }}>Quick Fix</button>
                <button 
                  onClick={handleFalsePositive}
                  style={{ background: '#21262d', color: '#c9d1d9', border: '1px solid #30363d', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 600, flex: 1, transition: 'all 0.2s' }} 
                  onMouseOver={e => e.target.style.background='#30363d'} 
                  onMouseOut={e => e.target.style.background='#21262d'}
                >
                  Ignore (FP Feedback)
                </button>
              </div>
            </motion.div>
          )}
          {fpSent && (
             <motion.div
               initial={{ opacity: 0, scale: 0.8 }}
               animate={{ opacity: 1, scale: 1 }}
               exit={{ opacity: 0 }}
               style={{ position: 'absolute', top: '100px', left: '40px', background: '#161b22', border: '1px solid #58a6ff', borderRadius: '8px', padding: '16px', width: '340px', textAlign: 'center', color: '#58a6ff', fontWeight: 'bold', zIndex: 100 }}
             >
               BACK-PROPAGATING TO MULTIVERSE...
               <div style={{ fontSize: '10px', marginTop: '8px', color: '#8b949e', fontWeight: 'normal' }}>Adjusting gradients across all active instances</div>
             </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Status Bar */}
      <div style={{ height: '24px', background: '#0d1117', borderTop: '1px solid #30363d', color: '#8b949e', display: 'flex', alignItems: 'center', padding: '0 12px', fontSize: '11px', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#58a6ff' }}><TermIcon size={14}/> Shadow-Omega Sync: Active</span>
          <span style={{ color: showWarning ? '#f85149' : '#8b949e' }}>{showWarning ? `${ruleData ? 1 : 0} Error` : '0 Errors'}, Shadow-Omega</span>
        </div>
        <div>UTF-8</div>
      </div>
    </div>
  );
}
