#!/usr/bin/env python3
"""
run_evaluation.py — Run all test questions through the local GGUF model (via Ollama)
and save raw answers to reports/.

Usage:
    python run_evaluation.py --model-path ../../05_model_output/gguf/islamic_llm_q4_k_m.gguf
    python run_evaluation.py --backend ollama --ollama-model noor
    python run_evaluation.py --categories aqeedah fiqh
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

QUESTIONS_DIR = Path(__file__).parent.parent / "test_questions"
REPORTS_DIR   = Path(__file__).parent.parent / "reports"

OLLAMA_API_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL   = "noor"

SYSTEM_PROMPT = (
    "You are Noor, an Islamic AI assistant. Answer every question using only authentic "
    "Quran and Hadith sources. Always include:\n"
    "1. Exact Arabic text\n"
    "2. Surah:Ayah reference for Quran, or Collection+Number for Hadith\n"
    "3. Hadith grade (Sahih, Hasan, Da'if) where applicable\n"
    "4. A summary at the end\n"
    "Never fabricate references. If you do not know, say so clearly."
)


def load_questions(categories: list[str] | None = None) -> list[dict]:
    questions = []
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        cat = path.stem
        if categories and cat not in categories:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data.get("questions", []):
            q["_category_file"] = cat
            q["_pass_criteria"] = data.get("pass_criteria", {})
            questions.append(q)
    return questions


def query_ollama(question: str, model: str = OLLAMA_MODEL, timeout: int = 300) -> tuple[str, float]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
        "max_tokens":  1024,
        "temperature": 0.1,
    }
    t0 = time.time()
    try:
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
        latency = time.time() - t0
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip(), latency
        return f"[HTTP {resp.status_code}] {resp.text[:200]}", latency
    except requests.exceptions.ConnectionError:
        return "[ERROR: Ollama not running — run: ollama serve]", 0.0
    except Exception as exc:
        return f"[ERROR: {exc}]", 0.0


def check_signals(answer: str, must_contain: list[str]) -> dict:
    a_lower = answer.lower()
    has_arabic = any("؀" <= c <= "ۿ" for c in answer)
    import re
    has_quran_ref = bool(re.search(r"\b\d{1,3}\s*:\s*\d{1,3}\b", answer))
    has_hadith_src = any(src in a_lower for src in [
        "bukhari", "muslim", "tirmidhi", "abu dawud", "ibn majah", "nasai", "nasa"
    ])
    has_grade = any(g in a_lower for g in ["sahih", "hasan", "da'if", "daif", "weak"])
    missing_keywords = [kw for kw in (must_contain or []) if kw.lower() not in a_lower]

    return {
        "has_arabic":     has_arabic,
        "has_quran_ref":  has_quran_ref,
        "has_hadith_src": has_hadith_src,
        "has_grade":      has_grade,
        "missing_keywords": missing_keywords,
        "answer_length":  len(answer),
        "is_error":       answer.startswith("[ERROR") or answer.startswith("[HTTP"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend",      choices=["ollama"], default="ollama")
    parser.add_argument("--ollama-model", default=OLLAMA_MODEL)
    parser.add_argument("--categories",   nargs="*",
                        help="Only run these categories, e.g. aqeedah fiqh")
    parser.add_argument("--max-questions", type=int, default=0,
                        help="Limit to N questions per category (0 = all)")
    args = parser.parse_args()

    questions = load_questions(args.categories)
    if not questions:
        print("No questions found. Check test_questions/ directory.")
        sys.exit(1)

    if args.max_questions:
        from collections import defaultdict
        by_cat: dict[str, list] = defaultdict(list)
        for q in questions:
            by_cat[q["_category_file"]].append(q)
        questions = []
        for qs in by_cat.values():
            questions.extend(qs[:args.max_questions])

    # Verify Ollama is running
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        tags = [m["name"] for m in r.json().get("models", [])]
        if not any(args.ollama_model in t for t in tags):
            print(f"Model '{args.ollama_model}' not found in Ollama.")
            print(f"Available: {tags or '(none)'}")
            print(f"Pull it: ollama pull {args.ollama_model}")
            print("Or import your GGUF: ollama create noor -f Modelfile")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Ollama is not running. Start it: ollama serve")
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"eval_{ts}_{args.ollama_model.replace('/', '_')}.json"

    print(f"Running {len(questions)} questions against model: {args.ollama_model}")
    print(f"Output: {output_path.name}\n")

    results = []
    for i, q in enumerate(questions, 1):
        qid  = q["id"]
        cat  = q["_category_file"]
        text = q["question"]
        print(f"[{i:3d}/{len(questions)}] {qid} ({cat})")
        print(f"  Q: {text[:90]}{'...' if len(text)>90 else ''}")

        answer, latency = query_ollama(text, model=args.ollama_model)
        signals = check_signals(answer, q.get("must_contain", []))

        result = {
            "id":             qid,
            "category":       cat,
            "question":       text,
            "answer":         answer,
            "signals":        signals,
            "must_contain":   q.get("must_contain", []),
            "expected_refs":  q.get("expected_refs", []),
            "latency_s":      round(latency, 2),
            "model":          args.ollama_model,
            "evaluated_at":   datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        status_parts = []
        if signals["has_arabic"]:     status_parts.append("arabic")
        if signals["has_quran_ref"]:  status_parts.append("quran_ref")
        if signals["has_hadith_src"]: status_parts.append("hadith_src")
        if signals["is_error"]:       status_parts.append("ERROR")
        if signals["missing_keywords"]:
            status_parts.append(f"missing:{signals['missing_keywords'][:2]}")
        print(f"  Signals: {','.join(status_parts) or 'none'}  ({latency:.1f}s)")
        print()

    output_path.write_text(
        json.dumps({
            "model":    args.ollama_model,
            "run_at":   datetime.now(timezone.utc).isoformat(),
            "total":    len(results),
            "results":  results,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Quick summary
    error_count   = sum(1 for r in results if r["signals"]["is_error"])
    arabic_count  = sum(1 for r in results if r["signals"]["has_arabic"])
    ref_count     = sum(1 for r in results if r["signals"]["has_quran_ref"] or r["signals"]["has_hadith_src"])
    print("=" * 60)
    print(f"Done.  {len(results)} questions")
    print(f"  Arabic text present  : {arabic_count}/{len(results)} ({100*arabic_count//len(results)}%)")
    print(f"  Citations present    : {ref_count}/{len(results)} ({100*ref_count//len(results)}%)")
    print(f"  Errors               : {error_count}")
    print(f"  Output               : {output_path}")
    print()
    print("Next: python hallucination_check.py --report", output_path.name)


if __name__ == "__main__":
    main()
