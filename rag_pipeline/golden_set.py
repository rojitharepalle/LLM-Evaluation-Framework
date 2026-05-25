"""
rag_pipeline/golden_set.py
Create, load, and manage the golden test set.

The golden set is a list of questions with expected answers and source references.
Used by the evaluation suite to score faithfulness, relevancy, and hallucination rate.
"""

import json
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()

GOLDEN_SET_PATH = Path("./evaluation/golden_set.json")

# ── Built-in golden set (sample data) ─────────────────────────────────────────
# These match the SAMPLE_FINANCIAL_TEXTS in data_loader.py
SAMPLE_GOLDEN_SET = [
    {
        "id": "q001",
        "question": "What was Apple's total net sales for fiscal year 2022?",
        "ground_truth": "Apple's total net sales for fiscal year 2022 were $394.3 billion.",
        "source_doc": "Apple 2022 Annual Report",
        "category": "revenue",
    },
    {
        "id": "q002",
        "question": "How much did Apple's iPhone revenue contribute to total net sales in 2022?",
        "ground_truth": "iPhone revenue was $205.5 billion, representing 52.1% of Apple's total net sales in 2022.",
        "source_doc": "Apple 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q003",
        "question": "What was Apple's Services revenue in fiscal year 2022?",
        "ground_truth": "Apple's Services revenue reached a record $78.1 billion in fiscal year 2022, growing 14.2% year-over-year.",
        "source_doc": "Apple 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q004",
        "question": "How much did Apple return to shareholders in fiscal year 2022?",
        "ground_truth": "Apple returned over $90 billion to shareholders through dividends and share repurchases in fiscal year 2022.",
        "source_doc": "Apple 2022 Annual Report",
        "category": "shareholder_returns",
    },
    {
        "id": "q005",
        "question": "What was Microsoft's fiscal year 2023 total revenue?",
        "ground_truth": "Microsoft Corporation's fiscal year 2023 revenue was $211.9 billion, up 7% year-over-year.",
        "source_doc": "Microsoft 2023 Annual Report",
        "category": "revenue",
    },
    {
        "id": "q006",
        "question": "How much did Microsoft's cloud revenue grow in fiscal year 2023?",
        "ground_truth": "Microsoft's cloud revenue including Azure grew 27% to $87.9 billion in fiscal year 2023.",
        "source_doc": "Microsoft 2023 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q007",
        "question": "What was Microsoft's Intelligent Cloud segment revenue in 2023?",
        "ground_truth": "Microsoft's Intelligent Cloud segment revenue was $87.9 billion in fiscal year 2023.",
        "source_doc": "Microsoft 2023 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q008",
        "question": "What was Microsoft's operating income in fiscal year 2023?",
        "ground_truth": "Microsoft's operating income was $88.5 billion in fiscal year 2023.",
        "source_doc": "Microsoft 2023 Annual Report",
        "category": "profitability",
    },
    {
        "id": "q009",
        "question": "What was Amazon's total net sales for 2022?",
        "ground_truth": "Amazon's total net sales for 2022 were $514.0 billion, an increase of 9% compared to 2021.",
        "source_doc": "Amazon 2022 Annual Report",
        "category": "revenue",
    },
    {
        "id": "q010",
        "question": "How much did AWS revenue grow in 2022?",
        "ground_truth": "AWS net sales grew 29% to $80.1 billion in 2022.",
        "source_doc": "Amazon 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q011",
        "question": "What was Amazon's advertising services revenue in 2022?",
        "ground_truth": "Amazon's Advertising services revenue was $37.7 billion in 2022.",
        "source_doc": "Amazon 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q012",
        "question": "How many Amazon Prime members are there?",
        "ground_truth": "Amazon Prime has over 200 million members worldwide.",
        "source_doc": "Amazon 2022 Annual Report",
        "category": "business_metrics",
    },
    {
        "id": "q013",
        "question": "What was Amazon's operating income in 2022 and why did it decrease?",
        "ground_truth": "Amazon's operating income decreased to $12.2 billion from $24.9 billion in 2021, primarily due to inflationary pressures and investments in fulfillment capacity.",
        "source_doc": "Amazon 2022 Annual Report",
        "category": "profitability",
    },
    {
        "id": "q014",
        "question": "What was Tesla's revenue for fiscal year 2022?",
        "ground_truth": "Tesla reported record revenue of $81.5 billion for fiscal year 2022, up 51% from 2021.",
        "source_doc": "Tesla 2022 Annual Report",
        "category": "revenue",
    },
    {
        "id": "q015",
        "question": "How many vehicles did Tesla deliver in 2022?",
        "ground_truth": "Tesla delivered 1.31 million vehicles globally in 2022.",
        "source_doc": "Tesla 2022 Annual Report",
        "category": "business_metrics",
    },
    {
        "id": "q016",
        "question": "What was Tesla's automotive gross margin in 2022?",
        "ground_truth": "Tesla's automotive gross margin was 28.5% in 2022.",
        "source_doc": "Tesla 2022 Annual Report",
        "category": "profitability",
    },
    {
        "id": "q017",
        "question": "What was Tesla's free cash flow in 2022?",
        "ground_truth": "Tesla's free cash flow was $7.6 billion in 2022.",
        "source_doc": "Tesla 2022 Annual Report",
        "category": "cash_flow",
    },
    {
        "id": "q018",
        "question": "What was Tesla's energy generation and storage revenue in 2022?",
        "ground_truth": "Tesla's energy generation and storage revenue grew 40% to $3.9 billion in 2022.",
        "source_doc": "Tesla 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q019",
        "question": "What was Alphabet's total revenue for fiscal year 2022?",
        "ground_truth": "Alphabet Inc. reported revenues of $282.8 billion for fiscal 2022, a 10% increase from 2021.",
        "source_doc": "Alphabet 2022 Annual Report",
        "category": "revenue",
    },
    {
        "id": "q020",
        "question": "What was Google Search revenue in 2022?",
        "ground_truth": "Google Search and other revenues were $162.5 billion in fiscal 2022.",
        "source_doc": "Alphabet 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q021",
        "question": "What was YouTube's advertising revenue in 2022?",
        "ground_truth": "YouTube advertising revenues were $29.2 billion in fiscal 2022.",
        "source_doc": "Alphabet 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q022",
        "question": "How much did Google Cloud grow in 2022?",
        "ground_truth": "Google Cloud revenues grew 37% to $26.3 billion in fiscal 2022.",
        "source_doc": "Alphabet 2022 Annual Report",
        "category": "segment_revenue",
    },
    {
        "id": "q023",
        "question": "What was Alphabet's operating income in 2022?",
        "ground_truth": "Alphabet had operating income of $74.8 billion in fiscal 2022.",
        "source_doc": "Alphabet 2022 Annual Report",
        "category": "profitability",
    },
    {
        "id": "q024",
        "question": "How much did Alphabet spend on R&D in 2022?",
        "ground_truth": "Alphabet's research and development expenses were $39.5 billion in fiscal 2022.",
        "source_doc": "Alphabet 2022 Annual Report",
        "category": "expenses",
    },
    {
        "id": "q025",
        "question": "Which company had the highest revenue in fiscal year 2022 among Apple, Amazon, and Alphabet?",
        "ground_truth": "Amazon had the highest revenue among the three at $514.0 billion in 2022, compared to Alphabet's $282.8 billion and Apple's $394.3 billion.",
        "source_doc": "Multiple",
        "category": "comparison",
    },
    # Hallucination trap questions — the correct answer is "not in the documents"
    {
        "id": "q026",
        "question": "What was Apple's net income margin for fiscal year 2022?",
        "ground_truth": "The provided documents do not contain information about Apple's net income margin for fiscal year 2022.",
        "source_doc": "N/A",
        "category": "hallucination_trap",
    },
    {
        "id": "q027",
        "question": "Who is the CEO of Tesla?",
        "ground_truth": "The provided documents do not contain information about Tesla's CEO.",
        "source_doc": "N/A",
        "category": "hallucination_trap",
    },
    {
        "id": "q028",
        "question": "What was Microsoft's stock price on January 1, 2023?",
        "ground_truth": "The provided documents do not contain information about Microsoft's stock price.",
        "source_doc": "N/A",
        "category": "hallucination_trap",
    },
    {
        "id": "q029",
        "question": "How many employees does Amazon have?",
        "ground_truth": "The provided documents do not contain information about Amazon's employee count.",
        "source_doc": "N/A",
        "category": "hallucination_trap",
    },
    {
        "id": "q030",
        "question": "What is Alphabet's dividend yield?",
        "ground_truth": "The provided documents do not contain information about Alphabet's dividend yield.",
        "source_doc": "N/A",
        "category": "hallucination_trap",
    },
]


