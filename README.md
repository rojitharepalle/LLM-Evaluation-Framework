# 🧪 Project A — LLM Evaluation Framework

Automated RAG evaluation pipeline scoring faithfulness, hallucination rate, and retrieval quality — integrated with GitHub Actions CI/CD.

## Architecture

```
project-a/
├── rag_pipeline/
│   ├── pipeline.py       # Core RAG: ChromaDB + LangChain + OpenAI
│   ├── data_loader.py    # Load FinanceBench / Wikipedia / PDFs / sample data
│   ├── golden_set.py     # 30-question golden test set with hallucination traps
│   └── api.py            # FastAPI: /query, /ingest, /collection
├── evaluation/
│   ├── evaluator.py      # RAGAS + DeepEval scoring (Phase 2)
│   └── golden_set.json   # Generated after first ingest
├── dashboard/            # React dashboard (Phase 3)
├── .github/workflows/    # CI/CD (Phase 4)
└── scripts/
    ├── ingest.py         # Step 1: load data into ChromaDB
    └── run_eval.py       # Step 2: score the pipeline (Phase 2)
```

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY
```

> **No OpenAI key?** Set `EMBEDDING_PROVIDER=local` in `.env` to use free HuggingFace embeddings.
> The LLM call still needs OpenAI, but you can swap it for Ollama (see below).

### 3. Ingest data

```bash
# Option A: Use built-in sample data (5 company reports — works immediately)
python scripts/ingest.py

# Option B: Use FinanceBench (real financial QA dataset — ~200 passages)
python scripts/ingest.py --financebench

# Option C: Load your own PDFs
python scripts/ingest.py --pdf ./your-pdf-folder/
```

### 4. Start the API

```bash
uvicorn rag_pipeline.api:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 5. Test a query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Apple revenue in 2022?"}'
```

## Using a Local LLM (Ollama)

If you want to avoid OpenAI costs:

```bash
# Install Ollama: https://ollama.ai
ollama pull llama3.2

# In pipeline.py, swap the LLM:
from langchain_community.llms import Ollama
self.llm = Ollama(model="llama3.2")

# Use local embeddings too:
EMBEDDING_PROVIDER=local   # in .env
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Ask a question — returns answer + source chunks |
| GET | `/collection` | ChromaDB collection info |
| POST | `/ingest/sample` | Load built-in sample data |
| DELETE | `/collection` | Reset collection |

## Phase Checklist

- [x] **Phase 1 (Day 1–2)**: RAG pipeline + ChromaDB + FastAPI + golden set
- [ ] **Phase 2 (Day 3–4)**: RAGAS + DeepEval evaluation suite
- [ ] **Phase 3 (Day 5–6)**: React dashboard
- [ ] **Phase 4 (Day 7)**: GitHub Actions CI/CD quality gate

## Resume Bullet

> Built an automated LLM evaluation framework using RAGAS and DeepEval, scoring RAG pipelines on faithfulness, hallucination rate, and retrieval quality; integrated with GitHub Actions CI/CD to block deployments on quality regression.

## Running the API

```bash
uvicorn rag_pipeline.api:app --reload
```

Query example:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What was NVIDIA Data Center revenue in 2022?"}'
```

## Running Evaluations

```bash
# Quick smoke test
python scripts/run_eval.py --questions 5 --no-ragas

# Full eval
python scripts/run_eval.py --no-ragas

# CI mode (exits 1 if hallucination rate > 10%)
python scripts/run_eval.py --ci
```
