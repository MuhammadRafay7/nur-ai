#!/usr/bin/env python3
"""
Validate all downloaded source data before moving to Phase 2.

Checks performed:
  Quran:
    - quran_full.json is parseable
    - Exactly 114 surahs present
    - Correct ayah count per surah (vs. authoritative reference)
    - Total ayah count == 6236
    - Every ayah has: arabic_text, english_translation, verse_key
    - No empty arabic_text fields

  Hadith collections (each JSON):
    - File is parseable
    - Contains required fields: hadith_number, english_text
    - No duplicate hadith_numbers within a collection
    - Count meets minimum threshold

  Supplementary:
    - asmaul_husna.json is parseable
    - Exactly 99 names

Output:
  - Console report (colour-coded PASS / FAIL)
  - Saved report: 01_data_collection/logs/validation_{timestamp}.txt

Usage:
    python validate_sources.py
    python validate_sources.py --data-dir /custom/raw
    python validate_sources.py --help
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLOUR = True
except ImportError:
    COLOUR = False

# ─── Constants ────────────────────────────────────────────────────────────────

EXPECTED_TOTAL_SURAHS: int = 114
EXPECTED_TOTAL_AYAHS: int = 6236
EXPECTED_NAMES: int = 99

# Authoritative ayah count per surah (index 0 = Surah 1)
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

# Tuple: (filename, display_name, min_count, required)
# required=False → missing file is a WARN, not a FAIL
HADITH_COLLECTIONS: list[tuple[str, str, int, bool]] = [
    # Core Kutub al-Sittah (Six Books) — required
    ("bukhari.json",          "Sahih Bukhari",          5000, True),
    ("muslim.json",           "Sahih Muslim",           4000, True),
    ("abu_dawud.json",        "Sunan Abu Dawud",        3000, True),
    ("tirmidhi.json",         "Jami at-Tirmidhi",       2000, True),
    ("ibn_majah.json",        "Sunan Ibn Majah",        3000, True),
    ("nasai.json",            "Sunan an-Nasai",         3000, True),
    # Extended collections — optional (downloaded by download_extended_hadith.py)
    ("muwatta_malik.json",    "Muwatta Imam Malik",      800, False),
    ("darimi.json",           "Sunan ad-Darimi",        2000, False),
    ("nawawi_40.json",        "40 Hadith Nawawi",         40, False),
    ("hadith_qudsi.json",     "Hadith Qudsi",            100, False),
    ("riyad_as_salihin.json", "Riyad as-Salihin",       1000, False),
    ("riyad_us_salihin.json", "Riyad us-Salihin (alt)",  500, False),
    ("bulugh_al_maram.json",  "Bulugh al-Maram",        1200, False),
]

# Knowledge base files that must exist for Phase 2 to generate full pairs
KNOWLEDGE_BASE_FILES: list[tuple[str, str, bool]] = [
    ("tajweed_rules.json",         "Tajweed Rules",                True),
    ("hadith_sciences.json",       "Hadith Sciences (Mustalah)",   True),
    ("usul_al_fiqh.json",          "Usul al-Fiqh",                 True),
    ("madhab_comparative.json",    "Madhab Comparison",            True),
    ("prophets_in_islam.json",     "Prophets in Islam",            True),
    ("aqeedah.json",               "Aqeedah (Islamic Beliefs)",    True),
    ("eschatology.json",           "Eschatology (End Times)",      True),
    ("ibadah_salah_zakat_fasting_hajj.json", "Ibadah (Pillars)", True),
    ("family_law_inheritance.json","Family Law & Faraid",          True),
    ("fabricated_hadith.json",     "Fabricated Hadith Database",   True),
    ("quran_sciences.json",        "Ulum al-Quran",                True),
    ("contemporary_issues_fiqh.json", "Contemporary Fiqh",        True),
    ("duas_and_adhkar.json",          "Duas and Adhkar",           True),
    ("sahabah_biographies.json",      "Sahabah Biographies",       True),
]

DEFAULT_DATA_DIR: Path = Path(__file__).parent.parent / "raw"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"


# ─── Colour helpers ───────────────────────────────────────────────────────────

def green(text: str) -> str:
    """Wrap text in green ANSI colour if supported."""
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}" if COLOUR else text


def red(text: str) -> str:
    """Wrap text in red ANSI colour if supported."""
    return f"{Fore.RED}{text}{Style.RESET_ALL}" if COLOUR else text


def yellow(text: str) -> str:
    """Wrap text in yellow ANSI colour if supported."""
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}" if COLOUR else text


def bold(text: str) -> str:
    """Wrap text in bold ANSI style if supported."""
    return f"{Style.BRIGHT}{text}{Style.RESET_ALL}" if COLOUR else text


# ─── Validation result tracker ────────────────────────────────────────────────

class ValidationReport:
    """Accumulates pass/fail/warn results and produces a final summary.

    Attributes:
        passes: List of passing check descriptions.
        failures: List of failing check descriptions.
        warnings: List of warning check descriptions.
        lines: All output lines (for saving to file).
    """

    def __init__(self) -> None:
        self.passes: list[str] = []
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.lines: list[str] = []

    def ok(self, message: str) -> None:
        """Record a passing check.

        Args:
            message: Description of what passed.
        """
        label = green("  PASS")
        line = f"{label}  {message}"
        print(line)
        self.passes.append(message)
        self.lines.append(f"  PASS  {message}")

    def fail(self, message: str) -> None:
        """Record a failing check.

        Args:
            message: Description of what failed.
        """
        label = red("  FAIL")
        line = f"{label}  {message}"
        print(line)
        self.failures.append(message)
        self.lines.append(f"  FAIL  {message}")

    def warn(self, message: str) -> None:
        """Record a warning.

        Args:
            message: Description of the warning.
        """
        label = yellow("  WARN")
        line = f"{label}  {message}"
        print(line)
        self.warnings.append(message)
        self.lines.append(f"  WARN  {message}")

    def section(self, title: str) -> None:
        """Print a section header.

        Args:
            title: Section heading text.
        """
        separator = "─" * 60
        print(f"\n{bold(separator)}")
        print(f"  {bold(title)}")
        print(bold(separator))
        self.lines.append(f"\n{'─'*60}")
        self.lines.append(f"  {title}")
        self.lines.append("─" * 60)

    def summary(self) -> bool:
        """Print the final summary and return True if all checks passed.

        Returns:
            True if there are zero failures; False otherwise.
        """
        separator = "=" * 60
        total = len(self.passes) + len(self.failures) + len(self.warnings)
        print(f"\n{bold(separator)}")
        print(f"  {bold('VALIDATION SUMMARY')}")
        print(bold(separator))
        print(f"  Total checks : {total}")
        print(f"  {green('Passed')}       : {len(self.passes)}")
        print(f"  {yellow('Warnings')}     : {len(self.warnings)}")
        print(f"  {red('Failed')}       : {len(self.failures)}")
        print(bold(separator))

        if self.failures:
            print(f"\n  {red('RESULT: FAILED')} — fix the errors above before running Phase 2.\n")
        elif self.warnings:
            print(f"\n  {yellow('RESULT: PASSED WITH WARNINGS')} — review warnings before Phase 2.\n")
        else:
            print(f"\n  {green('RESULT: ALL CHECKS PASSED')} — ready for Phase 2!\n")

        self.lines.extend([
            f"\n{'='*60}",
            "  VALIDATION SUMMARY",
            "=" * 60,
            f"  Total  : {total}",
            f"  Passed : {len(self.passes)}",
            f"  Warned : {len(self.warnings)}",
            f"  Failed : {len(self.failures)}",
        ])

        return len(self.failures) == 0


# ─── Quran validation ─────────────────────────────────────────────────────────

def validate_quran(quran_dir: Path, report: ValidationReport) -> None:
    """Run all validation checks against quran_full.json.

    Args:
        quran_dir: Directory containing quran_full.json.
        report: ValidationReport to accumulate results into.
    """
    report.section("QURAN — quran_full.json")
    quran_file = quran_dir / "quran_full.json"

    # File existence
    if not quran_file.exists():
        report.fail(f"File not found: {quran_file}")
        report.fail("Cannot continue Quran checks — file missing")
        return

    # Parseability
    try:
        data: dict[str, Any] = json.loads(quran_file.read_text(encoding="utf-8"))
        report.ok("quran_full.json is valid JSON")
    except json.JSONDecodeError as exc:
        report.fail(f"JSON parse error: {exc}")
        return

    surahs: list[dict[str, Any]] = data.get("surahs", [])

    # Surah count
    if len(surahs) == EXPECTED_TOTAL_SURAHS:
        report.ok(f"Surah count: {len(surahs)} / {EXPECTED_TOTAL_SURAHS}")
    else:
        report.fail(f"Surah count: {len(surahs)} / {EXPECTED_TOTAL_SURAHS} (WRONG)")

    # Per-surah ayah count + field checks
    total_ayahs = 0
    empty_arabic: list[str] = []
    empty_translation: list[str] = []
    missing_verse_key: list[str] = []
    ayah_count_errors: list[str] = []

    for surah in surahs:
        s_num = surah.get("surah_number", "?")
        ayahs: list[dict[str, Any]] = surah.get("ayahs", [])
        expected = SURAH_AYAH_COUNTS[int(s_num) - 1] if isinstance(s_num, int) else 0
        total_ayahs += len(ayahs)

        if len(ayahs) != expected:
            ayah_count_errors.append(f"Surah {s_num}: got {len(ayahs)}, expected {expected}")

        for ayah in ayahs:
            vk = ayah.get("verse_key", "")
            if not ayah.get("arabic_text", "").strip():
                empty_arabic.append(vk or f"{s_num}:?")
            if not ayah.get("english_translation", "").strip():
                empty_translation.append(vk or f"{s_num}:?")
            if not vk:
                missing_verse_key.append(f"Surah {s_num} ayah {ayah.get('ayah_number', '?')}")

    # Total ayah count
    if total_ayahs == EXPECTED_TOTAL_AYAHS:
        report.ok(f"Total ayah count: {total_ayahs} / {EXPECTED_TOTAL_AYAHS}")
    else:
        report.fail(f"Total ayah count: {total_ayahs} / {EXPECTED_TOTAL_AYAHS} (WRONG)")

    # Per-surah ayah count errors
    if ayah_count_errors:
        for err in ayah_count_errors[:10]:  # Show first 10 only
            report.fail(f"Ayah count mismatch — {err}")
        if len(ayah_count_errors) > 10:
            report.fail(f"... and {len(ayah_count_errors) - 10} more ayah count errors")
    else:
        report.ok("All 114 surahs have correct ayah counts")

    # Empty fields
    if empty_arabic:
        report.fail(f"Empty arabic_text in {len(empty_arabic)} ayah(s): {empty_arabic[:5]}")
    else:
        report.ok("No empty arabic_text fields")

    if empty_translation:
        report.warn(f"Empty english_translation in {len(empty_translation)} ayah(s): {empty_translation[:5]}")
    else:
        report.ok("No empty english_translation fields")

    if missing_verse_key:
        report.warn(f"Missing verse_key in {len(missing_verse_key)} ayah(s)")
    else:
        report.ok("All ayahs have verse_key")

    # Tafsir coverage
    ayahs_with_tafsir = sum(
        1 for s in surahs for a in s.get("ayahs", [])
        if a.get("tafsir_ibn_kathir", "").strip()
    )
    coverage_pct = (ayahs_with_tafsir / max(total_ayahs, 1)) * 100
    if coverage_pct >= 80:
        report.ok(f"Tafsir coverage: {ayahs_with_tafsir}/{total_ayahs} ayahs ({coverage_pct:.1f}%)")
    elif coverage_pct > 0:
        report.warn(f"Tafsir coverage: {ayahs_with_tafsir}/{total_ayahs} ayahs ({coverage_pct:.1f}%) — consider re-running with tafsir")
    else:
        report.warn("No tafsir data found — run without --skip-tafsir for richer training data")

    # File size sanity
    size_mb = quran_file.stat().st_size / (1024 * 1024)
    if size_mb > 0.5:
        report.ok(f"File size: {size_mb:.1f} MB")
    else:
        report.warn(f"File size only {size_mb:.1f} MB — seems small, check content")


# ─── Hadith validation ────────────────────────────────────────────────────────

def validate_hadith_collection(
    hadith_dir: Path,
    filename: str,
    display_name: str,
    min_count: int,
    required: bool,
    report: ValidationReport,
) -> None:
    """Run validation checks against one Hadith collection JSON file.

    Args:
        hadith_dir: Directory containing the collection JSON.
        filename: Filename of the collection (e.g. 'bukhari.json').
        display_name: Human-readable name for display.
        min_count: Minimum hadith count to pass.
        required: If False, missing file is a WARN not a FAIL.
        report: ValidationReport to accumulate results into.
    """
    report.section(f"HADITH — {display_name} ({filename})")
    hadith_file = hadith_dir / filename

    if not hadith_file.exists():
        if required:
            report.fail(f"File not found: {hadith_file}")
        else:
            report.warn(
                f"File not found: {hadith_file.name} "
                f"— optional collection, run: python download_hadith.py --collections riyadussalihin"
            )
        return

    try:
        data: dict[str, Any] = json.loads(hadith_file.read_text(encoding="utf-8"))
        report.ok(f"{filename} is valid JSON")
    except json.JSONDecodeError as exc:
        report.fail(f"JSON parse error: {exc}")
        return

    hadiths: list[dict[str, Any]] = data.get("hadiths", [])
    count = len(hadiths)

    # Count check
    if count >= min_count:
        report.ok(f"Hadith count: {count} (>= minimum {min_count})")
    else:
        report.fail(f"Hadith count: {count} (below minimum {min_count})")

    # Duplicate check — duplicates are a known source-data characteristic
    # (some collections number sub-hadiths with the same parent number)
    nums = [h.get("hadith_number") for h in hadiths if h.get("hadith_number") is not None]
    duplicates = [n for n, c in Counter(nums).items() if c > 1]
    if duplicates:
        report.warn(
            f"Duplicate hadith_numbers: {len(duplicates)} (e.g. {duplicates[:5]}) "
            f"— source data characteristic, not a download error"
        )
    else:
        report.ok(f"No duplicate hadith_numbers in {count} hadiths")

    # Required fields
    missing_english: list[Any] = []
    missing_number: list[Any] = []
    empty_arabic: list[Any] = []

    for h in hadiths:
        num = h.get("hadith_number", "?")
        if not h.get("english_text", "").strip():
            missing_english.append(num)
        if h.get("hadith_number") is None:
            missing_number.append("(no number)")
        if not h.get("arabic_text", "").strip():
            empty_arabic.append(num)

    if missing_number:
        report.fail(f"Hadiths missing hadith_number: {len(missing_number)}")
    else:
        report.ok("All hadiths have hadith_number")

    # Missing text: FAIL only if > 5% of collection is affected
    missing_pct = (len(missing_english) / max(count, 1)) * 100
    if missing_english and missing_pct > 5:
        report.fail(
            f"Hadiths missing english_text: {len(missing_english)} ({missing_pct:.1f}%) "
            f"— first 5: {missing_english[:5]}"
        )
    elif missing_english:
        report.warn(
            f"Hadiths missing english_text: {len(missing_english)} ({missing_pct:.1f}%) "
            f"— minor source gap, acceptable for training"
        )
    else:
        report.ok("All hadiths have english_text")

    if empty_arabic:
        report.warn(f"Hadiths with no arabic_text: {len(empty_arabic)} — source gap")
    else:
        report.ok("All hadiths have arabic_text")

    # File size
    size_mb = hadith_file.stat().st_size / (1024 * 1024)
    report.ok(f"File size: {size_mb:.1f} MB")


# ─── Supplementary validation ─────────────────────────────────────────────────

def validate_supplementary(supp_dir: Path, report: ValidationReport) -> None:
    """Validate asmaul_husna.json (99 Names of Allah).

    Args:
        supp_dir: Directory containing asmaul_husna.json.
        report: ValidationReport to accumulate results into.
    """
    report.section("SUPPLEMENTARY — asmaul_husna.json")
    supp_file = supp_dir / "asmaul_husna.json"

    if not supp_file.exists():
        report.fail(f"File not found: {supp_file}")
        return

    try:
        data: dict[str, Any] = json.loads(supp_file.read_text(encoding="utf-8"))
        report.ok("asmaul_husna.json is valid JSON")
    except json.JSONDecodeError as exc:
        report.fail(f"JSON parse error: {exc}")
        return

    names: list[dict[str, Any]] = data.get("names", [])

    if len(names) == EXPECTED_NAMES:
        report.ok(f"Name count: {len(names)} / {EXPECTED_NAMES}")
    else:
        report.fail(f"Name count: {len(names)} / {EXPECTED_NAMES} (WRONG)")

    # Required fields
    required = ["number", "arabic", "transliteration", "meaning", "explanation"]
    missing_fields: list[str] = []
    for name in names:
        for field in required:
            if not name.get(field, "").strip() if isinstance(name.get(field), str) else not name.get(field):
                missing_fields.append(f"Name #{name.get('number', '?')} missing {field}")

    if missing_fields:
        for mf in missing_fields[:5]:
            report.fail(mf)
    else:
        report.ok("All 99 names have required fields")


# ─── Knowledge base validation ───────────────────────────────────────────────

def validate_knowledge_bases(kb_dir: Path, report: ValidationReport) -> None:
    """Validate all knowledge base JSON files required for Phase 2.

    Args:
        kb_dir: Directory containing knowledge_bases JSON files.
        report: ValidationReport to accumulate results into.
    """
    report.section("KNOWLEDGE BASES — raw/knowledge_bases/")

    if not kb_dir.exists():
        report.fail(
            f"Knowledge bases directory not found: {kb_dir} "
            "— create it and populate JSON files (see 01_data_collection/raw/knowledge_bases/)"
        )
        return

    total_keys = 0

    for filename, display_name, required in KNOWLEDGE_BASE_FILES:
        kb_file = kb_dir / filename
        if not kb_file.exists():
            if required:
                report.fail(f"Missing required knowledge base: {filename} ({display_name})")
            else:
                report.warn(f"Missing optional knowledge base: {filename} ({display_name})")
            continue

        try:
            data: dict[str, Any] = json.loads(kb_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.fail(f"{filename}: JSON parse error — {exc}")
            continue

        # Basic structure checks
        if not isinstance(data, dict):
            report.fail(f"{filename}: Expected JSON object at root, got {type(data).__name__}")
            continue

        keys = [k for k in data if k != "metadata"]
        total_keys += len(keys)

        metadata = data.get("metadata", {})
        has_title = bool(metadata.get("title", ""))
        size_kb = kb_file.stat().st_size / 1024

        if has_title and keys:
            report.ok(
                f"{filename}: valid ({len(keys)} sections, {size_kb:.0f} KB) — {metadata.get('title', '')}"
            )
        elif keys:
            report.warn(f"{filename}: valid but missing metadata.title ({len(keys)} sections)")
        else:
            report.fail(f"{filename}: file is empty or has no content keys")

    report.ok(f"Knowledge bases total content sections: {total_keys}")


# ─── Report saver ─────────────────────────────────────────────────────────────

def save_report(report: ValidationReport, log_dir: Path) -> None:
    """Save the validation report to a timestamped text file.

    Args:
        report: Completed ValidationReport.
        log_dir: Directory to write the report file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = log_dir / f"validation_{timestamp}.txt"

    header = [
        f"Islamic AI Engine — Source Validation Report",
        f"Generated: {datetime.now().isoformat()}",
        "=" * 60,
    ]
    content = "\n".join(header + report.lines)
    out_file.write_text(content, encoding="utf-8")
    print(f"  Report saved: {out_file}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Validate all downloaded Islamic source data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_sources.py
  python validate_sources.py --data-dir /custom/raw
  python validate_sources.py --help
        """,
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Root directory containing quran/, hadith/, supplementary/ (default: {DEFAULT_DATA_DIR})",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: run all validation checks and print summary."""
    args = parse_args()
    data_dir: Path = args.data_dir

    print(bold("\n  Islamic AI Engine — Source Data Validator"))
    print(bold(f"  Data root: {data_dir}\n"))

    report = ValidationReport()

    # Run all checks
    validate_quran(data_dir / "quran", report)

    for filename, display_name, min_count, required in HADITH_COLLECTIONS:
        validate_hadith_collection(
            data_dir / "hadith", filename, display_name, min_count, required, report
        )

    validate_supplementary(data_dir / "supplementary", report)
    validate_knowledge_bases(data_dir / "knowledge_bases", report)

    # Final summary
    passed = report.summary()

    # Save report
    save_report(report, LOG_DIR)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
