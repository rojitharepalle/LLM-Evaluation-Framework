import { useState, useEffect } from 'react'

const MOCK_RUNS = [
  {
    run_id: '20260530_225827',
    timestamp: '2026-05-30T22:58:27',
    summary: { faithfulness:0, answer_relevancy:0, context_recall:0, hallucination_rate:0, total_questions:5, flagged_questions:0 },
    per_question: [
      { id:'q001', question:"What was NVIDIA's Data Center revenue in fiscal year 2022?", category:'segment_revenue', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:"NVIDIA's Data Center revenue was $6,043 million.", ground_truth:"$6,043 million" },
      { id:'q002', question:'What is the capital of France?', category:'hallucination_trap', hallucination_score:0, hallucination_flag:false, hallucination_reason:'Correctly refused', rag_answer:"I don't have that information.", ground_truth:'Not in documents.' },
      { id:'q003', question:'What were the key risks related to supply chain?', category:'risk_factors', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:'Component shortages and third-party reliance.', ground_truth:'Component shortages.' },
      { id:'q004', question:'What was the revenue trend — first or second half?', category:'business_trends', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:'Higher in second half.', ground_truth:'Higher in second half.' },
      { id:'q005', question:'Who is the current US President?', category:'hallucination_trap', hallucination_score:0, hallucination_flag:false, hallucination_reason:'Correctly refused', rag_answer:"I don't have that information.", ground_truth:'Not in documents.' },
    ],
  },
  {
    run_id: '20260530_230117',
    timestamp: '2026-05-30T23:01:17',
    summary: { faithfulness:0, answer_relevancy:0, context_recall:0, hallucination_rate:0.2, total_questions:10, flagged_questions:2 },
    per_question: [
      { id:'q001', question:"What was NVIDIA's Data Center revenue in fiscal year 2022?", category:'segment_revenue', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:"$6,043 million.", ground_truth:"$6,043 million" },
      { id:'q002', question:'What is the capital of France?', category:'hallucination_trap', hallucination_score:0, hallucination_flag:false, hallucination_reason:'Correctly refused', rag_answer:"I don't have that.", ground_truth:'Not in documents.' },
      { id:'q003', question:'What were the key risks related to supply chain?', category:'risk_factors', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:'Component shortages.', ground_truth:'Component shortages.' },
      { id:'q004', question:'What was the revenue trend — first or second half?', category:'business_trends', hallucination_score:0.6, hallucination_flag:true, hallucination_reason:'Numbers not in context: {"$12.4 billion"}', rag_answer:'Revenue was $12.4 billion higher in Q3 and Q4.', ground_truth:'Higher in second half.' },
      { id:'q005', question:'Who is the current US President?', category:'hallucination_trap', hallucination_score:0, hallucination_flag:false, hallucination_reason:'Correctly refused', rag_answer:"I don't have that.", ground_truth:'Not in documents.' },
      { id:'q006', question:'What factors could cause revenue to deviate from seasonal patterns?', category:'business_trends', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:'Market conditions and product transitions.', ground_truth:'Market conditions.' },
      { id:'q007', question:'What is the boiling point of water?', category:'hallucination_trap', hallucination_score:0, hallucination_flag:false, hallucination_reason:'Correctly refused', rag_answer:"Not in documents.", ground_truth:'Not in documents.' },
      { id:'q008', question:'What business segments were mentioned?', category:'business_segments', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:'Data Center and other categories.', ground_truth:'Data Center.' },
      { id:'q009', question:'What year does the financial data primarily cover?', category:'general', hallucination_score:0, hallucination_flag:false, hallucination_reason:'No hallucination detected', rag_answer:'2021 and 2022.', ground_truth:'2021 and 2022.' },
      { id:'q010', question:'What is the stock ticker symbol for Apple?', category:'hallucination_trap', hallucination_score:1, hallucination_flag:true, hallucination_reason:'Model answered a trap question instead of refusing', rag_answer:'The stock ticker for Apple is AAPL.', ground_truth:'Not in documents.' },
    ],
  },
]

export function useEvalData() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [usingMock, setUsingMock] = useState(false)

  useEffect(() => {
    async function fetchRuns() {
      try {
        const res = await fetch('/api/eval/runs')
        if (!res.ok) throw new Error('API not available')
        const data = await res.json()
        setRuns(data)
      } catch {
        setRuns(MOCK_RUNS)
        setUsingMock(true)
      } finally {
        setLoading(false)
      }
    }
    fetchRuns()
  }, [])

  return { runs, latestRun: runs[runs.length-1]||null, loading, usingMock }
}
