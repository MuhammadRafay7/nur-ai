#!/usr/bin/env python3
"""
download_p2_classical_books.py — Priority 2: Classical Islamic books from archive.org.

Downloads plain-text (DjVuTXT) versions of classical Islamic books:
  - Ihya Ulum al-Din (Al-Ghazali) — individual books
  - Seerah Ibn Hisham
  - Madarij al-Salikin (Ibn al-Qayyim)
  - Hilyat al-Awliya
  - Al-Aqeedah al-Tahawiyyah
  - Ranks of the Divine Seekers / Madarij al-Salikin
  - Additional books from islamhouse.com

Run:
  python download_p2_classical_books.py
"""

import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).resolve().parents[1]
CLASSICAL_DIR = ROOT / 'raw' / 'classical'
LOG_DIR      = ROOT / 'logs'

for d in [CLASSICAL_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────
log_file = LOG_DIR / f'p2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
ARCHIVE_DELAY   = 1.2
CONNECTOR_LIMIT = 3

# ─────────────────────────────────────────────────────────────────
# BOOK CATALOGUE
# ─────────────────────────────────────────────────────────────────
# (archive_identifier, output_filename, description, category)
CLASSICAL_BOOKS = [
    # ── Seerah ──────────────────────────────────────────────────
    (
        'SeerahIbnHisham',
        'seerah_ibn_hisham',
        'Seerah Ibn Hisham — Life of the Prophet',
        'seerah',
    ),
    (
        'abridgedsiratibnhishamthelifeof1',
        'seerah_ibn_hisham_abridged',
        'Abridged Sirat Ibn Hisham (Vol 1)',
        'seerah',
    ),

    # ── Tazkiyah / Spirituality ──────────────────────────────────
    (
        'ranks-of-the-divine-seekers-madarij-al-salikin',
        'madarij_al_salikin',
        'Madarij al-Salikin (Ranks of the Divine Seekers) — Ibn al-Qayyim',
        'tazkiyah',
    ),
    (
        'kitab-al-tabaqat-al-kabir-ibn-sad-volume-1',
        'tabaqat_ibn_sad',
        'Kitab al-Tabaqat al-Kabir (Companions & early Muslims) — Ibn Sa\'d',
        'biographies',
    ),
    (
        'the-mysteries-of-purity',
        'ihya_mysteries_of_purity',
        'Ihya Ulum al-Din: The Mysteries of Purity — Al-Ghazali',
        'tazkiyah',
    ),
    (
        'al-ghazali-on-poverty-and-abstinence-kitab-al-faqr-wal-zuhd-book-34-xxxiv-of-the',
        'ihya_poverty_abstinence',
        'Ihya Ulum al-Din: On Poverty and Abstinence (Book 34) — Al-Ghazali',
        'tazkiyah',
    ),
    (
        'al-ghazali-kitab-asrar-al-zakat-wa-kitab-asrar-al-siyam-the-mysteries-of-charity',
        'ihya_mysteries_zakat_fasting',
        'Ihya Ulum al-Din: Mysteries of Charity and Fasting — Al-Ghazali',
        'tazkiyah',
    ),

    # ── Aqeedah ─────────────────────────────────────────────────
    (
        'hisnAlmuslimFortressOfTheMuslimInvocationsFromTheQuranAndSunnah',
        'hisn_al_muslim_classical',
        'Hisn al-Muslim with full invocations — Said al-Qahtani',
        'dua',
    ),

    # ── History / Biographies ────────────────────────────────────
    (
        'the-battles-of-the-prophet-ibn-kathir',
        'battles_of_the_prophet_ibn_kathir',
        'The Battles of the Prophet — Ibn Kathir',
        'history',
    ),
    (
        'EarlyDays_ibnkatheer',
        'early_days_ibn_kathir',
        'Early Days (Al-Bidayah excerpt) — Ibn Kathir',
        'history',
    ),

    # ── Fiqh / Usul ─────────────────────────────────────────────
    (
        'BulughAlMaramIbnHajarAlAsqalani',
        'bulugh_al_maram_classical',
        'Bulugh al-Maram — Ibn Hajar al-Asqalani',
        'hadith_fiqh',
    ),

    # ── Hadith Explanation ───────────────────────────────────────
    (
        'the-khulasa-summary-of-imam-abu-isa-al-tirmidhis-ash-shamail-al-muhammadiyya-z-lib.io',
        'shamail_khulasa',
        'Khulasat al-Shamail — Summary of Shamail al-Muhammadiyya',
        'seerah',
    ),

    # ── Aqeedah books (replacing islamhouse.com 404s) ────────────
    (
        'tahawi_201701',
        'aqeedah_tahawiyyah',
        'Al-Aqeedah al-Tahawiyyah — Imam al-Tahawi',
        'aqeedah',
    ),
    (
        'AnExplanationOfMuhammadIbnAbdalWahabsKitabAl-tawhid.pdf',
        'kitab_al_tawhid',
        'Kitab al-Tawhid (with explanation) — Muhammad ibn Abd al-Wahhab',
        'aqeedah',
    ),
    (
        'SharhAlAqeedahAtTahawiyyahByShaykhAhmadMusaJibril',
        'sharh_aqeedah_tahawiyyah',
        'Sharh al-Aqeedah al-Tahawiyyah — Shaykh Ahmad Musa Jibril',
        'aqeedah',
    ),
    (
        'jaahiliyyah',
        'aspects_days_of_ignorance',
        'Aspects of the Days of Ignorance — Muhammad ibn Abd al-Wahhab',
        'aqeedah',
    ),
]

# islamhouse.com URL pattern changed — all downloads now handled via archive.org above
ISLAMHOUSE_BOOKS = []


# ─────────────────────────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────────────────────────
async def fetch_bytes(session: aiohttp.ClientSession, url: str,
                      delay: float = 0) -> bytes | None:
    if delay:
        await asyncio.sleep(delay)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=180)) as r:
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
            log.warning(f'Attempt {attempt} failed ({exc}) — retry in {wait:.0f}s')
            await asyncio.sleep(wait)
    return None


