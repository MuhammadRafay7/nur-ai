#!/usr/bin/env python3
"""
api_server.py — FastAPI server exposing the RAG pipeline as a REST API.

Endpoints:
    POST /chat          — RAG-powered question answering
    POST /chat/stream   — streaming version (future)
    GET  /health        — health check
    GET  /index/status  — RAG index statistics
    GET  /docs          — Swagger UI (auto-generated)

Usage:
    python api_server.py
    python api_server.py --model noor --port 8000

Test:
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d '{"question": "What does Islam say about patience?"}'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn[standard]")
    sys.exit(1)

from rag_pipeline import IslamicRAGPipeline

# ─── App setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Noor Islamic AI — RAG API",
    description=(
        "REST API for the Noor Islamic AI assistant. "
        "Retrieves relevant Quran, Hadith, and Fiqh sources via BM25, "
        "then generates detailed explanations with a summary."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline (initialised once at startup)
_pipeline: IslamicRAGPipeline | None = None


# ─── Request / Response models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000,
                          example="What does Islam say about patience?")
    sources:  list[str] | None = Field(
        default=None,
        example=["quran", "hadith", "fiqh"],
        description="Limit retrieval to specific sources. Omit for all three.",
    )
    rag_enabled: bool = Field(
        default=True,
        description="Set false to skip retrieval and use LLM knowledge only.",
    )
    top_k_quran:  int = Field(default=3, ge=0, le=10)
    top_k_hadith: int = Field(default=4, ge=0, le=10)
    top_k_fiqh:   int = Field(default=2, ge=0, le=10)


class SourceItem(BaseModel):
    ref:     str
    source:  str
    arabic:  str
    english: str
    tafsir:  str = ""


class ChatResponse(BaseModel):
    question:    str
    answer:      str
    summary:     str
    citations:   list[str]
    sources:     list[SourceItem]
    model:       str
    latency_s:   float
    rag_enabled: bool


class HealthResponse(BaseModel):
    status:     str
    ollama_ok:  bool
    model:      str
    index_docs: int


class IndexStatusResponse(BaseModel):
    built_at:    str
    quran_docs:  int
    hadith_docs: int
    fiqh_docs:   int
    total_docs:  int


# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event() -> None:
    global _pipeline
    model = app.state.model if hasattr(app.state, "model") else "noor"
    top_k_q = getattr(app.state, "top_k_quran",  3)
    top_k_h = getattr(app.state, "top_k_hadith", 4)
    top_k_f = getattr(app.state, "top_k_fiqh",   2)
    _pipeline = IslamicRAGPipeline(
        model=model,
        top_k_quran=top_k_q,
        top_k_hadith=top_k_h,
        top_k_fiqh=top_k_f,
    )
    print(f"Pipeline ready. Model: {model}")
    status = _pipeline._retriever.index_status()
    if "total_docs" in status:
        print(f"RAG index: {status['total_docs']:,} docs  (built {status['built_at'][:10]})")
    else:
        print("RAG index not found. Run: python build_rag_index.py")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not initialised")
    status = _pipeline._retriever.index_status()
    total  = status.get("total_docs", 0)
    return HealthResponse(
        status="ok",
        ollama_ok=_pipeline.is_ollama_running(),
        model=_pipeline.model,
        index_docs=total,
    )


@app.get("/index/status", response_model=IndexStatusResponse)
async def index_status() -> IndexStatusResponse:
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not initialised")
    s = _pipeline._retriever.index_status()
    if "status" in s:
        raise HTTPException(503, s["status"])
    return IndexStatusResponse(**s)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not initialised")

    if not _pipeline.is_ollama_running():
        raise HTTPException(503, "Ollama is not running — run: ollama serve")

    # Override pipeline top-k per request if specified
    _pipeline.top_k_quran  = req.top_k_quran
    _pipeline.top_k_hadith = req.top_k_hadith
    _pipeline.top_k_fiqh   = req.top_k_fiqh

    response = _pipeline.answer(
        question=req.question,
        sources=req.sources,
        rag_enabled=req.rag_enabled,
    )

    if response.error:
        raise HTTPException(502, response.error)

    # Build source detail list
    sources_list: list[SourceItem] = []
    for doc in response.retrieval.all_docs:
        sources_list.append(SourceItem(
            ref=doc.ref_label(),
            source=doc.source,
            arabic=doc.arabic(),
            english=doc.english()[:500],
            tafsir=doc.tafsir(),
        ))

    return ChatResponse(
        question=req.question,
        answer=response.detailed_only(),
        summary=response.summary_only(),
        citations=response.retrieval.citation_list(),
        sources=sources_list,
        model=response.model,
        latency_s=response.latency_s,
        rag_enabled=req.rag_enabled,
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Noor RAG API server")
    parser.add_argument("--model",        default="noor")
    parser.add_argument("--host",         default="0.0.0.0")
    parser.add_argument("--port",         type=int, default=8000)
    parser.add_argument("--top-k-quran",  type=int, default=3)
    parser.add_argument("--top-k-hadith", type=int, default=4)
    parser.add_argument("--top-k-fiqh",   type=int, default=2)
    parser.add_argument("--reload",       action="store_true",
                        help="Auto-reload on code changes (dev only)")
    args = parser.parse_args()

    # Pass args to app via app.state before uvicorn starts
    app.state.model        = args.model
    app.state.top_k_quran  = args.top_k_quran
    app.state.top_k_hadith = args.top_k_hadith
    app.state.top_k_fiqh   = args.top_k_fiqh

    print(f"Starting Noor RAG API  →  http://{args.host}:{args.port}")
    print(f"  Swagger UI           →  http://{args.host}:{args.port}/docs")
    print(f"  Model                : {args.model}")

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
