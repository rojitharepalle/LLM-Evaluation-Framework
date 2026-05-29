import { useState } from 'react'

const CATEGORY_COLORS = {
  hallucination_trap: { bg:'var(--amber-dim)', text:'var(--amber)' },
  segment_revenue:    { bg:'var(--blue-dim)',  text:'var(--blue)' },
  business_trends:    { bg:'#1a2a1a', text:'#4caf50' },
  risk_factors:       { bg:'#2a1a2a', text:'#ce93d8' },
  business_segments:  { bg:'#1a1a2a', text:'#80cbc4' },
  general:            { bg:'var(--bg-elevated)', text:'var(--text-secondary)' },
}

function ScoreBar({ score }) {
  const pct = Math.round(score * 100)
  const color = score === 0 ? 'var(--green)' : score < 0.5 ? 'var(--amber)' : 'var(--red)'
  return (
    <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
      <div style={{ width:'60px', height:'4px', background:'var(--border)', borderRadius:'2px', overflow:'hidden' }}>
        <div style={{ width:`${pct}%`, height:'100%', background:color, borderRadius:'2px' }} />
      </div>
      <span style={{ fontSize:'11px', color, fontWeight:500 }}>{pct}%</span>
    </div>
  )
}

export function QuestionTable({ questions }) {
  const [expanded, setExpanded] = useState(null)
  if (!questions?.length) return <div style={{ padding:'40px', textAlign:'center', color:'var(--text-dim)', fontSize:'12px' }}>No data</div>

  return (
    <div style={{ border:'1px solid var(--border)', borderRadius:'var(--radius-md)', overflow:'hidden' }}>
      <div style={{ display:'grid', gridTemplateColumns:'32px 1fr 140px 130px 80px', padding:'8px 16px', background:'var(--bg-elevated)', borderBottom:'1px solid var(--border)', fontSize:'10px', color:'var(--text-dim)', letterSpacing:'0.1em', textTransform:'uppercase', gap:'12px' }}>
        <span>#</span><span>Question</span><span>Category</span><span>Hallucination</span><span>Flag</span>
      </div>
      {questions.map((q, i) => {
        const style = CATEGORY_COLORS[q.category] || CATEGORY_COLORS.general
        return (
          <div key={q.id||i}>
            <div onClick={() => setExpanded(expanded===i?null:i)}
              style={{ display:'grid', gridTemplateColumns:'32px 1fr 140px 130px 80px', padding:'12px 16px', borderBottom:'1px solid var(--border)', gap:'12px', cursor:'pointer', background:expanded===i?'var(--bg-elevated)':'transparent', alignItems:'center' }}
              onMouseEnter={e=>{ if(expanded!==i) e.currentTarget.style.background='var(--bg-hover)' }}
              onMouseLeave={e=>{ if(expanded!==i) e.currentTarget.style.background='transparent' }}
            >
              <span style={{ fontSize:'11px', color:'var(--text-dim)' }}>{i+1}</span>
              <span style={{ fontSize:'12px', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{q.question}</span>
              <span style={{ fontSize:'9px', padding:'2px 7px', borderRadius:'2px', background:style.bg, color:style.text, letterSpacing:'0.08em', textTransform:'uppercase', whiteSpace:'nowrap' }}>
                {q.category.replace(/_/g,' ')}
              </span>
              <ScoreBar score={q.hallucination_score||0} />
              <span style={{ fontSize:'11px', fontWeight:600, color:q.hallucination_flag?'var(--red)':'var(--green)' }}>
                {q.hallucination_flag ? '🚨 YES' : '✓ NO'}
              </span>
            </div>
            {expanded===i && (
              <div style={{ padding:'16px 16px 16px 48px', background:'var(--bg-elevated)', borderBottom:'1px solid var(--border)', display:'grid', gridTemplateColumns:'1fr 1fr', gap:'16px', animation:'fadeUp 0.2s ease' }}>
                <div>
                  <div style={{ fontSize:'9px', color:'var(--text-dim)', letterSpacing:'0.1em', marginBottom:'6px' }}>MODEL ANSWER</div>
                  <div style={{ fontSize:'12px', color:'var(--text-secondary)', lineHeight:1.6 }}>{q.rag_answer}</div>
                </div>
                <div>
                  <div style={{ fontSize:'9px', color:'var(--text-dim)', letterSpacing:'0.1em', marginBottom:'6px' }}>GROUND TRUTH</div>
                  <div style={{ fontSize:'12px', color:'var(--text-secondary)', lineHeight:1.6, marginBottom:'10px' }}>{q.ground_truth}</div>
                  <div style={{ fontSize:'9px', color:'var(--text-dim)', letterSpacing:'0.1em', marginBottom:'6px' }}>REASON</div>
                  <div style={{ fontSize:'11px', color:q.hallucination_flag?'var(--amber)':'var(--green)', lineHeight:1.5 }}>{q.hallucination_reason}</div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
