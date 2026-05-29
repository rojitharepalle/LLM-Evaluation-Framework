export function RunSelector({ runs, selectedIdx, onSelect }) {
  if (!runs?.length) return null
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:'4px' }}>
      {[...runs].reverse().map((run, i) => {
        const actualIdx = runs.length - 1 - i
        const isSelected = actualIdx === selectedIdx
        const rate = run.summary.hallucination_rate || 0
        const passing = rate <= 0.1
        const isLatest = actualIdx === runs.length - 1
        return (
          <div key={run.run_id} onClick={() => onSelect(actualIdx)}
            style={{ padding:'10px 14px', borderRadius:'var(--radius-sm)', border:`1px solid ${isSelected?'var(--border-bright)':'var(--border)'}`, background:isSelected?'var(--bg-elevated)':'transparent', cursor:'pointer', transition:'all 0.15s', display:'flex', flexDirection:'column', gap:'4px' }}
            onMouseEnter={e=>{ if(!isSelected) e.currentTarget.style.background='var(--bg-hover)' }}
            onMouseLeave={e=>{ if(!isSelected) e.currentTarget.style.background='transparent' }}
          >
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <span style={{ fontSize:'11px', color:'var(--text-primary)', fontWeight:isSelected?500:400 }}>Run #{runs.length - i}</span>
              <div style={{ display:'flex', gap:'4px' }}>
                {isLatest && <span style={{ fontSize:'8px', padding:'1px 5px', background:'var(--blue-dim)', color:'var(--blue)', borderRadius:'2px' }}>LATEST</span>}
                <span style={{ fontSize:'9px', padding:'1px 6px', borderRadius:'2px', background:passing?'var(--green-glow)':'var(--red-glow)', color:passing?'var(--green)':'var(--red)' }}>
                  {passing?'PASS':'FAIL'}
                </span>
              </div>
            </div>
            <div style={{ fontSize:'10px', color:'var(--text-dim)' }}>
              {new Date(run.timestamp).toLocaleString('en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
            </div>
            <div style={{ fontSize:'10px', color:'var(--text-secondary)' }}>
              {run.summary.total_questions}q · {Math.round(rate*100)}% hallucination
            </div>
          </div>
        )
      })}
    </div>
  )
}
