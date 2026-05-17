#!/usr/bin/env python3
"""
Format IslamQA fatwa data into Q&A training pairs.

Source file: 01_data_collection/raw/fatwa/islamqa_fatwas.json
             ~19,000 authentic fatwas from islamqa.info (Sheikh al-Munajjid)

Each answer is authentic scholarly text that naturally contains:
  - Detailed explanation
  - Quranic evidence (inline citations)
  - Hadith evidence (inline citations)
  - Fiqh rulings / scholarly positions
  - Summary / conclusion

Produces pairs in the standard instruction/input/output format.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_fatwa")

# Minimum answer length to accept (chars) — filters stubs
MIN_ANSWER_CHARS = 300
# Maximum answer length (chars) — prevents truncation at 2048 tokens
MAX_ANSWER_CHARS = 5_500

# Signals that the answer contains Quran / hadith evidence (quality filter)
_QURAN_MARKERS  = re.compile(r"\b(surah|quran|verse|ayah|allah says|said:)\b", re.I)
_HADITH_MARKERS = re.compile(r"\b(hadith|prophet|narrated|bukhari|muslim|tirmidhi|abu dawud)\b", re.I)

CONSULT_FOOTER = (
    "\n\n*For complex personal situations, consult a qualified Islamic scholar "
    "who can consider all relevant circumstances.*"
)

# ─── Topic → category mapping ─────────────────────────────────────────────────

_TOPIC_CATEGORY: dict[str, str] = {
    "belief":          "aqeedah",
    "faith":           "aqeedah",
    "tawheed":         "aqeedah",
    "shirk":           "aqeedah",
    "prayer":          "ibadah",
    "salah":           "ibadah",
    "fasting":         "ibadah",
    "zakat":           "ibadah",
    "hajj":            "ibadah",
    "pilgrimage":      "ibadah",
    "quran":           "quran",
    "hadith":          "hadith",
    "marriage":        "family",
    "divorce":         "family",
    "family":          "family",
    "women":           "family",
    "children":        "family",
    "inheritance":     "family",
    "trade":           "finance",
    "finance":         "finance",
    "business":        "finance",
    "riba":            "finance",
    "interest":        "finance",
    "food":            "halal_haram",
    "halal":           "halal_haram",
    "haram":           "halal_haram",
    "ethics":          "ethics",
    "manners":         "ethics",
    "character":       "ethics",
    "knowledge":       "knowledge",
    "scholars":        "knowledge",
    "innovation":      "bidah",
    "bidah":           "bidah",
    "seerah":          "seerah",
    "prophet":         "seerah",
    "companions":      "seerah",
    "death":           "eschatology",
    "hereafter":       "eschatology",
    "paradise":        "eschatology",
    "hellfire":        "eschatology",
    "contemporary":    "contemporary",
    "non-muslims":     "dawah",
    "dawah":           "dawah",
}


def _topic_to_category(topic: str) -> str:
    t = topic.lower()
    for keyword, cat in _TOPIC_CATEGORY.items():
        if keyword in t:
            return cat
    return "fatwa"


# ─── Answer cleaner ───────────────────────────────────────────────────────────

def _clean_answer(raw: str) -> str:
    """Remove boilerplate phrases that appear in every IslamQA answer."""
    # Remove leading "Praise be to Allah." and similar openers
    raw = re.sub(r"^Praise be to Allah[\.,]?\s*", "", raw, flags=re.I)
    raw = re.sub(r"^And Allah knows best[\.,]?\s*", "", raw, flags=re.I)
    # Remove trailing "And Allah knows best." / "We ask Allah..."
    raw = re.sub(r"\s*And Allah knows best\.?\s*$", "", raw, flags=re.I | re.S)
    raw = re.sub(r"\s*We ask Allah.*$", "", raw, flags=re.I | re.S)
    return raw.strip()


def _has_evidence(answer: str) -> bool:
    """Return True if answer contains Quranic or hadith references."""
    return bool(_QURAN_MARKERS.search(answer) or _HADITH_MARKERS.search(answer))


# ─── Question template variations ────────────────────────────────────────────

_QUESTION_PREFIXES = [
    "",                                 # use title/question as-is
    "According to Islamic scholars, ",
    "From an Islamic perspective, ",
    "What does Islam say: ",
    "Islamic ruling: ",
]


def _make_instruction(entry: dict, idx: int) -> str:
    """Build the instruction (question) string from a fatwa entry."""
    question = entry["question"].strip()
    title    = entry.get("title", "").strip()

    # Remove "Question\n\n" prefix that some entries have
    question = re.sub(r"^Question\s*\n+", "", question, flags=re.I).strip()

    # If the question is very short, prepend the title
    if len(question) < 60 and title:
        question = f"{title}: {question}"

    prefix = _QUESTION_PREFIXES[idx % len(_QUESTION_PREFIXES)]
    return f"{prefix}{question}"


# ─── Main generator ───────────────────────────────────────────────────────────

def generate_fatwa_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    """Generate training pairs from the downloaded IslamQA fatwa dataset.

    Args:
        kb_dir: knowledge_bases directory — used to locate raw dir (parent).

    Returns:
        List of Q&A pair dicts.
    """
    fatwa_path = kb_dir.parent / "fatwa" / "islamqa_fatwas.json"
    if not fatwa_path.exists():
        logger.warning(
            "islamqa_fatwas.json not found at %s — run download_fatwa.py first", fatwa_path
        )
        return []

    data = json.loads(fatwa_path.read_text(encoding="utf-8"))
    fatwas: list[dict] = data.get("fatwas", [])
    logger.info("Loaded %d fatwa records", len(fatwas))

    pairs: list[dict[str, Any]] = []

    for idx, fatwa in enumerate(fatwas):
        topic    = fatwa.get("topic", "")
        category = _topic_to_category(topic)
        fatwa_id = fatwa.get("original_id", str(idx))

        for lang, entry in fatwa.get("entries", {}).items():
            raw_answer = entry.get("answer", "")
            if not raw_answer:
                continue

            answer = _clean_answer(raw_answer)

            # Quality filters
            if len(answer) < MIN_ANSWER_CHARS:
                continue
            if len(answer) > MAX_ANSWER_CHARS:
                # Truncate at last paragraph boundary before limit
                cutoff = answer.rfind("\n\n", 0, MAX_ANSWER_CHARS)
                if cutoff > MIN_ANSWER_CHARS:
                    answer = answer[:cutoff].strip()
                else:
                    continue

            # Only keep answers with at least one Quran/hadith reference
            if not _has_evidence(answer):
                continue

            instruction = _make_instruction(entry, idx)

            pairs.append({
                "instruction": instruction,
                "input": "",
                "output": answer + CONSULT_FOOTER,
                "metadata": {
                    "category":    "fatwa",
                    "sub_category": category,
                    "topic":       topic,
                    "fatwa_id":    fatwa_id,
                    "lang":        lang,
                    "source":      "islamqa.info",
                    "link":        entry.get("link", ""),
                },
            })

    logger.info("Fatwa pairs generated: %d (from %d records)", len(pairs), len(fatwas))
    return pairs
