#!/usr/bin/env python3
"""
rag_pipeline.py — Full RAG + LLM pipeline.

Flow:
  1. User question
  2. BM25 retrieval → relevant Quran ayahs + Hadiths + Fiqh rulings
  3. Inject retrieved context into a structured prompt
  4. LLM generates a DETAILED EXPLANATION (with citations from context)
  5. LLM generates a CONCISE SUMMARY
  6. Return structured response

Usage:
    from rag_pipeline import IslamicRAGPipeline
    pipeline = IslamicRAGPipeline()
    response = pipeline.answer("What does Islam say about patience?")
    print(response.full_text())
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from rag_retriever import IslamicRetriever, RetrievalResult

OLLAMA_API_URL = "http://localhost:11434/v1/chat/completions"

# ─── Prompts ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Noor, a precise Islamic AI assistant. You answer ONLY from the "
    "Islamic sources provided in the context. Your rules:\n"
    "1. Always include the exact Arabic text from the retrieved sources.\n"
    "2. Always cite the exact reference (Surah:Ayah or Collection #Number).\n"
    "3. Always state the Hadith grade (Sahih, Hasan, etc.) when citing hadith.\n"
    "4. NEVER fabricate a Quran verse or Hadith number.\n"
    "5. If the retrieved sources do not contain an answer, say so clearly.\n"
    "6. Be scholarly, respectful, and thorough in your explanations.\n"
    "7. End your detailed explanation with a '--- SUMMARY ---' section."
)

DETAIL_PROMPT_TEMPLATE = """\
Using ONLY the Islamic sources below, answer the following question in detail.

