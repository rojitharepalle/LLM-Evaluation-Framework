import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

function formatRunId(runId) {
  if (!runId) return ''
  const [date, time] = runId.split('_')
  return `${date.slice(4,6)}/${date.slice(6,8)} ${time.slice(0,2)}:${time.slice(2,4)}`
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background:'var(--bg-elevated)', border:'1px solid var(--border-bright)', borderRadius:'var(--radius-md)', padding:'12px', fontFamily:'var(--font-mono)', fontSize:'11px' }}>
      <div style={{ color:'var(--text-dim)', marginBottom:'8px', fontSize:'10px' }}>{label}</div>
      {payload.map(p => (
        <div key={p.dataKey} style={{ display:'flex', justifyContent:'space-between', gap:'20px', color:p.color, marginBottom:'3px' }}>
          <span>{p.name}</span>
          <span style={{ fontWeight:600 }}>{(p.value*100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  )
}

export function TrendChart({ runs }) {
  if (!runs?.length) return null
  const data = runs.map(r => ({
    name: formatRunId(r.run_id),
    faithfulness: r.summary.faithfulness||0,
    answer_relevancy: r.summary.answer_relevancy||0,
    context_recall: r.summary.context_recall||0,
    hallucination_rate: r.summary.hallucination_rate||0,
  }))
  return (
    <div style={{ width:'100%', height:260 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top:8, right:20, left:-10, bottom:0 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="name" tick={{ fill:'var(--text-dim)', fontSize:10, fontFamily:'var(--font-mono)' }} axisLine={{ stroke:'var(--border)' }} tickLine={false} />
          <YAxis tickFormatter={v=>`${Math.round(v*100)}%`} tick={{ fill:'var(--text-dim)', fontSize:10, fontFamily:'var(--font-mono)' }} axisLine={false} tickLine={false} domain={[0,1]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize:'10px', fontFamily:'var(--font-mono)', color:'var(--text-secondary)', paddingTop:'12px' }} />
          <ReferenceLine y={0.7} stroke="var(--green)" strokeDasharray="3 3" strokeOpacity={0.3} />
          <ReferenceLine y={0.1} stroke="var(--red)" strokeDasharray="3 3" strokeOpacity={0.3} />
          <Line dataKey="faithfulness" name="Faithfulness" stroke="var(--blue)" strokeWidth={2} dot={{ r:3 }} activeDot={{ r:5 }} />
          <Line dataKey="answer_relevancy" name="Ans. Relevancy" stroke="var(--green)" strokeWidth={2} dot={{ r:3 }} activeDot={{ r:5 }} />
          <Line dataKey="context_recall" name="Context Recall" stroke="#ce93d8" strokeWidth={2} dot={{ r:3 }} activeDot={{ r:5 }} />
          <Line dataKey="hallucination_rate" name="Hallucination Rate" stroke="var(--red)" strokeWidth={2} dot={{ r:3 }} activeDot={{ r:5 }} strokeDasharray="4 2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
