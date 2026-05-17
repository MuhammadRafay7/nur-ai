#!/usr/bin/env python3
"""
Validate the formatted JSONL dataset produced by Phase 2.

Checks:
  - Required fields present on every pair
  - Output length within acceptable bounds
  - Quran references are valid (surah:ayah exists)
  - Category distribution meets minimum targets
  - Total pair count meets minimum threshold
  - No empty instructions or outputs
  - Refusal category count meets minimum
  - Train/eval/test sizes are reasonable

Usage:
    python validate_dataset.py
    python validate_dataset.py --output-dir /custom/path
    python validate_dataset.py --help
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import jsonlines

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR: Path = Path(__file__).parent.parent / "formatted_output"

REQUIRED_FIELDS: list[str] = ["instruction", "input", "output", "metadata"]
REQUIRED_METADATA_FIELDS: list[str] = ["category"]  # "sources" or "source" both accepted

MIN_TOTAL_PAIRS: int = 10_000
MIN_REFUSAL_PAIRS: int = 50
MIN_INSTRUCTION_LEN: int = 10
MIN_OUTPUT_LEN: int = 20
MAX_OUTPUT_LEN: int = 8_000   # ~2000 tokens

# Minimum pairs expected per category (warn if below)
CATEGORY_MIN_TARGETS: dict[str, int] = {
    "quran_direct":   3000,   # ~3900 after dedup of template-similar questions
    "quran_topic":    75,     # ~86 after dedup
    "surah_meaning":  200,
    "hadith_direct":  4000,
    "refusal":        50,
    "aqeedah":        5,
    "dua":            5,
    "fiqh":           4,
    "names_of_allah": 85,  # 99 generated; ~13 deduped as near-similar
}

# Valid Quran range: surah 1–114, ayah 1–286 (max is Al-Baqarah 286)
VALID_SURAH_RANGE: tuple[int, int] = (1, 114)

# Ground-truth ayah counts per surah (used to validate quran references)
SURAH_AYAH_COUNTS: list[int] = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,   # 1–10
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,    # 11–20
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,       # 21–30
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,         # 31–40
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,          # 41–50
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,          # 51–60
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,          # 61–70
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,          # 71–80
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,          # 81–90
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,               # 91–100
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,                   # 101–110
    5, 4, 5, 6,                                        # 111–114
]
assert len(SURAH_AYAH_COUNTS) == 114, "Must have exactly 114 entries"


# ─── Validation report ────────────────────────────────────────────────────────

class ValidationReport:
    """Accumulates PASS / WARN / FAIL messages and produces a summary."""

    def __init__(self) -> None:
        self._pass: list[str] = []
        self._warn: list[str] = []
        self._fail: list[str] = []

    def passed(self, msg: str) -> None:
        self._pass.append(msg)
        print(f"  [PASS] {msg}")

    def warn(self, msg: str) -> None:
        self._warn.append(msg)
        print(f"  [WARN] {msg}")

    def fail(self, msg: str) -> None:
        self._fail.append(msg)
        print(f"  [FAIL] {msg}")

    def summary(self) -> bool:
        """Print summary and return True if no failures."""
        total = len(self._pass) + len(self._warn) + len(self._fail)
        print()
        print("=" * 60)
        print(f"RESULTS  {len(self._pass)} PASS  |  {len(self._warn)} WARN  |  {len(self._fail)} FAIL  |  {total} total")
        print("=" * 60)
        if self._fail:
            print("PHASE 2 VALIDATION: FAILED")
            return False
        if self._warn:
            print("PHASE 2 VALIDATION: PASSED WITH WARNINGS")
        else:
            print("PHASE 2 VALIDATION: PASSED")
        return True


# ─── Loaders ─────────────────────────────────────────────────────────────────

def load_split(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL split file."""
    with jsonlines.open(path) as reader:
        return list(reader)


# ─── Individual checks ───────────────────────────────────────────────────────

