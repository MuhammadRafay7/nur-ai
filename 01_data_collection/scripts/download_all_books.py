#!/usr/bin/env python3
"""
download_all_books.py — One command downloads everything.

Sources:
  1. quran.com API      — 8 tafsir books (Ibn Kathir EN, Ma'arif, Tabari AR,
                          Qurtubi AR, Sa'di AR, Baghawi AR, Jalalayn AR,
                          Fi Zilal AR) — FREE, no auth
  2. alquran.cloud API  — 6 additional Arabic tafsir editions — FREE, no auth
  3. sunnah.com API     — Riyadh al-Salihin, Al-Adab al-Mufrad, Mishkat,
                          Hisn al-Muslim — FREE API key required
                          Register at: https://ahadith.co.uk/hadithapi.php

Run:
  python download_all_books.py
  python download_all_books.py --sunnah-key YOUR_KEY_HERE
"""

import asyncio
import aiohttp
import argparse
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parents[1]
HADITH_DIR = ROOT / 'raw' / 'hadith'
TAFSIR_DIR = ROOT / 'raw' / 'tafsir'
LOG_DIR    = ROOT / 'logs'

for d in [HADITH_DIR, TAFSIR_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────
log_file = LOG_DIR / f'download_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────────
MAX_RETRIES        = 4
RETRY_BACKOFF      = 2.0
QURANCOM_DELAY     = 0.4   # seconds between quran.com calls
ALQURAN_DELAY      = 0.3
SUNNAH_DELAY       = 0.5
CONNECTOR_LIMIT    = 5

# ─────────────────────────────────────────────────────────────────
# BOOK DEFINITIONS
# ─────────────────────────────────────────────────────────────────

# quran.com tafsir: (id, output_filename, description)
QURANCOM_TAFSIRS = [
    (169, 'tafsir_ibn_kathir_en',     'Tafsir Ibn Kathir (English abridged)'),
    (168, 'tafsir_maarif_ul_quran_en','Ma\'arif al-Qur\'an (English — Mufti Shafi Usmani)'),
    ( 14, 'tafsir_ibn_kathir_ar',     'Tafsir Ibn Kathir (Arabic full)'),
    ( 15, 'tafsir_al_tabari_ar',      'Tafsir al-Tabari — Jami al-Bayan (Arabic)'),
    ( 90, 'tafsir_al_qurtubi_ar',     'Tafsir al-Qurtubi (Arabic)'),
    ( 91, 'tafsir_al_saadi_ar',       'Tafsir al-Sa\'di — Taysir al-Karim (Arabic)'),
    ( 94, 'tafsir_al_baghawi_ar',     'Tafsir al-Baghawi (Arabic)'),
    (157, 'tafsir_fi_zilal_ar',       'Fi Zilal al-Quran — Sayyid Qutb (Arabic)'),
    (817, 'tafsir_tazkirul_quran_en', 'Tazkirul Quran — Wahiduddin Khan (English)'),
]

# alquran.cloud tafsir editions
ALQURAN_TAFSIRS = [
    ('ar.muyassar',  'tafsir_muyassar_ar',  'Tafsir Muyassar — King Fahad Complex (Arabic)'),
    ('ar.jalalayn',  'tafsir_jalalayn_ar',   'Tafsir al-Jalalayn (Arabic)'),
    ('ar.qurtubi',   'tafsir_qurtubi_alquran_ar', 'Tafsir al-Qurtubi via alquran.cloud (Arabic)'),
    ('ar.miqbas',    'tafsir_ibn_abbas_ar',  'Tafsir Ibn Abbas — Tanwir al-Miqbas (Arabic)'),
    ('ar.waseet',    'tafsir_al_waseet_ar',  'Tafsir al-Waseet — Tantawi (Arabic)'),
    ('ar.baghawi',   'tafsir_baghawi_alquran_ar', 'Tafsir al-Baghawi via alquran.cloud (Arabic)'),
]

# sunnah.com hadith collections (needs free API key)
SUNNAH_COLLECTIONS = [
    ('riyadussalihin', 'riyadh_al_salihin',   'Riyadh al-Salihin — Imam Nawawi',       1896),
    ('adab',           'al_adab_al_mufrad',   'Al-Adab al-Mufrad — Imam Bukhari',      1329),
    ('mishkat',        'mishkat_al_masabih',  'Mishkat al-Masabih',                    6294),
    ('hisn',           'hisn_al_muslim',      'Hisn al-Muslim (Fortress of the Muslim)',  250),
]

# ─────────────────────────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────────────────────────
async def fetch_json(session: aiohttp.ClientSession, url: str,
                     headers: dict = None, delay: float = 0) -> Any:
    if delay:
        await asyncio.sleep(delay)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, headers=headers or {}, timeout=aiohttp.ClientTimeout(total=30)) as r:
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
            log.warning(f'Attempt {attempt} failed ({exc}) — retrying in {wait:.0f}s')
            await asyncio.sleep(wait)
    return None

