#!/usr/bin/env python3
"""
Priority 1 — Clean and grade every hadith in the dataset.

For each hadith collection JSON file:
  1. Normalise the raw 'grade' field to a canonical value:
       Sahih | Hasan | Da'if | Mawdu' | Mursal | Munkar | Unknown
  2. Detect and flag fabricated (Mawdu') hadiths from fabricated_hadith.json
  3. Write a cleaned copy with a normalised 'grade_normalised' field
  4. Produce a grading report: per-collection and overall grade distribution

Output:
  raw/hadith/<name>_graded.json     — cleaned copies with grade_normalised
  logs/grade_report_<timestamp>.json — full statistics report
  logs/grade_report_<timestamp>.txt  — human-readable summary

Usage:
    python grade_hadiths.py
    python grade_hadiths.py --raw-dir /custom/raw
    python grade_hadiths.py --dry-run        (report only, no file writes)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Grade normalisation map ──────────────────────────────────────────────────
# Maps every known raw grade string pattern → canonical grade.
# Keys are lowercased and stripped before lookup.
# Order matters for prefix matching — longer strings first.

GRADE_MAP: dict[str, str] = {
    # ── Sahih ──────────────────────────────────────────────────────────────────
    "sahih":                          "Sahih",
    "sahīh":                          "Sahih",
    "saheeh":                         "Sahih",
    "صحيح":                           "Sahih",
    "authentic":                      "Sahih",
    "sound":                          "Sahih",
    "sahih li dhatihi":               "Sahih",
    "sahih li ghayrihi":              "Sahih",
    "sahih lighayrihi":               "Sahih",
    "sahih - authentic":              "Sahih",
    "sahih (authentic)":              "Sahih",
    "graded authentic":               "Sahih",
    "muttafaq 'alayh":               "Sahih",
    "muttafaq alayh":                 "Sahih",
    "agreed upon":                    "Sahih",

    # ── Hasan ──────────────────────────────────────────────────────────────────
    "hasan":                          "Hasan",
    "حسن":                            "Hasan",
    "good":                           "Hasan",
    "fair":                           "Hasan",
    "hasan li dhatihi":               "Hasan",
    "hasan li ghayrihi":              "Hasan",
    "hasan lighayrihi":               "Hasan",
    "hasan (good)":                   "Hasan",
    "hasan sahih":                    "Hasan",  # Tirmidhi's grading — nearest to Sahih
    "hassan sahih":                   "Hasan",
    "hasan saheeh":                   "Hasan",
    "jayyid":                         "Hasan",  # "good" — used by some scholars
    "qawi":                           "Hasan",  # "strong" — below sahih
    "hasan - good":                   "Hasan",

    # ── Da'if ──────────────────────────────────────────────────────────────────
    "da'if":                          "Da'if",
    "daif":                           "Da'if",
    "da`if":                          "Da'if",
    "da''if":                         "Da'if",
    "daeef":                          "Da'if",
    "ضعيف":                           "Da'if",
    "weak":                           "Da'if",
    "weak hadith":                    "Da'if",
    "da'if jiddan":                   "Da'if",
    "very weak":                      "Da'if",
    "extremely weak":                 "Da'if",
    "da'if (weak)":                   "Da'if",
    "da'eef":                         "Da'if",
    "isnad da'if":                    "Da'if",
    "chain is weak":                  "Da'if",
    "weak chain":                     "Da'if",
    "munqati":                        "Da'if",   # broken chain subtype
    "munqati'":                       "Da'if",
    "mu'dal":                         "Da'if",   # two consecutive missing narrators
    "mudal":                          "Da'if",
    "mu'allaq":                       "Da'if",   # suspended chain
    "muallaq":                        "Da'if",
    "mudraj":                         "Da'if",   # interpolated text
    "mudtarib":                       "Da'if",   # contradictory chains
    "shadh":                          "Da'if",   # contradicts more reliable narrators
    "matruk":                         "Da'if",   # abandoned narrator
    "munkar":                         "Munkar",  # rejected — distinct status
    "maqlub":                         "Da'if",   # inverted text/chain

    # ── Mawdu' (Fabricated) ────────────────────────────────────────────────────
    "mawdu'":                         "Mawdu'",
    "mawdu":                          "Mawdu'",
    "موضوع":                          "Mawdu'",
    "fabricated":                     "Mawdu'",
    "forged":                         "Mawdu'",
    "invented":                       "Mawdu'",
    "batil":                          "Mawdu'",  # void / baseless
    "la asla lahu":                   "Mawdu'",  # no basis
    "no basis":                       "Mawdu'",
    "no foundation":                  "Mawdu'",

    # ── Mursal ──────────────────────────────────────────────────────────────────
    "mursal":                         "Mursal",  # Companion link missing
    "مرسل":                           "Mursal",

    # ── Munkar ──────────────────────────────────────────────────────────────────
    # Already mapped above; explicit entry for clarity
    "منكر":                           "Munkar",
}

# Canonical grades (order reflects reliability, high to low)
CANONICAL_GRADES: list[str] = ["Sahih", "Hasan", "Mursal", "Da'if", "Munkar", "Mawdu'", "Unknown"]

# Grades that should be flagged during training — model should note these
FLAGGED_GRADES: set[str] = {"Da'if", "Munkar", "Mawdu'", "Unknown"}

# Collections to process — tuple: (filename, display_name)
COLLECTIONS: list[tuple[str, str]] = [
    ("bukhari.json",          "Sahih Bukhari"),
    ("muslim.json",           "Sahih Muslim"),
    ("abu_dawud.json",        "Sunan Abu Dawud"),
    ("tirmidhi.json",         "Jami at-Tirmidhi"),
    ("ibn_majah.json",        "Sunan Ibn Majah"),
    ("nasai.json",            "Sunan an-Nasai"),
    ("muwatta_malik.json",    "Muwatta Imam Malik"),
    ("darimi.json",           "Sunan ad-Darimi"),
    ("nawawi_40.json",        "40 Hadith Nawawi"),
    ("hadith_qudsi.json",     "Hadith Qudsi"),
    ("riyad_as_salihin.json", "Riyad as-Salihin"),
    ("riyad_us_salihin.json", "Riyad us-Salihin"),
    ("bulugh_al_maram.json",  "Bulugh al-Maram"),
]

DEFAULT_RAW_DIR: Path = Path(__file__).parent.parent / "raw"
KB_DIR: Path = DEFAULT_RAW_DIR / "knowledge_bases"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"


# ─── Grade normalisation ──────────────────────────────────────────────────────

def normalise_grade(raw: str | None) -> str:
    """Normalise a raw grade string to a canonical value.

    Args:
        raw: Raw grade string from the source data.

    Returns:
        Canonical grade string: Sahih | Hasan | Mursal | Da'if | Munkar | Mawdu' | Unknown
    """
    if not raw:
        return "Unknown"

    cleaned = raw.strip().lower()
    # Remove square brackets and parenthetical content added by some API wrappers
    cleaned = re.sub(r"\[.*?\]", "", cleaned).strip()

    # Direct lookup
    if cleaned in GRADE_MAP:
        return GRADE_MAP[cleaned]

    # Partial match — check if any key is a substring of the cleaned grade
    for key, canonical in GRADE_MAP.items():
        if key in cleaned:
            return canonical

    # Heuristic patterns for multi-word grades not in the map
    if any(w in cleaned for w in ("sahih", "saheeh", "authentic", "sound")):
        return "Sahih"
    if any(w in cleaned for w in ("hasan", "hassan", "good", "fair", "jayyid")):
        return "Hasan"
    if any(w in cleaned for w in ("mawdu", "fabricat", "forged", "batil")):
        return "Mawdu'"
    if any(w in cleaned for w in ("mursal",)):
        return "Mursal"
    if any(w in cleaned for w in ("munkar",)):
        return "Munkar"
    if any(w in cleaned for w in ("da'if", "daif", "weak", "daeef")):
        return "Da'if"

    return "Unknown"


# ─── Fabricated hadith filter ──────────────────────────────────────────────────

def load_fabricated_texts(kb_dir: Path) -> list[str]:
    """Load known fabricated hadith text snippets for cross-reference.

    Args:
        kb_dir: Knowledge bases directory containing fabricated_hadith.json.

    Returns:
        List of lowercased text snippets from known fabricated hadith.
    """
    fab_file = kb_dir / "fabricated_hadith.json"
    if not fab_file.exists():
        print(f"  WARN  fabricated_hadith.json not found at {fab_file} — skipping fabrication cross-check")
        return []

    try:
        data = json.loads(fab_file.read_text(encoding="utf-8"))
        snippets: list[str] = []
        for entry in data.get("fabricated_hadith", []):
            text = entry.get("circulated_text", "")
            if text and entry.get("status", "").upper() not in ("AUTHENTIC", "NOTE"):
                # Extract the core phrase (first 60 chars) for matching
                snippets.append(text[:80].lower())
        print(f"  INFO  Loaded {len(snippets)} fabricated hadith snippets for cross-reference")
        return snippets
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"  WARN  Could not load fabricated_hadith.json: {exc}")
        return []


def is_likely_fabricated(hadith_text: str, fabricated_snippets: list[str]) -> bool:
    """Check if a hadith text matches known fabricated hadith snippets.

    Args:
        hadith_text: English text of the hadith.
        fabricated_snippets: List of lowercased fabricated text snippets.

    Returns:
        True if the hadith text appears to match a known fabricated hadith.
    """
    text_lower = hadith_text.lower()
    # Use substring matching on first 100 chars of snippet
    for snippet in fabricated_snippets:
        # Match on 5+ consecutive words from the snippet
        words = snippet.split()
        if len(words) >= 4:
            key_phrase = " ".join(words[:5])
            if key_phrase in text_lower:
                return True
    return False


# ─── Collection grader ────────────────────────────────────────────────────────

def grade_collection(
    hadith_dir: Path,
    filename: str,
    display_name: str,
    fabricated_snippets: list[str],
    dry_run: bool,
) -> dict[str, Any] | None:
    """Load, grade, and optionally save one hadith collection.

    Args:
        hadith_dir: Directory containing the collection JSON.
        filename: Filename of the collection.
        display_name: Human-readable collection name.
        fabricated_snippets: Known fabricated hadith text snippets.
        dry_run: If True, do not write output files.

    Returns:
        Statistics dict for this collection, or None if file missing.
    """
    input_path = hadith_dir / filename
    if not input_path.exists():
        print(f"  SKIP  {filename} not found — run download scripts first")
        return None

    print(f"\n  Processing {display_name} ({filename})...")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    hadiths: list[dict[str, Any]] = data.get("hadiths", [])

    grade_counter: Counter[str] = Counter()
    unknown_raw_grades: Counter[str] = Counter()
    fabrication_flags: list[int | str] = []
    processed: list[dict[str, Any]] = []

    for hadith in hadiths:
        raw_grade = hadith.get("grade") or hadith.get("grade_raw") or ""
        normalised = normalise_grade(raw_grade)
        grade_counter[normalised] += 1

        if normalised == "Unknown" and raw_grade:
            unknown_raw_grades[raw_grade.strip()[:60]] += 1

        # Cross-reference with fabricated hadith database
        english_text = hadith.get("english_text", "") or ""
        fabrication_flagged = False
        if normalised not in ("Mawdu'",) and fabricated_snippets:
            if is_likely_fabricated(english_text, fabricated_snippets):
                fabrication_flagged = True
                fabrication_flags.append(hadith.get("hadith_number", "?"))
                normalised = "Mawdu'"  # Override grade
                grade_counter["Mawdu'"] += 1
                grade_counter[normalised] -= 1  # adjust — we already counted above

        h_out = dict(hadith)
        h_out["grade_normalised"] = normalised
        h_out["grade_raw"] = raw_grade
        if fabrication_flagged:
            h_out["fabrication_flag"] = True
        processed.append(h_out)

    # Write graded file
    output_filename = filename.replace(".json", "_graded.json")
    output_path = hadith_dir / output_filename
    if not dry_run:
        out_data = dict(data)
        out_data["hadiths"] = processed
        out_data["grading_metadata"] = {
            "graded_at": datetime.now(timezone.utc).isoformat(),
            "grade_distribution": dict(grade_counter),
            "total_hadiths": len(processed),
            "fabrication_flags_count": len(fabrication_flags),
        }
        output_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"         → Saved: {output_filename} ({len(processed)} hadiths)")

    # Print distribution
    total = len(processed)
    for grade in CANONICAL_GRADES:
        count = grade_counter.get(grade, 0)
        pct = (count / max(total, 1)) * 100
        flag = " ⚠" if grade in FLAGGED_GRADES and count > 0 else ""
        print(f"         {grade:<10} {count:>5} ({pct:>5.1f}%){flag}")

    if unknown_raw_grades:
        top_unknown = unknown_raw_grades.most_common(5)
        print(f"         Unknown grade samples: {top_unknown}")

    if fabrication_flags:
        print(f"         Fabrication flags: {len(fabrication_flags)} hadith(s) matched known fabricated text")
        print(f"         Sample: {fabrication_flags[:5]}")

    return {
        "collection": display_name,
        "filename": filename,
        "total": total,
        "grade_distribution": dict(grade_counter),
        "unknown_raw_samples": dict(unknown_raw_grades.most_common(10)),
        "fabrication_flags_count": len(fabrication_flags),
        "fabrication_flag_numbers": fabrication_flags[:20],
        "output_file": str(output_path) if not dry_run else None,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean and grade every hadith in the Islamic AI dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python grade_hadiths.py
  python grade_hadiths.py --raw-dir /custom/raw
  python grade_hadiths.py --dry-run
  python grade_hadiths.py --collection bukhari.json
        """,
    )
    parser.add_argument(
        "--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
        help=f"Root raw data directory (default: {DEFAULT_RAW_DIR})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print report only — do not write graded JSON files",
    )
    parser.add_argument(
        "--collection",
        help="Process only this specific collection filename (e.g. bukhari.json)",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: grade all hadith collections and produce reports."""
    args = parse_args()
    raw_dir: Path = args.raw_dir
    hadith_dir = raw_dir / "hadith"
    kb_dir = raw_dir / "knowledge_bases"
    log_dir = LOG_DIR

    print("\n  Islamic AI Engine — Hadith Grading & Quality Control")
    print(f"  Raw dir  : {raw_dir}")
    print(f"  Dry run  : {args.dry_run}")
    if args.collection:
        print(f"  Filter   : {args.collection}")
    print("=" * 60)

    if not hadith_dir.exists():
        print(f"  ERROR  Hadith directory not found: {hadith_dir}")
        print("         Run Phase 1 download scripts first.")
        sys.exit(1)

    start = time.monotonic()

    # Load fabricated hadith snippets for cross-reference
    fabricated_snippets = load_fabricated_texts(kb_dir)

    # Filter collections if --collection specified
    collections = COLLECTIONS
    if args.collection:
        collections = [(f, d) for f, d in COLLECTIONS if f == args.collection]
        if not collections:
            print(f"  ERROR  Unknown collection: {args.collection}")
            print(f"         Available: {[f for f, _ in COLLECTIONS]}")
            sys.exit(1)

    # Process each collection
    results: list[dict[str, Any]] = []
    overall_grades: Counter[str] = Counter()

    for filename, display_name in collections:
        stats = grade_collection(
            hadith_dir, filename, display_name, fabricated_snippets, args.dry_run
        )
        if stats:
            results.append(stats)
            for grade, count in stats["grade_distribution"].items():
                overall_grades[grade] += count

    # Overall summary
    print("\n" + "=" * 60)
    print("  OVERALL GRADE DISTRIBUTION")
    print("=" * 60)
    grand_total = sum(overall_grades.values())
    for grade in CANONICAL_GRADES:
        count = overall_grades.get(grade, 0)
        pct = (count / max(grand_total, 1)) * 100
        bar = "█" * int(pct / 2)
        flag = " ⚠" if grade in FLAGGED_GRADES and count > 0 else ""
        print(f"  {grade:<10} {count:>6} ({pct:>5.1f}%)  {bar}{flag}")
    print(f"\n  Total hadiths processed: {grand_total}")

    total_fabs = sum(r.get("fabrication_flags_count", 0) for r in results)
    if total_fabs:
        print(f"  Fabrication flags raised: {total_fabs} hadith(s) matched known fabricated text")

    # Grading quality score
    sahih_hasan = overall_grades.get("Sahih", 0) + overall_grades.get("Hasan", 0)
    quality_pct = (sahih_hasan / max(grand_total, 1)) * 100
    print(f"\n  Dataset quality score: {quality_pct:.1f}% Sahih/Hasan (target: >75%)")

    if quality_pct < 60:
        print("  WARN  Quality score below 60% — review Da'if hadiths before training")
    elif quality_pct < 75:
        print("  NOTE  Good quality — consider removing/flagging Da'if hadiths")
    else:
        print("  PASS  Dataset quality is high — ready for training pipeline")

    # Save report
    if not args.dry_run:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON report
        report_json = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_hadiths": grand_total,
            "overall_grade_distribution": dict(overall_grades),
            "quality_score_pct": round(quality_pct, 2),
            "fabrication_flags_total": total_fabs,
            "collections": results,
        }
        json_path = log_dir / f"grade_report_{timestamp}.json"
        json_path.write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  Report saved: {json_path}")

        # Text summary
        txt_lines = [
            "Islamic AI Engine — Hadith Grade Report",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 60,
            f"Total hadiths: {grand_total}",
            f"Quality score: {quality_pct:.1f}% Sahih/Hasan",
            "",
            "Grade Distribution:",
        ]
        for grade in CANONICAL_GRADES:
            count = overall_grades.get(grade, 0)
            pct = (count / max(grand_total, 1)) * 100
            txt_lines.append(f"  {grade:<10} {count:>6} ({pct:>5.1f}%)")
        txt_path = log_dir / f"grade_report_{timestamp}.txt"
        txt_path.write_text("\n".join(txt_lines), encoding="utf-8")
        print(f"  Report saved: {txt_path}")

    elapsed = time.monotonic() - start
    print(f"\n  Done in {elapsed:.1f} seconds")
    print("  Next step: python filter_fabricated.py")


if __name__ == "__main__":
    main()
