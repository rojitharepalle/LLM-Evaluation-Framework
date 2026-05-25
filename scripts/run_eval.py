"""
scripts/run_eval.py
Run the full evaluation suite against the RAG pipeline.

Usage:
    python scripts/run_eval.py                    # run all questions
    python scripts/run_eval.py --questions 5      # quick smoke test (5 questions)
    python scripts/run_eval.py --no-ragas         # skip RAGAS, only hallucination
    python scripts/run_eval.py --openai           # use OpenAI instead of Ollama
    python scripts/run_eval.py --ci               # exit code 1 if hallucination > 10%
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

load_dotenv()
console = Console()


def main():
    parser = argparse.ArgumentParser(description="Run LLM evaluation suite")
    parser.add_argument("--questions", type=int, default=None, help="Limit number of questions")
    parser.add_argument("--no-ragas", action="store_true", help="Skip RAGAS metrics")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI instead of Ollama for RAGAS")
    parser.add_argument("--ci", action="store_true", help="Exit 1 if hallucination rate exceeds threshold")
    parser.add_argument("--golden-set", type=str, default=None, help="Path to custom golden set JSON")
    args = parser.parse_args()

    from rag_pipeline.pipeline import RAGPipeline
    from evaluation.evaluator import RAGASEvaluator, HallucinationDetector
    from evaluation.results_store import save_run, print_summary_table

    # ── Load golden set ──────────────────────────────────────────────────────
    if args.golden_set:
        golden_path = Path(args.golden_set)
    else:
        golden_path = Path("./evaluation/golden_set_financebench.json")

    if not golden_path.exists():
        # fall back to built-in sample golden set
        from rag_pipeline.golden_set import SAMPLE_GOLDEN_SET
        questions = SAMPLE_GOLDEN_SET
        console.print(f"[yellow]Using built-in sample golden set ({len(questions)} questions)[/yellow]")
    else:
        with open(golden_path) as f:
            questions = json.load(f)
        console.print(f"[green]✓ Loaded {len(questions)} questions from {golden_path}[/green]")

    if args.questions:
        questions = questions[: args.questions]
        console.print(f"[dim]Limited to {len(questions)} questions[/dim]")

    # ── Run RAG pipeline on every question ────────────────────────────────────
    console.print(Panel(
        f"[bold]Running RAG pipeline on {len(questions)} questions[/bold]\n"
        f"Model: Ollama llama3.2  |  Embeddings: HuggingFace all-MiniLM-L6-v2\n"
        f"RAGAS: {'disabled' if args.no_ragas else 'enabled'}  |  "
        f"DeepEval: enabled (rule-based fallback)",
        title="🧪 LLM Evaluation Suite",
        border_style="cyan",
    ))

    pipeline = RAGPipeline()
    info = pipeline.collection_info()
    if info["chunk_count"] == 0:
        console.print("[red]ChromaDB is empty! Run: python scripts/ingest.py[/red]")
        sys.exit(1)

    console.print(f"[dim]ChromaDB: {info['chunk_count']} chunks in '{info['collection']}'[/dim]\n")

    # Generate answers
    rag_results = []
    for q in track(questions, description="Querying RAG pipeline"):
        result = pipeline.query(q["question"])
        rag_results.append({
            **q,
            "rag_answer": result["answer"],
            "contexts": result["contexts"],
        })

    # ── RAGAS scoring ─────────────────────────────────────────────────────────
    ragas_scores = {}
    if not args.no_ragas:
        evaluator = RAGASEvaluator()
        ragas_scores = evaluator.evaluate(
            rag_results,
            use_ollama=not args.openai,
        )
        console.print(f"\n[bold]RAGAS scores:[/bold] {ragas_scores}")
    else:
        console.print("[dim]RAGAS skipped (--no-ragas)[/dim]")
        ragas_scores = {"faithfulness": 0.0, "answer_relevancy": 0.0, "context_recall": 0.0}

    # ── Hallucination detection ───────────────────────────────────────────────
    detector = HallucinationDetector(use_deepeval=True)
    scored_results = detector.score_all(rag_results)
    hallucination_rate = detector.hallucination_rate(scored_results)

    # ── Print summary ─────────────────────────────────────────────────────────
    ci_pass = print_summary_table(ragas_scores, hallucination_rate, scored_results)

    # ── Save results ──────────────────────────────────────────────────────────
    save_run(
        ragas_scores=ragas_scores,
        hallucination_rate=hallucination_rate,
        per_question=scored_results,
        metadata={
            "model": "ollama/llama3.2",
            "embedding_model": "all-MiniLM-L6-v2",
            "chunk_count": info["chunk_count"],
            "golden_set": str(golden_path),
            "ragas_enabled": not args.no_ragas,
        },
    )

    # ── CI gate ───────────────────────────────────────────────────────────────
    if args.ci and not ci_pass:
        console.print("[red bold]Exiting with code 1 — CI pipeline will fail.[/red bold]")
        sys.exit(1)

    console.print("\n[dim]View detailed results in evaluation/results/[/dim]")
    console.print("[dim]Next: python scripts/run_eval.py --ci  (for GitHub Actions)[/dim]")


if __name__ == "__main__":
    main()