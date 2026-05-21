#!/usr/bin/env python3
"""
cli_chat.py — Interactive RAG-powered terminal chat with the Noor Islamic AI.

Flow per message:
  1. User types a question
  2. BM25 retrieval → Quran ayahs + Hadiths + Fiqh rulings
  3. LLM generates detailed explanation using retrieved sources
  4. Response shows: Citations → Detailed Answer → Summary

Usage:
    python cli_chat.py
    python cli_chat.py --model noor                        # fine-tuned model
    python cli_chat.py --model llama3.2                    # base model (pre fine-tune)
    python cli_chat.py --no-rag                            # disable retrieval
    python cli_chat.py --model-path ../05_model_output/gguf/islamic_llm_q4_k_m.gguf

Commands inside the chat:
    /quit  — exit
    /reset — clear conversation history
    /save  — save conversation to JSON
    /rag   — toggle RAG on/off
    /src   — show/hide source passages
    /help  — show all commands
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import IslamicRAGPipeline

# ─── Terminal colours (works on Linux/Mac, graceful on Windows) ───────────────

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    C_CYAN   = Fore.CYAN
    C_GREEN  = Fore.GREEN
    C_YELLOW = Fore.YELLOW
    C_RED    = Fore.RED
    C_BLUE   = Fore.BLUE
    C_GREY   = Fore.WHITE
    C_RESET  = Style.RESET_ALL
    C_BOLD   = Style.BRIGHT
except ImportError:
    C_CYAN = C_GREEN = C_YELLOW = C_RED = C_BLUE = C_GREY = C_RESET = C_BOLD = ""

BANNER = f"""{C_CYAN}{C_BOLD}
╔══════════════════════════════════════════════════════════╗
║          Noor — Islamic AI Assistant (RAG Mode)          ║
║     Powered by Quran · Hadith · Fiqh Knowledge Base      ║
╚══════════════════════════════════════════════════════════╝{C_RESET}
"""

HELP_TEXT = f"""
{C_YELLOW}Commands:{C_RESET}
  /quit   — exit the chat
  /reset  — clear conversation history
  /save   — save this conversation to JSON
  /rag    — toggle RAG retrieval on/off (currently shows current state)
  /src    — toggle showing retrieved source passages
  /help   — show this help

{C_YELLOW}Tips:{C_RESET}
  • Ask about Quran verses, Hadith, Fiqh rulings, Aqeedah, Seerah, Duas
  • Questions about specific topics retrieve the most relevant Islamic texts
  • The model cites exact Quran Surah:Ayah and Hadith collection+number
