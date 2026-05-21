#!/usr/bin/env python3
"""
rag_retriever.py — BM25-powered retrieval engine for Quran, Hadith, and Fiqh.

Loads the pre-built BM25 indices from rag_index/ and answers queries by
returning the top-k most relevant passages from each corpus.

Usage:
    from rag_retriever import IslamicRetriever
    r = IslamicRetriever()
    results = r.retrieve("What does Islam say about patience?", top_k=3)
    print(results.format_context())
"""

from __future__ import annotations

import json
import pickle
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    raise ImportError("Install rank_bm25:  pip install rank-bm25")

INDEX_DIR = Path(__file__).parent / "rag_index"

Source = Literal["quran", "hadith", "fiqh"]


@dataclass
class RetrievedDoc:
    source:  Source
    score:   float
    doc:     dict

    def ref_label(self) -> str:
        if self.source == "quran":
            s = self.doc.get("surah_name", "")
            r = self.doc.get("ref", "")
            return f"Quran {r} — {s}"
        if self.source == "hadith":
            col = self.doc.get("collection", "")
            num = self.doc.get("number", "")
            grade = self.doc.get("grade", "")
            return f"{col} #{num}" + (f" ({grade})" if grade else "")
        topic = self.doc.get("topic", self.doc.get("file", ""))
        return f"Fiqh: {topic}"

    def arabic(self) -> str:
        return self.doc.get("arabic", "")

    def english(self) -> str:
        if self.source == "quran":
            return self.doc.get("translation", "")
        if self.source == "hadith":
            return self.doc.get("english", "")
        return self.doc.get("content", "")[:600]

    def tafsir(self) -> str:
        return self.doc.get("tafsir", "")[:400] if self.source == "quran" else ""

    def format_block(self, index: int) -> str:
        lines = [f"[{index}] {self.ref_label()}"]
        ar = self.arabic()
        en = self.english()
        tf = self.tafsir()
        if ar:
            lines.append(f"Arabic: {ar}")
        if en:
            lines.append(f"Text  : {en}")
        if tf:
            lines.append(f"Tafsir: {tf}")
        return "\n".join(lines)


@dataclass
class RetrievalResult:
    query:   str
    quran:   list[RetrievedDoc] = field(default_factory=list)
    hadith:  list[RetrievedDoc] = field(default_factory=list)
    fiqh:    list[RetrievedDoc] = field(default_factory=list)

    @property
    def all_docs(self) -> list[RetrievedDoc]:
        return self.quran + self.hadith + self.fiqh

    def has_results(self) -> bool:
        return bool(self.quran or self.hadith or self.fiqh)

    def format_context(self, max_quran: int = 3, max_hadith: int = 3, max_fiqh: int = 2) -> str:
        """Return a formatted context block ready to inject into the LLM prompt."""
        sections: list[str] = []

        if self.quran[:max_quran]:
            sections.append("── QURAN REFERENCES ──────────────────────────")
            for i, doc in enumerate(self.quran[:max_quran], 1):
                sections.append(doc.format_block(i))

        if self.hadith[:max_hadith]:
            sections.append("── HADITH REFERENCES ─────────────────────────")
            for i, doc in enumerate(self.hadith[:max_hadith], 1):
                sections.append(doc.format_block(i))

        if self.fiqh[:max_fiqh]:
            sections.append("── FIQH / SCHOLARLY KNOWLEDGE ────────────────")
            for i, doc in enumerate(self.fiqh[:max_fiqh], 1):
                sections.append(doc.format_block(i))

        return "\n\n".join(sections)

    def citation_list(self) -> list[str]:
        return [d.ref_label() for d in self.all_docs]


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s؀-ۿ]", " ", text)
    return [t for t in text.split() if len(t) > 1]


