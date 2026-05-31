# LLM Evaluation Dashboard

React dashboard for visualizing RAG pipeline evaluation results.

## Features

- CI/CD gate banner — green PASS / red FAIL based on hallucination rate
- 4 metric score cards — faithfulness, answer relevancy, context recall, hallucination rate
- Trend chart — scores across all eval runs over time (Recharts)
- Per-question breakdown — click any row to expand model answer vs ground truth
- Run selector — switch between historical eval runs

## Stack

- React 18 + Vite
- Recharts for trend visualization
- IBM Plex Mono — terminal aesthetic
- Connects to FastAPI backend at localhost:8000

## Setup

```bash
npm install
npm run dev
# Dashboard: http://localhost:5173
```

Requires FastAPI backend running:
```bash
uvicorn rag_pipeline.api:app --reload
```
