#!/usr/bin/env python3
"""
Download IslamQA.info fatwa dataset from HuggingFace.

Source: kingkaung/islamqainfo_parallel_corpus
        ~19,000 authentic Q&A pairs from islamqa.info (Sheikh al-Munajjid)
        English + Arabic + 13 other languages

Output: 01_data_collection/raw/fatwa/islamqa_fatwas.json

Usage:
    python download_fatwa.py
    python download_fatwa.py --output-dir /custom/path
    python download_fatwa.py --lang en          # English only (default)
    python download_fatwa.py --lang en ar       # English + Arabic
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

# ─── Constants ────────────────────────────────────────────────────────────────

DATASET_ID = "kingkaung/islamqainfo_parallel_corpus"
HF_VIEWER   = "https://datasets-server.huggingface.co/rows"
PAGE_SIZE   = 100
DEFAULT_OUTPUT = Path(__file__).parent.parent / "raw" / "fatwa"

SUPPORTED_LANGS = ["en", "ar", "bn", "fr", "es", "zh", "ru", "de", "hi", "tr", "id"]


# ─── Fetch helpers ────────────────────────────────────────────────────────────

def fetch_page(offset: int, length: int = PAGE_SIZE, retries: int = 6) -> list[dict]:
    params = {
        "dataset": DATASET_ID,
        "config": "default",
        "split": "train",
        "offset": offset,
        "length": length,
    }
    for attempt in range(retries):
        try:
            r = requests.get(HF_VIEWER, params=params, timeout=30)
            if r.status_code == 429:
                wait = 30 * (attempt + 1)   # 30s, 60s, 90s …
                logging.warning("Rate limited (429) at offset=%d — waiting %ds", offset, wait)
                time.sleep(wait)
                continue
            if r.status_code in (500, 502, 503, 504):
                wait = 10 * (2 ** attempt)  # 10s, 20s, 40s …
                logging.warning("Server error %d at offset=%d — retrying in %ds", r.status_code, offset, wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            return [row["row"] for row in data.get("rows", [])]
        except requests.exceptions.HTTPError:
            raise
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = 5 * (2 ** attempt)   # 5s, 10s, 20s …
            logging.warning("Page offset=%d failed (%s) — retrying in %ds", offset, exc, wait)
            time.sleep(wait)
    return []


def get_total_rows() -> int:
    data = requests.get(
        HF_VIEWER,
        params={"dataset": DATASET_ID, "config": "default", "split": "train", "offset": 0, "length": 1},
        timeout=15,
    ).json()
    return data.get("num_rows_total", 0)


# ─── Normalise a single row ───────────────────────────────────────────────────

def normalise_row(row: dict, langs: list[str]) -> dict:
    """Extract only the needed fields from a raw HuggingFace row."""
    result: dict = {
        "id":          row.get("Global ID", ""),
        "original_id": row.get("original_id", ""),
        "topic":       row.get("topic", ""),
        "entries":     {},
    }
    for lang in langs:
        q = (row.get(f"question_{lang}") or "").strip()
        a = (row.get(f"answer_{lang}") or "").strip()
        t = (row.get(f"title_{lang}") or "").strip()
        link = (row.get(f"link_{lang}") or "").strip()
        if q and a:
            result["entries"][lang] = {
                "title":    t,
                "question": q,
                "answer":   a,
                "link":     link,
            }
    return result


# ─── Main ─────────────────────────────────────────────────────────────────────

def download(langs: list[str], output_dir: Path, logger: logging.Logger) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path    = output_dir / "islamqa_fatwas.json"
    resume_path = output_dir / "islamqa_fatwas_partial.json"

    total = get_total_rows()
    logger.info("Total rows in dataset: %d", total)

    # Resume from partial file if it exists
    fatwas: list[dict] = []
    start_offset = 0
    if resume_path.exists():
        try:
            partial = json.loads(resume_path.read_text(encoding="utf-8"))
            fatwas = partial.get("fatwas", [])
            start_offset = partial.get("_next_offset", 0)
            logger.info("Resuming from offset %d (%d fatwas already saved)", start_offset, len(fatwas))
        except Exception:
            logger.warning("Could not read partial file — starting fresh")

    offsets = range(start_offset, total, PAGE_SIZE)

    for offset in tqdm(offsets, desc="Downloading pages", initial=start_offset // PAGE_SIZE, total=total // PAGE_SIZE):
        rows = fetch_page(offset)
        for row in rows:
            norm = normalise_row(row, langs)
            if norm["entries"]:
                fatwas.append(norm)

        # Save partial progress every 20 pages
        if ((offset // PAGE_SIZE) % 20) == 0:
            resume_path.write_text(
                json.dumps({"_next_offset": offset + PAGE_SIZE, "fatwas": fatwas}, ensure_ascii=False),
                encoding="utf-8",
            )

        time.sleep(1.5)   # polite pacing — avoids 429

    logger.info("Downloaded %d fatwa records (with ≥1 lang entry)", len(fatwas))

    out = {
        "metadata": {
            "source":        "kingkaung/islamqainfo_parallel_corpus on HuggingFace",
            "origin":        "islamqa.info — Sheikh Muhammad Salih al-Munajjid",
            "total":         len(fatwas),
            "languages":     langs,
            "downloaded_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        },
        "fatwas": fatwas,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    if resume_path.exists():
        resume_path.unlink()
    logger.info("Saved → %s", out_path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download IslamQA fatwa dataset from HuggingFace.")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--lang", nargs="+", default=["en"], choices=SUPPORTED_LANGS,
                   help="Languages to keep (default: en)")
    p.add_argument("--log-level", default="INFO")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("download_fatwa")
    download(args.lang, args.output_dir, logger)
