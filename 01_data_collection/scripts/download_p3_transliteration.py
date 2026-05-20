#!/usr/bin/env python3
"""
download_p3_transliteration.py — Priority 3: Quran transliteration.

Fetches word-level transliteration for all 6,236 ayat from quran.com API v4.
Saves standalone file AND merges transliteration into existing quran_full.json.

Output:
  raw/quran/quran_transliteration.json   — standalone transliteration map
  raw/quran/quran_full.json              — updated with 'transliteration' field per ayah

Run:
  python download_p3_transliteration.py
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[1]
QURAN_DIR  = ROOT / 'raw' / 'quran'
LOG_DIR    = ROOT / 'logs'

for d in [QURAN_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────
log_file = LOG_DIR / f'p3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────────
MAX_RETRIES     = 4
RETRY_BACKOFF   = 2.0
REQUEST_DELAY   = 0.4   # seconds between quran.com API calls
CONNECTOR_LIMIT = 4

BASE_URL = 'https://api.quran.com/api/v4'

# quran.com surah lengths (number of ayat per surah) for progress tracking
SURAH_LENGTHS = [
    7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,
    135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,
    54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,
    18,12,12,30,52,52,44,28,28,20,56,40,31,50,22,33,30,26,24,22,24,33,
    30,30,18,26,28,28,31,28,26,28,30,28,28,28,38,27,89,107,6
]

# Number of chapters (114 surahs in the Quran)
TOTAL_CHAPTERS = 114


# ─────────────────────────────────────────────────────────────────
# HTTP
# ─────────────────────────────────────────────────────────────────
async def fetch_json(session: aiohttp.ClientSession, url: str,
                     delay: float = 0) -> Any:
    if delay:
        await asyncio.sleep(delay)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
                if r.status in (429, 503):
                    wait = RETRY_BACKOFF ** attempt
                    log.warning(f'Rate limit {r.status} — waiting {wait:.0f}s  {url}')
                    await asyncio.sleep(wait)
                    continue
                log.warning(f'HTTP {r.status} — {url}')
                return None
        except Exception as exc:
            wait = RETRY_BACKOFF ** attempt
            log.warning(f'Attempt {attempt} failed ({exc}) — retry in {wait:.0f}s')
            await asyncio.sleep(wait)
    return None


# ─────────────────────────────────────────────────────────────────
# TRANSLITERATION FETCH
# ─────────────────────────────────────────────────────────────────
def words_to_transliteration(words: list[dict]) -> str:
    """Join word-level transliteration texts, skipping punctuation tokens."""
    parts = []
    for word in words:
        if word.get('char_type_name') != 'word':
            continue
        tlit = (word.get('transliteration') or {}).get('text') or ''
        if tlit:
            parts.append(tlit)
    return ' '.join(parts)


async def fetch_chapter_transliteration(
        session: aiohttp.ClientSession, chapter: int) -> dict[str, str]:
    """
    Returns mapping verse_key → transliteration string for all verses in chapter.
    Handles pagination (up to 300 verses per page, Quran max per chapter is 286).
    """
    result = {}
    page = 1
    while True:
        url = (
            f'{BASE_URL}/verses/by_chapter/{chapter}'
            f'?words=true&word_fields=transliteration&per_page=300&page={page}'
        )
        data = await fetch_json(session, url, delay=REQUEST_DELAY)
        if not data:
            log.warning(f'  No data for chapter {chapter} page {page}')
            break

        verses = data.get('verses', [])
        for verse in verses:
            key = verse.get('verse_key', f'{chapter}:{verse.get("verse_number",0)}')
            tlit = words_to_transliteration(verse.get('words', []))
            result[key] = tlit

        pagination = data.get('meta', {})
        current_page = pagination.get('current_page', 1)
        last_page = pagination.get('total_pages', 1)
        if current_page >= last_page:
            break
        page += 1

    return result


async def download_transliteration(session: aiohttp.ClientSession) -> dict[str, str]:
    """Download transliteration for all 114 chapters. Returns full verse_key → tlit map."""
    all_transliterations: dict[str, str] = {}

    for chapter in range(1, TOTAL_CHAPTERS + 1):
        chapter_tlit = await fetch_chapter_transliteration(session, chapter)
        all_transliterations.update(chapter_tlit)
        if chapter % 10 == 0 or chapter == TOTAL_CHAPTERS:
            log.info(f'  Chapter {chapter}/{TOTAL_CHAPTERS} — {len(all_transliterations)} verses done')

    return all_transliterations


# ─────────────────────────────────────────────────────────────────
# MERGE INTO QURAN FULL
# ─────────────────────────────────────────────────────────────────
def merge_into_quran_full(transliterations: dict[str, str]) -> int:
    """
    Adds transliteration field to each verse in quran_full.json.
    Returns number of verses updated.
    """
    quran_path = QURAN_DIR / 'quran_full.json'
    if not quran_path.exists():
        log.warning('  quran_full.json not found — skipping merge')
        return 0

    log.info('  Merging transliteration into quran_full.json…')
    with open(quran_path, encoding='utf-8') as f:
        quran = json.load(f)

    updated = 0
    surahs = quran.get('surahs') or quran.get('chapters') or []

    for surah in surahs:
        surah_num = surah.get('number') or surah.get('surah_number') or surah.get('id')
        verses = surah.get('ayahs') or surah.get('verses') or []
        for verse in verses:
            verse_num = verse.get('numberInSurah') or verse.get('verse_number') or verse.get('ayah_number')
            key = f'{surah_num}:{verse_num}'
            tlit = transliterations.get(key, '')
            if tlit:
                verse['transliteration'] = tlit
                updated += 1

    with open(quran_path, 'w', encoding='utf-8') as f:
        json.dump(quran, f, ensure_ascii=False, indent=2)

    size_mb = quran_path.stat().st_size / 1e6
    log.info(f'  Updated quran_full.json — {updated} verses got transliteration ({size_mb:.1f} MB)')
    return updated


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
async def main() -> None:
    log.info('═' * 60)
    log.info('Islamic AI — Priority 3: Quran Transliteration')
    log.info(f'Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log.info('═' * 60)

    tlit_path = QURAN_DIR / 'quran_transliteration.json'

    if tlit_path.exists():
        log.info('  quran_transliteration.json already exists.')
        log.info('  Loading cached transliterations to merge into quran_full.json…')
        with open(tlit_path, encoding='utf-8') as f:
            saved = json.load(f)
        transliterations = saved.get('transliterations', {})
    else:
        connector = aiohttp.TCPConnector(limit=CONNECTOR_LIMIT)
        async with aiohttp.ClientSession(connector=connector) as session:
            log.info('Fetching transliteration from quran.com API (114 chapters)…')
            transliterations = await download_transliteration(session)

        # Save standalone file
        result = {
            'metadata': {
                'source':       'api.quran.com/api/v4',
                'endpoint':     '/verses/by_chapter/{n}?words=true&word_fields=transliteration',
                'total_verses': len(transliterations),
                'downloaded_at': datetime.now(timezone.utc).isoformat(),
                'note': (
                    'Word-level transliterations joined per verse. '
                    'Uses standard Arabic transliteration with diacritics.'
                ),
            },
            'transliterations': transliterations,  # {"1:1": "bismi l-lahi ...", ...}
        }
        with open(tlit_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        size_mb = tlit_path.stat().st_size / 1e6
        log.info(f'Saved standalone → quran_transliteration.json ({len(transliterations)} verses, {size_mb:.1f} MB)')

    # Merge into quran_full.json
    updated = merge_into_quran_full(transliterations)

    log.info('\n' + '═' * 60)
    log.info(f'DONE — {len(transliterations)} transliterations, {updated} merged into quran_full.json')

    # Show sample output
    sample_keys = list(transliterations.keys())[:5]
    log.info('Sample transliterations:')
    for k in sample_keys:
        log.info(f'  {k}: {transliterations[k][:70]}')
    log.info('═' * 60)


if __name__ == '__main__':
    asyncio.run(main())