def load_golden_set(path: Optional[Path] = None) -> list[dict]:
    """Load golden set from JSON file, or return built-in sample set."""
    fpath = path or GOLDEN_SET_PATH
    if fpath.exists():
        with open(fpath) as f:
            data = json.load(f)
        console.print(f"[green]✓ Loaded {len(data)} golden questions from {fpath}[/green]")
        return data

    console.print(f"[yellow]No golden set found at {fpath}. Using built-in sample set ({len(SAMPLE_GOLDEN_SET)} questions).[/yellow]")
    return SAMPLE_GOLDEN_SET


def save_golden_set(questions: list[dict], path: Optional[Path] = None):
    """Save golden set to JSON."""
    fpath = path or GOLDEN_SET_PATH
    fpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fpath, "w") as f:
        json.dump(questions, f, indent=2)
    console.print(f"[green]✓ Saved {len(questions)} questions to {fpath}[/green]")


def generate_golden_set_from_pipeline(pipeline, questions: list[dict]) -> list[dict]:
    """
    Run the RAG pipeline on each question and attach the generated answer +
    retrieved contexts so the evaluator can score them later.
    """
    console.print(f"\n[bold]Generating RAG answers for {len(questions)} golden questions...[/bold]")
    results = []
    for q in questions:
        result = pipeline.query(q["question"])
        results.append({
            **q,
            "rag_answer": result["answer"],
            "contexts": result["contexts"],
        })
    return results