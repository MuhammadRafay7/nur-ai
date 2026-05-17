#!/usr/bin/env python3
"""
Priority 2 — Fabricated hadith filter.

Scans every hadith in the downloaded collections and removes / quarantines
hadith that:
  (a) have a normalised grade of Mawdu' or Munkar, OR
  (b) match text patterns from the fabricated_hadith.json knowledge base

Output:
  raw/hadith/<name>_clean.json       — collection with Mawdu'/Munkar removed
  raw/hadith/quarantine.json         — all removed hadiths (for audit)
  logs/filter_report_<timestamp>.json

Usage:
    python filter_fabricated.py
    python filter_fabricated.py --raw-dir /custom/raw
    python filter_fabricated.py --dry-run   (report only — no files written)
    python filter_fabricated.py --grade-file bukhari_graded.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RAW_DIR: Path = Path(__file__).parent.parent / "raw"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"

# Grades to quarantine — Mawdu' is fabricated; Munkar is rejected
QUARANTINE_GRADES: set[str] = {"Mawdu'", "Munkar"}

# Collections to filter — prefers _graded.json if available, falls back to original
COLLECTIONS: list[tuple[str, str]] = [
    ("bukhari",          "Sahih Bukhari"),
    ("muslim",           "Sahih Muslim"),
    ("abu_dawud",        "Sunan Abu Dawud"),
    ("tirmidhi",         "Jami at-Tirmidhi"),
    ("ibn_majah",        "Sunan Ibn Majah"),
    ("nasai",            "Sunan an-Nasai"),
    ("muwatta_malik",    "Muwatta Imam Malik"),
    ("darimi",           "Sunan ad-Darimi"),
    ("nawawi_40",        "40 Hadith Nawawi"),
    ("hadith_qudsi",     "Hadith Qudsi"),
    ("riyad_as_salihin", "Riyad as-Salihin"),
    ("riyad_us_salihin", "Riyad us-Salihin"),
    ("bulugh_al_maram",  "Bulugh al-Maram"),
]


# ─── Fabricated text patterns ─────────────────────────────────────────────────

def build_pattern_list(kb_dir: Path) -> list[tuple[str, str, str]]:
    """Build a list of (pattern, status, display_text) from fabricated_hadith.json.

    Args:
        kb_dir: Knowledge bases directory.

    Returns:
        List of (regex_pattern, status, display_text) tuples for matching.
    """
    fab_file = kb_dir / "fabricated_hadith.json"
    if not fab_file.exists():
        print(f"  WARN  fabricated_hadith.json not found at {fab_file}")
        return []

    data = json.loads(fab_file.read_text(encoding="utf-8"))
    patterns: list[tuple[str, str, str]] = []

    for entry in data.get("fabricated_hadith", []):
        status = entry.get("status", "").upper()
        # Skip entries that are confirmations of authentic hadith
        if "AUTHENTIC" in status:
            continue

        text = entry.get("circulated_text", "")
        if not text:
            continue

        # Build a conservative regex from 4-6 key words in the text
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())[:6]
        if len(words) >= 3:
            pattern = r"\b" + r"\b.*?\b".join(re.escape(w) for w in words[:4]) + r"\b"
            patterns.append((pattern, status, text[:80]))

    print(f"  INFO  Built {len(patterns)} text patterns from fabricated_hadith.json")
    return patterns


def matches_fabricated_pattern(
    text: str,
    patterns: list[tuple[str, str, str]],
) -> tuple[bool, str]:
    """Check if a hadith text matches any fabricated pattern.

    Args:
        text: Hadith English text to check.
        patterns: List of (regex_pattern, status, display_text) tuples.

    Returns:
        Tuple of (is_match, matched_display_text).
    """
    text_lower = text.lower()
    for pattern, _status, display in patterns:
        try:
            if re.search(pattern, text_lower, re.DOTALL):
                return True, display
        except re.error:
            pass
    return False, ""


# ─── Collection filter ────────────────────────────────────────────────────────

def filter_collection(
    hadith_dir: Path,
    base_name: str,
    display_name: str,
    patterns: list[tuple[str, str, str]],
    dry_run: bool,
) -> dict[str, Any] | None:
    """Filter fabricated and rejected hadith from one collection.

    Prefers <base_name>_graded.json (output of grade_hadiths.py) over
    the raw <base_name>.json so grade_normalised is available.

    Args:
        hadith_dir: Directory containing collection JSON files.
        base_name: Base name without extension (e.g. 'bukhari').
        display_name: Human-readable collection name.
        patterns: Fabricated text patterns for matching.
        dry_run: If True, do not write output files.

    Returns:
        Statistics dict for this collection, or None if file missing.
    """
    # Prefer graded file
    graded_path = hadith_dir / f"{base_name}_graded.json"
    raw_path    = hadith_dir / f"{base_name}.json"

    if graded_path.exists():
        source_path = graded_path
        using_graded = True
    elif raw_path.exists():
        source_path = raw_path
        using_graded = False
    else:
        print(f"  SKIP  {base_name} — no source file found (run download + grade scripts first)")
        return None

    print(f"\n  Filtering {display_name} ({source_path.name})...")
    if not using_graded:
        print(f"  NOTE  Using raw file — run grade_hadiths.py first for better accuracy")

    data = json.loads(source_path.read_text(encoding="utf-8"))
    hadiths: list[dict[str, Any]] = data.get("hadiths", [])

    kept: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    pattern_flags: int = 0

    for hadith in hadiths:
        grade_norm = hadith.get("grade_normalised", "")
        english_text = hadith.get("english_text", "") or ""

        reason: str | None = None

        # Grade-based quarantine
        if grade_norm in QUARANTINE_GRADES:
            reason = f"grade={grade_norm}"

        # Pattern-based quarantine (only if not already quarantined)
        if reason is None and patterns and english_text:
            matched, matched_text = matches_fabricated_pattern(english_text, patterns)
            if matched:
                reason = f"text_match: {matched_text[:50]}"
                pattern_flags += 1

        if reason:
            h_out = dict(hadith)
            h_out["quarantine_reason"] = reason
            h_out["quarantine_source"] = base_name
            quarantined.append(h_out)
        else:
            kept.append(hadith)

    removed = len(quarantined)
    total = len(hadiths)
    print(f"         Kept: {len(kept)} / {total}  |  Removed: {removed}  |  Pattern flags: {pattern_flags}")

    if not dry_run and kept:
        out_data = dict(data)
        out_data["hadiths"] = kept
        out_data["filter_metadata"] = {
            "filtered_at": datetime.now(timezone.utc).isoformat(),
            "original_count": total,
            "kept_count": len(kept),
            "removed_count": removed,
            "pattern_flags": pattern_flags,
        }
        clean_path = hadith_dir / f"{base_name}_clean.json"
        clean_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"         → Saved: {clean_path.name}")

    return {
        "collection": display_name,
        "base_name": base_name,
        "source_file": source_path.name,
        "total": total,
        "kept": len(kept),
        "removed": removed,
        "pattern_flags": pattern_flags,
        "quarantined_samples": [
            {"num": h.get("hadith_number"), "reason": h.get("quarantine_reason")}
            for h in quarantined[:10]
        ],
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Filter fabricated and rejected hadith from all collections.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python filter_fabricated.py
  python filter_fabricated.py --dry-run
  python filter_fabricated.py --raw-dir /custom/raw
        """,
    )
    parser.add_argument(
        "--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
        help=f"Root raw data directory (default: {DEFAULT_RAW_DIR})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report only — do not write _clean.json files",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: filter all collections and produce report."""
    args = parse_args()
    raw_dir: Path = args.raw_dir
    hadith_dir = raw_dir / "hadith"
    kb_dir = raw_dir / "knowledge_bases"
    log_dir = LOG_DIR

    print("\n  Islamic AI Engine — Fabricated Hadith Filter")
    print(f"  Raw dir  : {raw_dir}")
    print(f"  Dry run  : {args.dry_run}")
    print("=" * 60)
    print("  NOTE  Run grade_hadiths.py first for grade-based filtering.")
    print("        This script also filters on text patterns from fabricated_hadith.json.")

    if not hadith_dir.exists():
        print(f"  ERROR  Hadith directory not found: {hadith_dir}")
        sys.exit(1)

    start = time.monotonic()

    # Build fabricated text patterns
    patterns = build_pattern_list(kb_dir)

    # Filter each collection
    results: list[dict[str, Any]] = []
    quarantine_all: list[dict[str, Any]] = []
    total_kept = 0
    total_removed = 0

    for base_name, display_name in COLLECTIONS:
        stats = filter_collection(hadith_dir, base_name, display_name, patterns, args.dry_run)
        if stats:
            results.append(stats)
            total_kept    += stats["kept"]
            total_removed += stats["removed"]

    # Write quarantine file — all removed hadiths together for audit
    if not args.dry_run and quarantine_all:
        q_path = hadith_dir / "quarantine.json"
        q_data = {
            "metadata": {
                "description": "Hadith quarantined from training data — Mawdu'/Munkar grade or text match",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_quarantined": len(quarantine_all),
            },
            "hadiths": quarantine_all,
        }
        q_path.write_text(json.dumps(q_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  Quarantine file: {q_path} ({len(quarantine_all)} hadiths)")

    # Summary
    print("\n" + "=" * 60)
    print("  FILTER SUMMARY")
    print("=" * 60)
    print(f"  {'Collection':<30} {'Kept':>6} {'Removed':>8} {'Pat.Flags':>10}")
    print("  " + "-" * 56)
    for r in results:
        print(
            f"  {r['collection']:<30} {r['kept']:>6} {r['removed']:>8} {r['pattern_flags']:>10}"
        )
    print("  " + "-" * 56)
    print(f"  {'TOTAL':<30} {total_kept:>6} {total_removed:>8}")
    removal_pct = (total_removed / max(total_kept + total_removed, 1)) * 100
    print(f"\n  Removal rate: {removal_pct:.1f}%  (target: < 5%)")

    if removal_pct > 10:
        print("  WARN  High removal rate — review quarantine.json before proceeding")
    elif removal_pct > 0:
        print("  NOTE  Some hadiths removed — review quarantine.json to confirm correctness")
    else:
        print("  INFO  No hadiths removed — all collections appear clean")

    # Save JSON report
    if not args.dry_run:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_kept": total_kept,
            "total_removed": total_removed,
            "removal_rate_pct": round(removal_pct, 2),
            "collections": results,
        }
        report_path = log_dir / f"filter_report_{timestamp}.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  Report saved: {report_path}")

    elapsed = time.monotonic() - start
    print(f"  Done in {elapsed:.1f} seconds")
    print("  Next step: python ../../02_dataset_formatting/scripts/generate_qa_pairs.py")


if __name__ == "__main__":
    main()
