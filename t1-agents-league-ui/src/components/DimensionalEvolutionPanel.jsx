import { XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, AreaChart, Area } from 'recharts';
import { TrendingDown } from 'lucide-react';

export default function DimensionalEvolutionPanel({ entropyData, barcodes }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem', minHeight: 0 }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ color: 'var(--accent-red)', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px' }} className="title-font">
          [ POST-STAGE ]
        </div>
        <div style={{ color: 'var(--text-main)', fontSize: '0.9rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingDown size={16} /> Dimensional Collapse & Feedback
        </div>
      </div>

      {/* TDA Barcode */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', minHeight: 0 }}>
        <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }} className="mono">TDA Betti-0 Barcodes (Diversity)</div>
        <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', borderRadius: '6px', padding: '12px', border: '1px inset rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', gap: '4px', overflow: 'hidden' }}>
          {barcodes.map((b, i) => (
             <div key={i} style={{ width: `${b.length}%`, height: '4px', background: b.length < 20 ? 'var(--accent-red)' : 'var(--accent-blue)', borderRadius: '2px', marginLeft: `${b.start}%`, opacity: 0.8, boxShadow: `0 0 8px ${b.length < 20 ? 'var(--accent-red)' : 'var(--accent-blue)'}` }} />
          ))}
        </div>
      </div>

      {/* Autoencoder Bottleneck / Entropy Loss */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', minHeight: 0 }}>
        <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }} className="mono">Compression Entropy Loss (Auto-regressive)</div>
        <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', borderRadius: '6px', border: '1px inset rgba(255,255,255,0.05)', padding: '12px 12px 0 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={entropyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="turn" hide />
              <YAxis hide domain={[0, 100]} />
              <Tooltip contentStyle={{ background: 'rgba(10,14,23,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#fff' }} itemStyle={{ color: 'var(--accent-gold)' }} />
              <Area type="monotone" dataKey="loss" stroke="var(--accent-gold)" strokeWidth={2} fill="url(#colorLoss)" isAnimationActive={false} />
              <defs>
                <linearGradient id="colorLoss" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-gold)" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="var(--accent-gold)" stopOpacity={0}/>
                </linearGradient>
              </defs>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
