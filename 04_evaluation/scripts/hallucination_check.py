#!/usr/bin/env python3
"""
hallucination_check.py — Scan evaluation results for fabricated Quran/Hadith references.

Usage:
    python hallucination_check.py --report eval_20260521_120000_noor.json
    python hallucination_check.py --report-dir ../reports    (scans all reports)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from reference_validator import ReferenceValidator

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def check_report(report_path: Path, validator: ReferenceValidator) -> dict:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    results = data.get("results", [])

    summary = {
        "report":               report_path.name,
        "model":                data.get("model", "unknown"),
        "total_questions":      len(results),
        "fabrications_found":   0,
        "questions_with_fab":   [],
        "total_quran_cited":    0,
        "total_quran_valid":    0,
        "total_hadith_cited":   0,
        "total_hadith_valid":   0,
    }

    for r in results:
        answer = r.get("answer", "")
        if answer.startswith("[ERROR"):
            continue

        vr = validator.validate_answer(answer)
        summary["total_quran_cited"]  += len(vr.quran_cited)
        summary["total_quran_valid"]  += len(vr.quran_valid)
        summary["total_hadith_cited"] += len(vr.hadith_cited)
        summary["total_hadith_valid"] += len(vr.hadith_valid)

        if vr.has_fabrication:
            summary["fabrications_found"] += 1
            summary["questions_with_fab"].append({
                "id":              r["id"],
                "category":        r.get("category", "?"),
                "question_prefix": r["question"][:80],
                "fabricated_quran":  vr.quran_invalid,
                "fabricated_hadith": vr.hadith_invalid,
            })

    quran_acc  = (summary["total_quran_valid"]  / summary["total_quran_cited"]  * 100) if summary["total_quran_cited"]  else 100.0
    hadith_acc = (summary["total_hadith_valid"] / summary["total_hadith_cited"] * 100) if summary["total_hadith_cited"] else 100.0
    summary["quran_accuracy_pct"]  = round(quran_acc,  1)
    summary["hadith_accuracy_pct"] = round(hadith_acc, 1)
    summary["pass"] = (
        summary["fabrications_found"] == 0
        and quran_acc  >= 90.0
        and hadith_acc >= 90.0
    )
    return summary


def print_summary(s: dict) -> None:
    status = "PASS" if s["pass"] else "FAIL"
    print(f"\n{'='*65}")
    print(f"  {s['report']}")
    print(f"  Model  : {s['model']}")
    print(f"  Status : {status}")
    print(f"  Questions    : {s['total_questions']}")
    print(f"  Quran  refs  : {s['total_quran_cited']:4d}  valid={s['total_quran_valid']:4d}  accuracy={s['quran_accuracy_pct']}%  (target ≥90%)")
    print(f"  Hadith refs  : {s['total_hadith_cited']:4d}  valid={s['total_hadith_valid']:4d}  accuracy={s['hadith_accuracy_pct']}%  (target ≥90%)")
    print(f"  Fabrications : {s['fabrications_found']}  (target = 0)")

    if s["questions_with_fab"]:
        print("\n  Fabricated references found:")
        for q in s["questions_with_fab"]:
            print(f"    [{q['id']}] {q['question_prefix']}")
            if q["fabricated_quran"]:
                print(f"      Quran  (invalid): {q['fabricated_quran']}")
            if q["fabricated_hadith"]:
                print(f"      Hadith (invalid): {q['fabricated_hadith']}")
    print(f"{'='*65}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report",     help="Single report JSON filename (from reports/)")
    group.add_argument("--report-dir", action="store_true",
                       help="Scan all reports in reports/")
    args = parser.parse_args()

    validator = ReferenceValidator()

    if args.report:
        path = REPORTS_DIR / args.report
        if not path.exists():
            path = Path(args.report)
        if not path.exists():
            print(f"Report not found: {args.report}")
            sys.exit(1)
        s = check_report(path, validator)
        print_summary(s)
        sys.exit(0 if s["pass"] else 1)

    # Scan all reports
    reports = sorted(REPORTS_DIR.glob("eval_*.json"))
    if not reports:
        print("No evaluation reports found in reports/. Run run_evaluation.py first.")
        sys.exit(1)

    all_pass = True
    for rp in reports:
        s = check_report(rp, validator)
        print_summary(s)
        if not s["pass"]:
            all_pass = False

    print(f"Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
