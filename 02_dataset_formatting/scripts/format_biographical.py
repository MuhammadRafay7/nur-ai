#!/usr/bin/env python3
"""
Generate Q&A training pairs for biography-type questions.

Covers three source files:
  - sahabah_biographies.json  (rightly_guided_caliphs, ten_promised_paradise,
                                major_companions, female_companions_sahabiyyat)
  - scholars_biographies.json  (scholars list)
  - prophets_in_islam.json     (prophets list)

The model learns to answer "Tell me about Hazrat Umar RA", "Who was Imam
Bukhari?", "Life of Prophet Ibrahim AS" with a biography-specific format —
NOT the 5-section fiqh format.

Entry point:
    generate_biographical_pairs(seed=42) -> list[dict]
    Each dict: {instruction, input, output, metadata}
    metadata: {category: "biography", sub_category: "companion"/"scholar"/"prophet", name: "..."}

Usage:
    python format_biographical.py
    python format_biographical.py --output /custom/output/biographical_pairs.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_biographical")

# ─── Paths ────────────────────────────────────────────────────────────────────

KB_DIR: Path = (
    Path(__file__).parent.parent.parent
    / "01_data_collection" / "raw" / "knowledge_bases"
)

DEFAULT_OUTPUT: Path = (
    Path(__file__).parent.parent
    / "formatted_output" / "biographical_pairs.json"
)

# ─── Question templates ────────────────────────────────────────────────────────

COMPANION_TEMPLATES = [
    "Tell me about {name} (RA).",
    "Give a brief biography of {name}.",
    "Who was {name} in Islam?",
    "What is the life story of {name} (RA)?",
    "Write a note on {name} (RA).",
    "What do we know about the life of {name}?",
]

SCHOLAR_TEMPLATES = [
    "Who was {name}?",
    "Tell me about Imam {name}.",
    "What did {name} contribute to Islam?",
    "Give a biography of {name} (RH).",
    "Who founded the {madhab} madhab?",
]

PROPHET_TEMPLATES = [
    "Tell me about Prophet {name_english} (AS).",
    "Who was Prophet {name_english} in Islam?",
    "What is the story of Prophet {name_english} (AS)?",
    "Give a brief account of the life of Prophet {name_english}.",
]


# ─── Answer builders ──────────────────────────────────────────────────────────

def _bullet_list(items: list[str]) -> str:
    """Format a list of strings as a bullet list."""
    return "\n".join(f"• {item}" for item in items)


def _first_name(full_name: str) -> str:
    """
    Return the most natural short name for a person.
    - "Abu Bakr as-Siddiq"  -> "Abu Bakr"
    - "Umm Salamah ..."     -> "Umm Salamah"
    - "Umar ibn al-Khattab" -> "Umar"
    - "Ali ibn Abi Talib"   -> "Ali"
    """
    clean = full_name.replace("(", "").replace(")", "").strip()
    parts = clean.split()
    if not parts:
        return full_name
    prefixes = {"abu", "umm", "abd"}
    if parts[0].lower() in prefixes and len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    skip_continuations = {"ibn", "bint", "al-", "bin"}
    # Return everything up to the first connector word
    name_parts = []
    for part in parts:
        if part.lower().rstrip("-") in skip_continuations:
            break
        name_parts.append(part)
        if len(name_parts) >= 2:
            break
    return " ".join(name_parts) if name_parts else parts[0]


def _companion_bullets(entry: dict[str, Any]) -> list[str]:
    """
    Return a merged list of virtue/contribution bullet points for any companion
    type, handling both the caliph format (key_virtues + major_contributions)
    and the major-companion / female-companion format (distinction + character +
    scholarly_contribution + honor + journey + service, etc.).
    """
    items: list[str] = []
    # Structured list fields (caliphs / some others)
    items.extend(entry.get("key_virtues", []))
    items.extend(entry.get("major_contributions", []))
    # Scalar narrative fields used by major_companions & sahabiyyat
    for field in (
        "distinction", "character", "scholarly_contribution",
        "honor", "journey", "service", "hadith_transmission",
        "prophet_dua_for_him", "reason_for_memory",
    ):
        val = entry.get(field)
        if val and isinstance(val, str):
            items.append(val)
    return items


def build_companion_answer(entry: dict[str, Any]) -> str:
    """Build the biography answer for a Companion/Caliph entry."""
    name = entry.get("name", "")
    arabic = entry.get("arabic", "")
    title = entry.get("title", "")
    birth = entry.get("birth", "") or entry.get("birth", "")
    death = entry.get("death", "")
    caliphate = entry.get("caliphate", "")
    # Caliphs use early_life / acceptance_of_islam;
    # major companions / sahabiyyat use accepted_islam / journey / character.
    early_life = entry.get("early_life", "")
    acceptance = entry.get("acceptance_of_islam", "") or entry.get("accepted_islam", "")
    lessons: list[str] = entry.get("lessons", [])

    # hadith_praise may be a string or a list of dicts {text, source}
    hadith_raw = (
        entry.get("hadith_praise")
        or entry.get("hadith_about_her")
        or entry.get("the_prophet's_words")
        or entry.get("prophet_comment")
        or ""
    )
    if isinstance(hadith_raw, list) and hadith_raw:
        h = hadith_raw[0]
        hadith_text = h.get("text", "")
        hadith_source = h.get("source", "")
        hadith_block = f'"{hadith_text}"\n({hadith_source})'
    elif isinstance(hadith_raw, str) and hadith_raw:
        hadith_block = f'"{hadith_raw}"'
    else:
        hadith_block = ""

    fname = _first_name(name)
    combined = _companion_bullets(entry)
    combined_bullets = _bullet_list(combined) if combined else ""
    lessons_bullets = _bullet_list(lessons) if lessons else ""

    lines: list[str] = []
    lines.append(f"**{name} (RA)**")

    header_parts = [p for p in [arabic, title] if p]
    if header_parts:
        lines.append(" | ".join(header_parts))

    lines.append("")

    # Introduction sentence — derive from early_life or acceptance
    intro_parts = []
    if early_life:
        intro_parts.append(early_life)
    if acceptance:
        intro_parts.append(acceptance)
    if intro_parts:
        lines.append(" ".join(intro_parts))
        lines.append("")

    # Birth & Death
    birth_death_parts = []
    if birth:
        birth_death_parts.append(f"Born: {birth}")
    if death:
        birth_death_parts.append(f"Died: {death}")
    if birth_death_parts:
        lines.append("**Birth & Death:**")
        lines.append(" | ".join(birth_death_parts))
        if caliphate:
            lines.append(f"Caliphate: {caliphate}")
        lines.append("")

    # Key Virtues & Contributions
    if combined_bullets:
        lines.append("**Key Virtues & Contributions:**")
        lines.append(combined_bullets)
        lines.append("")

    # Hadith praise
    if hadith_block:
        lines.append(f"**The Prophet ﷺ's Words about {fname}:**")
        lines.append(hadith_block)
        lines.append("")

    # Lessons
    if lessons_bullets:
        lines.append(f"**Lessons from {fname}'s Life:**")
        lines.append(lessons_bullets)

    return "\n".join(lines).strip()


def build_scholar_answer(entry: dict[str, Any]) -> str:
    """Build the biography answer for a Scholar entry."""
    name = entry.get("name", "")
    arabic = entry.get("arabic", "")
    title = entry.get("title", "")
    born = entry.get("born", "")
    died = entry.get("died", "")
    origin = entry.get("origin", "")
    madhab = entry.get("madhab", "")
    specialty = entry.get("specialty", "")
    teachers: list[str] = entry.get("teachers", [])
    students: list[str] = entry.get("students", [])
    key_works: list[str] = entry.get("key_works", [])
    contributions: list[str] = entry.get("contributions", [])
    historical_note = entry.get("historical_note", "")
    quote = entry.get("quote", "")

    # Some entries use "teacher" (singular) instead of "teachers"
    if not teachers and entry.get("teacher"):
        teachers = [entry["teacher"]]
    # Some entries use "students" indirectly or "student"
    if not students and entry.get("student"):
        students = [entry["student"]]

    works_bullets = _bullet_list(key_works) if key_works else ""
    contrib_bullets = _bullet_list(contributions) if contributions else ""

    lines: list[str] = []
    lines.append(f"**{name} (RH)**")

    header_parts = [p for p in [arabic, title] if p]
    if header_parts:
        lines.append(" | ".join(header_parts))

    lines.append("")

    # Introduction based on madhab/specialty
    if madhab:
        lines.append(
            f"{name} was a major Islamic scholar and founder of the {madhab} school of jurisprudence."
        )
    elif specialty:
        lines.append(f"{name} was a major Islamic scholar specializing in {specialty}.")
    lines.append("")

    # Life section
    life_parts = []
    if born:
        life_parts.append(f"Born: {born}")
    if died:
        life_parts.append(f"Died: {died}")
    if origin:
        life_parts.append(f"Origin: {origin}")

    spec_parts = []
    if madhab:
        spec_parts.append(f"Madhab: {madhab}")
    if specialty:
        spec_parts.append(f"Specialty: {specialty}")

    if life_parts or spec_parts:
        lines.append("**Life:**")
        if life_parts:
            lines.append(" | ".join(life_parts))
        if spec_parts:
            lines.append(" | ".join(spec_parts))
        lines.append("")

    # Teachers & Students
    if teachers or students:
        lines.append("**Teachers & Students:**")
        if teachers:
            lines.append(f"Notable teachers: {', '.join(teachers)}")
        if students:
            lines.append(f"Notable students: {', '.join(students)}")
        lines.append("")

    # Major Works
    if works_bullets:
        lines.append("**Major Works:**")
        lines.append(works_bullets)
        lines.append("")

    # Key Contributions
    if contrib_bullets:
        lines.append("**Key Contributions:**")
        lines.append(contrib_bullets)
        lines.append("")

    # Quote
    if quote:
        lines.append("**His Words:**")
        lines.append(f'"{quote}"')
        lines.append("")

    # Historical note
    if historical_note:
        lines.append("**Historical Note:**")
        lines.append(historical_note)

    return "\n".join(lines).strip()


def build_prophet_answer(entry: dict[str, Any]) -> str:
    """Build the biography answer for a Prophet entry."""
    name_english = entry.get("name_english", "")
    name_arabic = entry.get("name_arabic", "")
    title = entry.get("title", "")
    key_events: list[str] = _prophet_key_events(entry)
    quran_refs: list[str] = entry.get("quran_references", [])
    dua = entry.get("dua_for_repentance") or entry.get("dua", "")
    lessons: list[str] = entry.get("lessons", [])
    mentioned_in_quran = entry.get("mentioned_in_quran", True)

    events_bullets = _bullet_list(key_events) if key_events else ""
    lessons_bullets = _bullet_list(lessons) if lessons else ""
    refs_str = ", ".join(quran_refs) if quran_refs else ""

    lines: list[str] = []

    title_part = f" — {title}" if title else ""
    lines.append(f"**Prophet {name_english} (AS)**")
    lines.append(f"{name_arabic}{title_part}")
    lines.append("")

    # Key Events
    if events_bullets:
        lines.append("**Key Events in His Life:**")
        lines.append(events_bullets)
        lines.append("")

    # Mentioned in Quran
    if refs_str:
        lines.append("**Mentioned in the Quran:**")
        note = "His story is mentioned across multiple Quranic chapters."
        if mentioned_in_quran is False:
            note = "He is among the prophets not explicitly named in the Quran."
        lines.append(f"{refs_str} — {note}")
        lines.append("")

    # Dua
    if dua:
        lines.append("**His Dua:**")
        lines.append(f'"{dua}"')
        lines.append("")

    # Lessons
    if lessons_bullets:
        lines.append("**Lessons:**")
        lines.append(lessons_bullets)

    return "\n".join(lines).strip()


# ─── Pair generators ──────────────────────────────────────────────────────────

def _make_pairs_for_companion(
    entry: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    """Return up to 5 Q&A pairs for a single companion/caliph entry."""
    name = entry.get("name", "")
    if not name:
        return []

    # Sparsity check: need at least 2 content items across all bullet fields
    if len(_companion_bullets(entry)) < 2:
        logger.debug("Skipping sparse companion: %s", name)
        return []

    answer = build_companion_answer(entry)
    chosen = rng.sample(templates, min(5, len(templates)))

    pairs = []
    for tmpl in chosen:
        question = tmpl.format(name=name)
        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "category": "biography",
                "sub_category": "companion",
                "name": name,
            },
        })
    return pairs


def _make_pairs_for_scholar(
    entry: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    """Return up to 5 Q&A pairs for a single scholar entry."""
    name = entry.get("name", "")
    if not name:
        return []

    # Sparsity check: need at least 2 contributions or key_works
    contributions = entry.get("contributions", [])
    key_works = entry.get("key_works", [])
    if len(contributions) + len(key_works) < 2:
        logger.debug("Skipping sparse scholar: %s", name)
        return []

    madhab = entry.get("madhab", "")
    answer = build_scholar_answer(entry)

    # Build a template pool — exclude madhab template if no madhab
    available = [t for t in templates if "{madhab}" not in t or madhab]
    chosen = rng.sample(available, min(5, len(available)))

    pairs = []
    for tmpl in chosen:
        # Strip "Imam " prefix from name when it already contains it
        display_name = name
        if tmpl.startswith("Tell me about Imam ") and name.lower().startswith("imam "):
            display_name = name[5:].strip()

        question = tmpl.format(name=display_name, madhab=madhab)
        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "category": "biography",
                "sub_category": "scholar",
                "name": name,
            },
        })
    return pairs


def _prophet_key_events(entry: dict[str, Any]) -> list[str]:
    """Return key events for a prophet, falling back to islamic_belief or miracles."""
    events = entry.get("key_events", [])
    if len(events) < 2:
        # Isa (Jesus) uses islamic_belief; others may have miracles
        events = events + entry.get("islamic_belief", []) + entry.get("miracles", [])
    return events


def _make_pairs_for_prophet(
    entry: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    """Return up to 4 Q&A pairs for a single prophet entry."""
    name_english = entry.get("name_english", "")
    if not name_english:
        return []

    # Sparsity check: need at least 2 key_events (including fallback fields)
    key_events = _prophet_key_events(entry)
    if len(key_events) < 2:
        logger.debug("Skipping sparse prophet: %s", name_english)
        return []

    answer = build_prophet_answer(entry)
    chosen = rng.sample(templates, min(4, len(templates)))

    pairs = []
    for tmpl in chosen:
        question = tmpl.format(name_english=name_english)
        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "category": "biography",
                "sub_category": "prophet",
                "name": name_english,
            },
        })
    return pairs


# ─── Data loaders ─────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _collect_companions(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect all companion entries from the sahabah JSON."""
    entries: list[dict[str, Any]] = []

    # Rightly Guided Caliphs — full entries
    for entry in data.get("rightly_guided_caliphs", []):
        entries.append(entry)

    # Ten Promised Paradise — individual_notes have abbreviated data;
    # the first four overlap with caliphs so we skip them and use individual_notes
    # for the remaining six (Talhah, Zubayr, etc.) but they only have 'distinction'
    # not key_virtues — build a synthetic entry so the sparsity check can pass.
    individual_notes = (
        data.get("ten_promised_paradise", {}).get("individual_notes", [])
    )
    caliph_names = {e.get("name") for e in data.get("rightly_guided_caliphs", [])}
    for note in individual_notes:
        name = note.get("name", "")
        if name in caliph_names:
            continue  # already processed above
        distinction = note.get("distinction", "")
        source = note.get("source", "")
        title = note.get("title", "")
        # Synthesize a minimal companion entry
        synthetic: dict[str, Any] = {
            "name": name,
            "arabic": "",
            "title": title,
            "key_virtues": [distinction] if distinction else [],
            "major_contributions": [
                f"One of the Ten Companions promised Paradise by the Prophet ﷺ. "
                f"(Source: {source})"
            ] if source else [],
            "lessons": [],
        }
        entries.append(synthetic)

    # Major Companions
    for entry in data.get("major_companions", []):
        entries.append(entry)

    # Female Companions
    for entry in data.get("female_companions_sahabiyyat", []):
        entries.append(entry)

    return entries


