"""
evaluation/evaluator.py

Scores the RAG pipeline using two frameworks:
  - RAGAS  : faithfulness, answer_relevancy, context_recall
  - DeepEval: hallucination detector (custom + built-in)

All results saved to evaluation/results/ as JSON with timestamps.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

load_dotenv()
console = Console()

RESULTS_DIR = Path("./evaluation/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── RAGAS Evaluator ────────────────────────────────────────────────────────────

class RAGASEvaluator:
    """
    Scores a set of RAG outputs using RAGAS metrics.

    Metrics:
      - faithfulness     : Is the answer supported by the retrieved context?
      - answer_relevancy : Does the answer address the question?
      - context_recall   : Were the right chunks retrieved? (needs ground_truth)
    """

    def __init__(self):
        self._check_imports()

    def _check_imports(self):
        try:
            import ragas
        except ImportError:
            console.print("[red]RAGAS not installed. Run: pip install ragas[/red]")
            sys.exit(1)

    def _build_dataset(self, results: list[dict]):
        """Convert pipeline results into a RAGAS EvaluationDataset."""
        from ragas import EvaluationDataset, SingleTurnSample

        samples = []
        for r in results:
            samples.append(SingleTurnSample(
                user_input=r["question"],
                response=r["rag_answer"],
                retrieved_contexts=r["contexts"],
                reference=r.get("ground_truth", ""),
            ))
        return EvaluationDataset(samples=samples)

    def evaluate(self, results: list[dict], use_ollama: bool = True) -> dict:
        """
        Run RAGAS evaluation.

        Args:
            results: list of dicts with keys:
                     question, rag_answer, contexts, ground_truth
            use_ollama: if True use local Ollama; else use OpenAI

        Returns:
            dict of metric_name -> score (0.0 to 1.0)
        """
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_recall

        console.print("\n[bold cyan]Running RAGAS evaluation...[/bold cyan]")

        # Configure LLM for RAGAS
        if use_ollama:
            llm, embeddings = self._get_ollama_config()
        else:
            llm, embeddings = self._get_openai_config()

        dataset = self._build_dataset(results)

        metrics = [faithfulness, answer_relevancy, context_recall]

        # Inject LLM into metrics
        for metric in metrics:
            if hasattr(metric, 'llm'):
                metric.llm = llm
            if hasattr(metric, 'embeddings'):
                metric.embeddings = embeddings

        try:
            eval_result = evaluate(dataset=dataset, metrics=metrics)
            scores = {
                "faithfulness": round(float(eval_result["faithfulness"]), 4),
                "answer_relevancy": round(float(eval_result["answer_relevancy"]), 4),
                "context_recall": round(float(eval_result["context_recall"]), 4),
            }
        except Exception as e:
            console.print(f"[yellow]RAGAS evaluation warning: {e}[/yellow]")
            console.print("[yellow]Falling back to per-question scoring...[/yellow]")
            scores = self._fallback_scoring(results)

        return scores

    def _get_ollama_config(self):
        """Configure RAGAS to use local Ollama."""
        try:
            from langchain_ollama import OllamaLLM
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from ragas.llms import LangchainLLMWrapper
            from ragas.embeddings import LangchainEmbeddingsWrapper

            llm = LangchainLLMWrapper(OllamaLLM(model="llama3.2"))
            embeddings = LangchainEmbeddingsWrapper(
                HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            )
            console.print("[dim]RAGAS using: Ollama llama3.2 + HuggingFace embeddings[/dim]")
            return llm, embeddings
        except Exception:
            from langchain_community.llms import Ollama
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from ragas.llms import LangchainLLMWrapper
            from ragas.embeddings import LangchainEmbeddingsWrapper

            llm = LangchainLLMWrapper(Ollama(model="llama3.2"))
            embeddings = LangchainEmbeddingsWrapper(
                HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            )
            return llm, embeddings

    def _get_openai_config(self):
        """Configure RAGAS to use OpenAI."""
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper

        llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini", temperature=0))
        embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
        console.print("[dim]RAGAS using: OpenAI gpt-4o-mini[/dim]")
        return llm, embeddings

    def _fallback_scoring(self, results: list[dict]) -> dict:
        """
        Simple rule-based fallback if RAGAS LLM scoring fails.
        Not as accurate but gives meaningful signal.
        """
        faithfulness_scores = []
        relevancy_scores = []
        recall_scores = []

        for r in results:
            answer = r["rag_answer"].lower()
            question = r["question"].lower()
            ground_truth = r.get("ground_truth", "").lower()
            contexts = " ".join(r["contexts"]).lower()

            # Faithfulness: key answer words appear in context
            answer_words = set(answer.split()) - {"the", "a", "an", "is", "was", "of", "in", "to"}
            context_words = set(contexts.split())
            overlap = len(answer_words & context_words) / max(len(answer_words), 1)
            faithfulness_scores.append(min(overlap * 2, 1.0))

            # Answer relevancy: question keywords appear in answer
            q_words = set(question.split()) - {"what", "how", "when", "where", "why", "was", "is", "the", "a"}
            a_words = set(answer.split())
            relevancy = len(q_words & a_words) / max(len(q_words), 1)
            relevancy_scores.append(min(relevancy * 1.5, 1.0))

            # Context recall: ground truth words appear in context
            if ground_truth:
                gt_words = set(ground_truth.split()) - {"the", "a", "an", "is", "was", "of", "in", "to"}
                recall = len(gt_words & context_words) / max(len(gt_words), 1)
                recall_scores.append(min(recall * 1.5, 1.0))

        return {
            "faithfulness": round(sum(faithfulness_scores) / max(len(faithfulness_scores), 1), 4),
            "answer_relevancy": round(sum(relevancy_scores) / max(len(relevancy_scores), 1), 4),
            "context_recall": round(sum(recall_scores) / max(len(recall_scores), 1), 4) if recall_scores else 0.0,
        }


# ── DeepEval Hallucination Detector ───────────────────────────────────────────

class HallucinationDetector:
    """
    Detects hallucinations per question using two approaches:
      1. DeepEval's HallucinationMetric (LLM-based, most accurate)
      2. Rule-based fallback (no LLM needed, fast)

    Hallucination = answer contains claims not supported by retrieved context.
    """

    def __init__(self, use_deepeval: bool = True):
        self.use_deepeval = use_deepeval
        if use_deepeval:
            self._check_deepeval()

    def _check_deepeval(self):
        try:
            import deepeval
        except ImportError:
            console.print("[yellow]DeepEval not installed. Using rule-based hallucination detection.[/yellow]")
            console.print("[dim]To install: pip install deepeval[/dim]")
            self.use_deepeval = False

    def score_all(self, results: list[dict]) -> list[dict]:
        """
        Score each result for hallucination.

        Returns results with added keys:
          - hallucination_score: 0.0 (no hallucination) to 1.0 (full hallucination)
          - hallucination_flag: True if score > threshold
          - hallucination_reason: explanation string
        """
        console.print("\n[bold cyan]Running hallucination detection...[/bold cyan]")

        if self.use_deepeval:
            return self._deepeval_score(results)
        else:
            return self._rule_based_score(results)

    def _deepeval_score(self, results: list[dict]) -> list[dict]:
        """Use DeepEval's HallucinationMetric."""
        try:
            from deepeval.metrics import HallucinationMetric
            from deepeval.test_case import LLMTestCase
            from deepeval.models.base_model import DeepEvalBaseLLM
            from langchain_community.llms import Ollama

            class OllamaWrapper(DeepEvalBaseLLM):
                def __init__(self):
                    self.model = Ollama(model="llama3.2")

                def load_model(self):
                    return self.model

                def generate(self, prompt: str) -> str:
                    return self.model.invoke(prompt)

                async def a_generate(self, prompt: str) -> str:
                    return self.generate(prompt)

                def get_model_name(self) -> str:
                    return "ollama/llama3.2"

            ollama_model = OllamaWrapper()
            metric = HallucinationMetric(threshold=0.5, model=ollama_model)

            scored = []
            for r in results:
                try:
                    test_case = LLMTestCase(
                        input=r["question"],
                        actual_output=r["rag_answer"],
                        context=r["contexts"],
                    )
                    metric.measure(test_case)
                    score = metric.score
                    scored.append({
                        **r,
                        "hallucination_score": round(score, 4),
                        "hallucination_flag": score > 0.5,
                        "hallucination_reason": metric.reason or "DeepEval scored",
                    })
                except Exception as e:
                    # Fall back to rule-based for this question
                    rb = self._rule_based_single(r)
                    scored.append(rb)

            return scored

        except Exception as e:
            console.print(f"[yellow]DeepEval error: {e}. Using rule-based fallback.[/yellow]")
            return self._rule_based_score(results)

    def _rule_based_score(self, results: list[dict]) -> list[dict]:
        """
        Rule-based hallucination detection — no LLM needed.

        Flags hallucination when:
          - Answer contains specific numbers/entities NOT in context
          - Answer confidently answers a hallucination_trap question
          - Answer length >> context (model is fabricating detail)
        """
        scored = []
        for r in results:
            scored.append(self._rule_based_single(r))
        return scored

    def _rule_based_single(self, r: dict) -> dict:
        answer = r["rag_answer"].lower()
        contexts = " ".join(r["contexts"]).lower()
        category = r.get("category", "")

        score = 0.0
        reasons = []

        # Rule 1: Hallucination trap — model should say "I don't have information"
        if category == "hallucination_trap":
            refusal_phrases = [
                "don't have", "do not have", "not contain", "no information",
                "cannot find", "not mentioned", "not provided", "not in the"
            ]
            if not any(phrase in answer for phrase in refusal_phrases):
                score += 0.7
                reasons.append("Model answered a trap question instead of refusing")
            else:
                score += 0.0
                reasons.append("Correctly refused to answer out-of-scope question")

        # Rule 2: Numbers in answer not found in context
        import re
        answer_numbers = set(re.findall(r'\$[\d,.]+|\b\d+\.?\d*\s*(?:billion|million|percent|%)\b', answer))
        context_numbers = set(re.findall(r'\$[\d,.]+|\b\d+\.?\d*\s*(?:billion|million|percent|%)\b', contexts))
        hallucinated_numbers = answer_numbers - context_numbers
        if hallucinated_numbers:
            score += min(0.3 * len(hallucinated_numbers), 0.5)
            reasons.append(f"Numbers not in context: {hallucinated_numbers}")

        # Rule 3: Answer is much longer than context suggests
        context_word_count = len(contexts.split())
        answer_word_count = len(answer.split())
        if answer_word_count > 150 and answer_word_count > context_word_count * 0.5:
            score += 0.2
            reasons.append("Answer unusually long relative to context")

        score = min(score, 1.0)

        return {
            **r,
            "hallucination_score": round(score, 4),
            "hallucination_flag": score > 0.4,
            "hallucination_reason": "; ".join(reasons) if reasons else "No hallucination detected",
        }

    def hallucination_rate(self, scored_results: list[dict]) -> float:
        """Return fraction of questions with hallucination_flag=True."""
        if not scored_results:
            return 0.0
        flagged = sum(1 for r in scored_results if r.get("hallucination_flag", False))
        return round(flagged / len(scored_results), 4)# Hallucination threshold: 0.4 rule-based, 0.5 DeepEval
