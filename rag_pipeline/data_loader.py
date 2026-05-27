"""
rag_pipeline/data_loader.py
Load documents from multiple sources:
  - HuggingFace dataset (FinanceBench, Wikipedia subsets)
  - Local PDF files
  - Local text / markdown files
  - Raw text strings (for testing)
"""

import os
from pathlib import Path
from typing import Optional

from langchain.schema import Document
from rich.console import Console
from rich.progress import track

console = Console()


# ── HuggingFace datasets ──────────────────────────────────────────────────────

def load_financebench(max_docs: int = 200) -> list[Document]:
    """
    Load FinanceBench — a public financial QA dataset with annual report passages.
    Source: https://huggingface.co/datasets/PatronusAI/financebench
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Run: pip install datasets")

    console.print("[bold]Loading FinanceBench dataset...[/bold]")
    ds = load_dataset("PatronusAI/financebench", split="train", trust_remote_code=True)

    docs = []
    for row in track(list(ds)[:max_docs], description="Converting to Documents"):
        # evidence can be a list of strings or a single string depending on dataset version
        evidence = row.get("evidence", "") or row.get("answer", "")
        if isinstance(evidence, list):
            content = " ".join([e if isinstance(e, str) else str(e) for e in evidence])
        else:
            content = str(evidence) if evidence else ""
        if not content.strip():
            continue
        docs.append(Document(
            page_content=content,
            metadata={
                "source": "financebench",
                "doc_name": row.get("doc_name", "unknown"),
                "page_num": row.get("page_num", 0),
                "question": row.get("question", ""),
            }
        ))

    console.print(f"[green]✓ Loaded {len(docs)} FinanceBench passages[/green]")
    return docs


def load_wikipedia_subset(topic: str = "financial statements", max_docs: int = 100) -> list[Document]:
    """
    Load Wikipedia articles on a topic using HuggingFace wikipedia dataset.
    Good for testing when FinanceBench is too large.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Run: pip install datasets")

    console.print(f"[bold]Loading Wikipedia subset: '{topic}'...[/bold]")
    ds = load_dataset(
        "wikipedia",
        "20220301.en",
        split="train",
        streaming=True,
        trust_remote_code=True,
    )

    docs = []
    for row in ds:
        if topic.lower() in row["title"].lower() or topic.lower() in row["text"].lower()[:500]:
            docs.append(Document(
                page_content=row["text"][:3000],  # cap per article
                metadata={"source": "wikipedia", "title": row["title"], "url": row["url"]}
            ))
        if len(docs) >= max_docs:
            break

    console.print(f"[green]✓ Loaded {len(docs)} Wikipedia articles[/green]")
    return docs


# ── Local files ───────────────────────────────────────────────────────────────

def load_pdfs(directory: str) -> list[Document]:
    """Load all PDFs from a directory."""
    try:
        from langchain_community.document_loaders import PyPDFLoader
    except ImportError:
        raise ImportError("Run: pip install pypdf langchain-community")

    pdf_files = list(Path(directory).glob("**/*.pdf"))
    if not pdf_files:
        console.print(f"[yellow]No PDFs found in {directory}[/yellow]")
        return []

    docs = []
    for pdf_path in track(pdf_files, description="Loading PDFs"):
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        for page in pages:
            page.metadata["file_name"] = pdf_path.name
        docs.extend(pages)

    console.print(f"[green]✓ Loaded {len(docs)} pages from {len(pdf_files)} PDFs[/green]")
    return docs


def load_text_files(directory: str, extensions: list[str] = None) -> list[Document]:
    """Load .txt and .md files from a directory."""
    extensions = extensions or [".txt", ".md"]
    files = []
    for ext in extensions:
        files.extend(Path(directory).glob(f"**/*{ext}"))

    docs = []
    for file_path in track(files, description="Loading text files"):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        docs.append(Document(
            page_content=text,
            metadata={"source": str(file_path), "file_name": file_path.name}
        ))

    console.print(f"[green]✓ Loaded {len(docs)} text files[/green]")
    return docs


def load_raw_texts(texts: list[dict]) -> list[Document]:
    """
    Load from a list of dicts: [{"text": "...", "metadata": {...}}, ...]
    Useful for testing or custom data pipelines.
    """
    return [
        Document(page_content=item["text"], metadata=item.get("metadata", {}))
        for item in texts
    ]


# ── Sample dataset for quick testing ─────────────────────────────────────────

SAMPLE_FINANCIAL_TEXTS = [
    {
        "text": """Apple Inc. reported total net sales of $394.3 billion for fiscal year 2022,
        compared to $365.8 billion in fiscal year 2021, an increase of 7.8%.
        iPhone revenue was $205.5 billion, representing 52.1% of total net sales.
        Services revenue reached a record $78.1 billion, growing 14.2% year-over-year.
        The company returned over $90 billion to shareholders through dividends and share repurchases.""",
        "metadata": {"source": "sample", "company": "Apple", "year": "2022", "doc_type": "annual_report"}
    },
    {
        "text": """Microsoft Corporation's fiscal year 2023 revenue was $211.9 billion,
        up 7% year-over-year. Cloud revenue including Azure grew 27% to $87.9 billion.
        Intelligent Cloud segment revenue was $87.9 billion. More Personal Computing revenue
        was $54.7 billion. The company's operating income was $88.5 billion.""",
        "metadata": {"source": "sample", "company": "Microsoft", "year": "2023", "doc_type": "annual_report"}
    },
    {
        "text": """Amazon's total net sales for 2022 were $514.0 billion, an increase of 9% compared
        to 2021. AWS net sales grew 29% to $80.1 billion. Advertising services revenue was
        $37.7 billion. Amazon Prime has over 200 million members worldwide.
        Operating income decreased to $12.2 billion from $24.9 billion in 2021,
        primarily due to inflationary pressures and investments in fulfillment capacity.""",
        "metadata": {"source": "sample", "company": "Amazon", "year": "2022", "doc_type": "annual_report"}
    },
    {
        "text": """Tesla reported record revenue of $81.5 billion for fiscal year 2022,
        up 51% from 2021. The company delivered 1.31 million vehicles globally.
        Automotive gross margin was 28.5%. Energy generation and storage revenue
        grew 40% to $3.9 billion. Free cash flow was $7.6 billion.
        Tesla's Gigafactory in Austin, Texas began production of the Model Y.""",
        "metadata": {"source": "sample", "company": "Tesla", "year": "2022", "doc_type": "annual_report"}
    },
    {
        "text": """Alphabet Inc. (Google) reported revenues of $282.8 billion for fiscal 2022,
        a 10% increase from 2021. Google Search and other revenues were $162.5 billion.
        YouTube advertising revenues were $29.2 billion. Google Cloud revenues grew 37%
        to $26.3 billion. The company had operating income of $74.8 billion.
        Research and development expenses were $39.5 billion.""",
        "metadata": {"source": "sample", "company": "Alphabet", "year": "2022", "doc_type": "annual_report"}
    },
]


def load_sample_data() -> list[Document]:
    """Load built-in sample financial documents for quick testing."""
    docs = load_raw_texts(SAMPLE_FINANCIAL_TEXTS)
    console.print(f"[green]✓ Loaded {len(docs)} sample financial documents[/green]")
    return docs# Supported sources: FinanceBench, Wikipedia, PDFs, raw text
