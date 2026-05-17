#!/usr/bin/env python3
"""
Download extended Hadith collections completing the Kutub al-Sittah + supplementary.

Collections downloaded:
  Kutub al-Sittah (6 major collections) — completes the set started in download_hadith.py:
    Sunan al-Nasai        → raw/hadith/nasai.json
  Additional authentic collections:
    Muwatta Imam Malik    → raw/hadith/muwatta_malik.json
    Sunan al-Darimi       → raw/hadith/darimi.json
    40 Hadith al-Nawawi + Ibn Rajab additions (42 total)
                          → raw/hadith/nawawi_40.json
    Hadith Qudsi (45)     → raw/hadith/hadith_qudsi.json
    Riyad as-Salihin      → raw/hadith/riyad_us_salihin_extended.json
    Bulugh al-Maram       → raw/hadith/bulugh_al_maram.json  (if available)

Source: https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/

Usage:
    python download_extended_hadith.py
    python download_extended_hadith.py --collections nasai nawawi40
    python download_extended_hadith.py --output-dir /custom/path
    python download_extended_hadith.py --help
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp
from tqdm import tqdm

# ─── Constants ────────────────────────────────────────────────────────────────

CDN_BASE: str = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
GH_RAW_BASE: str = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"

MAX_RETRIES: int = 3
RETRY_BACKOFF_BASE: float = 2.0
REQUEST_DELAY: float = 0.5
TIMEOUT_SECONDS: int = 180

DEFAULT_HADITH_DIR: Path = Path(__file__).parent.parent / "raw" / "hadith"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"

# (api_name, output_filename, display_name, expected_min_count, required)
EXTENDED_COLLECTIONS: list[tuple[str, str, str, int, bool]] = [
    # Completing the Kutub al-Sittah
    ("nasai",               "nasai.json",               "Sunan al-Nasai",              5000, True),
    # Other major authentic collections
    ("malik-muwatta",       "muwatta_malik.json",        "Muwatta Imam Malik",          1500, True),
    ("darimi",              "darimi.json",               "Sunan al-Darimi",             2500, True),
    ("nawawi42",            "nawawi_40.json",            "40 Hadith Nawawi (42 total)", 40,   True),
    ("qudsi",               "hadith_qudsi.json",         "Hadith Qudsi",                40,   True),
    ("riyadussalihin",      "riyad_us_salihin.json",     "Riyad as-Salihin",            1800, True),
    ("bulugh-al-maram",     "bulugh_al_maram.json",      "Bulugh al-Maram",             1200, False),
]

DEFAULT_GRADE: str = "See source"


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"download_extended_hadith_{timestamp}.log"
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("download_extended_hadith")
    logger.info("Log file: %s", log_file)
    return logger


# ─── HTTP helper ──────────────────────────────────────────────────────────────

async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    logger: logging.Logger,
    fallback_url: str | None = None,
) -> dict[str, Any]:
    urls_to_try = [url] + ([fallback_url] if fallback_url else [])
    for try_url in urls_to_try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    try_url,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status in (403, 404):
                        logger.warning("HTTP %d for %s — trying next URL", resp.status, try_url)
                        break
                    resp.raise_for_status()
                    await asyncio.sleep(REQUEST_DELAY)
                    return await resp.json(content_type=None)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt == MAX_RETRIES:
                    logger.warning("All %d retries failed for %s: %s", MAX_RETRIES, try_url, exc)
                    break
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning("Attempt %d/%d failed: %s — retrying in %.1fs",
                               attempt, MAX_RETRIES, exc, wait)
                await asyncio.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} (tried all URLs/retries)")


# ─── Collection downloader ────────────────────────────────────────────────────

async def download_collection(
    session: aiohttp.ClientSession,
    api_name: str,
    output_filename: str,
    display_name: str,
    expected_min: int,
    output_dir: Path,
    logger: logging.Logger,
) -> int:
    eng_url = f"{CDN_BASE}/eng-{api_name}.json"
    ara_url = f"{CDN_BASE}/ara-{api_name}.json"
    eng_fallback = f"{GH_RAW_BASE}/eng-{api_name}.json"
    ara_fallback = f"{GH_RAW_BASE}/ara-{api_name}.json"

    logger.info("Downloading %s...", display_name)

    # Fetch English + Arabic (Arabic may not exist for all collections — handle gracefully)
    eng_task = fetch_json(session, eng_url, logger, fallback_url=eng_fallback)
    ara_task = fetch_json(session, ara_url, logger, fallback_url=ara_fallback)

    try:
        eng_data, ara_data = await asyncio.gather(eng_task, ara_task)
    except RuntimeError:
        try:
            eng_data = await fetch_json(session, eng_url, logger, fallback_url=eng_fallback)
            ara_data = {"hadiths": []}
            logger.warning("%s: Arabic not available — English only", display_name)
        except RuntimeError as exc:
            raise RuntimeError(f"Cannot download {display_name}: {exc}") from exc

    # Build Arabic lookup
    ara_lookup: dict[int, str] = {}
    for h in ara_data.get("hadiths", []):
        num = h.get("hadithnumber")
        if num is not None:
            ara_lookup[int(num)] = h.get("text", "")

    # Merge English + Arabic
    hadiths: list[dict[str, Any]] = []
    for h in eng_data.get("hadiths", []):
        num = h.get("hadithnumber")
        if num is None:
            continue
        num = int(num)

        # Extract grade — handle different API grade formats
        grade_raw = DEFAULT_GRADE
        if h.get("grades"):
            grade_raw = h["grades"][0].get("grade", DEFAULT_GRADE)
        elif h.get("grade"):
            grade_raw = h["grade"]

        # Normalise grade strings to standard terms
        grade = _normalise_grade(grade_raw)

        hadiths.append({
            "hadith_number": num,
            "arabic_text": ara_lookup.get(num, ""),
            "english_text": h.get("text", ""),
            "grade": grade,
            "grade_raw": grade_raw,
        })

    hadiths.sort(key=lambda x: x["hadith_number"])

    meta_raw = eng_data.get("metadata", {})
    output: dict[str, Any] = {
        "metadata": {
            "name": display_name,
            "collection": api_name,
            "source": "cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "total_hadiths": len(hadiths),
            "original_metadata": meta_raw,
        },
        "hadiths": hadiths,
    }

    out_file = output_dir / output_filename
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    size_mb = out_file.stat().st_size / (1024 * 1024)
    logger.info("%s: %d hadiths → %s (%.1f MB)", display_name, len(hadiths), out_file.name, size_mb)

    if len(hadiths) < expected_min:
        logger.warning("%s: got %d hadiths, expected >= %d — check source",
                       display_name, len(hadiths), expected_min)
    return len(hadiths)


def _normalise_grade(raw: str) -> str:
    """Map raw grade strings to canonical Islamic hadith grades."""
    if not raw or raw == "See source":
        return "See source"
    r = raw.strip().lower()
    if any(x in r for x in ["sahih", "صحيح"]):
        return "Sahih"
    if any(x in r for x in ["hasan", "حسن"]):
        return "Hasan"
    if any(x in r for x in ["da'if", "daif", "weak", "ضعيف"]):
        return "Da'if"
    if any(x in r for x in ["mawdu", "fabricated", "false", "موضوع"]):
        return "Mawdu' (Fabricated)"
    if any(x in r for x in ["mursal", "مرسل"]):
        return "Mursal"
    if any(x in r for x in ["munkar", "منكر"]):
        return "Munkar"
    return raw.strip()


# ─── Main orchestrator ────────────────────────────────────────────────────────

async def download_all(
    hadith_dir: Path,
    selected_collections: list[str],
    logger: logging.Logger,
) -> None:
    hadith_dir.mkdir(parents=True, exist_ok=True)

    to_download = [
        c for c in EXTENDED_COLLECTIONS
        if not selected_collections or c[0] in selected_collections
    ]

    if not to_download:
        logger.error("No collections matched. Valid names: %s",
                     [c[0] for c in EXTENDED_COLLECTIONS])
        sys.exit(1)

    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        total = 0
        failed: list[str] = []

        for api_name, filename, display_name, expected_min, required in tqdm(to_download, desc="Collections"):
            try:
                count = await download_collection(
                    session, api_name, filename, display_name,
                    expected_min, hadith_dir, logger,
                )
                total += count
            except RuntimeError as exc:
                if required:
                    logger.error("FAILED %s: %s", display_name, exc)
                else:
                    logger.warning("SKIPPED %s (optional): %s", display_name, exc)
                failed.append(display_name)

    logger.info("=" * 50)
    logger.info("Total hadiths downloaded: %d", total)
    if failed:
        logger.warning("Failed/skipped (%d): %s", len(failed), ", ".join(failed))
    else:
        logger.info("All collections downloaded successfully")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download extended Hadith collections (Nasai, Muwatta, Darimi, 40 Nawawi, Qudsi).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Collections:
  nasai           Sunan al-Nasai      (completes Kutub al-Sittah)
  malik-muwatta   Muwatta Imam Malik
  darimi          Sunan al-Darimi
  nawawi42        40 Hadith Nawawi + Ibn Rajab (42 total)
  qudsi           Hadith Qudsi (45 divine hadiths)
  riyadussalihin  Riyad as-Salihin
  bulugh-al-maram Bulugh al-Maram     (optional)

Examples:
  python download_extended_hadith.py
  python download_extended_hadith.py --collections nasai nawawi42 qudsi
  python download_extended_hadith.py --hadith-dir /data/hadith
        """,
    )
    parser.add_argument("--hadith-dir", type=Path, default=DEFAULT_HADITH_DIR)
    parser.add_argument("--collections", nargs="+", default=[], metavar="NAME")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger = setup_logging(LOG_DIR, args.log_level)
    logger.info("=" * 60)
    logger.info("Extended Hadith Download — starting")
    logger.info("Hadith dir : %s", args.hadith_dir)
    logger.info("Collections: %s", args.collections or "all")
    logger.info("=" * 60)

    start = time.monotonic()
    try:
        asyncio.run(download_all(args.hadith_dir, args.collections, logger))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Download failed: %s", exc)
        sys.exit(1)
    logger.info("Completed in %.1f seconds", time.monotonic() - start)


if __name__ == "__main__":
    main()
