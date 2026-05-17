#!/usr/bin/env python3
"""
Master script: generate all Q&A training pairs from Phase 1 raw data.

Produces:
  formatted_output/train.jsonl   (80% of pairs)
  formatted_output/eval.jsonl    (10% of pairs)
  formatted_output/test.jsonl    (10% of pairs)

Categories generated:
  quran_direct    — one pair per Quranic ayah
  quran_topic     — topic-based Quran questions
  hadith_direct   — one pair per hadith (sampled)
  surah_meaning   — surah overview questions
  aqeedah         — Islamic belief questions + 99 Names
  fiqh            — Islamic rulings questions
  dua             — supplication questions
  refusal         — out-of-scope rejection training

Usage:
    python generate_qa_pairs.py
    python generate_qa_pairs.py --raw-dir /custom/raw --output-dir /custom/out
    python generate_qa_pairs.py --seed 42 --help
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonlines
from tqdm import tqdm

# Add scripts dir to path so we can import helper modules
sys.path.insert(0, str(Path(__file__).parent))
from format_quran import (
    generate_direct_verse_pairs,
    generate_surah_overview_pairs,
    generate_topic_quran_pairs,
    generate_recitation_verse_pairs,
    generate_reflection_verse_pairs,
    generate_study_verse_pairs,
)
from format_hadith import (
    generate_direct_hadith_pairs,
    generate_lesson_hadith_pairs,
    generate_narrative_hadith_pairs,
    generate_refusal_pairs,
    generate_aqeedah_pairs,
    generate_dua_pairs,
    generate_fiqh_pairs,
    generate_names_pairs,
)
from format_fiqh_extended import generate_fiqh_extended_pairs
from format_supplementary import generate_supplementary_pairs
from format_behaviors import generate_behavior_pairs
from format_advanced_behaviors import generate_advanced_behavior_pairs
from format_knowledge_bases import generate_all as generate_knowledge_base_pairs
from format_new_kb import generate_new_kb_pairs
from format_additional_10k import generate_additional_pairs
from format_comprehensive import generate_comprehensive_pairs
from format_fatwa import generate_fatwa_pairs
from format_books_kb import generate_books_kb_pairs

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_RAW_DIR: Path = Path(__file__).parent.parent.parent / "01_data_collection" / "raw"
DEFAULT_OUTPUT_DIR: Path = Path(__file__).parent.parent / "formatted_output"
LOG_DIR: Path = Path(__file__).parent.parent.parent / "01_data_collection" / "logs"
KB_DIR: Path = DEFAULT_RAW_DIR / "knowledge_bases"

TRAIN_RATIO: float = 0.80
EVAL_RATIO: float = 0.10
TEST_RATIO: float = 0.10

HADITH_SAMPLE_SIZE: int = 9000       # Increased — more collections available now
TOPIC_MAX_PER_TOPIC: int = 8         # Max Quran topic pairs per topic
DEFAULT_SEED: int = 42

HADITH_FILES: dict[str, str] = {
    # Core six collections
    "bukhari":          "hadith/bukhari.json",
    "muslim":           "hadith/muslim.json",
    "abu_dawud":        "hadith/abu_dawud.json",
    "tirmidhi":         "hadith/tirmidhi.json",
    "ibn_majah":        "hadith/ibn_majah.json",
    # Extended collections (downloaded by download_extended_hadith.py)
    "nasai":            "hadith/nasai.json",
    "muwatta_malik":    "hadith/muwatta_malik.json",
    "nawawi_40":        "hadith/nawawi_40.json",
    "hadith_qudsi":     "hadith/hadith_qudsi.json",
    "dehlawi":          "hadith/dehlawi.json",
    # Legacy filename support
    "riyad_us_salihin": "hadith/riyad_us_salihin.json",
}


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure console logging.

    Args:
        log_level: Logging level string.

    Returns:
        Configured logger instance.
    """
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("generate_qa")


# ─── Data loaders ─────────────────────────────────────────────────────────────

