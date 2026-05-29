"""
evaluation/results_store.py
Save, load, and compare eval runs over time.
Each run is saved as a timestamped JSON file in evaluation/results/.
"""

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
RESULTS_DIR = Path("./evaluation/results")


def save_run(
    ragas_scores: dict,
    hallucination_rate: float,
    per_question: list[dict],
    metadata: dict = None,
) -> Path:
    """Save a complete eval run to disk. Returns the file path."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
        "summary": {
            **ragas_scores,
            "hallucination_rate": hallucination_rate,
            "total_questions": len(per_question),
            "flagged_questions": sum(1 for q in per_question if q.get("hallucination_flag")),
        },
        "per_question": [
            {
                "id": q.get("id", ""),
                "question": q["question"],
                "ground_truth": q.get("ground_truth", ""),
                "rag_answer": q["rag_answer"],
                "category": q.get("category", ""),
                "hallucination_score": q.get("hallucination_score", 0),
                "hallucination_flag": q.get("hallucination_flag", False),
                "hallucination_reason": q.get("hallucination_reason", ""),
                "contexts_preview": [c[:200] for c in q.get("contexts", [])],
            }
            for q in per_question
        ],
    }

    out_path = RESULTS_DIR / f"eval_run_{run_id}.json"
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    console.print(f"[green]✓ Results saved → {out_path}[/green]")
    return out_path


def load_all_runs() -> list[dict]:
    """Load all past eval runs, sorted oldest → newest."""
    if not RESULTS_DIR.exists():
        return []
    runs = []
    for f in sorted(RESULTS_DIR.glob("eval_run_*.json")):
        with open(f) as fp:
            runs.append(json.load(fp))
    return runs


def load_latest_run() -> dict | None:
    runs = load_all_runs()
    return runs[-1] if runs else None


def print_summary_table(ragas_scores: dict, hallucination_rate: float, per_question: list[dict]):
    """Print a rich formatted summary to the terminal."""

    # ── Overall scores ──
    console.print()
    overall = Table(title="📊 Evaluation Summary", box=box.ROUNDED, show_header=True)
    overall.add_column("Metric", style="bold")
    overall.add_column("Score", justify="right")
    overall.add_column("Status", justify="center")

    thresholds = {
        "faithfulness": 0.7,
        "answer_relevancy": 0.7,
        "context_recall": 0.6,
    }

    for metric, score in ragas_scores.items():
        threshold = thresholds.get(metric, 0.7)
        status = "[green]✓ PASS[/green]" if score >= threshold else "[red]✗ FAIL[/red]"
        overall.add_row(metric.replace("_", " ").title(), f"{score:.2%}", status)

    hr_status = "[green]✓ PASS[/green]" if hallucination_rate <= 0.1 else "[red]✗ FAIL[/red]"
    overall.add_row(
        "Hallucination Rate",
        f"{hallucination_rate:.2%}",
        hr_status,
    )
    console.print(overall)

    # ── Per-question breakdown ──
    console.print()
    detail = Table(
        title="📋 Per-Question Results",
        box=box.SIMPLE_HEAD,
        show_header=True,
    )
    detail.add_column("#", style="dim", width=4)
    detail.add_column("Question", width=45)
    detail.add_column("Category", width=18)
    detail.add_column("Hallucination", justify="center", width=14)
    detail.add_column("Flag", justify="center", width=6)

    for i, q in enumerate(per_question, 1):
        flag = "[red]🚨 YES[/red]" if q.get("hallucination_flag") else "[green]✓ NO[/green]"
        score = q.get("hallucination_score", 0)
        detail.add_row(
            str(i),
            q["question"][:44],
            q.get("category", ""),
            f"{score:.2f}",
            flag,
        )
    console.print(detail)

    # ── CI/CD gate check ──
    ci_pass = hallucination_rate <= 0.10
    if ci_pass:
        console.print(Panel(
            f"[bold green]✓ CI/CD GATE: PASSED[/bold green]\n"
            f"Hallucination rate {hallucination_rate:.1%} ≤ 10% threshold",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ CI/CD GATE: FAILED[/bold red]\n"
            f"Hallucination rate {hallucination_rate:.1%} exceeds 10% threshold\n"
            f"Pipeline would be BLOCKED in GitHub Actions",
            border_style="red",
        ))

    return ci_pass# Results directory: evaluation/results/eval_run_TIMESTAMP.json
