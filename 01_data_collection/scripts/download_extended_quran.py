#!/usr/bin/env python3
"""
Download extended Quran data: multiple tafsirs + word-by-word morphology.

Downloads from api.quran.com/api/v4:
  - Tafsir al-Tabari (Arabic)   → raw/quran/tafsir_tabari.json
  - Tafsir al-Saadi  (Arabic)   → raw/quran/tafsir_saadi.json
  - Tafsir al-Jalalayn (Arabic) → raw/quran/tafsir_jalalayn.json
  - Tafsir Ma'ariful Quran (English, Mufti Shafi) → raw/quran/tafsir_maariful.json
  - Word-by-word morphology     → raw/quran/word_by_word.json
  - Asbab al-Nuzul (reasons of revelation) — embedded in existing tafsirs where available

These files are used by Phase 2 to generate richer Q&A pairs with:
  - Multiple scholar opinions on the same verse
  - Morphological analysis for Arabic language learning pairs
  - Historical context (Asbab al-Nuzul) for "why was this revealed?" questions

Tafsir IDs (quran.com API v4):
  169  — Ibn Kathir English     (already in quran_full.json)
  33   — Tafsir al-Tabari       (classical, ~10th century)
  91   — Tafsir al-Saadi        (modern, accessible)
  74   — Tafsir al-Jalalayn     (concise, classical)
  169  — Ma'ariful Quran        (Mufti Shafi Usmani, English)

To list ALL available tafsirs: GET /tafsirs?language=en

Usage:
    python download_extended_quran.py
    python download_extended_quran.py --skip-word-by-word
    python download_extended_quran.py --tafsirs 33 91
    python download_extended_quran.py --help
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

QURANCOM_BASE: str = "https://api.quran.com/api/v4"
ALQURAN_CLOUD_BASE: str = "https://api.alquran.cloud/v1"

TOTAL_SURAHS: int = 114
EXPECTED_TOTAL_AYAHS: int = 6236

TAFSIR_PER_PAGE: int = 50
MAX_RETRIES: int = 3
RETRY_BACKOFF_BASE: float = 2.0
REQUEST_DELAY: float = 0.4
CONCURRENT_REQUESTS: int = 3        # Conservative to avoid rate limits

DEFAULT_OUTPUT_DIR: Path = Path(__file__).parent.parent / "raw" / "quran"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"

# Tafsirs to download: (id, output_file, display_name, language)
TAFSIRS: list[tuple[int, str, str, str]] = [
    (33,  "tafsir_tabari.json",   "Tafsir al-Tabari (Ibn Jarir)",     "ar"),
    (91,  "tafsir_saadi.json",    "Tafsir al-Saadi (Taysir al-Karim)", "ar"),
    (74,  "tafsir_jalalayn.json", "Tafsir al-Jalalayn",               "ar"),
    (817, "tafsir_maariful.json", "Ma'ariful Quran (Mufti Shafi)",    "en"),
]

SURAH_AYAH_COUNTS: list[int] = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6,
]


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"download_extended_quran_{timestamp}.log"
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=fmt, datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("download_extended_quran")
    logger.info("Log file: %s", log_file)
    return logger


# ─── HTTP helper ──────────────────────────────────────────────────────────────

async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any] | None = None,
    semaphore: asyncio.Semaphore | None = None,
    timeout: int = 90,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    _log = logger or logging.getLogger("download_extended_quran")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ctx = semaphore if semaphore else asyncio.nullcontext()
            async with ctx:
                async with session.get(
                    url, params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status == 429:
                        wait = RETRY_BACKOFF_BASE ** attempt * 3
                        _log.warning("Rate limited — waiting %.1fs", wait)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    await asyncio.sleep(REQUEST_DELAY)
                    return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Failed to fetch {url}") from exc
            wait = RETRY_BACKOFF_BASE ** attempt
            _log.warning("Attempt %d/%d failed: %s — retrying in %.1fs",
                         attempt, MAX_RETRIES, exc, wait)
            await asyncio.sleep(wait)
    raise RuntimeError(f"Unreachable: {url}")


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


# ─── Tafsir downloader ────────────────────────────────────────────────────────

async def fetch_tafsir_chapter(
    session: aiohttp.ClientSession,
    tafsir_id: int,
    chapter_num: int,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
) -> dict[str, str]:
    """Fetch one tafsir for all ayahs in one chapter. Returns verse_key → text."""
    tafsir_map: dict[str, str] = {}
    page = 1
    while True:
        url = f"{QURANCOM_BASE}/tafsirs/{tafsir_id}/by_chapter/{chapter_num}"
        try:
            data = await fetch_json(
                session, url,
                params={"per_page": TAFSIR_PER_PAGE, "page": page},
                semaphore=semaphore, logger=logger,
            )
        except RuntimeError:
            break
        for item in data.get("tafsirs", []):
            vk = item.get("verse_key", "")
            text = strip_html(item.get("text", ""))
            if vk and text:
                tafsir_map[vk] = text
        if not data.get("pagination", {}).get("next_page"):
            break
        page += 1
    return tafsir_map


async def download_tafsir(
    session: aiohttp.ClientSession,
    tafsir_id: int,
    output_file: Path,
    display_name: str,
    language: str,
    semaphore: asyncio.Semaphore,
    output_dir: Path,
    logger: logging.Logger,
) -> int:
    logger.info("Downloading %s (ID %d)...", display_name, tafsir_id)
    tafsir_by_surah: dict[int, dict[str, str]] = {}

    for surah_num in tqdm(range(1, TOTAL_SURAHS + 1),
                          desc=f"  {display_name[:30]}", unit="surah", leave=False):
        tafsir_by_surah[surah_num] = await fetch_tafsir_chapter(
            session, tafsir_id, surah_num, semaphore, logger
        )

    # Flatten to verse_key → text dict
    flat: dict[str, str] = {}
    for chap in tafsir_by_surah.values():
        flat.update(chap)

    output: dict[str, Any] = {
        "metadata": {
            "name": display_name,
            "tafsir_id": tafsir_id,
            "language": language,
            "source": "api.quran.com/api/v4",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(flat),
        },
        "verses": flat,
    }

    out_path = output_dir / output_file
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    logger.info("%s: %d verse entries → %s (%.1f MB)",
                display_name, len(flat), out_path.name, size_mb)
    return len(flat)


# ─── Word-by-word downloader ──────────────────────────────────────────────────

async def download_word_by_word(
    session: aiohttp.ClientSession,
    output_dir: Path,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
) -> None:
    """Download word-by-word morphology for entire Quran from quran.com."""
    logger.info("Downloading word-by-word morphology (all 6236 verses)...")

    all_verses: dict[str, list[dict[str, Any]]] = {}

    for surah_num in tqdm(range(1, TOTAL_SURAHS + 1),
                          desc="  Word-by-word", unit="surah", leave=False):
        ayah_count = SURAH_AYAH_COUNTS[surah_num - 1]
        surah_words: dict[str, list[dict[str, Any]]] = {}

        for ayah_num in range(1, ayah_count + 1):
            verse_key = f"{surah_num}:{ayah_num}"
            url = f"{QURANCOM_BASE}/verses/by_key/{verse_key}"
            try:
                data = await fetch_json(
                    session, url,
                    params={"words": "true", "word_fields": "text_uthmani,transliteration,translation"},
                    semaphore=semaphore, logger=logger,
                )
                words_raw = data.get("verse", {}).get("words", [])
                words = [
                    {
                        "position": w.get("position"),
                        "arabic": w.get("text_uthmani", ""),
                        "transliteration": w.get("transliteration", {}).get("text", ""),
                        "translation": w.get("translation", {}).get("text", ""),
                        "char_type": w.get("char_type_name", ""),
                    }
                    for w in words_raw
                    if w.get("char_type_name") != "end"   # exclude verse-number symbols
                ]
                surah_words[verse_key] = words
            except RuntimeError:
                logger.warning("Word-by-word failed for %s — skipping", verse_key)
                surah_words[verse_key] = []

        all_verses.update(surah_words)

    output: dict[str, Any] = {
        "metadata": {
            "description": "Word-by-word Quran morphology — Arabic text, transliteration, translation per word",
            "source": "api.quran.com/api/v4",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "total_verses": len(all_verses),
        },
        "verses": all_verses,
    }

    out_path = output_dir / "word_by_word.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    size_mb = out_path.stat().st_size / (1024 * 1024)
    logger.info("Word-by-word: %d verses → %s (%.1f MB)", len(all_verses), out_path.name, size_mb)


# ─── List available tafsirs ───────────────────────────────────────────────────

async def list_available_tafsirs(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    logger: logging.Logger,
) -> None:
    """Print all tafsirs available from quran.com API."""
    url = f"{QURANCOM_BASE}/tafsirs"
    try:
        data = await fetch_json(session, url, params={"language": "en"},
                                semaphore=semaphore, logger=logger)
        tafsirs = data.get("tafsirs", [])
        print("\nAvailable tafsirs on quran.com API v4:")
        print(f"{'ID':<6} {'Language':<10} Name")
        print("-" * 60)
        for t in sorted(tafsirs, key=lambda x: x.get("id", 0)):
            print(f"{t.get('id', '?'):<6} {t.get('language_name', '?'):<10} {t.get('translated_name', {}).get('name', '?')}")
    except RuntimeError as exc:
        logger.error("Could not list tafsirs: %s", exc)


# ─── Main orchestrator ────────────────────────────────────────────────────────

async def download_all(
    output_dir: Path,
    tafsir_ids: list[int],
    skip_word_by_word: bool,
    list_tafsirs: bool,
    logger: logging.Logger,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(connector=connector) as session:

        if list_tafsirs:
            await list_available_tafsirs(session, semaphore, logger)
            return

        # Determine which tafsirs to download
        if tafsir_ids:
            to_download = [(tid, f"tafsir_{tid}.json", f"Tafsir ID {tid}", "?")
                           for tid in tafsir_ids]
        else:
            to_download = [(t[0], t[1], t[2], t[3]) for t in TAFSIRS]

        for tafsir_id, filename, display_name, language in to_download:
            try:
                await download_tafsir(
                    session, tafsir_id, Path(filename), display_name,
                    language, semaphore, output_dir, logger,
                )
            except Exception as exc:
                logger.error("FAILED %s: %s", display_name, exc)

        if not skip_word_by_word:
            await download_word_by_word(session, output_dir, semaphore, logger)
        else:
            logger.info("Skipping word-by-word (--skip-word-by-word)")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download extended Quran data: multiple tafsirs + word-by-word morphology.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Default tafsirs downloaded:
  33  — Tafsir al-Tabari
  91  — Tafsir al-Saadi
  74  — Tafsir al-Jalalayn
  817 — Ma'ariful Quran (Mufti Shafi, English)

Examples:
  python download_extended_quran.py
  python download_extended_quran.py --list-tafsirs
  python download_extended_quran.py --tafsirs 33 91
  python download_extended_quran.py --skip-word-by-word
        """,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--tafsirs", nargs="+", type=int, default=[],
                        help="Tafsir IDs to download (default: all configured)")
    parser.add_argument("--skip-word-by-word", action="store_true",
                        help="Skip word-by-word morphology download")
    parser.add_argument("--list-tafsirs", action="store_true",
                        help="Print all available tafsirs from quran.com and exit")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger = setup_logging(LOG_DIR, args.log_level)
    logger.info("=" * 60)
    logger.info("Extended Quran Download — starting")
    logger.info("Output dir        : %s", args.output_dir)
    logger.info("Tafsirs           : %s", args.tafsirs or "all configured")
    logger.info("Skip word-by-word : %s", args.skip_word_by_word)
    logger.info("=" * 60)

    start = time.monotonic()
    try:
        asyncio.run(download_all(
            args.output_dir,
            args.tafsirs,
            args.skip_word_by_word,
            args.list_tafsirs,
            logger,
        ))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Download failed: %s", exc)
        sys.exit(1)
    logger.info("Completed in %.1f seconds", time.monotonic() - start)


if __name__ == "__main__":
    main()