def check_file_exists(output_dir: Path, report: ValidationReport) -> dict[str, list[dict[str, Any]]]:
    """Verify all three split files exist and are non-empty."""
    splits: dict[str, list[dict[str, Any]]] = {}
    for name in ("train.jsonl", "eval.jsonl", "test.jsonl"):
        path = output_dir / name
        if not path.exists():
            report.fail(f"{name} not found in {output_dir}")
            splits[name] = []
        else:
            pairs = load_split(path)
            if not pairs:
                report.fail(f"{name} is empty")
            else:
                report.passed(f"{name} exists with {len(pairs):,} pairs")
            splits[name] = pairs
    return splits


def check_required_fields(
    pairs: list[dict[str, Any]],
    split_name: str,
    report: ValidationReport,
) -> None:
    """Check every pair has required top-level and metadata fields."""
    missing_top: int = 0
    missing_meta: int = 0

    for p in pairs:
        for field in REQUIRED_FIELDS:
            if field not in p:
                missing_top += 1
                break
        meta = p.get("metadata", {})
        if not isinstance(meta, dict):
            missing_meta += 1
            continue
        for field in REQUIRED_METADATA_FIELDS:
            if field not in meta:
                missing_meta += 1
                break
        # Accept either "sources" or "source"
        if "sources" not in meta and "source" not in meta:
            missing_meta += 1

    if missing_top == 0:
        report.passed(f"{split_name}: all pairs have required top-level fields")
    else:
        report.fail(f"{split_name}: {missing_top} pairs missing top-level fields")

    if missing_meta == 0:
        report.passed(f"{split_name}: all pairs have required metadata fields")
    else:
        report.fail(f"{split_name}: {missing_meta} pairs missing metadata fields")


def check_field_lengths(
    pairs: list[dict[str, Any]],
    split_name: str,
    report: ValidationReport,
) -> None:
    """Check instruction/output lengths are within bounds."""
    short_instruction = sum(
        1 for p in pairs if len(p.get("instruction", "").strip()) < MIN_INSTRUCTION_LEN
    )
    short_output = sum(
        1 for p in pairs if len(p.get("output", "").strip()) < MIN_OUTPUT_LEN
    )
    long_output = sum(
        1 for p in pairs if len(p.get("output", "").strip()) > MAX_OUTPUT_LEN
    )

    if short_instruction == 0:
        report.passed(f"{split_name}: all instructions >= {MIN_INSTRUCTION_LEN} chars")
    else:
        report.fail(f"{split_name}: {short_instruction} instructions shorter than {MIN_INSTRUCTION_LEN} chars")

    if short_output == 0:
        report.passed(f"{split_name}: all outputs >= {MIN_OUTPUT_LEN} chars")
    else:
        report.fail(f"{split_name}: {short_output} outputs shorter than {MIN_OUTPUT_LEN} chars")

    if long_output == 0:
        report.passed(f"{split_name}: all outputs <= {MAX_OUTPUT_LEN} chars")
    else:
        report.warn(f"{split_name}: {long_output} outputs exceed {MAX_OUTPUT_LEN} chars (will be truncated at training)")


def check_quran_references(
    pairs: list[dict[str, Any]],
    split_name: str,
    report: ValidationReport,
) -> None:
    """Validate all quran:S:A source references are within range."""
    invalid: list[str] = []

    for p in pairs:
        sources = p.get("metadata", {}).get("sources", [])
        for src in sources:
            if not isinstance(src, str):
                continue
            if not src.startswith("quran:"):
                continue
            parts = src.split(":")
            if len(parts) == 3 and parts[2] == "overview":
                # surah overview — just validate surah number
                try:
                    s = int(parts[1])
                    if not (VALID_SURAH_RANGE[0] <= s <= VALID_SURAH_RANGE[1]):
                        invalid.append(src)
                except ValueError:
                    invalid.append(src)
            elif len(parts) == 3:
                try:
                    s = int(parts[1])
                    a = int(parts[2])
                    if not (VALID_SURAH_RANGE[0] <= s <= VALID_SURAH_RANGE[1]):
                        invalid.append(src)
                    elif a < 1 or a > SURAH_AYAH_COUNTS[s - 1]:
                        invalid.append(src)
                except (ValueError, IndexError):
                    invalid.append(src)
            else:
                invalid.append(src)

    if not invalid:
        report.passed(f"{split_name}: all Quran references are valid")
    elif len(invalid) <= 10:
        report.fail(f"{split_name}: {len(invalid)} invalid Quran references: {invalid[:5]}")
    else:
        report.fail(f"{split_name}: {len(invalid)} invalid Quran references (showing first 5): {invalid[:5]}")