def load_quran(raw_dir: Path, logger: logging.Logger) -> dict[str, Any]:
    """Load quran_full.json from the raw data directory.

    Args:
        raw_dir: Root raw data directory.
        logger: Logger instance.

    Returns:
        Parsed quran_full.json dict.

    Raises:
        SystemExit: If the file does not exist or cannot be parsed.
    """
    path = raw_dir / "quran" / "quran_full.json"
    if not path.exists():
        logger.error("quran_full.json not found at %s — run Phase 1 first", path)
        sys.exit(1)
    logger.info("Loading Quran data from %s", path)
    data = json.loads(path.read_text(encoding="utf-8"))
    total = data.get("metadata", {}).get("total_ayahs", "?")
    logger.info("Quran loaded: %s ayahs", total)
    return data


def load_all_hadiths(raw_dir: Path, logger: logging.Logger) -> list[dict[str, Any]]:
    """Load all available hadith collections and return a flat list.

    Args:
        raw_dir: Root raw data directory.
        logger: Logger instance.

    Returns:
        Flat list of hadith dicts, each including a 'collection_key' field.
    """
    all_hadiths: list[dict[str, Any]] = []

    for collection_key, rel_path in HADITH_FILES.items():
        path = raw_dir / rel_path
        if not path.exists():
            logger.warning("Skipping %s — file not found (run Phase 1 to download)", path.name)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            hadiths = data.get("hadiths", [])
            for h in hadiths:
                h["collection_key"] = collection_key
            all_hadiths.extend(hadiths)
            logger.info("Loaded %s: %d hadiths", path.name, len(hadiths))
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Could not load %s: %s", path.name, exc)

    logger.info("Total hadiths loaded: %d", len(all_hadiths))
    return all_hadiths


def load_names(raw_dir: Path, logger: logging.Logger) -> dict[str, Any]:
    """Load asmaul_husna.json (99 Names of Allah).

    Args:
        raw_dir: Root raw data directory.
        logger: Logger instance.

    Returns:
        Parsed dict, or empty dict if file not found.
    """
    path = raw_dir / "supplementary" / "asmaul_husna.json"
    if not path.exists():
        logger.warning("asmaul_husna.json not found — skipping 99 Names pairs")
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    logger.info("Loaded 99 Names: %d names", len(data.get("names", [])))
    return data


# ─── Pair assembly ────────────────────────────────────────────────────────────

def add_timestamps(pairs: list[dict[str, Any]]) -> None:
    """Add generated_at timestamp to every pair's metadata in-place.

    Args:
        pairs: List of Q&A pair dicts to modify.
    """
    ts = datetime.now(timezone.utc).isoformat()
    for p in pairs:
        p["metadata"]["generated_at"] = ts