# ─── Main generator ───────────────────────────────────────────────────────────

def generate_biographical_pairs(seed: int = 42) -> list[dict]:
    """
    Generate Q&A biography training pairs from all three knowledge bases.

    Returns a list of dicts:
        {instruction, input, output, metadata}
    where metadata = {category: "biography", sub_category: ..., name: ...}
    """
    rng = random.Random(seed)
    pairs: list[dict[str, Any]] = []

    # ── Companions ────────────────────────────────────────────────────────────
    sahabah_path = KB_DIR / "sahabah_biographies.json"
    if sahabah_path.exists():
        sahabah_data = _load_json(sahabah_path)
        companions = _collect_companions(sahabah_data)
        logger.info("Loaded %d companion entries", len(companions))
        for entry in companions:
            pairs.extend(
                _make_pairs_for_companion(entry, rng, COMPANION_TEMPLATES)
            )
    else:
        logger.warning("File not found: %s", sahabah_path)

    # ── Scholars ─────────────────────────────────────────────────────────────
    scholars_path = KB_DIR / "scholars_biographies.json"
    if scholars_path.exists():
        scholars_data = _load_json(scholars_path)
        scholars = scholars_data.get("scholars", [])
        logger.info("Loaded %d scholar entries", len(scholars))
        for entry in scholars:
            pairs.extend(
                _make_pairs_for_scholar(entry, rng, SCHOLAR_TEMPLATES)
            )
    else:
        logger.warning("File not found: %s", scholars_path)

    # ── Prophets ──────────────────────────────────────────────────────────────
    prophets_path = KB_DIR / "prophets_in_islam.json"
    if prophets_path.exists():
        prophets_data = _load_json(prophets_path)
        prophets = prophets_data.get("prophets", [])
        logger.info("Loaded %d prophet entries", len(prophets))
        for entry in prophets:
            pairs.extend(
                _make_pairs_for_prophet(entry, rng, PROPHET_TEMPLATES)
            )
    else:
        logger.warning("File not found: %s", prophets_path)

    logger.info("Total biographical pairs generated: %d", len(pairs))
    return pairs


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate biographical Q&A training pairs for the Islamic AI engine."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output JSON file (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for template sampling (default: 42)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    pairs = generate_biographical_pairs(seed=args.seed)

    if not pairs:
        logger.error("No pairs generated — check that the knowledge base files exist.")
        sys.exit(1)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "metadata": {
            "title": "Biographical Q&A Training Pairs",
            "description": (
                "Biography-specific question-answer pairs covering Companions, "
                "Islamic scholars, and Quranic prophets. "
                "Uses a narrative biography format, NOT the fiqh 5-section format."
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "seed": args.seed,
            "total_pairs": len(pairs),
            "sub_categories": {
                "companion": sum(
                    1 for p in pairs
                    if p["metadata"]["sub_category"] == "companion"
                ),
                "scholar": sum(
                    1 for p in pairs
                    if p["metadata"]["sub_category"] == "scholar"
                ),
                "prophet": sum(
                    1 for p in pairs
                    if p["metadata"]["sub_category"] == "prophet"
                ),
            },
        },
        "pairs": pairs,
    }

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    print(f"Wrote {len(pairs)} pairs to {output_path}")
    sub = output["metadata"]["sub_categories"]
    print(
        f"  companions: {sub['companion']}  |  "
        f"scholars: {sub['scholar']}  |  "
        f"prophets: {sub['prophet']}"
    )


if __name__ == "__main__":
    main()
