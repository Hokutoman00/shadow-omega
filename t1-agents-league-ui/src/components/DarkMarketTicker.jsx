import { motion, AnimatePresence } from 'framer-motion';
import { Database } from 'lucide-react';

export default function DarkMarketTicker({ trades }) {
  return (
    <div style={{ height: '54px', background: 'transparent', display: 'flex', alignItems: 'center', overflow: 'hidden', padding: '0 1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderRight: '1px solid rgba(255,255,255,0.1)', paddingRight: '1rem', marginRight: '1rem', whiteSpace: 'nowrap' }}>
        <Database size={16} className="glow-text-gold" /> 
        <span className="title-font glow-text-gold" style={{ fontSize: '0.85rem', fontWeight: 700, letterSpacing: '1px' }}>DARKMARKET</span>
      </div>
      
      <div style={{ display: 'flex', gap: '1.5rem', flex: 1, overflow: 'hidden', position: 'relative' }}>
        <AnimatePresence>
          {trades.map((trade) => (
            <motion.div 
              key={trade.id}
              initial={{ x: 200, opacity: 0, scale: 0.9 }}
              animate={{ x: 0, opacity: 1, scale: 1 }}
              exit={{ opacity: 0, x: -100, scale: 0.8 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              style={{ display: 'flex', gap: '12px', alignItems: 'center', fontSize: '0.8rem', whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.03)', padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.08)', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05)' }}
              className="mono"
            >
              <span style={{ color: 'var(--text-dim)' }}>[0DAY_{trade.hash}]</span>
              <span style={{ color: 'var(--accent-green)', fontWeight: 'bold' }}>dF/dA: {trade.purity}</span>
              <span style={{ color: 'var(--accent-red)', fontWeight: 'bold', textShadow: '0 0 8px rgba(248,113,113,0.4)' }}>{trade.price} TKN</span>
              <span style={{ color: 'var(--accent-blue)' }}>{trade.buyer}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {trades.length === 0 && (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', display: 'flex', alignItems: 'center' }} className="mono">
            AWAITING HIGH-PURITY MUTATIONS...
          </div>
        )}
      </div>
    </div>
  );
}