def check_category_distribution(
    all_pairs: list[dict[str, Any]],
    report: ValidationReport,
) -> Counter:
    """Check category distribution against minimum targets."""
    counts: Counter = Counter(
        p.get("metadata", {}).get("category", "unknown") for p in all_pairs
    )

    report.passed(f"Categories found: {dict(counts)}")

    for cat, min_count in CATEGORY_MIN_TARGETS.items():
        actual = counts.get(cat, 0)
        if actual >= min_count:
            report.passed(f"Category '{cat}': {actual} pairs (min {min_count})")
        else:
            report.fail(f"Category '{cat}': only {actual} pairs, need >= {min_count}")

    if "unknown" in counts:
        report.warn(f"{counts['unknown']} pairs with unknown category")

    return counts


def check_total_pairs(
    all_pairs: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    """Check total pair count meets minimum threshold."""
    total = len(all_pairs)
    if total >= MIN_TOTAL_PAIRS:
        report.passed(f"Total pairs: {total:,} (min {MIN_TOTAL_PAIRS:,})")
    else:
        report.fail(f"Total pairs: {total:,}, need >= {MIN_TOTAL_PAIRS:,}")


def check_refusal_pairs(
    all_pairs: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    """Check refusal category has enough pairs for safety training."""
    refusal_count = sum(
        1 for p in all_pairs
        if p.get("metadata", {}).get("category") == "refusal"
    )
    if refusal_count >= MIN_REFUSAL_PAIRS:
        report.passed(f"Refusal pairs: {refusal_count} (min {MIN_REFUSAL_PAIRS})")
    else:
        report.fail(f"Refusal pairs: {refusal_count}, need >= {MIN_REFUSAL_PAIRS}")


def check_split_ratios(
    splits: dict[str, list[dict[str, Any]]],
    report: ValidationReport,
) -> None:
    """Check train/eval/test ratios are approximately 80/10/10."""
    train_n = len(splits.get("train.jsonl", []))
    eval_n  = len(splits.get("eval.jsonl", []))
    test_n  = len(splits.get("test.jsonl", []))
    total   = train_n + eval_n + test_n

    if total == 0:
        report.fail("Cannot check split ratios — no pairs loaded")
        return

    train_pct = 100 * train_n / total
    eval_pct  = 100 * eval_n  / total
    test_pct  = 100 * test_n  / total

    # Allow ±5% tolerance around 80/10/10
    if 70 <= train_pct <= 90:
        report.passed(f"Train split: {train_n:,} pairs ({train_pct:.1f}%)")
    else:
        report.warn(f"Train split: {train_n:,} pairs ({train_pct:.1f}%) — expected ~80%")

    if 5 <= eval_pct <= 20:
        report.passed(f"Eval split: {eval_n:,} pairs ({eval_pct:.1f}%)")
    else:
        report.warn(f"Eval split: {eval_n:,} pairs ({eval_pct:.1f}%) — expected ~10%")

    if 5 <= test_pct <= 20:
        report.passed(f"Test split: {test_n:,} pairs ({test_pct:.1f}%)")
    else:
        report.warn(f"Test split: {test_n:,} pairs ({test_pct:.1f}%) — expected ~10%")


def check_duplicate_instructions(
    all_pairs: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    """Check for exact-duplicate instruction strings."""
    instructions = [p.get("instruction", "").strip().lower() for p in all_pairs]
    total = len(instructions)
    unique = len(set(instructions))
    duplicates = total - unique

    dup_pct = 100 * duplicates / max(total, 1)
    if dup_pct < 1.0:
        report.passed(f"Exact duplicate instructions: {duplicates} ({dup_pct:.2f}%) — acceptable")
    elif dup_pct < 5.0:
        report.warn(f"Exact duplicate instructions: {duplicates} ({dup_pct:.2f}%) — consider re-running deduplicate.py")
    else:
        report.fail(f"Exact duplicate instructions: {duplicates} ({dup_pct:.2f}%) — run deduplicate.py")


def check_summary_json(output_dir: Path, report: ValidationReport) -> None:
    """Check summary.json exists and has expected fields."""
    path = output_dir / "summary.json"
    if not path.exists():
        report.warn("summary.json not found — run generate_qa_pairs.py to create it")
        return

    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.fail(f"summary.json is invalid JSON: {exc}")
        return

    required_keys = {"total_pairs", "train", "eval", "test", "categories"}
    missing = required_keys - set(summary.keys())
    if missing:
        report.warn(f"summary.json missing keys: {missing}")
    else:
        report.passed("summary.json has all required fields")

    if "after_dedup" in summary:
        report.passed("summary.json contains deduplication stats")
    else:
        report.warn("summary.json missing 'after_dedup' — run deduplicate.py")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate the Phase 2 formatted JSONL dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_dataset.py
  python validate_dataset.py --output-dir /data/formatted
        """,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help=f"Formatted output directory (default: {DEFAULT_OUTPUT_DIR})")
    return parser.parse_args()


def main() -> None:
    """Entry point: run all validation checks and report."""
    args = parse_args()
    output_dir: Path = args.output_dir
    report = ValidationReport()

    print("=" * 60)
    print("Phase 2 Dataset Validation")
    print(f"Output dir : {output_dir}")
    print("=" * 60)
    print()

    # ── 1. File existence ─────────────────────────────────────────────────────
    print("[ Checking split files ]")
    splits = check_file_exists(output_dir, report)
    print()

    all_pairs: list[dict[str, Any]] = []
    for pairs in splits.values():
        all_pairs.extend(pairs)

    if not all_pairs:
        print("No pairs loaded — cannot continue validation.")
        report.summary()
        sys.exit(1)

    # ── 2. Required fields ────────────────────────────────────────────────────
    print("[ Checking required fields ]")
    for split_name, pairs in splits.items():
        if pairs:
            check_required_fields(pairs, split_name, report)
    print()

    # ── 3. Field lengths ──────────────────────────────────────────────────────
    print("[ Checking field lengths ]")
    for split_name, pairs in splits.items():
        if pairs:
            check_field_lengths(pairs, split_name, report)
    print()

    # ── 4. Quran references ───────────────────────────────────────────────────
    print("[ Checking Quran references ]")
    for split_name, pairs in splits.items():
        if pairs:
            check_quran_references(pairs, split_name, report)
    print()

    # ── 5. Category distribution ──────────────────────────────────────────────
    print("[ Checking category distribution ]")
    check_category_distribution(all_pairs, report)
    print()

    # ── 6. Total pairs ────────────────────────────────────────────────────────
    print("[ Checking pair counts ]")
    check_total_pairs(all_pairs, report)
    check_refusal_pairs(all_pairs, report)
    print()

    # ── 7. Split ratios ───────────────────────────────────────────────────────
    print("[ Checking split ratios ]")
    check_split_ratios(splits, report)
    print()

    # ── 8. Duplicates ─────────────────────────────────────────────────────────
    print("[ Checking for exact duplicates ]")
    check_duplicate_instructions(all_pairs, report)
    print()

    # ── 9. Summary JSON ───────────────────────────────────────────────────────
    print("[ Checking summary.json ]")
    check_summary_json(output_dir, report)
    print()

    # ── Final summary ─────────────────────────────────────────────────────────
    ok = report.summary()
    if ok:
        print()
        print("Next step: open 03_model_training/notebooks/01_setup_colab.ipynb")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
