"""
rag_pipeline/pipeline.py
Core RAG pipeline: document loading, chunking, embedding, ChromaDB storage, retrieval.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from rich.console import Console
from rich.progress import track
from langchain_community.llms import Ollama

load_dotenv()
console = Console()

# ── Prompt template ────────────────────────────────────────────────────────────
RAG_PROMPT = ChatPromptTemplate.from_template("""
You are a helpful assistant. Answer the question using ONLY the provided context.
If the context does not contain enough information, say "I don't have enough information
to answer this question based on the provided documents."

Context:
{context}

Question: {question}

Answer:""")


def get_embeddings():
    """Return embedding model based on EMBEDDING_PROVIDER env var."""
    provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    if provider == "openai":
        console.print(f"[dim]Using OpenAI embeddings: {model}[/dim]")
        return OpenAIEmbeddings(model=model)
    else:
        console.print(f"[dim]Using local HuggingFace embeddings: {model}[/dim]")
        return HuggingFaceEmbeddings(model_name=model)


class RAGPipeline:
    """
    Full RAG pipeline wrapping ChromaDB.

    Usage:
        pipeline = RAGPipeline()
        pipeline.ingest_documents(docs)
        result = pipeline.query("What is the revenue?")
    """

    def __init__(self, collection_name: Optional[str] = None):
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.collection_name = collection_name or os.getenv(
            "CHROMA_COLLECTION_NAME", "rag_documents"
        )
        self.chunk_size = int(os.getenv("CHUNK_SIZE", 512))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 64))
        self.top_k = int(os.getenv("TOP_K_RETRIEVAL", 5))

        self.embeddings = get_embeddings()
        self.llm = Ollama(model="llama3.2")
        self.vectorstore: Optional[Chroma] = None
        self._load_existing_vectorstore()

    # ── Vectorstore ─────────────────────────────────────────────────────────────

    def _load_existing_vectorstore(self):
        """Load ChromaDB if it already exists on disk."""
        if Path(self.persist_dir).exists():
            try:
                self.vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_dir,
                )
                count = self.vectorstore._collection.count()
                if count > 0:
                    console.print(
                        f"[green]✓ Loaded existing ChromaDB:[/green] {count} chunks in '{self.collection_name}'"
                    )
                    return
            except Exception:
                pass
        console.print("[yellow]No existing ChromaDB found. Run ingest_documents() first.[/yellow]")

    def ingest_documents(self, documents: list[Document]) -> int:
        """
        Chunk and embed documents into ChromaDB.
        Returns the number of chunks stored.
        """
        console.print(f"\n[bold]Ingesting {len(documents)} documents...[/bold]")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(documents)
        console.print(f"  Split into [cyan]{len(chunks)}[/cyan] chunks "
                      f"(size={self.chunk_size}, overlap={self.chunk_overlap})")

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_dir,
        )
        console.print(f"[green]✓ Stored {len(chunks)} chunks in ChromaDB[/green] → {self.persist_dir}")
        return len(chunks)

    def add_documents(self, documents: list[Document]) -> int:
        """Append new documents to an existing vectorstore."""
        if not self.vectorstore:
            return self.ingest_documents(documents)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        self.vectorstore.add_documents(chunks)
        console.print(f"[green]✓ Added {len(chunks)} chunks to existing collection[/green]")
        return len(chunks)

    # ── Retrieval ────────────────────────────────────────────────────────────────

    def retrieve(self, question: str, top_k: Optional[int] = None) -> list[Document]:
        """Return top-k most relevant chunks for a question."""
        if not self.vectorstore:
            raise RuntimeError("No vectorstore loaded. Call ingest_documents() first.")
        k = top_k or self.top_k
        return self.vectorstore.similarity_search(question, k=k)

    def retrieve_with_scores(self, question: str, top_k: Optional[int] = None):
        """Return chunks with relevance scores [(Document, score), ...]."""
        if not self.vectorstore:
            raise RuntimeError("No vectorstore loaded. Call ingest_documents() first.")
        k = top_k or self.top_k
        return self.vectorstore.similarity_search_with_relevance_scores(question, k=k)

    # ── Generation ───────────────────────────────────────────────────────────────

    def query(self, question: str, top_k: Optional[int] = None) -> dict:
        """
        Full RAG: retrieve → format context → generate answer.

        Returns:
            {
                "question": str,
                "answer": str,
                "contexts": [str, ...],          # text of retrieved chunks
                "source_documents": [Document],  # full Document objects
            }
        """
        if not self.vectorstore:
            raise RuntimeError("No vectorstore loaded. Call ingest_documents() first.")

        source_documents = self.retrieve(question, top_k=top_k)
        context_text = "\n\n---\n\n".join(doc.page_content for doc in source_documents)

        chain = (
            {"context": lambda _: context_text, "question": RunnablePassthrough()}
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )
        answer = chain.invoke(question)

        return {
            "question": question,
            "answer": answer,
            "contexts": [doc.page_content for doc in source_documents],
            "source_documents": source_documents,
        }

    # ── Utilities ─────────────────────────────────────────────────────────────────

    def collection_info(self) -> dict:
        """Return metadata about the current collection."""
        if not self.vectorstore:
            return {"status": "empty", "count": 0}
        count = self.vectorstore._collection.count()
        return {
            "status": "loaded",
            "collection": self.collection_name,
            "persist_dir": self.persist_dir,
            "chunk_count": count,
        }

    def reset_collection(self):
        """Delete all documents from the collection (for re-ingestion)."""
        if self.vectorstore:
            self.vectorstore.delete_collection()
            self.vectorstore = None
            console.print("[yellow]Collection deleted.[/yellow]")# Chunk size and overlap configurable via .env
