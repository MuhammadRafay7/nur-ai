#!/usr/bin/env python3
"""
format_translation.py — Generate Q&A training pairs focused on Quran
translation, recitation, and text lookup.

The model learns to answer questions like:
  - "Translate Surah Al-Ikhlas"
  - "What does verse 2:255 say?"
  - "Give the Arabic and translation of Ayat al-Kursi"

Three generation categories:
  1. Full-surah translation (Juz Amma, surah 78-114, <= 30 ayat)
  2. Famous individual verses / verse groups with a brief significance note
  3. "What does Surah X verse N say?" for a sample from the first 10 surahs

Entry point:
  generate_translation_pairs(seed: int = 42) -> list[dict]
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

# ─── Paths ────────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).parent
RAW_DIR     = SCRIPTS_DIR.parent.parent / "01_data_collection" / "raw"
QURAN_PATH  = RAW_DIR / "quran" / "quran_full.json"

# ─── Question templates ───────────────────────────────────────────────────────

_FULL_SURAH_QUESTIONS: list[str] = [
    "Translate Surah {name}.",
    "Give me the full text and translation of Surah {name}.",
    "Recite Surah {name} with translation.",
    "What does Surah {name} say in English?",
]

_FAMOUS_VERSE_QUESTIONS: list[str] = [
    "What is {common_name}?",
    "Give me the Arabic and translation of {common_name}.",
    "Translate {verse_key} from the Quran.",
    "What does {verse_key} say?",
]

_SINGLE_VERSE_QUESTIONS: list[str] = [
    "What does Surah {name} verse {ayah_number} say?",
    "Translate verse {ayah_number} of Surah {name}.",
    "Give the Arabic text and translation of {verse_key}.",
    "What does {verse_key} mean?",
    "Recite and translate {verse_key}.",
]

# ─── Famous verse definitions ─────────────────────────────────────────────────
# Each entry: (start_verse_key, count, common_name, significance_note)

_FAMOUS_VERSE_GROUPS: list[tuple[str, int, str, str]] = [
    (
        "2:255", 1,
        "Ayat al-Kursi",
        "Ayat al-Kursi (the Throne Verse) is considered the greatest verse of "
        "the Quran. The Prophet Muhammad ﷺ taught that reciting it after every "
        "obligatory prayer is among the most virtuous of acts.",
    ),
    (
        "2:286", 1,
        "the last verse of Surah Al-Baqarah (2:286)",
        "The last verse of Surah Al-Baqarah contains a beautiful supplication "
        "affirming that Allah does not burden a soul beyond what it can bear, "
        "and ends with du'a for forgiveness and mercy.",
    ),
    (
        "3:18", 1,
        "the Shahada verse (3:18)",
        "This verse contains the testimony of divine oneness (Tawhid), witnessed "
        "by Allah Himself, His angels, and the people of knowledge — affirming "
        "that there is no deity worthy of worship except Allah.",
    ),
    (
        "36:1", 3,
        "the opening verses of Surah Ya-Sin (36:1-3)",
        "Surah Ya-Sin is often called the 'heart of the Quran'. The Prophet ﷺ "
        "is said to have described it as such, and it is widely recited for "
        "the dying, at funerals, and in seeking Allah's mercy.",
    ),
    (
        "55:1", 4,
        "the opening verses of Surah Al-Rahman (55:1-4)",
        "Surah Al-Rahman opens by naming Allah as 'Ar-Rahman' (the Most "
        "Merciful) and lists His blessings, with the refrain 'Which of the "
        "favors of your Lord will you deny?' repeated throughout.",
    ),
    (
        "112:1", 4,
        "Surah Al-Ikhlas (112:1-4)",
        "Surah Al-Ikhlas is a declaration of pure monotheism. The Prophet ﷺ "
        "said it is equal in reward to one-third of the Quran, as it "
        "encapsulates the essence of Tawhid.",
    ),
    (
        "113:1", 5,
        "Surah Al-Falaq (113:1-5)",
        "Surah Al-Falaq is one of the two 'seeking refuge' surahs (Al-Mu'awwidhatayn). "
        "The Prophet ﷺ regularly recited Al-Falaq and An-Nas for protection, "
        "especially before sleep.",
    ),
    (
        "114:1", 6,
        "Surah An-Nas (114:1-6)",
        "Surah An-Nas is the final surah of the Quran, seeking refuge in Allah "
        "from the whispering of Shaytan. Together with Al-Falaq it forms the "
        "Al-Mu'awwidhatayn, the two protective surahs.",
    ),
    (
        "1:1", 7,
        "Surah Al-Fatiha (1:1-7)",
        "Surah Al-Fatiha is the opening chapter of the Quran and is recited in "
        "every unit (rak'ah) of the daily prayers. The Prophet ﷺ called it "
        "'Umm Al-Kitab' (Mother of the Book).",
    ),
    (
        "2:1", 5,
        "the opening verses of Surah Al-Baqarah (2:1-5)",
        "The opening verses of Surah Al-Baqarah describe the qualities of the "
        "God-conscious (muttaqeen) who believe in the unseen, establish prayer, "
        "spend in charity, and are certain of the Hereafter.",
    ),
]

# ─── Data loading ─────────────────────────────────────────────────────────────

def _load_quran() -> tuple[list[dict], dict[str, tuple[dict, dict]]]:
    """Return (surahs list, verse_index mapping verse_key -> (surah, ayah))."""
    with open(QURAN_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    surahs: list[dict] = data["surahs"]
    verse_index: dict[str, tuple[dict, dict]] = {}
    for surah in surahs:
        for ayah in surah["ayahs"]:
            verse_index[ayah["verse_key"]] = (surah, ayah)
    return surahs, verse_index

# ─── Answer formatters ────────────────────────────────────────────────────────

def _fmt_ayah_block(ayah: dict) -> str:
    """Single-ayah block: arabic / transliteration / translation lines."""
    lines = [
        f"**Verse {ayah['ayah_number']}:**",
        ayah["arabic_text"],
        f"Transliteration: {ayah['transliteration']}",
        f"Translation: \"{ayah['english_translation']}\"",
    ]
    return "\n".join(lines)


def _fmt_full_surah_answer(surah: dict) -> str:
    """Full surah answer block."""
    header = (
        f"**Surah {surah['name_transliteration']} ({surah['surah_number']}) "
        f"— {surah['name_english']}**\n"
        f"{surah['revelation_type'].capitalize()} Surah | "
        f"{surah['ayah_count']} Ayat"
    )
    ayah_blocks = "\n\n".join(_fmt_ayah_block(a) for a in surah["ayahs"])
    return f"{header}\n\n{ayah_blocks}"


def _fmt_single_verse_answer(surah: dict, ayah: dict) -> str:
    """Single verse answer block."""
    header = (
        f"**Surah {surah['name_transliteration']} ({ayah['verse_key']})**"
    )
    body = (
        f"{ayah['arabic_text']}\n"
        f"Transliteration: {ayah['transliteration']}\n"
        f"Translation: \"{ayah['english_translation']}\""
    )
    return f"{header}\n\n{body}"


def _fmt_famous_verse_answer(
    surah: dict,
    ayahs: list[dict],
    common_name: str,
    note: str,
    verse_key: str,
) -> str:
    """Famous verse answer block with brief note."""
    # Title: use common_name as the label, surah info as context
    header = (
        f"**{common_name} — Surah {surah['name_transliteration']} ({verse_key})**"
    )
    if len(ayahs) == 1:
        a = ayahs[0]
        body = (
            f"{a['arabic_text']}\n"
            f"Transliteration: {a['transliteration']}\n"
            f"Translation: \"{a['english_translation']}\""
        )
    else:
        body = "\n\n".join(_fmt_ayah_block(a) for a in ayahs)

    return f"{header}\n\n{body}\n\n**Brief Note:**\n{note}"

# ─── Pair builders ────────────────────────────────────────────────────────────

def _build_full_surah_pairs(surahs: list[dict], rng: random.Random) -> list[dict]:
    """Category 1: full surah translation for Juz Amma (<= 30 ayat)."""
    pairs: list[dict] = []
    for surah in surahs:
        num = surah["surah_number"]
        if num < 78:
            continue
        if surah["ayah_count"] > 30:
            continue  # too long

        answer = _fmt_full_surah_answer(surah)
        questions = [
            t.format(name=surah["name_transliteration"])
            for t in _FULL_SURAH_QUESTIONS
        ]
        for q in questions:
            pairs.append({
                "instruction": q,
                "input":       "",
                "output":       answer,
                "metadata": {
                    "category":     "translation",
                    "type":         "full_surah",
                    "surah_number": num,
                    "verse_key":    None,
                },
            })
    return pairs


def _build_famous_verse_pairs(
    verse_index: dict[str, tuple[dict, dict]],
    rng: random.Random,
) -> list[dict]:
    """Category 2: famous individual verses / verse groups with context note."""
    pairs: list[dict] = []
    for start_key, count, common_name, note in _FAMOUS_VERSE_GROUPS:
        if start_key not in verse_index:
            continue
        surah, first_ayah = verse_index[start_key]
        start_num = first_ayah["ayah_number"]
        surah_num = surah["surah_number"]

        # Collect the ayahs for this group
        ayahs: list[dict] = []
        for offset in range(count):
            vk = f"{surah_num}:{start_num + offset}"
            if vk in verse_index:
                ayahs.append(verse_index[vk][1])

        if not ayahs:
            continue

        # Determine the verse_key label (range or single)
        if len(ayahs) == 1:
            verse_key_label = start_key
        else:
            verse_key_label = f"{surah_num}:{start_num}-{start_num + len(ayahs) - 1}"

        answer = _fmt_famous_verse_answer(
            surah, ayahs, common_name, note, verse_key_label
        )

        questions = [
            t.format(common_name=common_name, verse_key=verse_key_label)
            for t in _FAMOUS_VERSE_QUESTIONS
        ]
        for q in questions:
            pairs.append({
                "instruction": q,
                "input":       "",
                "output":       answer,
                "metadata": {
                    "category":     "translation",
                    "type":         "famous_verse",
                    "surah_number": surah_num,
                    "verse_key":    verse_key_label,
                },
            })
    return pairs


def _build_verse_lookup_pairs(
    surahs: list[dict],
    verse_index: dict[str, tuple[dict, dict]],
    rng: random.Random,
) -> list[dict]:
    """Category 3: individual verse lookup for first 10 surahs."""
    pairs: list[dict] = []
    first_ten = [s for s in surahs if s["surah_number"] <= 10]

    for surah in first_ten:
        ayahs = surah["ayahs"]
        # Sample up to 5 ayahs, always include ayah 1 if possible
        sample_size = min(5, len(ayahs))
        sampled = rng.sample(ayahs, sample_size)
        # Ensure first ayah is included for variety
        first = ayahs[0]
        if first not in sampled:
            sampled[0] = first

        for ayah in sampled:
            answer = _fmt_single_verse_answer(surah, ayah)
            questions = [
                t.format(
                    name=surah["name_transliteration"],
                    ayah_number=ayah["ayah_number"],
                    verse_key=ayah["verse_key"],
                )
                for t in _SINGLE_VERSE_QUESTIONS
            ]
            # Pick 2-3 question variants to avoid padding with too many near-dups
            chosen_qs = rng.sample(questions, min(3, len(questions)))
            for q in chosen_qs:
                pairs.append({
                    "instruction": q,
                    "input":       "",
                    "output":       answer,
                    "metadata": {
                        "category":     "translation",
                        "type":         "single_verse",
                        "surah_number": surah["surah_number"],
                        "verse_key":    ayah["verse_key"],
                    },
                })
    return pairs

# ─── Public entry point ───────────────────────────────────────────────────────

def generate_translation_pairs(seed: int = 42) -> list[dict]:
    """
    Generate Q&A training pairs for translation / recitation questions.

    Returns a list of dicts with keys:
        instruction : str   — the question
        response    : str   — the clean formatted answer
        metadata    : dict  — category, type, surah_number, verse_key
    """
    rng = random.Random(seed)
    surahs, verse_index = _load_quran()

    pairs: list[dict] = []
    pairs.extend(_build_full_surah_pairs(surahs, rng))
    pairs.extend(_build_famous_verse_pairs(verse_index, rng))
    pairs.extend(_build_verse_lookup_pairs(surahs, verse_index, rng))

    # Shuffle so categories are interleaved in the output
    rng.shuffle(pairs)
    return pairs


# ─── CLI smoke-test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    pairs = generate_translation_pairs()
    print(f"Generated {len(pairs)} pairs.")
    type_counts: dict[str, int] = {}
    for p in pairs:
        t = p["metadata"]["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    print()
    # Print one example of each type
    shown: set[str] = set()
    for p in pairs:
        t = p["metadata"]["type"]
        if t not in shown:
            shown.add(t)
            print(f"=== Example [{t}] ===")
            print(f"Q: {p['instruction']}")
            # Truncate long answers
            ans = p["response"]
            if len(ans) > 600:
                ans = ans[:600] + "\n...[truncated]"
            print(f"A:\n{ans}")
            print()
        if len(shown) == 3:
            break