async def fetch_json(session: aiohttp.ClientSession, url: str,
                     delay: float = 0) -> Any:
    data = await fetch_bytes(session, url, delay=delay)
    if data is None:
        return None
    try:
        return json.loads(data)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────
# TEXT PROCESSING
# ─────────────────────────────────────────────────────────────────
def clean_djvu_text(raw: str) -> str:
    text = re.sub(r'\x0c', '\n\n', raw)
    text = re.sub(r'(?m)^\s*Page\s+\d+\s*$', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber; fall back to raw extraction."""
    try:
        import pdfplumber, io
        pages = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return '\n\n'.join(pages)
    except ImportError:
        log.warning('  pdfplumber not available; install it for PDF extraction')
        return ''
    except Exception as exc:
        log.warning(f'  PDF extraction failed: {exc}')
        return ''


def split_into_sections(text: str, max_chars: int = 3000) -> list[dict]:
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


def save_book(path: Path, sections: list[dict], meta: dict) -> None:
    result = {'metadata': meta, 'sections': sections}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    size_mb = path.stat().st_size / 1e6
    log.info(f'  Saved → {path.name} ({len(sections)} sections, {size_mb:.1f} MB)')


# ─────────────────────────────────────────────────────────────────
# ARCHIVE.ORG DOWNLOADER
# ─────────────────────────────────────────────────────────────────
async def download_archive_book(session: aiohttp.ClientSession,
                                identifier: str, filename: str,
                                desc: str, category: str) -> None:
    out_path = CLASSICAL_DIR / f'{filename}.json'
    if out_path.exists():
        log.info(f'  Skip (exists): {filename}')
        return

    meta_url = f'https://archive.org/metadata/{identifier}'
    meta = await fetch_json(session, meta_url, delay=ARCHIVE_DELAY)
    if not meta:
        log.error(f'  Metadata fetch failed: {identifier}')
        return

    files = meta.get('files', [])
    # Priority: DjVuTXT > plain Text > EPUB > PDF
    format_priority = {'DjVuTXT': 0, 'Text': 1, 'EPUB': 2,
                       'Additional Text PDF': 3, 'Image Container PDF': 4, 'PDF': 5}
    candidates = [
        (format_priority[f['format']], f['name'], f['format'])
        for f in files if f.get('format') in format_priority
    ]
    if not candidates:
        log.warning(f'  No usable format found for {identifier}')
        log.info(f'  Available: {list({f.get("format") for f in files})}')
        return

    candidates.sort()
    _, chosen_file, chosen_format = candidates[0]
    log.info(f'  Downloading [{chosen_format}] {desc}')

    dl_url = f'https://archive.org/download/{identifier}/{chosen_file}'
    raw_bytes = await fetch_bytes(session, dl_url, delay=ARCHIVE_DELAY)
    if not raw_bytes:
        log.error(f'  Download failed: {dl_url}')
        return

    if chosen_format in ('DjVuTXT', 'Text'):
        raw_text = raw_bytes.decode('utf-8', errors='replace')
        clean = clean_djvu_text(raw_text)
    elif chosen_format in ('Additional Text PDF', 'Image Container PDF', 'PDF'):
        clean = extract_pdf_text(raw_bytes)
        if not clean:
            log.error(f'  PDF text extraction failed for {desc}')
            return
    else:
        # EPUB — treat as zip, extract content.opf or just raw text
        log.warning(f'  EPUB format not directly handled for {identifier} — skipping')
        return

    sections = split_into_sections(clean)
    save_book(out_path, sections, {
        'source':         f'archive.org/{identifier}',
        'name':           desc,
        'category':       category,
        'file':           chosen_file,
        'format':         chosen_format,
        'total_sections': len(sections),
        'total_chars':    len(clean),
        'downloaded_at':  datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────────────────────────────
# ISLAMHOUSE.COM PDF DOWNLOADER
# ─────────────────────────────────────────────────────────────────
async def download_islamhouse_book(session: aiohttp.ClientSession,
                                   url: str, filename: str,
                                   desc: str, category: str) -> None:
    out_path = CLASSICAL_DIR / f'{filename}.json'
    if out_path.exists():
        log.info(f'  Skip (exists): {filename}')
        return

    log.info(f'  Downloading islamhouse PDF: {desc}')
    raw_bytes = await fetch_bytes(session, url, delay=1.0)
    if not raw_bytes:
        log.error(f'  Failed: {url}')
        return

    clean = extract_pdf_text(raw_bytes)
    if not clean or len(clean) < 500:
        log.error(f'  PDF text too short or empty for {desc}')
        return

    sections = split_into_sections(clean)
    save_book(out_path, sections, {
        'source':         url,
        'name':           desc,
        'category':       category,
        'format':         'PDF',
        'total_sections': len(sections),
        'total_chars':    len(clean),
        'downloaded_at':  datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
async def main() -> None:
    log.info('═' * 60)
    log.info('Islamic AI — Priority 2: Classical Books')
    log.info(f'Start: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log.info('═' * 60)

    connector = aiohttp.TCPConnector(limit=CONNECTOR_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:

        log.info('\n── Archive.org classical books ──────────────────────────')
        for identifier, filename, desc, category in CLASSICAL_BOOKS:
            await download_archive_book(session, identifier, filename, desc, category)

        log.info('\n── islamhouse.com books (PDF) ────────────────────────────')
        for url, filename, desc, category in ISLAMHOUSE_BOOKS:
            await download_islamhouse_book(session, url, filename, desc, category)

    # Summary
    log.info('\n' + '═' * 60)
    files = list(CLASSICAL_DIR.glob('*.json'))
    total_mb = sum(f.stat().st_size for f in files) / 1e6
    log.info(f'Classical files: {len(files)}  |  Total: {total_mb:.0f} MB')
    log.info('═' * 60)


if __name__ == '__main__':
    asyncio.run(main())
