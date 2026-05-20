#!/usr/bin/env python3
"""
baseline_test.py — Test Llama 3.2 3B Instruct locally via Ollama or via HuggingFace API.

Runs a fixed set of Islamic questions and saves responses so you can compare
the base model against the fine-tuned Noor model later.

── LOCAL (Ollama) ──────────────────────────────────────────────────────────────
  # 1. Install ollama (one-time):
  #    curl -fsSL https://ollama.com/install.sh | sh
  #
  # 2. Pull the model (one-time, ~2GB download):
  #    ollama pull llama3.2
  #
  # 3. Run the test:
  python baseline_test.py --backend ollama

── HuggingFace API (no GPU needed, needs free token) ───────────────────────────
  python baseline_test.py --backend hf --token hf_xxxx

── Filter categories ───────────────────────────────────────────────────────────
  python baseline_test.py --backend ollama --categories quran hadith

Output:
    baseline_results/baseline_<timestamp>.json
    baseline_results/baseline_<timestamp>_report.txt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# ─── Config ───────────────────────────────────────────────────────────────────

HF_MODEL_ID    = "meta-llama/Llama-3.2-3B-Instruct"
HF_API_URL     = "https://api-inference.huggingface.co/v1/chat/completions"

OLLAMA_MODEL   = "llama3.2"           # name used in `ollama pull llama3.2`
OLLAMA_API_URL = "http://localhost:11434/v1/chat/completions"

MAX_TOKENS  = 512
TEMPERATURE = 0.1
RETRY_WAIT  = 10

SYSTEM_PROMPT = (
    "You are a knowledgeable Islamic assistant. Answer questions about Islam "
    "clearly and accurately, citing Quran and Hadith where relevant. "
    "For Quranic verses, include the Arabic text and surah:ayah reference. "
    "For hadith, include the book and hadith number."
)

OUTPUT_DIR = Path(__file__).parent / "baseline_results"

# ─── Test questions ────────────────────────────────────────────────────────────
# Grouped by category — same questions will be tested against the fine-tuned model

TEST_QUESTIONS: list[dict[str, str]] = [
    # ── Quran ──────────────────────────────────────────────────────────────────
    {
        "id":       "quran_01",
        "category": "quran",
        "question": "Recite Surah Al-Fatiha with Arabic text and explain its meaning.",
    },
    {
        "id":       "quran_02",
        "category": "quran",
        "question": "What is Ayat al-Kursi? Give the Arabic text and explain its significance.",
    },
    {
        "id":       "quran_03",
        "category": "quran",
        "question": "What does Surah Al-Ikhlas say? Give the Arabic and explain why it equals one-third of the Quran.",
    },
    {
        "id":       "quran_04",
        "category": "quran",
        "question": "What is the last verse revealed in the Quran?",
    },
    {
        "id":       "quran_05",
        "category": "quran",
        "question": "Explain the tafsir of Surah Al-Asr (103). What does it teach about time?",
    },

    # ── Hadith ─────────────────────────────────────────────────────────────────
    {
        "id":       "hadith_01",
        "category": "hadith",
        "question": "What is the first hadith in Sahih Bukhari? State it in full with the source.",
    },
    {
        "id":       "hadith_02",
        "category": "hadith",
        "question": "What are the Five Pillars of Islam according to hadith?",
    },
    {
        "id":       "hadith_03",
        "category": "hadith",
        "question": "What did the Prophet ﷺ say about intention (niyyah)?",
    },
    {
        "id":       "hadith_04",
        "category": "hadith",
        "question": "What is the hadith of Jibreel (Gabriel) about Islam, Iman, and Ihsan?",
    },
    {
        "id":       "hadith_05",
        "category": "hadith",
        "question": "What did the Prophet ﷺ say about the best of people?",
    },

    # ── Fiqh ───────────────────────────────────────────────────────────────────
    {
        "id":       "fiqh_01",
        "category": "fiqh",
        "question": "How many rak'ahs are in each of the five daily prayers?",
    },
    {
        "id":       "fiqh_02",
        "category": "fiqh",
        "question": "What are the conditions (shurut) that make wudu (ablution) valid?",
    },
    {
        "id":       "fiqh_03",
        "category": "fiqh",
        "question": "What is the nisab for zakat on gold and silver?",
    },
    {
        "id":       "fiqh_04",
        "category": "fiqh",
        "question": "When does fasting in Ramadan become obligatory, and who is exempt?",
    },
    {
        "id":       "fiqh_05",
        "category": "fiqh",
        "question": "What are the pillars (arkan) of Hajj?",
    },

    # ── Aqeedah ────────────────────────────────────────────────────────────────
    {
        "id":       "aqeedah_01",
        "category": "aqeedah",
        "question": "What are the six pillars of Iman (faith) in Islam?",
    },
    {
        "id":       "aqeedah_02",
        "category": "aqeedah",
        "question": "What does Islam say about Shirk (associating partners with Allah)?",
    },
    {
        "id":       "aqeedah_03",
        "category": "aqeedah",
        "question": "List the 99 Names of Allah (Asma ul Husna) — give at least 20 with meanings.",
    },
    {
        "id":       "aqeedah_04",
        "category": "aqeedah",
        "question": "Explain the concept of Qadar (divine decree) in Islam.",
    },

    # ── Seerah ─────────────────────────────────────────────────────────────────
    {
        "id":       "seerah_01",
        "category": "seerah",
        "question": "When and where was the Prophet Muhammad ﷺ born?",
    },
    {
        "id":       "seerah_02",
        "category": "seerah",
        "question": "What was the first revelation received by the Prophet ﷺ?",
    },
    {
        "id":       "seerah_03",
        "category": "seerah",
        "question": "What were the key events of the Battle of Badr?",
    },

    # ── Dua ────────────────────────────────────────────────────────────────────
    {
        "id":       "dua_01",
        "category": "dua",
        "question": "What is the dua to say before eating? Give Arabic, transliteration, and meaning.",
    },
    {
        "id":       "dua_02",
        "category": "dua",
        "question": "What is the morning remembrance (adhkar) the Prophet ﷺ recommended?",
    },

    # ── Ethics / Behavior ──────────────────────────────────────────────────────
    {
        "id":       "ethics_01",
        "category": "ethics",
        "question": "What does Islam say about honoring one's parents?",
    },
    {
        "id":       "ethics_02",
        "category": "ethics",
        "question": "What are the rights of a Muslim upon another Muslim according to hadith?",
    },

    # ── Halal / Haram food ─────────────────────────────────────────────────────
    {
        "id":       "halal_01",
        "category": "halal_haram",
        "question": "Is horse meat halal or haram in Islam?",
    },
    {
        "id":       "halal_02",
        "category": "halal_haram",
        "question": "Is it halal to eat shrimp and other seafood?",
    },
    {
        "id":       "halal_03",
        "category": "halal_haram",
        "question": "Is it permissible to eat food cooked with alcohol if the alcohol evaporates?",
    },

    # ── Refusal / Scope ────────────────────────────────────────────────────────
    {
        "id":       "refusal_01",
        "category": "refusal",
        "question": "Who will win the next FIFA World Cup?",
    },
    {
        "id":       "refusal_02",
        "category": "refusal",
        "question": "Write me a love poem.",
    },
    {
        "id":       "refusal_03",
        "category": "refusal",
        "question": "Is it permissible to declare a specific Muslim as a kafir (takfir)?",
    },
]


# ─── API helpers ──────────────────────────────────────────────────────────────

def _post_openai_compat(
    url: str,
    model: str,
    question: str,
    token: str = "",
    retries: int = 3,
    timeout: int = 120,
) -> tuple[str, float]:
    """POST to any OpenAI-compatible /v1/chat/completions endpoint."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
        "max_tokens":  MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    for attempt in range(1, retries + 1):
        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            latency = time.time() - t0

            if resp.status_code == 200:
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()
                return answer, latency

            elif resp.status_code in (429, 503):
                wait = RETRY_WAIT * attempt
                print(f"    [{resp.status_code}] Rate limited — waiting {wait}s")
                time.sleep(wait)
                continue

            elif resp.status_code == 401:
                return "[ERROR: invalid token — check HF_TOKEN]", 0.0

            elif resp.status_code == 404:
                return "[ERROR: model not found — accept terms at huggingface.co/meta-llama/Llama-3.2-3B-Instruct]", 0.0

            else:
                return f"[ERROR: HTTP {resp.status_code} — {resp.text[:150]}]", 0.0

        except requests.exceptions.ConnectionError:
            if attempt == 1:
                print("    Connection refused — is ollama running? Start it with:  ollama serve")
            return "[ERROR: cannot connect to ollama — run: ollama serve]", 0.0
        except requests.exceptions.Timeout:
            print(f"    Timeout on attempt {attempt}/{retries} — model may still be loading, waiting...")
            time.sleep(10)
        except Exception as exc:
            return f"[ERROR: {exc}]", 0.0

    return "[ERROR: max retries exceeded]", 0.0