def save(path: Path, data: Any, description: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_mb = path.stat().st_size / 1e6
    log.info(f'  Saved {description} → {path.name} ({size_mb:.1f} MB)')

# ─────────────────────────────────────────────────────────────────
# DOWNLOADER 1 — quran.com tafsir
# ─────────────────────────────────────────────────────────────────
async def download_qurancom_tafsir(session: aiohttp.ClientSession,
                                   tafsir_id: int, filename: str, desc: str) -> None:
    out_path = TAFSIR_DIR / f'{filename}.json'
    if out_path.exists():
        log.info(f'  Skip (exists): {filename}')
        return

    log.info(f'Downloading: {desc}')
    base = 'https://api.quran.com/api/v4'
    all_verses = []

    for chapter in range(1, 115):
        url = f'{base}/tafsirs/{tafsir_id}/by_chapter/{chapter}?per_page=300'
        data = await fetch_json(session, url, delay=QURANCOM_DELAY)
        if not data:
            log.warning(f'  Failed chapter {chapter} of {desc}')
            continue
        verses = data.get('tafsirs', [])
        all_verses.extend(verses)
        if chapter % 20 == 0:
            log.info(f'  {desc} — chapter {chapter}/114 ({len(all_verses)} verses so far)')

    result = {
        'metadata': {
            'source':       'api.quran.com/api/v4',
            'tafsir_id':    tafsir_id,
            'name':         desc,
            'total_verses': len(all_verses),
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
        },
        'verses': all_verses,
    }
    save(out_path, result, desc)

# ─────────────────────────────────────────────────────────────────
# DOWNLOADER 2 — alquran.cloud tafsir
# ─────────────────────────────────────────────────────────────────
async def download_alquran_tafsir(session: aiohttp.ClientSession,
                                  edition: str, filename: str, desc: str) -> None:
    out_path = TAFSIR_DIR / f'{filename}.json'
    if out_path.exists():
        log.info(f'  Skip (exists): {filename}')
        return

    log.info(f'Downloading: {desc}')
    url = f'https://api.alquran.cloud/v1/quran/{edition}'
    data = await fetch_json(session, url, delay=ALQURAN_DELAY)
    if not data or data.get('code') != 200:
        log.error(f'  Failed: {desc}')
        return

    quran_data = data.get('data', {})
    all_ayahs = []
    for surah in quran_data.get('surahs', []):
        for ayah in surah.get('ayahs', []):
            all_ayahs.append({
                'surah_number': surah['number'],
                'surah_name':   surah['englishName'],
                'ayah_number':  ayah['numberInSurah'],
                'text':         ayah['text'],
            })

    result = {
        'metadata': {
            'source':       'api.alquran.cloud/v1',
            'edition':      edition,
            'name':         desc,
            'total_ayahs':  len(all_ayahs),
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
        },
        'ayahs': all_ayahs,
    }
    save(out_path, result, desc)

# ─────────────────────────────────────────────────────────────────
# DOWNLOADER 3 — sunnah.com hadith (needs API key)
# ─────────────────────────────────────────────────────────────────
async def download_sunnah_collection(session: aiohttp.ClientSession, api_key: str,
                                     collection: str, filename: str,
                                     desc: str, expected: int) -> None:
    out_path = HADITH_DIR / f'{filename}.json'
    if out_path.exists():
        log.info(f'  Skip (exists): {filename}')
        return

    log.info(f'Downloading: {desc}')
    base    = 'https://api.sunnah.com/v1'
    headers = {'X-API-Key': api_key}
    limit   = 50
    page    = 1
    hadiths = []

    while True:
        url  = f'{base}/collections/{collection}/hadiths?limit={limit}&page={page}'
        data = await fetch_json(session, url, headers=headers, delay=SUNNAH_DELAY)
        if not data:
            break
        items = data.get('data', [])
        if not items:
            break
        for item in items:
            hadiths.append({
                'hadith_number': item.get('hadithNumber'),
                'arabic':        item.get('hadith', [{}])[0].get('body', '') if item.get('hadith') else '',
                'english':       item.get('hadith', [{}, {}])[1].get('body', '') if len(item.get('hadith', [])) > 1 else '',
                'grade':         item.get('grades', [{}])[0].get('grade', '') if item.get('grades') else '',
                'collection':    collection,
            })
        log.info(f'  {desc} — page {page} ({len(hadiths)} hadiths)')
        if len(items) < limit:
            break
        page += 1

    result = {
        'metadata': {
            'source':        'api.sunnah.com/v1',
            'collection':    collection,
            'display_name':  desc,
            'total_hadiths': len(hadiths),
            'expected_min':  expected,
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
        },
        'hadiths': hadiths,
    }
    save(out_path, result, desc)
    if len(hadiths) < expected * 0.9:
        log.warning(f'  Only {len(hadiths)} hadiths (expected ~{expected}) — check API key/limits')

# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
async def main(sunnah_key: str) -> None:
    log.info('═' * 60)
    log.info('Islamic AI — Full Book Download')
    log.info(f'Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log.info('═' * 60)

    connector = aiohttp.TCPConnector(limit=CONNECTOR_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:

        # ── 1. quran.com tafsir ──────────────────────────────────
        log.info('\n── TAFSIR (quran.com) ──────────────────────────────')
        for tafsir_id, filename, desc in QURANCOM_TAFSIRS:
            await download_qurancom_tafsir(session, tafsir_id, filename, desc)

        # ── 2. alquran.cloud tafsir ──────────────────────────────
        log.info('\n── TAFSIR (alquran.cloud) ──────────────────────────')
        for edition, filename, desc in ALQURAN_TAFSIRS:
            await download_alquran_tafsir(session, edition, filename, desc)

        # ── 3. sunnah.com hadith ─────────────────────────────────
        if sunnah_key:
            log.info('\n── HADITH (sunnah.com) ─────────────────────────────')
            for collection, filename, desc, expected in SUNNAH_COLLECTIONS:
                await download_sunnah_collection(
                    session, sunnah_key, collection, filename, desc, expected)
        else:
            log.info('\n── HADITH (sunnah.com) — SKIPPED (no API key) ──────')
            log.info('  Get a free key at: https://ahadith.co.uk/hadithapi.php')
            log.info('  Then run: python download_all_books.py --sunnah-key YOUR_KEY')

    # ── Summary ──────────────────────────────────────────────────
    log.info('\n' + '═' * 60)
    log.info('DOWNLOAD COMPLETE')
    tafsir_files = list(TAFSIR_DIR.glob('*.json'))
    hadith_files = list(HADITH_DIR.glob('*.json'))
    total_mb = sum(f.stat().st_size for f in tafsir_files + hadith_files) / 1e6
    log.info(f'  Tafsir files : {len(tafsir_files)}')
    log.info(f'  Hadith files : {len(hadith_files)}')
    log.info(f'  Total size   : {total_mb:.0f} MB')
    log.info('═' * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all Islamic books')
    parser.add_argument('--sunnah-key', default='', help='sunnah.com API key (free registration)')
    args = parser.parse_args()
    asyncio.run(main(sunnah_key=args.sunnah_key))