"""

SAVE_DIR = Path(__file__).parent / "saved_conversations"


def wrap(text: str, width: int = 80, indent: str = "  ") -> str:
    lines = text.split("\n")
    wrapped = []
    for line in lines:
        if len(line) <= width:
            wrapped.append(line)
        else:
            wrapped.extend(
                textwrap.wrap(line, width=width, subsequent_indent=indent)
            )
    return "\n".join(wrapped)


def print_banner(model: str, rag_on: bool) -> None:
    print(BANNER)
    print(f"  Model : {C_GREEN}{model}{C_RESET}")
    print(f"  RAG   : {C_GREEN}ON{C_RESET}" if rag_on else f"  RAG   : {C_RED}OFF{C_RESET}")
    print(f"  Index : ", end="")


def print_citations(retrieval) -> None:
    citations = retrieval.citation_list()
    if not citations:
        print(f"  {C_GREY}(no sources retrieved){C_RESET}")
        return
    print(f"\n{C_YELLOW}┌─ Retrieved Sources ({len(citations)}) ──────────────────────────────{C_RESET}")
    for c in citations:
        print(f"{C_YELLOW}│{C_RESET}  • {c}")
    print(f"{C_YELLOW}└──────────────────────────────────────────────────────────{C_RESET}")


def print_sources(retrieval) -> None:
    ctx = retrieval.format_context()
    if not ctx:
        return
    print(f"\n{C_BLUE}┌─ Source Passages ──────────────────────────────────────────{C_RESET}")
    for line in ctx.split("\n"):
        print(f"{C_BLUE}│{C_RESET} {line}")
    print(f"{C_BLUE}└────────────────────────────────────────────────────────────{C_RESET}")


def print_answer(response) -> None:
    detail  = response.detailed_only()
    summary = response.summary_only()

    print(f"\n{C_GREEN}━━━ Answer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C_RESET}")
    print(wrap(detail))

    if "summary" in response.llm_answer.lower():
        print(f"\n{C_CYAN}━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C_RESET}")
        print(wrap(summary))

    print(f"\n{C_GREY}[{response.model}  |  {response.latency_s:.1f}s]{C_RESET}\n")


def save_conversation(history: list[dict], model: str) -> None:
    SAVE_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SAVE_DIR / f"conversation_{ts}.json"
    path.write_text(
        json.dumps({
            "model":   model,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "turns":   history,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{C_GREEN}Saved → {path}{C_RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Noor — RAG-powered Islamic AI CLI")
    parser.add_argument("--model",      default="noor",
                        help="Ollama model name (default: noor)")
    parser.add_argument("--model-path", default="",
                        help="Path to GGUF file (use with llama-cpp-python backend)")
    parser.add_argument("--no-rag",     action="store_true",
                        help="Disable RAG retrieval")
    parser.add_argument("--show-src",   action="store_true",
                        help="Always show full source passages")
    parser.add_argument("--top-k-quran",  type=int, default=3)
    parser.add_argument("--top-k-hadith", type=int, default=4)
    parser.add_argument("--top-k-fiqh",   type=int, default=2)
    args = parser.parse_args()

    rag_on  = not args.no_rag
    show_src = args.show_src

    pipeline = IslamicRAGPipeline(
        model=args.model,
        top_k_quran=args.top_k_quran,
        top_k_hadith=args.top_k_hadith,
        top_k_fiqh=args.top_k_fiqh,
    )

    print_banner(args.model, rag_on)

    # Check RAG index
    status = pipeline._retriever.index_status()
    if "total_docs" in status:
        print(f"{C_GREEN}{status['total_docs']:,} docs  (built {status['built_at'][:10]}){C_RESET}")
    else:
        print(f"{C_YELLOW}not built{C_RESET}  (run: python build_rag_index.py)")
        rag_on = False
        print(f"  RAG disabled until index is built.")

    # Check Ollama
    if not pipeline.is_ollama_running():
        print(f"\n{C_RED}Ollama is not running.{C_RESET}")
        print("  Start it:  ollama serve")
        print("  Then pull: ollama pull llama3.2  (or import your GGUF)")
        sys.exit(1)

    models = pipeline.available_models()
    if args.model not in " ".join(models):
        available = ", ".join(models) or "(none)"
        print(f"\n{C_YELLOW}Model '{args.model}' not found in Ollama.{C_RESET}")
        print(f"  Available: {available}")
        print(f"  Switching to first available model...")
        if models:
            pipeline.model = models[0]
            print(f"  Using: {pipeline.model}")
        else:
            print(f"  No models available. Pull one: ollama pull llama3.2")
            sys.exit(1)

    print(f"\n{C_GREY}Type your question or /help for commands.{C_RESET}\n")

    history: list[dict] = []

    while True:
        try:
            user_input = input(f"{C_CYAN}You:{C_RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nFi amanillah. Assalamu Alaikum.")
            break

        if not user_input:
            continue

        # ── Commands ──────────────────────────────────────────────────────────
        cmd = user_input.lower()

        if cmd in ("/quit", "/exit", "/q"):
            print("Fi amanillah. Assalamu Alaikum.")
            break

        if cmd == "/help":
            print(HELP_TEXT)
            continue

        if cmd == "/reset":
            history.clear()
            print(f"{C_GREEN}Conversation reset.{C_RESET}\n")
            continue

        if cmd == "/save":
            save_conversation(history, pipeline.model)
            continue

        if cmd == "/rag":
            rag_on = not rag_on
            state = f"{C_GREEN}ON{C_RESET}" if rag_on else f"{C_RED}OFF{C_RESET}"
            print(f"RAG retrieval: {state}\n")
            continue

        if cmd == "/src":
            show_src = not show_src
            state = f"{C_GREEN}ON{C_RESET}" if show_src else f"{C_RED}OFF{C_RESET}"
            print(f"Show source passages: {state}\n")
            continue

        # ── Normal question ───────────────────────────────────────────────────
        print(f"{C_GREY}Retrieving sources...{C_RESET}")
        response = pipeline.answer(user_input, rag_enabled=rag_on)

        if response.error:
            print(f"{C_RED}Error: {response.error}{C_RESET}\n")
            continue

        print_citations(response.retrieval)

        if show_src and response.retrieval.has_results():
            print_sources(response.retrieval)

        print_answer(response)

        history.append({
            "question":  user_input,
            "citations": response.retrieval.citation_list(),
            "answer":    response.llm_answer,
            "latency_s": response.latency_s,
        })


if __name__ == "__main__":
    main()
