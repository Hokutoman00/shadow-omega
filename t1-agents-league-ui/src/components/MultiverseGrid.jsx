export default function MultiverseGrid({ snapshot, deadUniverses, rebornUniverses, chainInfections }) {
  // snapshot.universes is expected to be an array of length 5
  const universes = snapshot?.universes || Array.from({ length: 5 }, (_, i) => ({ id: i, label: `U${i} base` }));
  
  return (
    <div style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto' }}>
      <h2 className="title-font" style={{ color: 'var(--text-main)', fontSize: '1rem', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>
        MULTIVERSE TOPOLOGY (ISLAND GRID)
      </h2>
      
      {universes.map((u) => {
        const isDead = deadUniverses.includes(u.id);
        const isReborn = rebornUniverses.includes(u.id);
        
        return (
          <div 
            key={u.id} 
            className={isReborn ? 'flash-white' : ''}
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '1rem',
              opacity: isDead ? 0.2 : 1,
              transition: 'opacity 0.5s ease-in-out',
            }}
          >
            {/* Row Label */}
            <div style={{ flex: '0 0 100px', textAlign: 'right' }}>
              <div className="title-font" style={{ fontSize: '1.2rem', color: isDead ? '#666' : 'var(--text-main)' }}>U{u.id}</div>
              <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{u.label || 'linux aggr'}</div>
            </div>

            {/* Grid Cells (20 columns) */}
            <div style={{ display: 'flex', gap: '4px', flex: 1 }}>
              {Array.from({ length: 20 }).map((_, colIndex) => {
                // Determine if this cell is part of an infection
                const isInfected = chainInfections.some(inf => inf.target_universes.includes(u.id));
                const infectionHighlight = isInfected ? 'var(--accent-red)' : 'var(--grid-line)';
                
                return (
                  <div 
                    key={colIndex} 
                    style={{ 
                      flex: 1, 
                      height: '30px', 
                      background: '#05050a', 
                      border: `1px solid ${infectionHighlight}`,
                      transition: 'border-color 0.3s'
                    }}
                  />
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
