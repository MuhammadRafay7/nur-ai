#!/usr/bin/env python3
"""
download_p1_hadith_fatwas.py — Priority 1 downloads.

Part A: Missing hadith books from archive.org (DjVuTXT plain text):
  Riyadh al-Salihin, Bulugh al-Maram, Al-Adab al-Mufrad,
  Mishkat al-Masabih, Hisn al-Muslim, Shamail al-Muhammadiyya

Part B: HuggingFace — fawazahmed0/hadith-data (Arabic text for all 10 books)
         meeAtif/hadith_datasets (Arabic+English with grades)

Part C: Fatwas — islamqa.info (extend beyond existing 19k)
                  seekersguidance.org (Hanafi-focused English Q&A)

Run:
  python download_p1_hadith_fatwas.py              # all parts
  python download_p1_hadith_fatwas.py --part a     # archive.org only
  python download_p1_hadith_fatwas.py --part b     # HuggingFace only
  python download_p1_hadith_fatwas.py --part c     # fatwas only
"""

import asyncio
import aiohttp
import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parents[1]
HADITH_DIR  = ROOT / 'raw' / 'hadith'
FATWA_DIR   = ROOT / 'raw' / 'fatwa'
LOG_DIR     = ROOT / 'logs'

for d in [HADITH_DIR, FATWA_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────
log_file = LOG_DIR / f'p1_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-7s  %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────────
MAX_RETRIES          = 4
RETRY_BACKOFF        = 2.0
ARCHIVE_DELAY        = 1.0
ISLAMQA_DELAY        = 0.8   # per-slot delay; effective rate = CONCURRENCY / delay
ISLAMQA_CONCURRENCY  = 8     # concurrent islamqa fetches
SG_DELAY             = 1.5
CONNECTOR_LIMIT      = 12

# ─────────────────────────────────────────────────────────────────
# PART A — ARCHIVE.ORG HADITH BOOKS
# ─────────────────────────────────────────────────────────────────

# (archive_identifier, output_filename, description)
ARCHIVE_HADITH_BOOKS = [
    (
        'Riyad-Us-Saliheen-InEnglish-eBook-PDF',
        'riyadh_al_salihin',
        'Riyadh al-Salihin — Imam al-Nawawi',
    ),
    (
        'AdabAlMufradPerfectionOfCharacter',
        'al_adab_al_mufrad',
        'Al-Adab al-Mufrad — Imam al-Bukhari',
    ),
    (
        'MishkatAlMasabihVol1Pdfbooksfree.pk',
        'mishkat_al_masabih',
        'Mishkat al-Masabih — Al-Tabrizi',
    ),
    (
        'hisnAlmuslimFortressOfTheMuslimInvocationsFromTheQuranAndSunnah',
        'hisn_al_muslim',
        'Hisn al-Muslim — Said ibn Ali al-Qahtani',
    ),
    (
        'tobaa-the-abridged-shamail-e-tirmizi-shamail-e-tirmazi-english',
        'shamail_muhammadiyya',
        'Shamail al-Muhammadiyya — Imam al-Tirmidhi',
    ),
    (
        'BulughAlMaramIbnHajarAlAsqalani',
        'bulugh_al_maram',
        'Bulugh al-Maram — Ibn Hajar al-Asqalani',
    ),
]


async def fetch_bytes(session: aiohttp.ClientSession, url: str,
                      delay: float = 0) -> bytes | None:
    if delay:
        await asyncio.sleep(delay)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as r:
                if r.status == 200:
                    return await r.read()
                if r.status in (429, 503):
                    wait = RETRY_BACKOFF ** attempt
                    log.warning(f'Rate limit {r.status} — waiting {wait:.0f}s')
                    await asyncio.sleep(wait)
                    continue
                log.warning(f'HTTP {r.status} — {url}')
                return None
        except Exception as exc:
            wait = RETRY_BACKOFF ** attempt
            log.warning(f'Attempt {attempt} failed ({exc}) — retrying in {wait:.0f}s')
            await asyncio.sleep(wait)
    return None


async def fetch_json(session: aiohttp.ClientSession, url: str,
                     headers: dict = None, delay: float = 0) -> Any:
    data = await fetch_bytes(session, url, delay=delay)
    if data is None:
        return None
    try:
        return json.loads(data)
    except Exception:
        return None


def clean_djvu_text(raw: str) -> str:
    """Strip DjVuTXT page markers and OCR artefacts, return clean prose."""
    # Remove form-feed page breaks and page headers like "Page 1"
    text = re.sub(r'\x0c', '\n\n', raw)
    text = re.sub(r'(?m)^\s*Page\s+\d+\s*$', '', text)
    # Collapse excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_into_sections(text: str, max_chars: int = 3000) -> list[dict]:
    """Split raw text into paragraph-level chunks for storage."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    sections = []
    buf = []
    buf_len = 0
    sec_idx = 1
    for para in paragraphs:
        if buf_len + len(para) > max_chars and buf:
            sections.append({'section': sec_idx, 'text': '\n\n'.join(buf)})
            sec_idx += 1
            buf = []
            buf_len = 0
        buf.append(para)
        buf_len += len(para)
    if buf:
        sections.append({'section': sec_idx, 'text': '\n\n'.join(buf)})
    return sections


async def download_archive_book(session: aiohttp.ClientSession,
                                identifier: str, filename: str, desc: str) -> None:
    out_path = HADITH_DIR / f'{filename}.json'
    if out_path.exists():
        log.info(f'  Skip (exists): {filename}')
        return

    log.info(f'Fetching metadata: {desc}')
    meta_url = f'https://archive.org/metadata/{identifier}'
    meta = await fetch_json(session, meta_url, delay=ARCHIVE_DELAY)
    if not meta:
        log.error(f'  Failed to get metadata: {identifier}')
        return

    files = meta.get('files', [])
    # Prefer DjVuTXT (already extracted text), then plain Text, then EPUB
    priority = {'DjVuTXT': 0, 'Text': 1, 'EPUB': 2}
    candidates = [(priority[f['format']], f['name'])
                  for f in files if f.get('format') in priority]
    if not candidates:
        log.error(f'  No text format found for {identifier}')
        log.info(f'  Available formats: {[f.get("format") for f in files]}')
        return
    candidates.sort()
    chosen_file = candidates[0][1]
    log.info(f'  Downloading {chosen_file} ({candidates[0][1]})')

    dl_url = f'https://archive.org/download/{identifier}/{chosen_file}'
    raw_bytes = await fetch_bytes(session, dl_url, delay=ARCHIVE_DELAY)
    if not raw_bytes:
        log.error(f'  Download failed: {dl_url}')
        return

    raw_text = raw_bytes.decode('utf-8', errors='replace')
    clean = clean_djvu_text(raw_text)
    sections = split_into_sections(clean)

    result = {
        'metadata': {
            'source':       f'archive.org/{identifier}',
            'name':         desc,
            'file':         chosen_file,
            'total_sections': len(sections),
            'total_chars':  len(clean),
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
        },
        'sections': sections,
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    size_mb = out_path.stat().st_size / 1e6
    log.info(f'  Saved {desc} → {out_path.name} ({size_mb:.1f} MB, {len(sections)} sections)')


async def run_part_a(session: aiohttp.ClientSession) -> None:
    log.info('\n── PART A: Archive.org hadith books ─────────────────────')
    for identifier, filename, desc in ARCHIVE_HADITH_BOOKS:
        await download_archive_book(session, identifier, filename, desc)


# ─────────────────────────────────────────────────────────────────
# PART B — HUGGINGFACE HADITH DATASETS
# ─────────────────────────────────────────────────────────────────

def run_part_b() -> None:
    log.info('\n── PART B: HuggingFace hadith datasets ──────────────────')

    try:
        from datasets import load_dataset
    except ImportError:
        log.error('  datasets library not installed. Run: pip install datasets')
        return

    # ── fawazahmed0/hadith-data ───────────────────────────────────
    # Contains all 10 fawazahmed0 books with both Arabic and English rows.
    # Useful to pair Arabic text with our existing English hadiths.
    out_path = HADITH_DIR / 'fawazahmed0_all_hadith_arabic.json'
    if out_path.exists():
        log.info('  Skip (exists): fawazahmed0_all_hadith_arabic')
    else:
        log.info('  Loading fawazahmed0/hadith-data (Arabic rows)…')
        try:
            ds = load_dataset('fawazahmed0/hadith-data', split='train')
            # Keep only Arabic rows (they have the Arabic hadith text)
            arabic_rows = [
                {
                    'book':         row['bookname'],
                    'book_id':      row['book'],
                    'hadith_number': row['hadithnumber'],
                    'arabic_text':  row['text'],
                    'section':      row['section'],
                    'grade_albani': row.get('Al-Albani') or '',
                    'grade_arnaut': row.get('Shuaib Al Arnaut') or '',
                }
                for row in ds
                if (row.get('language') or '').lower() == 'arabic'
            ]
            result = {
                'metadata': {
                    'source':        'huggingface:fawazahmed0/hadith-data',
                    'total_hadiths': len(arabic_rows),
                    'downloaded_at': datetime.now(timezone.utc).isoformat(),
                },
                'hadiths': arabic_rows,
            }
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            size_mb = out_path.stat().st_size / 1e6
            log.info(f'  Saved fawazahmed0 Arabic rows → {out_path.name} ({size_mb:.1f} MB)')
        except Exception as exc:
            log.error(f'  fawazahmed0/hadith-data failed: {exc}')

    # ── meeAtif/hadith_datasets ───────────────────────────────────
    # Has Arabic + English + Grade for 6 major books — good quality
    out_path2 = HADITH_DIR / 'meeAtif_hadith_ar_en.json'
    if out_path2.exists():
        log.info('  Skip (exists): meeAtif_hadith_ar_en')
    else:
        log.info('  Loading meeAtif/hadith_datasets…')
        try:
            ds2 = load_dataset('meeAtif/hadith_datasets', split='train')
            rows = [
                {
                    'book':          row['Book'],
                    'chapter_num':   row['Chapter_Number'],
                    'chapter_ar':    row['Chapter_Title_Arabic'],
                    'chapter_en':    row['Chapter_Title_English'],
                    'arabic_text':   row['Arabic_Text'],
                    'english_text':  row['English_Text'],
                    'grade':         row['Grade'],
                    'reference':     row['Reference'],
                }
                for row in ds2
            ]
            result2 = {
                'metadata': {
                    'source':        'huggingface:meeAtif/hadith_datasets',
                    'license':       'MIT',
                    'total_hadiths': len(rows),
                    'downloaded_at': datetime.now(timezone.utc).isoformat(),
                },
                'hadiths': rows,
            }
            with open(out_path2, 'w', encoding='utf-8') as f:
                json.dump(result2, f, ensure_ascii=False, indent=2)
            size_mb = out_path2.stat().st_size / 1e6
            log.info(f'  Saved meeAtif AR+EN → {out_path2.name} ({size_mb:.1f} MB)')
        except Exception as exc:
            log.error(f'  meeAtif/hadith_datasets failed: {exc}')


# ─────────────────────────────────────────────────────────────────
# PART C — FATWAS
# ─────────────────────────────────────────────────────────────────

def load_existing_islamqa_ids() -> set:
    path = FATWA_DIR / 'islamqa_fatwas.json'
    if not path.exists():
        return set()
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return {int(ft['original_id']) for ft in data.get('fatwas', [])
            if str(ft.get('original_id', '')).isdigit()}


def parse_islamqa_page(html: str, fatwa_id: int) -> dict | None:
    """Extract question and answer from an islamqa.info answer page."""
    # Title
    title_m = re.search(
        r'<h1[^>]*class=["\']?.*?title.*?["\']?[^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
    if not title_m:
        title_m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ''

    # Question block
    q_m = re.search(
        r'class=["\']question["\'][^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
    question = re.sub(r'<[^>]+>', ' ', q_m.group(1)).strip() if q_m else ''

    # Answer block (main content div)
    a_m = re.search(
        r'class=["\']answer-content["\'][^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
    if not a_m:
        a_m = re.search(
            r'<div[^>]*id=["\']answer["\'][^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
    answer = re.sub(r'<[^>]+>', ' ', a_m.group(1)).strip() if a_m else ''
    answer = re.sub(r'\s{2,}', ' ', answer)

    if not title or not answer or len(answer) < 100:
        return None

    # Category
    cat_m = re.search(r'<a[^>]*category[^>]*>(.*?)</a>', html, re.IGNORECASE)
    category = re.sub(r'<[^>]+>', '', cat_m.group(1)).strip() if cat_m else ''

    return {
        'id':       fatwa_id,
        'title':    title,
        'category': category,
        'question': question,
        'answer':   answer,
        'url':      f'https://islamqa.info/en/answers/{fatwa_id}',
    }


async def _fetch_islamqa_sitemap_ids(session: aiohttp.ClientSession) -> list[int]:
    """Return valid answer IDs from islamqa.info sitemaps (avoids brute-force 404s)."""
    # Try top-level sitemap; islamqa uses a sitemap index with sub-sitemaps
    index_urls = [
        'https://islamqa.info/sitemaps/sitemap-index.xml',  # from robots.txt
        'https://islamqa.info/sitemap.xml',
        'https://islamqa.info/sitemap_index.xml',
        'https://islamqa.info/en/sitemap.xml',
    ]
    id_pattern = re.compile(r'/(?:en|ar)/answers/(\d+)')
    loc_pattern = re.compile(r'<loc>(https://islamqa\.info[^<]+)</loc>')

    ids: set[int] = set()

    async def _scan_sitemap(url: str) -> None:
        data = await fetch_bytes(session, url)
        if not data:
            return
        text = data.decode('utf-8', errors='replace')
        # Collect answer IDs directly in this file
        for m in id_pattern.finditer(text):
            ids.add(int(m.group(1)))
        # If this is a sitemap index, recurse into sub-sitemaps
        sub_urls = loc_pattern.findall(text)
        sub_tasks = [
            _scan_sitemap(u) for u in sub_urls
            if 'sitemap' in u and u not in index_urls
        ]
        if sub_tasks:
            await asyncio.gather(*sub_tasks)

    for index_url in index_urls:
        data = await fetch_bytes(session, index_url)
        if data:
            text = data.decode('utf-8', errors='replace')
            await _scan_sitemap(index_url)
            if ids:
                log.info(f'  Sitemap: found {len(ids):,} answer IDs from {index_url}')
                break

    return sorted(ids)


async def _fetch_one_islamqa(session: aiohttp.ClientSession,
                             semaphore: asyncio.Semaphore,
                             fatwa_id: int) -> dict | None:
    async with semaphore:
        url = f'https://islamqa.info/en/answers/{fatwa_id}'
        data = await fetch_bytes(session, url, delay=ISLAMQA_DELAY)
        if data is None:
            return None
        html = data.decode('utf-8', errors='replace')
        if 'Page not found' in html or '404' in html[:500]:
            return None
        return parse_islamqa_page(html, fatwa_id)


async def scrape_islamqa(session: aiohttp.ClientSession,
                         existing_ids: set, max_new: int = 50000) -> None:
    out_path = FATWA_DIR / 'islamqa_extended.json'
    if out_path.exists():
        log.info('  Skip (exists): islamqa_extended.json')
        log.info('  Delete the file to re-scrape.')
        return

    log.info(f'  Scraping islamqa.info (have {len(existing_ids)} IDs, target {max_new} new)…')

    # ── 1. Discover valid IDs via sitemap (eliminates 404 brute-force) ──
    sitemap_ids = await _fetch_islamqa_sitemap_ids(session)
    if sitemap_ids:
        candidate_ids = [i for i in sitemap_ids if i not in existing_ids]
        log.info(f'  Sitemap IDs to fetch: {len(candidate_ids):,} '
                 f'(skipped {len(sitemap_ids) - len(candidate_ids):,} already collected)')
    else:
        log.warning('  Sitemap unavailable — falling back to sequential scan (slow)')
        candidate_ids = [i for i in range(1, 520_000) if i not in existing_ids]

    # ── 2. Concurrent fetch with incremental saves ───────────────────
    semaphore = asyncio.Semaphore(ISLAMQA_CONCURRENCY)
    fatwas: list[dict] = []
    BATCH = 100  # fetch in batches so we can save progress

    for batch_start in range(0, len(candidate_ids), BATCH):
        if len(fatwas) >= max_new:
            break
        batch = candidate_ids[batch_start: batch_start + BATCH]
        tasks = [_fetch_one_islamqa(session, semaphore, fid) for fid in batch]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r:
                fatwas.append(r)

        if len(fatwas) % 500 < BATCH and fatwas:
            log.info(f'  islamqa.info — {len(fatwas):,} new fatwas scraped '
                     f'(scanned up to id {candidate_ids[min(batch_start + BATCH, len(candidate_ids) - 1)]})')

        # Incremental save every 1000 new fatwas
        if len(fatwas) % 1000 < BATCH and fatwas:
            _save_islamqa(out_path, fatwas, partial=True)

    _save_islamqa(out_path, fatwas, partial=False)


def _save_islamqa(out_path: Path, fatwas: list, partial: bool) -> None:
    result = {
        'metadata': {
            'source':       'islamqa.info',
            'total_fatwas': len(fatwas),
            'partial':      partial,
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
        },
        'fatwas': fatwas,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    if not partial:
        size_mb = out_path.stat().st_size / 1e6
        log.info(f'  Saved islamqa extended → {out_path.name} ({len(fatwas):,} fatwas, {size_mb:.1f} MB)')


def parse_seekersguidance_page(html: str, url: str) -> dict | None:
    """Extract Q&A from a seekersguidance.org answer page."""
    # Title
    title_m = re.search(r'<h1[^>]*class=["\']?.*?entry-title.*?["\']?[^>]*>(.*?)</h1>',
                        html, re.DOTALL | re.IGNORECASE)
    if not title_m:
        title_m = re.search(r'<title>(.*?)\s*[\|\–\-]', html)
    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ''

    # Content div
    content_m = re.search(
        r'class=["\']entry-content["\'][^>]*>(.*?)<div[^>]*class=["\'].*?share',
        html, re.DOTALL | re.IGNORECASE)
    if not content_m:
        content_m = re.search(
            r'class=["\']entry-content["\'][^>]*>(.*?)</article>',
            html, re.DOTALL | re.IGNORECASE)
    if not content_m:
        return None

    content = re.sub(r'<[^>]+>', ' ', content_m.group(1))
    content = re.sub(r'\s{2,}', ' ', content).strip()

    # Split question / answer (seekersguidance usually has "Question:" and "Answer:")
    question = ''
    answer = content
    q_split = re.split(r'(?i)\bquestion\b\s*[:\.]', content, maxsplit=1)
    if len(q_split) == 2:
        a_split = re.split(r'(?i)\banswer\b\s*[:\.]', q_split[1], maxsplit=1)
        if len(a_split) == 2:
            question = a_split[0].strip()
            answer = a_split[1].strip()

    if not title or len(answer) < 150:
        return None

    # Category from breadcrumb or URL
    cat_m = re.search(r'/answers/([^/]+)/', url)
    category = cat_m.group(1).replace('-', ' ').title() if cat_m else ''

    return {
        'title':    title,
        'category': category,
        'question': question,
        'answer':   answer,
        'url':      url,
    }


async def scrape_seekersguidance(session: aiohttp.ClientSession,
                                 max_pages: int = 500) -> None:
    out_path = FATWA_DIR / 'seekersguidance.json'
    if out_path.exists():
        log.info('  Skip (exists): seekersguidance.json')
        return

    log.info('  Scraping seekersguidance.org…')
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; IslamicAI-Research/1.0)',
    }

    # Collect answer URLs via pagination
    answer_urls = set()
    for page in range(1, max_pages + 1):
        list_url = f'https://seekersguidance.org/answers/page/{page}/'
        data = await fetch_bytes(session, list_url, delay=SG_DELAY)
        if data is None:
            break
        html = data.decode('utf-8', errors='replace')
        if 'Page not found' in html or page > 1 and len(answer_urls) == 0:
            break
        found = re.findall(r'href=["\']https://seekersguidance\.org/answers/[^"\']+["\']', html)
        urls = {re.search(r'href=["\']([^"\']+)["\']', h).group(1)
                for h in found}
        answer_urls.update(urls)
        if page % 50 == 0:
            log.info(f'  seekersguidance.org — {page} index pages, {len(answer_urls)} URLs found')
        if not found:
            break

    log.info(f'  Found {len(answer_urls)} answer URLs. Fetching content…')
    fatwas = []
    for url in answer_urls:
        data = await fetch_bytes(session, url, delay=SG_DELAY)
        if data is None:
            continue
        html = data.decode('utf-8', errors='replace')
        parsed = parse_seekersguidance_page(html, url)
        if parsed:
            fatwas.append(parsed)
        if len(fatwas) % 500 == 0 and fatwas:
            log.info(f'  seekersguidance.org — {len(fatwas)} Q&A extracted')

    result = {
        'metadata': {
            'source':       'seekersguidance.org',
            'total_fatwas': len(fatwas),
            'downloaded_at': datetime.now(timezone.utc).isoformat(),
        },
        'fatwas': fatwas,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    size_mb = out_path.stat().st_size / 1e6
    log.info(f'  Saved seekersguidance → {out_path.name} ({len(fatwas)} Q&A, {size_mb:.1f} MB)')


async def run_part_c(session: aiohttp.ClientSession) -> None:
    log.info('\n── PART C: Fatwas ────────────────────────────────────────')
    existing_ids = load_existing_islamqa_ids()
    log.info(f'  Existing islamqa IDs: {len(existing_ids)}')
    await scrape_islamqa(session, existing_ids, max_new=50_000)
    await scrape_seekersguidance(session, max_pages=300)


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
async def main(part: str) -> None:
    log.info('═' * 60)
    log.info('Islamic AI — Priority 1: Hadith Books + Fatwas')
    log.info(f'Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log.info('═' * 60)

    connector = aiohttp.TCPConnector(limit=CONNECTOR_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:
        if part in ('all', 'a'):
            await run_part_a(session)
        if part in ('all', 'b'):
            run_part_b()
        if part in ('all', 'c'):
            await run_part_c(session)

    log.info('\n' + '═' * 60)
    log.info('DONE')
    log.info('═' * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Priority 1: hadith books + fatwas')
    parser.add_argument('--part', choices=['all', 'a', 'b', 'c'], default='all',
                        help='a=archive.org books  b=HuggingFace  c=fatwas')
    args = parser.parse_args()
    asyncio.run(main(part=args.part))
