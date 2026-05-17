#!/usr/bin/env python3
"""
Remove near-duplicate questions from the generated JSONL dataset.

Uses TF-IDF cosine similarity to find question pairs with >= 85% similarity
and removes all but one. Operates on the combined pool before re-splitting.

Usage:
    python deduplicate.py
    python deduplicate.py --similarity-threshold 0.85
    python deduplicate.py --help
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import jsonlines
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR: Path = Path(__file__).parent.parent / "formatted_output"
DEFAULT_THRESHOLD: float = 0.85
BATCH_SIZE: int = 5000    # Process similarity in batches to avoid OOM
DEFAULT_SEED: int = 42


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure console logging."""
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=fmt, datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("deduplicate")


# ─── I/O ─────────────────────────────────────────────────────────────────────

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file into a list of dicts.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of parsed JSON objects.
    """
    with jsonlines.open(path) as reader:
        return list(reader)


def save_jsonl(pairs: list[dict[str, Any]], path: Path) -> None:
    """Save a list of dicts to a JSONL file.

    Args:
        pairs: List of dicts to save.
        path: Output file path.
    """
    with jsonlines.open(path, mode="w") as writer:
        for pair in pairs:
            writer.write(pair)


# ─── Deduplication logic ──────────────────────────────────────────────────────

def find_duplicates_tfidf(
    questions: list[str],
    threshold: float,
    logger: logging.Logger,
) -> set[int]:
    """Find indices of duplicate questions using TF-IDF cosine similarity.

    For each pair of questions with similarity >= threshold, the one with the
    higher index is marked as a duplicate (keeps first occurrence).

    Processes in batches to handle large datasets without OOM.

    Args:
        questions: List of question strings (one per pair).
        threshold: Cosine similarity threshold (0.0–1.0).
        logger: Logger instance.

    Returns:
        Set of indices to remove.
    """
    logger.info("Building TF-IDF matrix for %d questions...", len(questions))
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        max_features=50000,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(questions)
    logger.info("TF-IDF matrix shape: %s", tfidf_matrix.shape)

    to_remove: set[int] = set()
    n = len(questions)

    logger.info("Comparing question similarity in batches of %d...", BATCH_SIZE)
    for start in tqdm(range(0, n, BATCH_SIZE), desc="Dedup batches"):
        end = min(start + BATCH_SIZE, n)
        batch = tfidf_matrix[start:end]

        # Compare batch against ALL subsequent rows (upper triangle only)
        sims = cosine_similarity(batch, tfidf_matrix[start:])

        for i, row in enumerate(sims):
            global_i = start + i
            if global_i in to_remove:
                continue
            # Find similar items (excluding self-similarity)
            similar_indices = np.where(row >= threshold)[0]
            for j in similar_indices:
                global_j = start + j
                if global_j != global_i and global_j not in to_remove:
                    to_remove.add(global_j)

    return to_remove


def deduplicate_pairs(
    pairs: list[dict[str, Any]],
    threshold: float,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """Remove near-duplicate pairs from a list.

    Args:
        pairs: List of Q&A pair dicts.
        threshold: Similarity threshold for duplicate detection.
        logger: Logger instance.

    Returns:
        Deduplicated list of pairs.
    """
    questions = [p["instruction"].strip().lower() for p in pairs]
    duplicates = find_duplicates_tfidf(questions, threshold, logger)

    kept = [p for i, p in enumerate(pairs) if i not in duplicates]
    logger.info("Removed %d duplicates (%.1f%%) — kept %d pairs",
                len(duplicates), 100 * len(duplicates) / max(len(pairs), 1), len(kept))
    return kept


# ─── Split helper ─────────────────────────────────────────────────────────────

def resplit_and_save(
    pairs: list[dict[str, Any]],
    output_dir: Path,
    seed: int,
    logger: logging.Logger,
) -> None:
    """Shuffle and re-split deduplicated pairs into train/eval/test JSONL.

    Args:
        pairs: Deduplicated list of Q&A pairs.
        output_dir: Directory to save JSONL files.
        seed: Random seed for reproducibility.
        logger: Logger instance.
    """
    import random
    rng = random.Random(seed)
    shuffled = pairs.copy()
    rng.shuffle(shuffled)

    total = len(shuffled)
    eval_size = max(1, int(total * 0.10))
    test_size = max(1, int(total * 0.10))
    train_size = total - eval_size - test_size

    train = shuffled[:train_size]
    eval_ = shuffled[train_size : train_size + eval_size]
    test  = shuffled[train_size + eval_size :]

    save_jsonl(train, output_dir / "train.jsonl")
    save_jsonl(eval_,  output_dir / "eval.jsonl")
    save_jsonl(test,   output_dir / "test.jsonl")

    logger.info("Saved deduplicated splits:")
    logger.info("  train.jsonl : %d pairs", len(train))
    logger.info("  eval.jsonl  : %d pairs", len(eval_))
    logger.info("  test.jsonl  : %d pairs", len(test))

    # Update summary
    summary_path = output_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        summary = {}

    summary["after_dedup"] = {
        "total_pairs": total,
        "train": len(train),
        "eval": len(eval_),
        "test": len(test),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Remove near-duplicate questions from the dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deduplicate.py
  python deduplicate.py --similarity-threshold 0.90
  python deduplicate.py --output-dir /data/formatted
        """,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--similarity-threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"Cosine similarity threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> None:
    """Entry point: load JSONL files, deduplicate, re-save."""
    args = parse_args()
    logger = setup_logging(args.log_level)

    output_dir = args.output_dir

    logger.info("=" * 60)
    logger.info("Deduplication")
    logger.info("Output dir : %s", output_dir)
    logger.info("Threshold  : %.2f", args.similarity_threshold)
    logger.info("=" * 60)

    # Load all splits into one pool
    all_pairs: list[dict[str, Any]] = []
    for split_name in ("train.jsonl", "eval.jsonl", "test.jsonl"):
        path = output_dir / split_name
        if not path.exists():
            logger.error("%s not found — run generate_qa_pairs.py first", split_name)
            sys.exit(1)
        split_pairs = load_jsonl(path)
        logger.info("Loaded %s: %d pairs", split_name, len(split_pairs))
        all_pairs.extend(split_pairs)

    logger.info("Total before dedup: %d pairs", len(all_pairs))
    start = time.monotonic()

    # Deduplicate
    deduped = deduplicate_pairs(all_pairs, args.similarity_threshold, logger)

    # Re-split and save
    resplit_and_save(deduped, output_dir, args.seed, logger)

    logger.info("Completed in %.1f seconds", time.monotonic() - start)
    logger.info("Next step: python validate_dataset.py")


if __name__ == "__main__":
    main()
