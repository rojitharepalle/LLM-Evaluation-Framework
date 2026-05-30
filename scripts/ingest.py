"""
scripts/ingest.py
Run this first to load data into ChromaDB and verify your setup.

Usage:
    python scripts/ingest.py              # use sample data (no API needed)
    python scripts/ingest.py --financebench   # use FinanceBench dataset
    python scripts/ingest.py --pdf ./data/    # load your own PDFs
"""

import argparse
import sys
from pathlib import Path

from rag_pipeline import pipeline

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


def main():
    parser.add_argument("--skip-test", action="store_true", help="Skip test query (use in CI)")
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB")
    parser.add_argument("--financebench", action="store_true", help="Load FinanceBench dataset")
    parser.add_argument("--pdf", type=str, help="Path to directory of PDF files")
    parser.add_argument("--max-docs", type=int, default=200, help="Max documents to load")
    parser.add_argument("--reset", action="store_true", help="Reset collection before ingesting")
    args = parser.parse_args()

    from rag_pipeline.pipeline import RAGPipeline
    from rag_pipeline.data_loader import (
        load_sample_data, load_financebench, load_pdfs
    )

    pipeline = RAGPipeline()

    if args.reset:
        pipeline.reset_collection()

    # Choose data source
    if args.financebench:
        docs = load_financebench(max_docs=args.max_docs)
    elif args.pdf:
        docs = load_pdfs(args.pdf)
    else:
        console.print(Panel(
            "[bold]Using built-in sample data[/bold]\n"
            "5 financial reports: Apple, Microsoft, Amazon, Tesla, Alphabet\n\n"
            "To use real data, run:\n"
            "  python scripts/ingest.py --financebench\n"
            "  python scripts/ingest.py --pdf ./your-pdfs/",
            title="Data Source",
            border_style="dim",
        ))
        docs = load_sample_data()

    if not docs:
        console.print("[red]No documents loaded. Exiting.[/red]")
        sys.exit(1)

    # Ingest
    chunk_count = pipeline.ingest_documents(docs)

# Verify with a test query (skip in CI where Ollama is not available)
if not args.skip_test:
    console.print("\n[bold]Running test query...[/bold]")
    result = pipeline.query("What was the highest revenue company in 2022?")
else:
    console.print("[dim]Skipping test query (--skip-test)[/dim]")
    result = {"answer": "skipped", "contexts": []}

    # Summary table
    table = Table(title="Ingestion Summary", show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Documents loaded[/dim]", f"[cyan]{len(docs)}[/cyan]")
    table.add_row("[dim]Chunks stored[/dim]", f"[cyan]{chunk_count}[/cyan]")
    table.add_row("[dim]Collection[/dim]", f"[cyan]{pipeline.collection_name}[/cyan]")
    table.add_row("[dim]Persist dir[/dim]", f"[cyan]{pipeline.persist_dir}[/cyan]")
    console.print(table)

    console.print("\n[bold]Test answer:[/bold]")
    console.print(f"[green]{result['answer']}[/green]")
    console.print(f"\n[dim]Retrieved {len(result['contexts'])} chunks[/dim]")

    console.print(Panel(
        "[bold green]Setup complete![/bold green]\n\n"
        "Next steps:\n"
        "  1. Start the API:  [cyan]uvicorn rag_pipeline.api:app --reload[/cyan]\n"
        "  2. Open docs:      [cyan]http://localhost:8000/docs[/cyan]\n"
        "  3. Run evals:      [cyan]python scripts/run_eval.py[/cyan]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()