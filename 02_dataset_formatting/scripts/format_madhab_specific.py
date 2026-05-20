#!/usr/bin/env python3
"""
Generate Q&A training pairs for school/sect-specific Islamic jurisprudence questions.

Covers questions such as:
  - "What does the Hanafi madhab say about X?"
  - "What is the Sunni position on Y?"
  - "Tell me about the Shafi'i school."

Data sources:
  - madhab_comparative.json  — madhab_profiles (4 profiles) + comparative_rulings (14 rulings)
  - comprehensive_topics.json — topics list with per-madhab fiqh positions

Target: 200–350 pairs.

Entry point:
    pairs = generate_madhab_pairs(seed=42)

Usage:
    python format_madhab_specific.py
    python format_madhab_specific.py --output-dir /custom/output
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

logger = logging.getLogger("format_madhab_specific")

# ─── Paths ────────────────────────────────────────────────────────────────────

KB_DIR: Path = (
    Path(__file__).parent.parent.parent
    / "01_data_collection" / "raw" / "knowledge_bases"
)
DEFAULT_OUTPUT_DIR: Path = (
    Path(__file__).parent.parent / "formatted_output" / "madhab_specific"
)

# ─── Constants ────────────────────────────────────────────────────────────────

SCHOOLS = ("Hanafi", "Maliki", "Shafi'i", "Hanbali")

# Keys used in the comparative_rulings "rulings" dict and in comprehensive_topics "fiqh"
RULING_KEY: dict[str, str] = {
    "Hanafi": "Hanafi",
    "Maliki": "Maliki",
    "Shafi'i": "Shafi'i",
    "Hanbali": "Hanbali",
}

# Keys used in comprehensive_topics fiqh sub-dict (note: shafi without apostrophe)
TOPIC_FIQH_KEY: dict[str, str] = {
    "Hanafi": "hanafi",
    "Maliki": "maliki",
    "Shafi'i": "shafi",
    "Hanbali": "hanbali",
}

# Geographic spread lookup (supplement the madhab_profiles data)
GEO_SPREAD: dict[str, str] = {
    "Hanafi": (
        "The Hanafi madhab is the most widely followed school numerically, "
        "predominant in South Asia (Pakistan, India, Bangladesh, Afghanistan), "
        "Turkey, Central Asia, the Balkans, and parts of the Arab world."
    ),
    "Maliki": (
        "The Maliki madhab is dominant across North Africa (Morocco, Algeria, "
        "Tunisia, Libya), West Africa, Sudan, and parts of Egypt and the Gulf."
    ),
    "Shafi'i": (
        "The Shafi'i madhab is widely followed in Egypt, East Africa, and "
        "Southeast Asia — particularly Indonesia, Malaysia, Brunei, and parts "
        "of the Philippines and South Asia."
    ),
    "Hanbali": (
        "The Hanbali madhab is the official school of Saudi Arabia and is "
        "followed in Qatar, parts of the UAE and Kuwait, and by communities "
        "influenced by Salafi scholarship worldwide."
    ),
}

CONSULT_FOOTER = (
    "\n\n*For your specific situation, please consult a qualified Islamic scholar "
    "who can consider all relevant circumstances.*"
)

IKHTILAF_NOTE = (
    "**Note:** Differences between madhabs are valid scholarly disagreements "
    "(ikhtilaf) — all four schools are accepted within Sunni Islam."
)

# ─── Question templates ───────────────────────────────────────────────────────

RULING_TEMPLATES: list[str] = [
    "What does the {school} madhab say about {topic}?",
    "What is the {school} position on {topic}?",
    "How does the {school} school rule on {topic}?",
    "Explain the {school} ruling on {topic}.",
    "What is the {school} view regarding {topic}?",
]

SUNNI_TEMPLATES: list[str] = [
    "What is the Sunni position on {topic}?",
    "What do Sunni Muslims believe about {topic}?",
    "What does mainstream Sunni Islam say about {topic}?",
    "How do Sunni scholars approach the question of {topic}?",
]

PROFILE_TEMPLATES: list[str] = [
    "Tell me about the {name} madhab.",
    "What is the {name} school of thought?",
    "Who founded the {name} madhab and what are its principles?",
    "Describe the methodology of the {name} school.",
    "Give me an overview of the {name} madhab.",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_pair(
    instruction: str,
    output: str,
    school: str,
    topic: str,
    consult_scholar: bool = False,
) -> dict[str, Any]:
    if consult_scholar:
        output = output + CONSULT_FOOTER
    return {
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip(),
        "metadata": {
            "category": "madhab_specific",
            "school": school,
            "topic": topic,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _load(kb_dir: Path, filename: str) -> dict[str, Any]:
    path = kb_dir / filename
    if not path.exists():
        logger.warning("Knowledge base not found: %s", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _bullet_list(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def _other_schools_block(school: str, rulings: dict[str, str]) -> str:
    lines: list[str] = []
    for s in SCHOOLS:
        if s == school:
            continue
        ruling = rulings.get(RULING_KEY[s], "").strip()
        if ruling:
            lines.append(f"• **{s}:** {ruling}")
    return "\n".join(lines)


def _majority_ruling(rulings: dict[str, str]) -> str:
    """Return the majority ruling text (most common ruling among the 4 schools)."""
    from collections import Counter
    # Normalise whitespace then count
    counts: Counter[str] = Counter(
        v.strip().lower() for v in rulings.values() if v.strip()
    )
    if not counts:
        return ""
    most_common_text = counts.most_common(1)[0][0]
    # Return the original-case version
    for v in rulings.values():
        if v.strip().lower() == most_common_text:
            return v.strip()
    return ""


# ─── Pair generators ──────────────────────────────────────────────────────────

def _ruling_pairs_from_comparative(
    rulings_list: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """
    For each of the 14 comparative_rulings, generate:
      - 4 school-specific pairs (one per madhab)
      - 1 Sunni-position pair
    """
    pairs: list[dict[str, Any]] = []

    for ruling in rulings_list:
        topic: str = ruling.get("topic", "")
        rulings: dict[str, str] = ruling.get("rulings", {})
        basis: str = ruling.get("basis", "")
        # Some entries have a consensus note
        consensus_note: str = ruling.get("consensus", "")
        minority_note: str = ruling.get("minority_view", "")

        # ── Per-school pairs ──────────────────────────────────────────────────
        for school in SCHOOLS:
            school_ruling = rulings.get(RULING_KEY[school], "").strip()
            if not school_ruling:
                continue

            profile = profiles.get(school, {})
            methodology: str = profile.get("methodology", "")
            key_principles: list[str] = profile.get("key_principles", [])
            principle_note = key_principles[0] if key_principles else methodology

            other_block = _other_schools_block(school, rulings)

            answer = (
                f"**{topic} — {school} Position**\n\n"
                f"The {school} madhab holds that: {school_ruling}\n\n"
                f"**Their Evidence (Dalil):**\n"
                f"{basis if basis else 'Derived from the primary sources of Quran and Sunnah.'}\n\n"
                f"**Why They Hold This View:**\n"
                f"{principle_note}\n\n"
            )
            if other_block:
                answer += (
                    f"**Other Scholarly Views:**\n"
                    f"{other_block}\n\n"
                )
            answer += IKHTILAF_NOTE

            if minority_note:
                answer += f"\n\n*Minority/contemporary view:* {minority_note}"

            template = rng.choice(RULING_TEMPLATES)
            question = template.format(school=school, topic=topic)
            pairs.append(_make_pair(question, answer, school, topic))

        # ── Sunni-position pair ───────────────────────────────────────────────
        majority = _majority_ruling(rulings) if not consensus_note else "All four Sunni madhabs agree on this point."
        sunni_answer = (
            f"**{topic} — Sunni Position**\n\n"
            f"{consensus_note if consensus_note else majority}\n\n"
        )
        if basis:
            # Try to split into Quranic vs hadith basis heuristically
            if "Quran" in basis or "quran" in basis or "ayah" in basis.lower():
                sunni_answer += f"**Quranic Basis:**\n{basis}\n\n"
            else:
                sunni_answer += f"**Hadith Basis:**\n{basis}\n\n"

        # Add scholarly consensus / where they differ
        all_agree = len(set(v.strip().lower() for v in rulings.values() if v.strip())) == 1
        if all_agree or consensus_note:
            sunni_answer += (
                f"**Scholarly Consensus:**\n"
                f"Most Sunni scholars agree: {majority or consensus_note}\n\n"
                f"Where they differ:\n"
                f"All four madhabs hold the same position on this issue."
            )
        else:
            majority_text = majority or "the established ruling"
            sunni_answer += (
                f"**Scholarly Consensus:**\n"
                f"Most Sunni scholars agree: {majority_text}\n\n"
                f"Where they differ:\n"
            )
            for s in SCHOOLS:
                r = rulings.get(RULING_KEY[s], "").strip()
                if r:
                    sunni_answer += f"• **{s}:** {r}\n"

        sunni_template = rng.choice(SUNNI_TEMPLATES)
        sunni_question = sunni_template.format(topic=topic)
        pairs.append(_make_pair(sunni_question, sunni_answer, "Sunni", topic))

    return pairs


def _ruling_pairs_from_topics(
    topics: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    rng: random.Random,
    max_topics: int = 30,
) -> list[dict[str, Any]]:
    """
    For each topic (up to max_topics) that has per-madhab fiqh positions, generate:
      - 4 school-specific pairs
      - 1 Sunni-position pair
    """
    pairs: list[dict[str, Any]] = []
    processed = 0

    for topic_entry in topics:
        if processed >= max_topics:
            break

        fiqh: dict[str, Any] = topic_entry.get("fiqh", {})
        if not fiqh:
            continue

        # Check that at least one school-specific key exists
        has_madhab_data = any(
            fiqh.get(TOPIC_FIQH_KEY[s]) for s in SCHOOLS
        )
        if not has_madhab_data:
            continue

        title: str = topic_entry.get("title", topic_entry.get("id", ""))
        topic_label = title  # human-readable label used in questions

        consensus: str = fiqh.get("consensus", "")
        overall_ruling: str = fiqh.get("ruling", "")
        details: str = fiqh.get("details", "")

        # Build rulings dict for this topic
        rulings: dict[str, str] = {}
        for school in SCHOOLS:
            key = TOPIC_FIQH_KEY[school]
            val = fiqh.get(key, "").strip()
            if val:
                rulings[school] = val

        # Quran/hadith refs for Sunni answer
        quran_refs: list[str] = topic_entry.get("quran_refs", [])
        hadith_entries: list[dict[str, Any]] = topic_entry.get("hadith", [])

        # ── Per-school pairs ──────────────────────────────────────────────────
        for school in SCHOOLS:
            school_text = rulings.get(school, "").strip()
            if not school_text:
                continue

            profile = profiles.get(school, {})
            methodology: str = profile.get("methodology", "")
            key_principles: list[str] = profile.get("key_principles", [])
            principle_note = key_principles[0] if key_principles else methodology

            other_block_lines: list[str] = []
            for s in SCHOOLS:
                if s == school:
                    continue
                other_text = rulings.get(s, "").strip()
                if other_text:
                    # Truncate to first sentence for brevity in "other views"
                    brief = other_text.split(".")[0].strip()
                    if len(brief) > 120:
                        brief = brief[:117] + "..."
                    other_block_lines.append(f"• **{s}:** {brief}")

            answer = (
                f"**{topic_label} — {school} Position**\n\n"
                f"The {school} madhab holds that: {school_text}\n\n"
                f"**Their Evidence (Dalil):**\n"
                f"{details if details else 'Derived from the primary sources of Quran and Sunnah.'}\n\n"
                f"**Why They Hold This View:**\n"
                f"{principle_note}\n\n"
            )
            if other_block_lines:
                answer += (
                    "**Other Scholarly Views:**\n"
                    + "\n".join(other_block_lines)
                    + "\n\n"
                )
            answer += IKHTILAF_NOTE

            template = rng.choice(RULING_TEMPLATES)
            question = template.format(school=school, topic=topic_label)
            pairs.append(
                _make_pair(question, answer, school, topic_label, consult_scholar=True)
            )

        # ── Sunni-position pair ───────────────────────────────────────────────
        sunni_answer = f"**{topic_label} — Sunni Position**\n\n"

        if overall_ruling:
            sunni_answer += f"{overall_ruling}\n\n"
        elif details:
            sunni_answer += f"{details}\n\n"

        if quran_refs:
            sunni_answer += f"**Quranic Basis:**\n" + ", ".join(
                f"Quran {r}" for r in quran_refs[:3]
            ) + "\n\n"

        if hadith_entries:
            h = hadith_entries[0]
            sunni_answer += (
                f"**Hadith Basis:**\n"
                f"{h.get('collection', '')} #{h.get('number', '')} — "
                f"{h.get('text', '')}\n\n"
            )

        if consensus == "IJMA":
            sunni_answer += (
                f"**Scholarly Consensus:**\n"
                f"Most Sunni scholars agree: {overall_ruling or 'this ruling is established by scholarly consensus (ijma).'}\n\n"
                f"Where they differ:\n"
            )
        else:
            sunni_answer += (
                f"**Scholarly Consensus:**\n"
                f"Sunni scholars generally hold: {overall_ruling or details or 'see individual madhab positions below.'}\n\n"
                f"Where they differ:\n"
            )

        for s in SCHOOLS:
            r = rulings.get(s, "").strip()
            if r:
                brief = r.split(".")[0].strip()
                if len(brief) > 130:
                    brief = brief[:127] + "..."
                sunni_answer += f"• **{s}:** {brief}\n"

        sunni_template = rng.choice(SUNNI_TEMPLATES)
        sunni_question = sunni_template.format(topic=topic_label)
        pairs.append(_make_pair(sunni_question, sunni_answer, "Sunni", topic_label))

        processed += 1

    return pairs


def _profile_pairs(
    profiles_list: list[dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """
    Generate one profile Q&A pair per question template per madhab.
    (4 madhabs × 5 templates = 20 pairs)
    """
    pairs: list[dict[str, Any]] = []

    for profile in profiles_list:
        name: str = profile.get("name", "")
        arabic: str = profile.get("arabic", "")
        founder: str = profile.get("founder", "")
        founder_dates: str = profile.get("founder_dates", "")
        founded_in: str = profile.get("founded_in", "")
        methodology: str = profile.get("methodology", "")
        key_principles: list[str] = profile.get("key_principles", [])
        major_scholars: list[str] = profile.get("major_scholars", [])
        geo = GEO_SPREAD.get(name, profile.get("geographic_prevalence", ""))

        answer = (
            f"**The {name} Madhab**\n"
            f"{arabic} — Founded by {founder} ({founder_dates})\n\n"
            f"**Origin:** {founded_in}\n\n"
            f"**Methodology:**\n"
            f"{methodology}\n\n"
            f"**Key Principles:**\n"
            f"{_bullet_list(key_principles)}\n\n"
            f"**Major Scholars of This School:**\n"
            f"{', '.join(major_scholars)}\n\n"
            f"**Geographic Spread:**\n"
            f"{geo}"
        )

        for template in PROFILE_TEMPLATES:
            question = template.format(name=name)
            pairs.append(_make_pair(question, answer, name, f"{name} school overview"))

    return pairs


def _extra_variant_pairs(
    rulings_list: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """
    Generate additional variant-phrasing pairs to help reach the 200-350 target.
    Uses "Why do {school} scholars say..." and "How does {school} school rule on..."
    templates applied to a random subset of rulings.
    """
    pairs: list[dict[str, Any]] = []
    extra_templates = [
        "Why do {school} scholars say {topic} is ruled the way it is?",
        "Can you explain the {school} school's reasoning on {topic}?",
        "What is the {school} madhab's stance on {topic}?",
    ]

    sampled = rng.sample(rulings_list, min(len(rulings_list), 8))
    for ruling in sampled:
        topic: str = ruling.get("topic", "")
        rulings: dict[str, str] = ruling.get("rulings", {})
        basis: str = ruling.get("basis", "")

        school = rng.choice(SCHOOLS)
        school_ruling = rulings.get(RULING_KEY[school], "").strip()
        if not school_ruling:
            continue

        profile = profiles.get(school, {})
        methodology: str = profile.get("methodology", "")
        key_principles: list[str] = profile.get("key_principles", [])

        reasoning_text = (
            key_principles[0] if key_principles else methodology
        )

        answer = (
            f"**{topic} — {school} Position**\n\n"
            f"The {school} madhab holds that: {school_ruling}\n\n"
            f"**Their Evidence (Dalil):**\n"
            f"{basis if basis else 'Derived from Quran and Sunnah.'}\n\n"
            f"**Why They Hold This View:**\n"
            f"{reasoning_text}\n\n"
        )
        other_block = _other_schools_block(school, rulings)
        if other_block:
            answer += f"**Other Scholarly Views:**\n{other_block}\n\n"
        answer += IKHTILAF_NOTE

        template = rng.choice(extra_templates)
        question = template.format(school=school, topic=topic)
        pairs.append(_make_pair(question, answer, school, topic))

    return pairs


# ─── Main entry point ─────────────────────────────────────────────────────────

def generate_madhab_pairs(seed: int = 42) -> list[dict]:
    """
    Generate 200–350 Q&A training pairs covering madhab-specific rulings,
    Sunni-position questions, and madhab profile overviews.

    Args:
        seed: Random seed for reproducible question-template selection.

    Returns:
        List of training pair dicts with keys: instruction, input, output, metadata.
    """
    rng = random.Random(seed)
    kb_dir = KB_DIR

    # ── Load data ─────────────────────────────────────────────────────────────
    comparative_data = _load(kb_dir, "madhab_comparative.json")
    topics_data = _load(kb_dir, "comprehensive_topics.json")

    if not comparative_data:
        logger.error("madhab_comparative.json not found or empty — aborting.")
        return []

    profiles_list: list[dict[str, Any]] = comparative_data.get("madhab_profiles", [])
    rulings_list: list[dict[str, Any]] = comparative_data.get("comparative_rulings", [])
    topics_list: list[dict[str, Any]] = topics_data.get("topics", []) if topics_data else []

    # Build a name-keyed profiles dict for quick lookup
    profiles: dict[str, dict[str, Any]] = {
        p["name"]: p for p in profiles_list if "name" in p
    }

    all_pairs: list[dict[str, Any]] = []

    # ── 1. Profile overview pairs (4 schools × 5 templates = 20 pairs) ───────
    logger.info("Generating madhab profile pairs…")
    profile_pairs = _profile_pairs(profiles_list, rng)
    all_pairs.extend(profile_pairs)
    logger.info("  → %d profile pairs", len(profile_pairs))

    # ── 2. Comparative-ruling pairs (14 rulings × 5 pairs each = 70 pairs) ───
    logger.info("Generating comparative ruling pairs…")
    comp_pairs = _ruling_pairs_from_comparative(rulings_list, profiles, rng)
    all_pairs.extend(comp_pairs)
    logger.info("  → %d comparative ruling pairs", len(comp_pairs))

    # ── 3. Comprehensive-topic pairs (up to 30 topics × 5 pairs each ≤ 150) ──
    logger.info("Generating comprehensive topic pairs…")
    topic_pairs = _ruling_pairs_from_topics(topics_list, profiles, rng, max_topics=30)
    all_pairs.extend(topic_pairs)
    logger.info("  → %d topic pairs", len(topic_pairs))

    # ── 4. Extra variant pairs to pad / enrich ────────────────────────────────
    logger.info("Generating extra variant pairs…")
    extra = _extra_variant_pairs(rulings_list, profiles, rng)
    all_pairs.extend(extra)
    logger.info("  → %d extra variant pairs", len(extra))

    logger.info("Total pairs generated: %d", len(all_pairs))
    return all_pairs


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate madhab-specific Q&A training pairs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write the JSONL output file (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible template selection (default: %(default)s)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    pairs = generate_madhab_pairs(seed=args.seed)

    if not pairs:
        logger.error("No pairs generated — check knowledge-base paths.")
        sys.exit(1)

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "madhab_specific.jsonl"

    with output_path.open("w", encoding="utf-8") as fh:
        for pair in pairs:
            fh.write(json.dumps(pair, ensure_ascii=False) + "\n")

    logger.info("Wrote %d pairs to %s", len(pairs), output_path)

    # Print a summary to stdout
    from collections import Counter
    school_counts: Counter[str] = Counter(
        p["metadata"]["school"] for p in pairs
    )
    print(f"\nMadhab-specific Q&A generation complete.")
    print(f"Total pairs : {len(pairs)}")
    print(f"Output file : {output_path}")
    print("\nBreakdown by school:")
    for school, count in sorted(school_counts.items()):
        print(f"  {school:<12} {count:>4} pairs")


if __name__ == "__main__":
    main()