def query_model(question: str, backend: str, token: str = "", ollama_model: str = "llama3.2") -> tuple[str, float]:
    """Route a question to the selected backend. Returns (answer, latency_seconds)."""
    if backend == "ollama":
        return _post_openai_compat(
            url=OLLAMA_API_URL,
            model=ollama_model,
            question=question,
            timeout=300,   # CPU inference can be slow — allow 5 min
        )
    else:  # hf
        return _post_openai_compat(
            url=HF_API_URL,
            model=HF_MODEL_ID,
            question=question,
            token=token,
            timeout=60,
        )


# ─── Report helpers ────────────────────────────────────────────────────────────

def score_answer(question_id: str, answer: str) -> str:
    """Simple heuristic signal — not a score, just a flag for manual review."""
    a = answer.lower()
    if answer.startswith("[ERROR"):
        return "ERROR"
    if len(answer) < 30:
        return "TOO_SHORT"

    signals: list[str] = []

    # Check for Arabic text presence (Unicode Arabic block)
    has_arabic = any("؀" <= c <= "ۿ" for c in answer)
    if has_arabic:
        signals.append("has_arabic")

    # Check for Quran reference pattern e.g. (2:255)
    import re
    if re.search(r"\d+:\d+", answer):
        signals.append("has_verse_ref")

    # Check for hadith source mention
    if any(src in a for src in ["bukhari", "muslim", "tirmidhi", "abu dawud", "ibn majah", "nasa"]):
        signals.append("cites_hadith_src")

    # Refusal questions — should NOT mention Islamic content deeply
    if question_id.startswith("refusal_"):
        if any(kw in a for kw in ["world cup", "love poem", "sorry", "outside", "not able"]):
            signals.append("good_refusal")
        return "REFUSAL | " + ("|".join(signals) if signals else "no_signals")

    return "|".join(signals) if signals else "no_signals"


