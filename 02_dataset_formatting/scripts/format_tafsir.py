#!/usr/bin/env python3
"""
format_tafsir.py — Generate Q&A pairs from the three English tafsir files.

Sources (raw/tafsir/):
  - tafsir_ibn_kathir_en.json    (6,236 verses)
  - tafsir_maarif_ul_quran_en.json (6,236 verses)
  - tafsir_tazkirul_quran_en.json  (1,952 verses)

Structure: {"verses": [{"verse_key": "2:1", "text": "<p>HTML...</p>"}]}
Cross-references quran_full.json for Arabic text, transliteration, and English translation.
"""

from __future__ import annotations

import json
import random
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

# ─── Paths ────────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).parent
PHASE1_RAW  = SCRIPTS_DIR.parent.parent / "01_data_collection" / "raw"
TAFSIR_DIR  = PHASE1_RAW / "tafsir"
QURAN_PATH  = PHASE1_RAW / "quran" / "quran_full.json"

# ─── HTML stripping ───────────────────────────────────────────────────────────

class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)


def strip_html(html: str) -> str:
    """Strip HTML tags and return clean plain text."""
    parser = _TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ─── Quran verse index ────────────────────────────────────────────────────────

def build_verse_index(quran_path: Path) -> dict[str, dict[str, Any]]:
    """Build a dict keyed by verse_key ('1:1') with surah/ayah metadata."""
    data = json.loads(quran_path.read_text(encoding="utf-8"))
    index: dict[str, dict[str, Any]] = {}
    for surah in data.get("surahs", []):
        surah_num  = surah["surah_number"]
        surah_name = surah["name_transliteration"]   # e.g. "Al-Fatiha"
        surah_name_en = surah["name_english"]        # e.g. "The Opening"
        for ayah in surah.get("ayahs", []):
            vk = ayah["verse_key"]
            index[vk] = {
                "surah_num":    surah_num,
                "surah_name":   surah_name,
                "surah_name_en": surah_name_en,
                "ayah_num":     ayah["ayah_number"],
                "arabic":       ayah.get("arabic_text", ""),
                "english":      ayah.get("english_translation", ""),
                "transliteration": ayah.get("transliteration", ""),
            }
    return index


# ─── Q&A templates ────────────────────────────────────────────────────────────

_IK_TEMPLATES = [
    "What does Ibn Kathir say about {surah_name} {surah_num}:{ayah_num}?",
    "Explain the tafsir of Surah {surah_name} verse {ayah_num} according to Ibn Kathir.",
    "What is the meaning of Ayah {ayah_num} in Surah {surah_name}?",
    "Give the tafsir commentary on {surah_name} ({surah_num}:{ayah_num}).",
    'What is the explanation of the verse: "{english_short}"?',
]

_MAARIF_TEMPLATES = [
    "What does Maarif ul Quran say about Surah {surah_name} verse {ayah_num}?",
    "Explain {surah_name} {surah_num}:{ayah_num} according to Mufti Shafi Usmani.",
    "What is the tafsir commentary on verse {ayah_num} of Surah {surah_name}?",
    "Describe the meaning of {surah_name} ({surah_num}:{ayah_num}).",
    'Explain the verse: "{english_short}" from Surah {surah_name}.',
]

_TAZKIRUL_TEMPLATES = [
    "What does Tazkirul Quran say about {surah_name} {surah_num}:{ayah_num}?",
    "Explain Ayah {ayah_num} of Surah {surah_name} according to Tazkirul Quran.",
    "What is the commentary on {surah_name} verse {ayah_num}?",
    "Give a scholarly explanation of {surah_name} ({surah_num}:{ayah_num}).",
]

_TAFSIR_META = {
    "tafsir_ibn_kathir_en": {
        "scholar": "Ibn Kathir",
        "book":    "Tafsir Ibn Kathir",
        "templates": _IK_TEMPLATES,
        "category": "tafsir",
    },
    "tafsir_maarif_ul_quran_en": {
        "scholar": "Mufti Muhammad Shafi (Ma'arif ul Quran)",
        "book":    "Ma'arif ul Quran",
        "templates": _MAARIF_TEMPLATES,
        "category": "tafsir",
    },
    "tafsir_tazkirul_quran_en": {
        "scholar": "Maulana Wahiduddin Khan (Tazkirul Quran)",
        "book":    "Tazkirul Quran",
        "templates": _TAZKIRUL_TEMPLATES,
        "category": "tafsir",
    },
}