def generate_all_pairs(
    quran_data: dict[str, Any],
    all_hadiths: list[dict[str, Any]],
    names_data: dict[str, Any],
    rng: random.Random,
    logger: logging.Logger,
    kb_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Run all generators and return the combined pair list.

    Args:
        quran_data: Parsed quran_full.json.
        all_hadiths: Flat list of all hadiths.
        names_data: Parsed asmaul_husna.json.
        rng: Seeded random instance.
        logger: Logger instance.
        kb_dir: Knowledge bases directory (optional — skipped if None or missing).

    Returns:
        Combined list of all Q&A pairs (unshuffled, unfiltered).
    """
    all_pairs: list[dict[str, Any]] = []

    steps: list[tuple[str, Any]] = [
        # Core Quran pairs
        ("Quran direct verse pairs",       lambda: generate_direct_verse_pairs(quran_data, rng)),
        ("Quran recitation pairs",         lambda: generate_recitation_verse_pairs(quran_data, rng)),
        ("Quran reflection pairs",         lambda: generate_reflection_verse_pairs(quran_data, rng)),
        ("Quran study pairs (tafsir)",     lambda: generate_study_verse_pairs(quran_data, rng)),
        ("Quran topic pairs",              lambda: generate_topic_quran_pairs(quran_data, rng, TOPIC_MAX_PER_TOPIC)),
        ("Surah overview pairs",           lambda: generate_surah_overview_pairs(quran_data, rng)),
        # Core Hadith pairs
        ("Hadith direct pairs",            lambda: generate_direct_hadith_pairs(all_hadiths, rng, HADITH_SAMPLE_SIZE)),
        ("Hadith lesson pairs",            lambda: generate_lesson_hadith_pairs(all_hadiths, rng, HADITH_SAMPLE_SIZE)),
        ("Hadith narrative pairs",         lambda: generate_narrative_hadith_pairs(all_hadiths, rng, HADITH_SAMPLE_SIZE)),
        # Topic / category pairs
        ("Refusal training pairs",         lambda: generate_refusal_pairs(rng)),
        ("Aqeedah (belief) pairs",         generate_aqeedah_pairs),
        ("Dua (supplication) pairs",       generate_dua_pairs),
        ("Fiqh (rulings) pairs",           generate_fiqh_pairs),
        ("99 Names of Allah pairs",        lambda: generate_names_pairs(names_data)),
        ("Extended Fiqh pairs",            generate_fiqh_extended_pairs),
        ("Supplementary pairs",            generate_supplementary_pairs),
        ("Behavior & safety pairs",        generate_behavior_pairs),
        ("Advanced behavior pairs",        generate_advanced_behavior_pairs),
        ("Additional topical pairs",       generate_additional_pairs),
        ("Comprehensive topic pairs",      lambda: generate_comprehensive_pairs(kb_dir)),
        ("IslamQA fatwa pairs",            lambda: generate_fatwa_pairs(kb_dir)),
    ]

    for description, generator in tqdm(steps, desc="Generating categories"):
        try:
            pairs = generator()
            logger.info("%-35s → %d pairs", description, len(pairs))
            all_pairs.extend(pairs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("%-35s → SKIPPED (%s)", description, exc)

    # Knowledge base pairs — loaded from JSON knowledge bases in Phase 1 raw dir
    if kb_dir is not None and kb_dir.is_dir():
        try:
            kb_pairs = generate_knowledge_base_pairs(kb_dir)
            logger.info("%-35s → %d pairs", "Knowledge base pairs (original)", len(kb_pairs))
            all_pairs.extend(kb_pairs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Knowledge base pairs (original) → SKIPPED (%s)", exc)
        try:
            new_kb_pairs = generate_new_kb_pairs(kb_dir)
            logger.info("%-35s → %d pairs", "Knowledge base pairs (new 20)", len(new_kb_pairs))
            all_pairs.extend(new_kb_pairs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Knowledge base pairs (new 20) → SKIPPED (%s)", exc)
        try:
            books_kb_pairs = generate_books_kb_pairs(kb_dir)
            logger.info("%-35s → %d pairs", "Classical books KB pairs", len(books_kb_pairs))
            all_pairs.extend(books_kb_pairs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Classical books KB pairs → SKIPPED (%s)", exc)
    else:
        logger.warning(
            "Knowledge bases dir not found (%s) — run Phase 1 and create knowledge_bases/", kb_dir
        )

    return all_pairs


# ─── Split and save ───────────────────────────────────────────────────────────

def split_pairs(
    pairs: list[dict[str, Any]],
    rng: random.Random,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Shuffle and split pairs into train / eval / test sets.

    Args:
        pairs: Full list of Q&A pairs.
        rng: Seeded random instance.

    Returns:
        Tuple of (train_pairs, eval_pairs, test_pairs).
    """
    shuffled = pairs.copy()
    rng.shuffle(shuffled)

    total = len(shuffled)
    eval_size = max(1, int(total * EVAL_RATIO))
    test_size = max(1, int(total * TEST_RATIO))
    train_size = total - eval_size - test_size

    train = shuffled[:train_size]
    eval_ = shuffled[train_size : train_size + eval_size]
    test  = shuffled[train_size + eval_size :]

    return train, eval_, test


def save_jsonl(pairs: list[dict[str, Any]], path: Path) -> None:
    """Save a list of pairs to a JSONL file.

    Args:
        pairs: List of Q&A pair dicts to save.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with jsonlines.open(path, mode="w") as writer:
        for pair in pairs:
            writer.write(pair)


def print_category_stats(pairs: list[dict[str, Any]], label: str, logger: logging.Logger) -> None:
    """Log a breakdown of pairs by category.

    Args:
        pairs: List of Q&A pair dicts.
        label: Label for the set (e.g. 'TRAIN').
        logger: Logger instance.
    """
    from collections import Counter
    counts = Counter(p["metadata"].get("category", "unknown") for p in pairs)
    logger.info("─── %s set (%d total) ───", label, len(pairs))
    for cat, n in sorted(counts.items()):
        logger.info("  %-25s %d", cat, n)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate all Islamic AI Q&A training pairs from Phase 1 raw data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_qa_pairs.py
  python generate_qa_pairs.py --seed 123
  python generate_qa_pairs.py --raw-dir /data/raw --output-dir /data/out
  python generate_qa_pairs.py --help
        """,
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
                        help=f"Root raw data dir from Phase 1 (default: {DEFAULT_RAW_DIR})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f"Output dir for JSONL files (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> None:
    """Entry point: load data, generate pairs, split, save."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("Islamic AI — Q&A Pair Generator")
    logger.info("Raw dir   : %s", args.raw_dir)
    logger.info("Output dir: %s", args.output_dir)
    logger.info("Seed      : %d", args.seed)
    logger.info("=" * 60)

    rng = random.Random(args.seed)
    start = time.monotonic()

    # Load data
    quran_data = load_quran(args.raw_dir, logger)
    all_hadiths = load_all_hadiths(args.raw_dir, logger)
    names_data = load_names(args.raw_dir, logger)

    if not all_hadiths:
        logger.error("No hadiths loaded — run Phase 1 download first")
        sys.exit(1)

    # Resolve knowledge bases directory (can differ from raw_dir)
    kb_dir = args.raw_dir / "knowledge_bases"

    # Generate all pairs
    logger.info("Generating Q&A pairs...")
    all_pairs = generate_all_pairs(quran_data, all_hadiths, names_data, rng, logger, kb_dir=kb_dir)

    # Add timestamps
    add_timestamps(all_pairs)

    logger.info("Total pairs generated: %d", len(all_pairs))

    # Drop pairs that exceed ~7,500 chars — at 2,048 token limit they get silently
    # truncated mid-sentence, corrupting that training example.
    MAX_PAIR_CHARS = 7_500
    before = len(all_pairs)
    all_pairs = [
        p for p in all_pairs
        if len(p.get("instruction", "")) + len(p.get("output", "")) <= MAX_PAIR_CHARS
    ]
    dropped = before - len(all_pairs)
    if dropped:
        logger.warning("Dropped %d pairs exceeding %d chars (would be truncated at 2048 tokens)", dropped, MAX_PAIR_CHARS)
    logger.info("Pairs after length filter: %d", len(all_pairs))

    # Split
    train, eval_, test = split_pairs(all_pairs, rng)
    logger.info("Split: train=%d  eval=%d  test=%d", len(train), len(eval_), len(test))

    # Print category stats
    print_category_stats(train, "TRAIN", logger)

    # Save
    output_dir = args.output_dir
    save_jsonl(train, output_dir / "train.jsonl")
    save_jsonl(eval_,  output_dir / "eval.jsonl")
    save_jsonl(test,   output_dir / "test.jsonl")

    # Save summary JSON
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "total_pairs": len(all_pairs),
        "train": len(train),
        "eval": len(eval_),
        "test": len(test),
        "categories": {},
    }
    from collections import Counter
    for pair in all_pairs:
        cat = pair["metadata"].get("category", "unknown")
        summary["categories"][cat] = summary["categories"].get(cat, 0) + 1

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    elapsed = time.monotonic() - start
    logger.info("=" * 60)
    logger.info("Done in %.1f seconds", elapsed)
    logger.info("Output files:")
    logger.info("  train.jsonl : %d pairs", len(train))
    logger.info("  eval.jsonl  : %d pairs", len(eval_))
    logger.info("  test.jsonl  : %d pairs", len(test))
    logger.info("  summary.json")
    logger.info("")
    logger.info("Next step: python deduplicate.py")


if __name__ == "__main__":
    main()
