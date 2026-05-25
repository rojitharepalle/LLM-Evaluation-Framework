"""
rag_pipeline/api.py
FastAPI server exposing the RAG pipeline.

Endpoints:
  POST /query          — ask a question, get answer + source chunks
  GET  /collection     — inspect ChromaDB collection metadata
  POST /ingest/sample  — ingest the built-in sample dataset
  DELETE /collection   — reset the collection (dev only)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import time
import json

from rag_pipeline.pipeline import RAGPipeline
from rag_pipeline.data_loader import load_sample_data

app = FastAPI(
    title="RAG Pipeline API",
    description="LLM Evaluation Framework — RAG query and ingestion endpoints",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared pipeline instance
_pipeline: Optional[RAGPipeline] = None


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


# ── Request / Response models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, examples=["What was Apple's revenue in 2022?"])
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")


class SourceChunk(BaseModel):
    content: str
    metadata: dict
    relevance_score: Optional[float] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    contexts: list[str]
    source_chunks: list[SourceChunk]
    latency_ms: float


class CollectionInfo(BaseModel):
    status: str
    collection: Optional[str] = None
    persist_dir: Optional[str] = None
    chunk_count: int = 0


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "RAG Pipeline API is running", "docs": "/docs"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """Run a question through the full RAG pipeline."""
    pipeline = get_pipeline()
    info = pipeline.collection_info()
    if info["chunk_count"] == 0:
        raise HTTPException(
            status_code=400,
            detail="Collection is empty. POST /ingest/sample to load data first."
        )

    start = time.perf_counter()
    result = pipeline.query(request.question, top_k=request.top_k)
    latency_ms = (time.perf_counter() - start) * 1000

    # Get chunks with scores for the response
    scored = pipeline.retrieve_with_scores(request.question, top_k=request.top_k)
    source_chunks = [
        SourceChunk(
            content=doc.page_content,
            metadata=doc.metadata,
            relevance_score=round(score, 4),
        )
        for doc, score in scored
    ]

    return QueryResponse(
        question=result["question"],
        answer=result["answer"],
        contexts=result["contexts"],
        source_chunks=source_chunks,
        latency_ms=round(latency_ms, 2),
    )


@app.get("/collection", response_model=CollectionInfo)
def collection_info():
    """Get metadata about the current ChromaDB collection."""
    pipeline = get_pipeline()
    info = pipeline.collection_info()
    return CollectionInfo(**info)


@app.post("/ingest/sample")
def ingest_sample():
    """Ingest the built-in sample financial dataset (5 company reports)."""
    pipeline = get_pipeline()
    docs = load_sample_data()
    chunk_count = pipeline.ingest_documents(docs)
    return {
        "message": "Sample data ingested successfully",
        "documents_loaded": len(docs),
        "chunks_stored": chunk_count,
    }


@app.delete("/collection")
def reset_collection():
    """Delete all documents. Use during development to re-ingest."""
    pipeline = get_pipeline()
    pipeline.reset_collection()
    return {"message": "Collection deleted. Ready to re-ingest."}


# ── Eval results endpoint ──────────────────────────────────────────────────────

@app.get("/eval/runs")
def get_eval_runs():
    """Return all eval run results for the dashboard."""
    results_dir = Path("./evaluation/results")
    if not results_dir.exists():
        return []
    runs = []
    for f in sorted(results_dir.glob("eval_run_*.json")):
        with open(f) as fp:
            runs.append(json.load(fp))
    return runs