MIN_TAFSIR_CHARS = 80   # skip very short / stub tafsir entries
MAX_TAFSIR_CHARS = 900  # truncate long explanations to keep output manageable


def _format_answer(
    verse: dict[str, Any],
    tafsir_text: str,
    scholar: str,
) -> str:
    parts: list[str] = []

    sname = verse["surah_name"]
    snum  = verse["surah_num"]
    anum  = verse["ayah_num"]
    arabic = verse["arabic"]
    english = verse["english"]
    translit = verse.get("transliteration", "")

    parts.append(f"Allah ﷻ says in Surah {sname} ({snum}:{anum}):\n")
    if arabic:
        parts.append(arabic)
    if translit:
        parts.append(f"Transliteration: {translit}")
    parts.append(f'\nTranslation (Sahih International):\n"{english}"')

    # Truncate tafsir text if needed
    if len(tafsir_text) > MAX_TAFSIR_CHARS:
        tafsir_text = tafsir_text[:MAX_TAFSIR_CHARS].rsplit(" ", 1)[0] + "..."

    parts.append(f"\n{scholar} explains:\n{tafsir_text}")
    return "\n".join(parts)


# ─── Generator ────────────────────────────────────────────────────────────────

def generate_tafsir_pairs(seed: int = 42, max_per_tafsir: int = 3000) -> list[dict[str, Any]]:
    """Generate Q&A pairs from the three English tafsir files.

    Args:
        seed: Random seed for reproducibility.
        max_per_tafsir: Maximum pairs to generate per tafsir book.

    Returns:
        List of Q&A pair dicts.
    """
    if not QURAN_PATH.exists():
        print(f"[format_tafsir] quran_full.json not found at {QURAN_PATH}", file=sys.stderr)
        return []

    verse_index = build_verse_index(QURAN_PATH)
    rng = random.Random(seed)
    all_pairs: list[dict[str, Any]] = []

    for tafsir_key, meta in _TAFSIR_META.items():
        tafsir_path = TAFSIR_DIR / f"{tafsir_key}.json"
        if not tafsir_path.exists():
            print(f"[format_tafsir] Missing: {tafsir_path.name} — skipping", file=sys.stderr)
            continue

        data = json.loads(tafsir_path.read_text(encoding="utf-8"))
        verses = data.get("verses", [])

        scholar   = meta["scholar"]
        book      = meta["book"]
        templates = meta["templates"]
        category  = meta["category"]

        book_pairs: list[dict[str, Any]] = []

        for entry in verses:
            vk   = entry.get("verse_key", "")
            raw  = entry.get("text", "")
            if not vk or not raw:
                continue

            verse_meta = verse_index.get(vk)
            if not verse_meta:
                continue

            tafsir_text = strip_html(raw)
            if len(tafsir_text) < MIN_TAFSIR_CHARS:
                continue

            # Prepare template variables
            english = verse_meta["english"]
            english_short = (english[:60].rstrip() + "...") if len(english) > 60 else english
            fmt_vars = {
                "surah_name":    verse_meta["surah_name"],
                "surah_num":     verse_meta["surah_num"],
                "ayah_num":      verse_meta["ayah_num"],
                "english_short": english_short,
            }

            # Pick one template per verse to keep dataset diverse
            template = rng.choice(templates)
            question = template.format(**fmt_vars)
            answer   = _format_answer(verse_meta, tafsir_text, scholar)

            book_pairs.append({
                "instruction": question,
                "input":       "",
                "output":      answer,
                "metadata": {
                    "category":  category,
                    "source":    book,
                    "verse_key": vk,
                    "surah":     verse_meta["surah_name"],
                    "ayah":      verse_meta["ayah_num"],
                },
            })

        # Sample down if over limit
        if len(book_pairs) > max_per_tafsir:
            rng.shuffle(book_pairs)
            book_pairs = book_pairs[:max_per_tafsir]

        print(
            f"[format_tafsir] {book}: {len(book_pairs)} pairs from {len(verses)} verses",
            file=sys.stderr,
        )
        all_pairs.extend(book_pairs)

    print(f"[format_tafsir] Total tafsir pairs: {len(all_pairs)}", file=sys.stderr)
    return all_pairs


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pairs = generate_tafsir_pairs()
    for p in pairs[:3]:
        print(json.dumps(p, ensure_ascii=False, indent=2))
        print("---")
    print(f"\nTotal: {len(pairs)} pairs")
