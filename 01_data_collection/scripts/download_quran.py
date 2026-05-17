#!/usr/bin/env python3
"""
Download complete Quran data.

Sources:
  - Arabic (Uthmani) + English (Sahih International): api.alquran.cloud/v1
    Two bulk requests return all 6236 verses — fast and reliable.
  - Chapter metadata: api.quran.com/api/v4
  - Tafsir Ibn Kathir (English): api.quran.com/api/v4 (per chapter)

Output: 01_data_collection/raw/quran/quran_full.json

Usage:
    python download_quran.py
    python download_quran.py --output-dir /custom/path
    python download_quran.py --skip-tafsir
    python download_quran.py --help
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp
from tqdm import tqdm

# ─── Constants ────────────────────────────────────────────────────────────────

ALQURAN_CLOUD_BASE: str = "https://api.alquran.cloud/v1"
QURANCOM_BASE: str = "https://api.quran.com/api/v4"

ARABIC_EDITION: str = "quran-uthmani"          # Uthmani script Arabic
ENGLISH_EDITION: str = "en.sahih"              # Sahih International
TAFSIR_ID: int = 169                           # Ibn Kathir English
TAFSIR_PER_PAGE: int = 50

TOTAL_SURAHS: int = 114
EXPECTED_TOTAL_AYAHS: int = 6236

MAX_RETRIES: int = 3
RETRY_BACKOFF_BASE: float = 2.0
REQUEST_DELAY: float = 0.3
CONCURRENT_REQUESTS: int = 5

DEFAULT_OUTPUT_DIR: Path = Path(__file__).parent.parent / "raw" / "quran"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"

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

assert len(SURAH_AYAH_COUNTS) == TOTAL_SURAHS
assert sum(SURAH_AYAH_COUNTS) == EXPECTED_TOTAL_AYAHS


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    """Configure file + console logging.

    Args:
        log_dir: Directory for the log file.
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"download_quran_{timestamp}.log"

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
    logger = logging.getLogger("download_quran")
    logger.info("Log file: %s", log_file)
    return logger


# ─── HTTP helper ──────────────────────────────────────────────────────────────

