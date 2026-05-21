#!/usr/bin/env python3
"""
generate_report.py — Produce a full evaluation report (JSON + HTML) from
one or all report files in reports/.

Usage:
    python generate_report.py                          # latest report
    python generate_report.py --report eval_xxx.json  # specific report
    python generate_report.py --all                   # all reports combined
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from reference_validator import ReferenceValidator

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def analyse_report(report_path: Path, validator: ReferenceValidator) -> dict:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    results = data.get("results", [])

    by_cat: dict[str, list] = {}
    for r in results:
        by_cat.setdefault(r.get("category", "unknown"), []).append(r)

    category_stats = {}
    total_fab = 0
    total_q  = 0
    total_ar = 0
    total_ref = 0

    for cat, items in by_cat.items():
        n = len(items)
        arabic   = sum(1 for r in items if r["signals"].get("has_arabic", False))
        quran_r  = sum(1 for r in items if r["signals"].get("has_quran_ref", False))
        hadith_r = sum(1 for r in items if r["signals"].get("has_hadith_src", False))
        errors   = sum(1 for r in items if r["signals"].get("is_error", False))
        avg_lat  = sum(r["latency_s"] for r in items) / n if n else 0

        fabs = 0
        missing_kw_cases = []
        for r in items:
            vr = validator.validate_answer(r.get("answer", ""))
            if vr.has_fabrication:
                fabs += 1
            if r["signals"].get("missing_keywords"):
                missing_kw_cases.append({
                    "id": r["id"],
                    "missing": r["signals"]["missing_keywords"],
                })

        category_stats[cat] = {
            "questions":       n,
            "arabic_rate":     round(arabic / n, 3) if n else 0,
            "quran_ref_rate":  round(quran_r / n, 3) if n else 0,
            "hadith_ref_rate": round(hadith_r / n, 3) if n else 0,
            "fabrications":    fabs,
            "errors":          errors,
            "avg_latency_s":   round(avg_lat, 1),
            "missing_keywords": missing_kw_cases,
        }
        total_fab += fabs
        total_q   += n
        total_ar  += arabic
        total_ref += quran_r + hadith_r

    pass_criteria = {
        "arabic_rate":        round(total_ar  / total_q, 3) if total_q else 0,
        "reference_rate":     round(total_ref / (total_q * 2), 3) if total_q else 0,
        "zero_fabrications":  total_fab == 0,
    }

    return {
        "report_file":  report_path.name,
        "model":        data.get("model", "unknown"),
        "run_at":       data.get("run_at", ""),
        "total":        total_q,
        "fabrications": total_fab,
        "pass_criteria": pass_criteria,
        "overall_pass": (
            pass_criteria["arabic_rate"]    >= 0.90
            and pass_criteria["reference_rate"] >= 0.80
            and pass_criteria["zero_fabrications"]
        ),
        "by_category":  category_stats,
    }


def render_html(analysis: dict) -> str:
    status = "PASS" if analysis["overall_pass"] else "FAIL"
    status_color = "#22c55e" if analysis["overall_pass"] else "#ef4444"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = ""
    for cat, s in analysis["by_category"].items():
        fab_badge = f'<span style="color:#ef4444;font-weight:bold">{s["fabrications"]} FABRICATED</span>' if s["fabrications"] else '<span style="color:#22c55e">0</span>'
        rows += (
            f"<tr><td>{cat}</td><td>{s['questions']}</td>"
            f"<td>{s['arabic_rate']*100:.0f}%</td>"
            f"<td>{s['quran_ref_rate']*100:.0f}%</td>"
            f"<td>{s['hadith_ref_rate']*100:.0f}%</td>"
            f"<td>{fab_badge}</td>"
            f"<td>{s['avg_latency_s']}s</td></tr>\n"
        )

    pc = analysis["pass_criteria"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Noor Evaluation — {analysis['model']}</title>
<style>
  body {{ font-family: monospace; max-width: 960px; margin: 40px auto; padding: 0 20px; background:#0f172a; color:#e2e8f0; }}
  h1 {{ color:#38bdf8; }}
  h2 {{ color:#94a3b8; margin-top:2em; }}
  .badge {{ display:inline-block; padding:6px 20px; border-radius:4px; font-size:1.4em; font-weight:bold; color:white; background:{status_color}; }}
  table {{ border-collapse:collapse; width:100%; }}
  th {{ background:#1e293b; padding:8px 12px; text-align:left; color:#94a3b8; }}
  td {{ padding:8px 12px; border-bottom:1px solid #1e293b; }}
  .metric {{ margin:6px 0; }}
  .ok {{ color:#22c55e; }}
  .fail {{ color:#ef4444; }}
</style>
</head>
<body>
<h1>Noor Islamic AI — Evaluation Report</h1>
<p>Model: <strong>{analysis['model']}</strong> &nbsp;|&nbsp; Run: {analysis['run_at'][:19]} &nbsp;|&nbsp; Generated: {ts}</p>
<div class="badge">{status}</div>
<h2>Overall Metrics</h2>
<div class="metric">Arabic text rate  : <strong>{pc['arabic_rate']*100:.1f}%</strong> (target ≥90%) {'<span class="ok">✓</span>' if pc['arabic_rate']>=0.9 else '<span class="fail">✗</span>'}</div>
<div class="metric">Reference rate    : <strong>{pc['reference_rate']*100:.1f}%</strong> (target ≥80%) {'<span class="ok">✓</span>' if pc['reference_rate']>=0.8 else '<span class="fail">✗</span>'}</div>
<div class="metric">Fabrications      : <strong>{analysis['fabrications']}</strong> (target = 0) {'<span class="ok">✓</span>' if analysis['fabrications']==0 else '<span class="fail">✗</span>'}</div>
<div class="metric">Total questions   : {analysis['total']}</div>
<h2>By Category</h2>
<table>
<tr><th>Category</th><th>Questions</th><th>Arabic</th><th>Quran ref</th><th>Hadith ref</th><th>Fabrications</th><th>Avg latency</th></tr>
{rows}
</table>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="Specific eval_xxx.json filename in reports/")
    parser.add_argument("--all",    action="store_true", help="Process all reports")
    args = parser.parse_args()

    validator = ReferenceValidator()

    if args.all:
        paths = sorted(REPORTS_DIR.glob("eval_*.json"))
        if not paths:
            print("No reports found.")
            sys.exit(1)
    elif args.report:
        p = REPORTS_DIR / args.report
        paths = [p] if p.exists() else [Path(args.report)]
    else:
        paths_list = sorted(REPORTS_DIR.glob("eval_*.json"))
        if not paths_list:
            print("No reports found. Run run_evaluation.py first.")
            sys.exit(1)
        paths = [paths_list[-1]]  # latest

    for rp in paths:
        if not rp.exists():
            print(f"Not found: {rp}")
            continue

        analysis = analyse_report(rp, validator)
        stem = rp.stem

        json_out = REPORTS_DIR / f"{stem}_summary.json"
        html_out = REPORTS_DIR / f"{stem}_report.html"

        json_out.write_text(
            json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        html_out.write_text(render_html(analysis), encoding="utf-8")

        status = "PASS" if analysis["overall_pass"] else "FAIL"
        print(f"{status}  {rp.name}")
        print(f"  Arabic rate    : {analysis['pass_criteria']['arabic_rate']*100:.1f}%")
        print(f"  Reference rate : {analysis['pass_criteria']['reference_rate']*100:.1f}%")
        print(f"  Fabrications   : {analysis['fabrications']}")
        print(f"  JSON summary   → {json_out.name}")
        print(f"  HTML report    → {html_out.name}")
        print()


if __name__ == "__main__":
    main()
