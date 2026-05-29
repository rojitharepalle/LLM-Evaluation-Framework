import { useState } from 'react'
import { useEvalData } from './hooks/useEvalData'
import { MetricCard } from './components/MetricCard'
import { QuestionTable } from './components/QuestionTable'
import { TrendChart } from './components/TrendChart'
import { RunSelector } from './components/RunSelector'

function Section({ title, children, action }) {
  return (
    <div style={{ marginBottom:'32px' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'14px', paddingBottom:'10px', borderBottom:'1px solid var(--border)' }}>
        <span style={{ fontSize:'10px', letterSpacing:'0.15em', color:'var(--text-dim)', textTransform:'uppercase' }}>{title}</span>
        {action}
      </div>
      {children}
    </div>
  )
}

function CIGateBanner({ run }) {
  if (!run) return null
  const rate = run.summary.hallucination_rate || 0
  const passing = rate <= 0.1
  return (
    <div style={{ padding:'12px 20px', background:passing?'var(--green-glow)':'var(--red-glow)', border:`1px solid ${passing?'var(--green-dim)':'var(--red-dim)'}`, borderLeft:`3px solid ${passing?'var(--green)':'var(--red)'}`, borderRadius:'var(--radius-md)', display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'28px', animation:'fadeUp 0.3s ease' }}>
      <div>
        <span style={{ fontSize:'11px', fontWeight:600, color:passing?'var(--green)':'var(--red)', letterSpacing:'0.08em' }}>
          {passing ? '✓ CI/CD GATE: PASSED' : '✗ CI/CD GATE: FAILED'}
        </span>
        <span style={{ fontSize:'11px', color:'var(--text-secondary)', marginLeft:'16px' }}>
          Hallucination rate {Math.round(rate*100)}%{passing?' ≤ 10% threshold':' exceeds 10% threshold — deployment blocked'}
        </span>
      </div>
      <span style={{ fontSize:'10px', color:'var(--text-dim)' }}>
        {run.summary.flagged_questions} / {run.summary.total_questions} questions flagged
      </span>
    </div>
  )
}

export default function App() {
  const { runs, loading, usingMock } = useEvalData()
  const [selectedIdx, setSelectedIdx] = useState(null)

  const effectiveIdx = selectedIdx ?? (runs.length - 1)
  const selectedRun = runs[effectiveIdx] || null
  const prevRun = effectiveIdx > 0 ? runs[effectiveIdx - 1] : null

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'100vh', flexDirection:'column', gap:'12px' }}>
      <div style={{ fontSize:'11px', color:'var(--text-dim)', letterSpacing:'0.15em', animation:'pulse 1.5s infinite' }}>LOADING EVAL DATA</div>
    </div>
  )

  return (
    <div style={{ display:'flex', minHeight:'100vh' }}>
      <div style={{ width:'220px', flexShrink:0, background:'var(--bg-surface)', borderRight:'1px solid var(--border)', padding:'24px 16px', display:'flex', flexDirection:'column', gap:'24px', position:'sticky', top:0, height:'100vh', overflowY:'auto' }}>
        <div>
          <div style={{ fontSize:'11px', fontWeight:600, color:'var(--text-primary)', letterSpacing:'0.05em', marginBottom:'2px' }}>LLM EVAL</div>
          <div style={{ fontSize:'9px', color:'var(--text-dim)', letterSpacing:'0.1em' }}>FRAMEWORK v1.0</div>
        </div>
        <div style={{ display:'flex', flexDirection:'column', gap:'6px' }}>
          <div style={{ fontSize:'9px', color:'var(--text-dim)', letterSpacing:'0.1em', marginBottom:'2px' }}>PIPELINE</div>
          {[['LLM','llama3.2'],['EMBED','MiniLM-L6'],['DB','ChromaDB'],['CHUNKS','2122']].map(([k,v]) => (
            <div key={k} style={{ display:'flex', justifyContent:'space-between', fontSize:'10px' }}>
              <span style={{ color:'var(--text-dim)' }}>{k}</span>
              <span style={{ color:'var(--text-secondary)' }}>{v}</span>
            </div>
          ))}
        </div>
        <div style={{ flex:1 }}>
          <div style={{ fontSize:'9px', color:'var(--text-dim)', letterSpacing:'0.1em', marginBottom:'8px' }}>EVAL RUNS ({runs.length})</div>
          <RunSelector runs={runs} selectedIdx={effectiveIdx} onSelect={setSelectedIdx} />
        </div>
        {usingMock && (
          <div style={{ fontSize:'9px', color:'var(--amber)', padding:'6px 10px', background:'var(--amber-dim)', borderRadius:'var(--radius-sm)' }}>
            ⚠ Mock data — start FastAPI to see live results
          </div>
        )}
      </div>

      <div style={{ flex:1, padding:'32px 40px', overflowY:'auto', maxWidth:'1100px' }}>
        <div style={{ marginBottom:'28px', animation:'fadeUp 0.3s ease' }}>
          <h1 style={{ fontSize:'20px', fontWeight:500, color:'var(--text-primary)', marginBottom:'4px', fontFamily:'var(--font-sans)' }}>Evaluation Dashboard</h1>
          <div style={{ fontSize:'11px', color:'var(--text-dim)' }}>
            {selectedRun ? `Run #${effectiveIdx+1} · ${new Date(selectedRun.timestamp).toLocaleString()} · ${selectedRun.summary.total_questions} questions` : 'No runs yet'}
          </div>
        </div>

        <CIGateBanner run={selectedRun} />

        <Section title="Metrics — Latest Run">
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:'12px' }}>
            <MetricCard label="Faithfulness"       value={selectedRun?.summary.faithfulness}        previousValue={prevRun?.summary.faithfulness}        threshold={0.7} skipped={!selectedRun?.summary.faithfulness} />
            <MetricCard label="Answer Relevancy"   value={selectedRun?.summary.answer_relevancy}    previousValue={prevRun?.summary.answer_relevancy}    threshold={0.7} skipped={!selectedRun?.summary.answer_relevancy} />
            <MetricCard label="Context Recall"     value={selectedRun?.summary.context_recall}      previousValue={prevRun?.summary.context_recall}      threshold={0.6} skipped={!selectedRun?.summary.context_recall} />
            <MetricCard label="Hallucination Rate" value={selectedRun?.summary.hallucination_rate}  previousValue={prevRun?.summary.hallucination_rate}  threshold={0.1} />
          </div>
        </Section>

        {runs.length > 1 && (
          <Section title="Score Trends — All Runs">
            <div style={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:'var(--radius-md)', padding:'20px' }}>
              <TrendChart runs={runs} />
            </div>
          </Section>
        )}

        <Section
          title={`Per-Question Results — ${selectedRun?.summary.total_questions||0} questions`}
          action={selectedRun?.summary.flagged_questions > 0 && (
            <span style={{ fontSize:'10px', color:'var(--red)', letterSpacing:'0.08em' }}>{selectedRun.summary.flagged_questions} FLAGGED</span>
          )}
        >
          <QuestionTable questions={selectedRun?.per_question} />
        </Section>
      </div>
    </div>
  )
}
