export function MetricCard({ label, value, previousValue, threshold, skipped }) {
  const pct = skipped ? null : Math.round((value || 0) * 100)
  const isHallucination = label.toLowerCase().includes('hallucination')
  const passing = isHallucination ? (value||0) <= (threshold||0.10) : (value||0) >= (threshold||0.7)
  const delta = previousValue != null && value != null ? Math.round((value - previousValue) * 100) : null
  const color = skipped ? 'var(--text-dim)' : passing ? 'var(--green)' : 'var(--red)'
  const bgColor = skipped ? 'transparent' : passing ? 'var(--green-glow)' : 'var(--red-glow)'

  return (
    <div style={{ background:'var(--bg-surface)', border:`1px solid var(--border)`, borderTop:`2px solid ${color}`, borderRadius:'var(--radius-md)', padding:'20px', display:'flex', flexDirection:'column', gap:'10px', animation:'fadeUp 0.3s ease forwards' }}>
      <div style={{ fontSize:'10px', color:'var(--text-secondary)', letterSpacing:'0.12em', textTransform:'uppercase' }}>{label}</div>
      <div style={{ display:'flex', alignItems:'baseline', gap:'10px' }}>
        <span style={{ fontSize:'32px', fontWeight:600, color, lineHeight:1 }}>{skipped ? '—' : `${pct}%`}</span>
        {delta != null && !skipped && (
          <span style={{ fontSize:'11px', color: isHallucination ? (delta<=0?'var(--green)':'var(--red)') : (delta>=0?'var(--green)':'var(--red)') }}>
            {delta >= 0 ? '▲' : '▼'} {Math.abs(delta)}pp
          </span>
        )}
      </div>
      <div style={{ display:'flex', alignItems:'center', gap:'6px' }}>
        <span style={{ fontSize:'10px', padding:'2px 8px', borderRadius:'2px', background:bgColor, color, letterSpacing:'0.08em' }}>
          {skipped ? 'SKIPPED' : passing ? 'PASS' : 'FAIL'}
        </span>
        {!skipped && <span style={{ fontSize:'10px', color:'var(--text-dim)' }}>threshold {isHallucination?'≤':'≥'} {Math.round((threshold||(isHallucination?0.1:0.7))*100)}%</span>}
      </div>
    </div>
  )
}