def build_report(results: list[dict[str, Any]], model_label: str) -> str:
    lines = [
        "=" * 70,
        f"Noor Baseline Evaluation — {model_label}",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Questions: {len(results)}",
        "=" * 70,
        "",
    ]

    for r in results:
        lines.append(f"[{r['id']}] ({r['category']})")
        lines.append(f"Q: {r['question']}")
        lines.append(f"Signals: {r['signals']}  |  Latency: {r['latency_s']:.1f}s")
        lines.append("A: " + r["answer"][:500] + ("..." if len(r["answer"]) > 500 else ""))
        lines.append("-" * 70)
        lines.append("")

    # Category summary
    from collections import defaultdict
    by_cat: dict[str, list[str]] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r["signals"])

    lines.append("CATEGORY SUMMARY")
    lines.append("-" * 40)
    for cat, signals_list in sorted(by_cat.items()):
        lines.append(f"  {cat:20s} {len(signals_list)} questions")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline test for Llama 3.2 3B Instruct")
    parser.add_argument(
        "--backend", choices=["ollama", "hf"], default="ollama",
        help="ollama = local Ollama server  |  hf = HuggingFace Serverless API",
    )
    parser.add_argument("--token",      default=os.getenv("HF_TOKEN", ""), help="HuggingFace token (only for --backend hf)")
    parser.add_argument("--categories", nargs="*", help="Run only these categories e.g. --categories quran hadith")
    parser.add_argument("--ollama-model", default="llama3.2", help="Ollama model tag (default: llama3.2)")
    parser.add_argument("--ask", metavar="QUESTION", help="Ask a single question and print the answer")
    args = parser.parse_args()

    # ── Resolve model names ────────────────────────────────────────────────────
    ollama_model = args.ollama_model
    if args.backend == "hf" and not args.token:
        print("ERROR: --backend hf requires a HuggingFace token.")
        print("  python baseline_test.py --backend hf --token hf_xxxx")
        print("  Get a free token at: https://huggingface.co/settings/tokens")
        sys.exit(1)

    if args.backend == "ollama":
        # Check ollama is reachable before starting
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            tags = [m["name"] for m in r.json().get("models", [])]
            if not any(ollama_model in t for t in tags):
                print(f"Model '{ollama_model}' not found in ollama. Pull it first:")
                print(f"  ollama pull {ollama_model}")
                print(f"\nAvailable models: {tags or '(none)'}")
                sys.exit(1)
            print(f"Ollama running  — using model: {ollama_model}")
        except requests.exceptions.ConnectionError:
            print("Ollama is not running. Start it first:")
            print("  ollama serve")
            print()
            print("If not installed:")
            print("  curl -fsSL https://ollama.com/install.sh | sh")
            print("  ollama pull llama3.2")
            sys.exit(1)

    model_label = ollama_model if args.backend == "ollama" else HF_MODEL_ID

    # ── Single question mode ───────────────────────────────────────────────────
    if args.ask:
        print(f"\nQ: {args.ask}\n")
        print("(generating...)\n")
        answer, latency = query_model(args.ask, backend=args.backend, token=args.token, ollama_model=ollama_model)
        print(f"A: {answer}")
        print(f"\n[{model_label}  |  {latency:.1f}s]")
        return

    questions = TEST_QUESTIONS
    if args.categories:
        questions = [q for q in questions if q["category"] in args.categories]
        print(f"Filtered to: {args.categories}  ({len(questions)} questions)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path   = OUTPUT_DIR / f"baseline_{ts}.json"
    report_path = OUTPUT_DIR / f"baseline_{ts}_report.txt"

    backend_label = f"ollama ({ollama_model})" if args.backend == "ollama" else f"HuggingFace ({HF_MODEL_ID})"
    print("=" * 60)
    print(f"  Backend : {backend_label}")
    print(f"  Questions: {len(questions)}")
    if args.backend == "ollama":
        print("  Note: CPU inference is ~3-8 tokens/sec — each answer takes 30-90s")
    print(f"  Output: {json_path.name}")
    print("=" * 60)
    print()

    results: list[dict[str, Any]] = []

    for i, q in enumerate(questions, 1):
        cat = q["category"]
        qid = q["id"]
        print(f"[{i:2d}/{len(questions)}] {qid} ({cat})")
        print(f"  Q: {q['question'][:80]}{'...' if len(q['question'])>80 else ''}")

        answer, latency = query_model(q["question"], backend=args.backend, token=args.token, ollama_model=ollama_model)
        signals = score_answer(qid, answer)

        result = {
            "id":        qid,
            "category":  cat,
            "question":  q["question"],
            "answer":    answer,
            "signals":   signals,
            "latency_s": round(latency, 2),
            "model":     model_label,
            "tested_at": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        preview = answer[:120].replace("\n", " ")
        print(f"  A: {preview}{'...' if len(answer)>120 else ''}")
        print(f"  Signals: {signals}  ({latency:.1f}s)")
        print()

        # Small delay between questions (skip for ollama — no rate limit)
        if args.backend == "hf" and i < len(questions):
            time.sleep(1.5)

    # Save JSON
    json_path.write_text(
        json.dumps({"model": model_label, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Save human-readable report
    report = build_report(results, model_label)
    report_path.write_text(report, encoding="utf-8")

    total_time = sum(r["latency_s"] for r in results)
    print("=" * 60)
    print(f"Done.  {len(results)} questions  |  {total_time:.0f}s total")
    print(f"  JSON   → {json_path}")
    print(f"  Report → {report_path}")
    print()
    print("After fine-tuning, compare with:")
    print("  python baseline_test.py --backend ollama --ollama-model noor")
    print("  (once you've imported the fine-tuned GGUF into ollama)")


if __name__ == "__main__":
    main()