Your response MUST include:
• The Arabic text of every Quran verse or Hadith you cite
• The exact Surah:Ayah or Collection #Number reference
• Ibn Kathir tafsir commentary where provided in the context
• The Hadith grade (Sahih / Hasan / Da'if) for every Hadith cited
• A detailed explanation connecting all sources to the question
• End with a section: --- SUMMARY --- (3-5 bullet points)

═══════════════════════════════════════════════════════
RETRIEVED ISLAMIC SOURCES:
{context}
═══════════════════════════════════════════════════════

QUESTION: {question}

ANSWER:"""


# ─── Response dataclass ──────────────────────────────────────────────────────

@dataclass
class RAGResponse:
    question:   str
    retrieval:  RetrievalResult
    llm_answer: str
    latency_s:  float
    model:      str
    error:      str = ""

    def full_text(self) -> str:
        parts: list[str] = []

        parts.append(f"Question: {self.question}\n")

        if self.retrieval.has_results():
            parts.append("━" * 60)
            parts.append("Retrieved Sources:")
            parts.append("━" * 60)
            for label in self.retrieval.citation_list():
                parts.append(f"  • {label}")
            parts.append("")

        if self.error:
            parts.append(f"[ERROR] {self.error}")
        else:
            parts.append("━" * 60)
            parts.append("Answer:")
            parts.append("━" * 60)
            parts.append(self.llm_answer)

        parts.append("")
        parts.append(f"[{self.model}  |  {self.latency_s:.1f}s]")
        return "\n".join(parts)

    def summary_only(self) -> str:
        """Return just the SUMMARY section if present."""
        marker = "--- SUMMARY ---"
        idx = self.llm_answer.upper().find("SUMMARY")
        if idx == -1:
            return self.llm_answer[-600:]
        return self.llm_answer[idx:]

    def detailed_only(self) -> str:
        """Return the explanation part before the summary."""
        idx = self.llm_answer.upper().find("SUMMARY")
        if idx == -1:
            return self.llm_answer
        return self.llm_answer[:idx].rstrip()

    def to_dict(self) -> dict:
        return {
            "question":  self.question,
            "citations": self.retrieval.citation_list(),
            "answer":    self.llm_answer,
            "summary":   self.summary_only(),
            "model":     self.model,
            "latency_s": self.latency_s,
            "error":     self.error,
        }


# ─── Pipeline ────────────────────────────────────────────────────────────────

class IslamicRAGPipeline:
    """
    Full RAG pipeline: retrieve → prompt → generate detailed explanation + summary.

    Args:
        model:       Ollama model name (default: 'noor' — your fine-tuned model).
                     Use 'llama3.2' for the base model before fine-tuning.
        top_k_quran: Max Quran ayahs to retrieve.
        top_k_hadith: Max Hadiths to retrieve.
        top_k_fiqh:  Max Fiqh/KB entries to retrieve.
        max_tokens:  Max tokens for LLM response.
        temperature: LLM sampling temperature (low = more focused).
        timeout:     HTTP timeout for Ollama in seconds.
    """

    def __init__(
        self,
        model:         str  = "noor",
        top_k_quran:   int  = 3,
        top_k_hadith:  int  = 4,
        top_k_fiqh:    int  = 2,
        max_tokens:    int  = 1500,
        temperature:   float = 0.1,
        timeout:       int  = 300,
        retriever:     IslamicRetriever | None = None,
    ) -> None:
        self.model       = model
        self.top_k_quran = top_k_quran
        self.top_k_hadith = top_k_hadith
        self.top_k_fiqh  = top_k_fiqh
        self.max_tokens  = max_tokens
        self.temperature = temperature
        self.timeout     = timeout
        self._retriever  = retriever or IslamicRetriever()

    def _call_llm(self, prompt: str) -> tuple[str, float]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens":  self.max_tokens,
            "temperature": self.temperature,
        }
        t0 = time.time()
        try:
            resp = requests.post(OLLAMA_API_URL, json=payload, timeout=self.timeout)
            latency = time.time() - t0
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip(), latency
            return f"[HTTP {resp.status_code}] {resp.text[:200]}", latency
        except requests.exceptions.ConnectionError:
            return "[ERROR: Ollama not running — run: ollama serve]", 0.0
        except Exception as exc:
            return f"[ERROR: {exc}]", 0.0

    def answer(
        self,
        question: str,
        sources: list[str] | None = None,
        rag_enabled: bool = True,
    ) -> RAGResponse:
        """
        Answer a question using RAG.

        Args:
            question:    The user's question.
            sources:     Limit retrieval to specific sources: ["quran", "hadith", "fiqh"].
                         None = use all three.
            rag_enabled: If False, skip retrieval and use LLM knowledge only.

        Returns:
            RAGResponse with detailed explanation + summary.
        """
        # Step 1: Retrieve
        if rag_enabled:
            retrieval = self._retriever.retrieve(
                query=question,
                top_k_quran=self.top_k_quran,
                top_k_hadith=self.top_k_hadith,
                top_k_fiqh=self.top_k_fiqh,
                sources=sources,
            )
        else:
            from rag_retriever import RetrievalResult
            retrieval = RetrievalResult(query=question)

        # Step 2: Build context-augmented prompt
        context = retrieval.format_context(
            max_quran=self.top_k_quran,
            max_hadith=self.top_k_hadith,
            max_fiqh=self.top_k_fiqh,
        ) if retrieval.has_results() else (
            "No specific sources retrieved. Use your Islamic knowledge to answer."
        )

        prompt = DETAIL_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        # Step 3: Generate
        answer, latency = self._call_llm(prompt)

        error = ""
        if answer.startswith("[ERROR") or answer.startswith("[HTTP"):
            error = answer
            answer = ""

        return RAGResponse(
            question=question,
            retrieval=retrieval,
            llm_answer=answer,
            latency_s=round(latency, 2),
            model=self.model,
            error=error,
        )

    def is_ollama_running(self) -> bool:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def available_models(self) -> list[str]:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []


if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "What does the Quran and Hadith say about patience during hardship?"
    )

    pipeline = IslamicRAGPipeline(model="llama3.2")

    if not pipeline.is_ollama_running():
        print("Ollama is not running. Start it: ollama serve")
        sys.exit(1)

    print(f"Question: {question}")
    print("Retrieving relevant sources...")
    response = pipeline.answer(question)
    print(response.full_text())