class IslamicRetriever:
    """
    Lazy-loading BM25 retriever across Quran, Hadith, and Fiqh corpora.
    Call retrieve() to get relevant passages for any query.
    """

    def __init__(self, index_dir: Path | None = None) -> None:
        self._dir = index_dir or INDEX_DIR
        self._quran_bm25:  BM25Okapi | None = None
        self._hadith_bm25: BM25Okapi | None = None
        self._fiqh_bm25:   BM25Okapi | None = None
        self._quran_docs:  list[dict] = []
        self._hadith_docs: list[dict] = []
        self._fiqh_docs:   list[dict] = []
        self._loaded: set[str] = set()

    def _load_corpus(self, name: str) -> None:
        if name in self._loaded:
            return
        docs_path = self._dir / f"{name}_docs.json"
        bm25_path = self._dir / f"{name}_bm25.pkl"

        if not docs_path.exists() or not bm25_path.exists():
            print(f"[WARN] RAG index for '{name}' not found at {self._dir}.")
            print(f"       Run: python build_rag_index.py")
            self._loaded.add(name)
            return

        docs = json.loads(docs_path.read_text(encoding="utf-8"))
        with open(bm25_path, "rb") as f:
            bm25 = pickle.load(f)

        if name == "quran":
            self._quran_docs, self._quran_bm25 = docs, bm25
        elif name == "hadith":
            self._hadith_docs, self._hadith_bm25 = docs, bm25
        elif name == "fiqh":
            self._fiqh_docs, self._fiqh_bm25 = docs, bm25

        self._loaded.add(name)

    def _search(
        self,
        query: str,
        source: Source,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[RetrievedDoc]:
        self._load_corpus(source)

        if source == "quran":
            bm25, docs = self._quran_bm25, self._quran_docs
        elif source == "hadith":
            bm25, docs = self._hadith_bm25, self._hadith_docs
        else:
            bm25, docs = self._fiqh_bm25, self._fiqh_docs

        if bm25 is None or not docs:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = bm25.get_scores(tokens)
        ranked = sorted(
            ((float(s), i) for i, s in enumerate(scores) if float(s) > min_score),
            reverse=True,
        )[:top_k]

        return [
            RetrievedDoc(source=source, score=score, doc=docs[idx])
            for score, idx in ranked
        ]

    def retrieve(
        self,
        query: str,
        top_k_quran:  int = 3,
        top_k_hadith: int = 4,
        top_k_fiqh:   int = 2,
        min_score:    float = 0.5,
        sources: list[Source] | None = None,
    ) -> RetrievalResult:
        """
        Retrieve the most relevant Quran, Hadith, and Fiqh passages for a query.

        Args:
            query:        The user's question (in any language — English works best).
            top_k_quran:  Max Quran ayahs to return.
            top_k_hadith: Max hadiths to return.
            top_k_fiqh:   Max fiqh/KB entries to return.
            min_score:    Minimum BM25 score — filters low-relevance docs.
            sources:      Limit to specific sources, e.g. ["quran", "hadith"].

        Returns:
            RetrievalResult with ranked docs from each corpus.
        """
        active = set(sources) if sources else {"quran", "hadith", "fiqh"}
        result = RetrievalResult(query=query)

        if "quran" in active:
            result.quran  = self._search(query, "quran",  top_k_quran,  min_score)
        if "hadith" in active:
            result.hadith = self._search(query, "hadith", top_k_hadith, min_score)
        if "fiqh" in active:
            result.fiqh   = self._search(query, "fiqh",   top_k_fiqh,   min_score)

        return result

    def index_status(self) -> dict:
        meta_path = self._dir / "index_meta.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))
        return {"status": "index not built — run build_rag_index.py"}


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What does Islam say about patience?"
    print(f"Query: {query}\n")

    r = IslamicRetriever()
    status = r.index_status()
    if "status" in status:
        print(status["status"])
        sys.exit(1)

    print(f"Index: {status['total_docs']:,} docs  (built {status['built_at'][:10]})\n")
    results = r.retrieve(query)
    print(results.format_context())
    print(f"\nCitations: {results.citation_list()}")
