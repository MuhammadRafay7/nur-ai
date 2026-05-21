#!/usr/bin/env python3
"""
batch_test.py — Run evaluation questions through the RAG pipeline and save results.

Unlike run_evaluation.py (which is in Phase 4 and tests just model answers),
this script tests the FULL RAG pipeline — retrieval quality + answer quality.

Usage:
    python batch_test.py
    python batch_test.py --model noor --categories aqeedah fiqh
    python batch_test.py --questions-dir ../04_evaluation/test_questions
    python batch_test.py --max-per-category 5   # quick smoke test

Output: ../04_evaluation/reports/rag_batch_{timestamp}.json
         ../04_evaluation/reports/rag_batch_{timestamp}_report.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import IslamicRAGPipeline

QUESTIONS_DIR = Path(__file__).parent.parent / "04_evaluation" / "test_questions"
REPORTS_DIR   = Path(__file__).parent.parent / "04_evaluation" / "reports"


def load_questions(questions_dir: Path, categories: list[str] | None = None) -> list[dict]:
    questions = []
    for path in sorted(questions_dir.glob("*.json")):
        cat = path.stem
        if categories and cat not in categories:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[SKIP] {path.name}: {e}")
            continue
        for q in data.get("questions", []):
            q["_category"] = cat
            q["_pass_criteria"] = data.get("pass_criteria", {})
            questions.append(q)
    return questions


def score_result(response, question: dict) -> dict:
    answer  = response.llm_answer
    a_lower = answer.lower()
    import re

    has_arabic    = any("؀" <= c <= "ۿ" for c in answer)
    has_quran_ref = bool(re.search(r"\b\d{1,3}\s*:\s*\d{1,3}\b", answer))
    has_hadith    = any(s in a_lower for s in ["bukhari", "muslim", "tirmidhi", "abu dawud", "ibn majah", "nasai"])
    has_grade     = any(g in a_lower for g in ["sahih", "hasan", "da'if", "daif", "weak"])
    has_summary   = "summary" in a_lower

    must_contain  = question.get("must_contain", [])
    missing_kw    = [kw for kw in must_contain if kw.lower() not in a_lower]

    rag_retrieved = response.retrieval.has_results()
    n_quran  = len(response.retrieval.quran)
    n_hadith = len(response.retrieval.hadith)
    n_fiqh   = len(response.retrieval.fiqh)

    return {
        "has_arabic":     has_arabic,
        "has_quran_ref":  has_quran_ref,
        "has_hadith_src": has_hadith,
        "has_grade":      has_grade,
        "has_summary":    has_summary,
        "missing_keywords": missing_kw,
        "rag_retrieved":  rag_retrieved,
        "rag_quran_hits": n_quran,
        "rag_hadith_hits": n_hadith,
        "rag_fiqh_hits":  n_fiqh,
        "answer_length":  len(answer),
        "is_error":       response.error != "",
    }


def build_txt_report(results: list[dict], model: str) -> str:
    lines = ["=" * 70, f"Noor RAG Batch Test — {model}", f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", f"Questions: {len(results)}", "=" * 70, ""]

    by_cat: dict[str, list] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)

    for cat, items in sorted(by_cat.items()):
        n  = len(items)
        ar = sum(1 for r in items if r["signals"]["has_arabic"])
        qr = sum(1 for r in items if r["signals"]["has_quran_ref"])
        hr = sum(1 for r in items if r["signals"]["has_hadith_src"])
        sm = sum(1 for r in items if r["signals"]["has_summary"])
        rg = sum(1 for r in items if r["signals"]["rag_retrieved"])
        mk = sum(len(r["signals"]["missing_keywords"]) for r in items)
        avg_lat = sum(r["latency_s"] for r in items) / n

        lines.append(f"[{cat.upper()}]  {n} questions")
        lines.append(f"  Arabic       : {ar}/{n}")
        lines.append(f"  Quran refs   : {qr}/{n}")
        lines.append(f"  Hadith refs  : {hr}/{n}")
        lines.append(f"  Has summary  : {sm}/{n}")
        lines.append(f"  RAG retrieved: {rg}/{n}")
        lines.append(f"  Missing kw   : {mk} total")
        lines.append(f"  Avg latency  : {avg_lat:.1f}s")
        lines.append("")

        for r in items:
            sig = r["signals"]
            flags = []
            if not sig["has_arabic"]:     flags.append("NO_ARABIC")
            if not sig["has_quran_ref"] and not sig["has_hadith_src"]: flags.append("NO_REF")
            if not sig["has_summary"]:    flags.append("NO_SUMMARY")
            if sig["missing_keywords"]:   flags.append(f"MISSING:{sig['missing_keywords'][:2]}")
            if sig["is_error"]:           flags.append("ERROR")
            flag_str = " | ".join(flags) if flags else "OK"

            lines.append(f"  [{r['id']}]  {flag_str}  ({r['latency_s']:.1f}s)")
            lines.append(f"    Q: {r['question'][:80]}")
            if r["citations"]:
                lines.append(f"    C: {', '.join(r['citations'][:3])}")
            lines.append("")

    # Overall stats
    total = len(results)
    ar_total = sum(1 for r in results if r["signals"]["has_arabic"])
    ref_total = sum(1 for r in results if r["signals"]["has_quran_ref"] or r["signals"]["has_hadith_src"])
    sm_total  = sum(1 for r in results if r["signals"]["has_summary"])
    err_total = sum(1 for r in results if r["signals"]["is_error"])

    lines.extend([
        "=" * 70,
        "OVERALL",
        f"  Arabic rate   : {ar_total}/{total} ({100*ar_total//total if total else 0}%)",
        f"  Reference rate: {ref_total}/{total} ({100*ref_total//total if total else 0}%)",
        f"  Summary rate  : {sm_total}/{total} ({100*sm_total//total if total else 0}%)",
        f"  Error count   : {err_total}",
        "=" * 70,
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch test the RAG pipeline")
    parser.add_argument("--model",             default="noor")
    parser.add_argument("--categories",        nargs="*")
    parser.add_argument("--questions-dir",     type=Path, default=QUESTIONS_DIR)
    parser.add_argument("--output-dir",        type=Path, default=REPORTS_DIR)
    parser.add_argument("--max-per-category",  type=int, default=0,
                        help="Limit to N questions per category (0 = all)")
    parser.add_argument("--no-rag",            action="store_true")
    parser.add_argument("--top-k-quran",       type=int, default=3)
    parser.add_argument("--top-k-hadith",      type=int, default=4)
    parser.add_argument("--top-k-fiqh",        type=int, default=2)
    args = parser.parse_args()

    pipeline = IslamicRAGPipeline(
        model=args.model,
        top_k_quran=args.top_k_quran,
        top_k_hadith=args.top_k_hadith,
        top_k_fiqh=args.top_k_fiqh,
    )

    if not pipeline.is_ollama_running():
        print("Ollama is not running. Start it: ollama serve")
        sys.exit(1)

    questions = load_questions(args.questions_dir, args.categories)
    if not questions:
        print("No questions found.")
        sys.exit(1)

    if args.max_per_category:
        by_cat: dict[str, list] = defaultdict(list)
        for q in questions:
            by_cat[q["_category"]].append(q)
        questions = []
        for qs in by_cat.values():
            questions.extend(qs[:args.max_per_category])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path   = args.output_dir / f"rag_batch_{ts}_{args.model}.json"
    report_path = args.output_dir / f"rag_batch_{ts}_{args.model}_report.txt"

    rag_state = "OFF" if args.no_rag else "ON"
    print(f"Batch test: {len(questions)} questions | model={args.model} | RAG={rag_state}")
    print()

    results = []
    for i, q in enumerate(questions, 1):
        qid  = q["id"]
        cat  = q["_category"]
        text = q["question"]
        print(f"[{i:3d}/{len(questions)}] {qid} ({cat})")
        print(f"  Q: {text[:90]}{'...' if len(text)>90 else ''}")

        response = pipeline.answer(text, rag_enabled=not args.no_rag)
        signals  = score_result(response, q)

        result = {
            "id":         qid,
            "category":   cat,
            "question":   text,
            "answer":     response.llm_answer,
            "summary":    response.summary_only(),
            "citations":  response.retrieval.citation_list(),
            "signals":    signals,
            "latency_s":  response.latency_s,
            "model":      args.model,
            "rag_on":     not args.no_rag,
            "tested_at":  datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        # Live summary
        flags = []
        if signals["rag_retrieved"]:
            flags.append(f"RAG({signals['rag_quran_hits']}Q,{signals['rag_hadith_hits']}H,{signals['rag_fiqh_hits']}F)")
        if signals["has_arabic"]:  flags.append("arabic")
        if signals["has_summary"]: flags.append("summary")
        if signals["missing_keywords"]: flags.append(f"miss:{signals['missing_keywords'][:1]}")
        if signals["is_error"]:    flags.append("ERROR")
        print(f"  [{','.join(flags) or 'ok'}]  {response.latency_s:.1f}s")
        print()

    json_path.write_text(
        json.dumps({
            "model":   args.model,
            "rag_on":  not args.no_rag,
            "run_at":  datetime.now(timezone.utc).isoformat(),
            "total":   len(results),
            "results": results,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path.write_text(build_txt_report(results, args.model), encoding="utf-8")

    total_time = sum(r["latency_s"] for r in results)
    print("=" * 60)
    print(f"Done.  {len(results)} questions  |  {total_time:.0f}s total")
    print(f"  JSON   → {json_path}")
    print(f"  Report → {report_path}")


if __name__ == "__main__":
    main()