async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any] | None = None,
    semaphore: asyncio.Semaphore | None = None,
    timeout: int = 60,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """Fetch a URL and return parsed JSON with retry + exponential backoff.

    Args:
        session: Active aiohttp client session.
        url: Full URL to request.
        params: Optional query parameters.
        semaphore: Optional concurrency limiter.
        timeout: Request timeout in seconds.
        logger: Logger instance.

    Returns:
        Parsed JSON response dict.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    _log = logger or logging.getLogger("download_quran")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ctx = semaphore if semaphore else asyncio.nullcontext()
            async with ctx:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF_BASE ** attempt
                        _log.warning("Rate limited — waiting %.1fs", wait)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    await asyncio.sleep(REQUEST_DELAY)
                    return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} attempts") from exc
            wait = RETRY_BACKOFF_BASE ** attempt
            _log.warning("Attempt %d/%d failed for %s: %s — retrying in %.1fs",
                         attempt, MAX_RETRIES, url, exc, wait)
            await asyncio.sleep(wait)

    raise RuntimeError(f"Unreachable: {url}")


def strip_html(text: str) -> str:
    """Remove all HTML tags from a string.

    Args:
        text: Input string possibly containing HTML.

    Returns:
        Clean text with HTML tags removed.
    """
    return re.sub(r"<[^>]+>", "", text).strip()


# ─── Verse data (alquran.cloud) ───────────────────────────────────────────────

async def fetch_bulk_edition(
    session: aiohttp.ClientSession,
    edition: str,
    semaphore: asyncio.Semaphore,
    label: str,
    logger: logging.Logger,
) -> dict[int, dict[int, str]]:
    """Fetch ALL verses for one edition from alquran.cloud in a single request.

    Args:
        session: Active aiohttp client session.
        edition: Edition identifier (e.g. 'quran-uthmani', 'en.sahih').
        semaphore: Concurrency limiter.
        label: Human label for logging.
        logger: Logger instance.

    Returns:
        Nested dict: surah_number → ayah_number_in_surah → text.
    """
    url = f"{ALQURAN_CLOUD_BASE}/quran/{edition}"
    logger.info("Fetching %s from alquran.cloud (%s)...", label, edition)

    data = await fetch_json(session, url, semaphore=semaphore, timeout=120, logger=logger)

    verse_map: dict[int, dict[int, str]] = {}
    for surah in data["data"]["surahs"]:
        s_num = int(surah["number"])
        verse_map[s_num] = {}
        for ayah in surah["ayahs"]:
            a_num = int(ayah["numberInSurah"])
            verse_map[s_num][a_num] = strip_html(ayah.get("text", ""))

    total = sum(len(v) for v in verse_map.values())
    logger.info("%s: %d verses loaded across %d surahs", label, total, len(verse_map))
    return verse_map


# ─── Chapter metadata (quran.com) ─────────────────────────────────────────────

async def fetch_chapters_meta(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
) -> dict[int, dict[str, Any]]:
    """Fetch chapter metadata (names, revelation type) from quran.com.

    Args:
        session: Active aiohttp client session.
        semaphore: Concurrency limiter.
        logger: Logger instance.

    Returns:
        Dict mapping surah_number → chapter metadata.
    """
    url = f"{QURANCOM_BASE}/chapters"
    logger.info("Fetching chapter metadata from quran.com...")
    try:
        data = await fetch_json(session, url, params={"language": "en"},
                                semaphore=semaphore, logger=logger)
        meta = {int(ch["id"]): ch for ch in data["chapters"]}
        logger.info("Chapter metadata: %d chapters", len(meta))
        return meta
    except RuntimeError:
        logger.warning("Chapter metadata unavailable — using fallback names")
        return {}


# ─── Tafsir (quran.com) ───────────────────────────────────────────────────────

async def fetch_tafsir_for_chapter(
    session: aiohttp.ClientSession,
    chapter_number: int,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
) -> dict[str, str]:
    """Fetch Ibn Kathir tafsir for all ayahs in one chapter.

    Args:
        session: Active aiohttp client session.
        chapter_number: Surah number 1–114.
        semaphore: Concurrency limiter.
        logger: Logger instance.

    Returns:
        Dict mapping verse_key (e.g. '2:5') → tafsir text.
    """
    tafsir_map: dict[str, str] = {}
    page = 1

    while True:
        url = f"{QURANCOM_BASE}/tafsirs/{TAFSIR_ID}/by_chapter/{chapter_number}"
        params: dict[str, Any] = {"per_page": TAFSIR_PER_PAGE, "page": page}
        try:
            data = await fetch_json(session, url, params=params,
                                    semaphore=semaphore, logger=logger)
        except RuntimeError:
            break

        for item in data.get("tafsirs", []):
            vk = item.get("verse_key", "")
            text = strip_html(item.get("text", ""))
            if vk and text:
                tafsir_map[vk] = text

        pagination = data.get("pagination", {})
        if pagination.get("next_page") is None:
            break
        page += 1

    return tafsir_map


# ─── Assembly ─────────────────────────────────────────────────────────────────

async def download_all(
    output_dir: Path,
    skip_tafsir: bool,
    logger: logging.Logger,
) -> None:
    """Download Quran Arabic + English + Tafsir and save to disk.

    Args:
        output_dir: Directory to save quran_full.json.
        skip_tafsir: If True, skip the tafsir download step.
        logger: Logger instance.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(connector=connector) as session:

        # Step 1: fetch Arabic + English + chapter meta in parallel
        arabic_task = fetch_bulk_edition(session, ARABIC_EDITION, semaphore, "Arabic Uthmani", logger)
        english_task = fetch_bulk_edition(session, ENGLISH_EDITION, semaphore, "English Sahih Int.", logger)
        chapters_task = fetch_chapters_meta(session, semaphore, logger)

        arabic_map, english_map, chapters_meta = await asyncio.gather(
            arabic_task, english_task, chapters_task
        )

        # Step 2: tafsir per chapter (optional)
        tafsir_maps: dict[int, dict[str, str]] = {}
        if not skip_tafsir:
            logger.info("Fetching tafsir for 114 chapters (quran.com)...")
            for surah_num in tqdm(range(1, TOTAL_SURAHS + 1), desc="Tafsir", unit="surah"):
                tafsir_maps[surah_num] = await fetch_tafsir_for_chapter(
                    session, surah_num, semaphore, logger
                )

        # Step 3: assemble final document
        all_surahs: list[dict[str, Any]] = []
        total_ayahs = 0

        for surah_num in range(1, TOTAL_SURAHS + 1):
            meta = chapters_meta.get(surah_num, {})
            ayah_count = SURAH_AYAH_COUNTS[surah_num - 1]
            tafsir_map = tafsir_maps.get(surah_num, {})

            ayahs: list[dict[str, Any]] = []
            for ayah_num in range(1, ayah_count + 1):
                verse_key = f"{surah_num}:{ayah_num}"
                ayahs.append({
                    "ayah_number": ayah_num,
                    "verse_key": verse_key,
                    "arabic_text": arabic_map.get(surah_num, {}).get(ayah_num, ""),
                    "english_translation": english_map.get(surah_num, {}).get(ayah_num, ""),
                    "tafsir_ibn_kathir": tafsir_map.get(verse_key, ""),
                })

            total_ayahs += len(ayahs)
            all_surahs.append({
                "surah_number": surah_num,
                "name_arabic": meta.get("name_arabic", ""),
                "name_english": meta.get("name_simple", ""),
                "name_transliteration": meta.get("name_complex", ""),
                "revelation_type": meta.get("revelation_place", ""),
                "ayah_count": len(ayahs),
                "ayahs": ayahs,
            })

        # Step 4: save
        output: dict[str, Any] = {
            "metadata": {
                "arabic_source": f"alquran.cloud — {ARABIC_EDITION}",
                "translation": "Sahih International",
                "translation_source": f"alquran.cloud — {ENGLISH_EDITION}",
                "tafsir": "Ibn Kathir (English)" if not skip_tafsir else "skipped",
                "tafsir_source": f"quran.com API v4 — tafsir ID {TAFSIR_ID}",
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "total_surahs": len(all_surahs),
                "total_ayahs": total_ayahs,
            },
            "surahs": all_surahs,
        }

        out_file = output_dir / "quran_full.json"
        out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

        size_mb = out_file.stat().st_size / (1024 * 1024)
        logger.info("Saved: %s (%.1f MB)", out_file, size_mb)
        logger.info("Total surahs: %d | Total ayahs: %d", len(all_surahs), total_ayahs)

        if total_ayahs != EXPECTED_TOTAL_AYAHS:
            logger.warning("Ayah count mismatch — expected %d, got %d",
                           EXPECTED_TOTAL_AYAHS, total_ayahs)
        else:
            logger.info("Ayah count verified: %d / %d", total_ayahs, EXPECTED_TOTAL_AYAHS)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download full Quran data (Arabic + English + Tafsir).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_quran.py
  python download_quran.py --skip-tafsir
  python download_quran.py --output-dir /data/quran
  python download_quran.py --log-level DEBUG
        """,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-tafsir", action="store_true",
                        help="Skip tafsir — faster but no commentary")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    logger = setup_logging(LOG_DIR, args.log_level)
    logger.info("=" * 60)
    logger.info("Quran Download — starting (alquran.cloud + quran.com tafsir)")
    logger.info("Output dir : %s", args.output_dir)
    logger.info("Skip tafsir: %s", args.skip_tafsir)
    logger.info("=" * 60)

    start = time.monotonic()
    try:
        asyncio.run(download_all(args.output_dir, args.skip_tafsir, logger))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Download failed: %s", exc)
        sys.exit(1)

    logger.info("Completed in %.1f seconds", time.monotonic() - start)


if __name__ == "__main__":
    main()
