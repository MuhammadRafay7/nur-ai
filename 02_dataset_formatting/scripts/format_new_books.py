#!/usr/bin/env python3
"""
format_new_books.py — Format newly downloaded real-book data into Q&A training pairs.

Sources handled:
  1. meeAtif_hadith_ar_en.json   — 33k hadiths with Arabic + English + grade
  2. raw/hadith/*.json (archive) — Riyadh al-Salihin, Bulugh al-Maram, etc.
  3. raw/classical/*.json        — Seerah, Madarij, Ihya, Aqeedah, etc.

Called by generate_qa_pairs.py via generate_new_books_pairs().
Can also run standalone to preview output.
"""

from __future__ import annotations

import json
import logging
import random
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_new_books")

# ─────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────
_SCRIPTS_DIR = Path(__file__).parent
_PHASE2_DIR  = _SCRIPTS_DIR.parent
_RAW_DIR     = _PHASE2_DIR.parent / '01_data_collection' / 'raw'
_HADITH_DIR  = _RAW_DIR / 'hadith'
_CLASSICAL_DIR = _RAW_DIR / 'classical'

# ─────────────────────────────────────────────────────────────────
# ISNAD STRIPPER  (reused from format_hadith.py logic)
# ─────────────────────────────────────────────────────────────────
_AR_ISNAD_START = re.compile(
    r'^(حَدَّثَنَا|حدثنا|أَخْبَرَنَا|اخبرنا|حَدَّثَنِي|حدثني'
    r'|أَخْبَرَنِي|اخبرني|وَحَدَّثَنَا|وحدثنا|رَوَى|روى)',
    re.UNICODE,
)
_AR_QALA = re.compile(r'(قَالَ|قَالَتْ|قال|قالت)\s*[:\-]?\s*', re.UNICODE)
_EN_ISNAD = re.compile(
    r'^(it\s+was\s+narrated|narrated\s+by|transmitted\s+by|reported\s+by)',
    re.IGNORECASE,
)
_EN_SAID = re.compile(r'\bsaid\s*:\s*', re.IGNORECASE)


def _strip_isnad_ar(text: str) -> str:
    if not text or not _AR_ISNAD_START.match(text.strip()):
        return text
    matches = list(_AR_QALA.finditer(text))
    if matches:
        last = matches[-1]
        matn = text[last.end():].strip()
        if len(matn) > 30:
            return matn
    return text


def _strip_isnad_en(text: str) -> str:
    if not text or not _EN_ISNAD.match(text.strip()):
        return text
    m = _EN_SAID.search(text)
    if m:
        rest = text[m.end():].strip()
        if len(rest) > 40:
            return rest
    return text


def _clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', ' ', text).strip()


# ─────────────────────────────────────────────────────────────────
# 1. meeAtif HADITH (Arabic + English + Grade)
# ─────────────────────────────────────────────────────────────────

# Question templates keyed by phrasing style
_HADITH_Q_TEMPLATES = [
    "What does the hadith say about {topic}?",
    "Is there a hadith regarding {topic}?",
    "What guidance does the Prophet ﷺ provide on {topic}?",
    "Share a hadith about {topic}.",
    "What did the Prophet ﷺ teach about {topic}?",
    "What Islamic hadith relates to {topic}?",
]

# meeAtif has Arabic+English — valuable even for books already in fawazahmed0
# because fawazahmed0 pairs are English-only; meeAtif pairs are bilingual


def _format_hadith_answer(arabic: str, english: str, grade: str,
                          book: str, chapter: str) -> str:
    arabic_clean = _strip_isnad_ar(arabic).strip()
    english_clean = _strip_isnad_en(english).strip()

    if not english_clean or len(english_clean) < 30:
        return ''

    parts = [f"The Prophet ﷺ said (regarding {chapter}):\n"]
    if arabic_clean:
        parts.append(f"Arabic:\n{arabic_clean}\n")
    parts.append(f'Translation:\n"{english_clean}"')
    parts.append(f"\n({book})")
    if grade:
        parts.append(f"\nGrade: {grade}")
    return '\n'.join(parts)


def generate_meeAtif_pairs(rng: random.Random, max_per_chapter: int = 2) -> list[dict]:
    path = _HADITH_DIR / 'meeAtif_hadith_ar_en.json'
    if not path.exists():
        logger.warning('meeAtif_hadith_ar_en.json not found')
        return []

    data = json.loads(path.read_text(encoding='utf-8'))
    hadiths = data.get('hadiths', [])
    logger.info('meeAtif: loaded %d hadiths', len(hadiths))

    # Group by (book, chapter_en) — pick at most max_per_chapter per group
    from collections import defaultdict
    groups: dict[tuple, list] = defaultdict(list)
    for h in hadiths:
        key = (h.get('book', ''), h.get('chapter_en', ''))
        groups[key].append(h)

    pairs = []
    for (book, chapter_en), rows in groups.items():
        if not chapter_en or len(chapter_en) < 5:
            continue

        # Clean chapter name for question
        topic = re.sub(r'^(Chapter:|Book of|Kitab|The\s)', '', chapter_en, flags=re.I).strip()
        topic = topic.rstrip('.')
        if not topic:
            continue

        sampled = rng.sample(rows, min(max_per_chapter, len(rows)))
        for row in sampled:
            answer = _format_hadith_answer(
                row.get('arabic_text', ''),
                row.get('english_text', ''),
                row.get('grade', ''),
                book,
                chapter_en,
            )
            if not answer:
                continue

            question = rng.choice(_HADITH_Q_TEMPLATES).format(topic=topic)
            pairs.append({
                'instruction': question,
                'input': '',
                'output': answer,
                'metadata': {
                    'source': f'meeAtif/{book}',
                    'category': 'hadith',
                    'chapter': chapter_en,
                },
            })

    logger.info('meeAtif: generated %d pairs', len(pairs))
    return pairs


# ─────────────────────────────────────────────────────────────────
# 2. ARCHIVE.ORG HADITH BOOKS (raw text sections)
# ─────────────────────────────────────────────────────────────────

# Map filename → (display name, category)
_ARCHIVE_HADITH_META = {
    'riyadh_al_salihin':   ('Riyadh al-Salihin by Imam al-Nawawi', 'hadith_fiqh'),
    'bulugh_al_maram':     ('Bulugh al-Maram by Ibn Hajar al-Asqalani', 'hadith_fiqh'),
    'al_adab_al_mufrad':   ('Al-Adab al-Mufrad by Imam al-Bukhari', 'adab'),
    'mishkat_al_masabih':  ('Mishkat al-Masabih by al-Tabrizi', 'hadith'),
    'hisn_al_muslim':      ('Hisn al-Muslim (Fortress of the Muslim)', 'dua'),
    'shamail_muhammadiyya':('Shamail al-Muhammadiyya by Imam al-Tirmidhi', 'seerah'),
}

_ARCHIVE_HADITH_Q_TEMPLATES = [
    "What does {book} teach?",
    "Share a passage from {book}.",
    "What guidance is found in {book} regarding Islamic practice?",
    "What does the book {book} say about this topic?",
]


def _ocr_quality_ok(text: str, min_ratio: float = 0.75) -> bool:
    """Return True if text has enough clean ASCII/Arabic characters (not garbled OCR)."""
    if not text:
        return False
    clean = sum(1 for c in text if c.isalpha() or c.isspace() or c in '.,;:!?()\'"،؟')
    return (clean / max(len(text), 1)) >= min_ratio


def _extract_topic_keywords(text: str, max_words: int = 6) -> str:
    """Extract a short topic phrase from the beginning of a text section."""
    # Take the first sentence or first 60 chars, whichever is shorter
    first = text.split('.')[0].strip()
    if len(first) > 80:
        first = ' '.join(first.split()[:max_words])
    # Strip leading "The " etc.
    first = re.sub(r'^(The\s|It\s|He\s|Allah\s)', '', first).strip()
    return first[:70] if first else ''


def generate_archive_hadith_pairs(rng: random.Random,
                                   max_sections: int = 200) -> list[dict]:
    pairs = []
    for fname, (display_name, category) in _ARCHIVE_HADITH_META.items():
        path = _HADITH_DIR / f'{fname}.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        sections = data.get('sections', [])
        logger.info('archive hadith %s: %d sections', fname, len(sections))

        # Sample sections, prefer longer ones (more content)
        good = [s for s in sections if len(s.get('text', '')) > 300]
        sampled = rng.sample(good, min(max_sections, len(good)))

        for sec in sampled:
            text = sec.get('text', '').strip()
            if not text:
                continue
            text = re.sub(r'\s{2,}', ' ', text)
            if len(text) < 200 or not _ocr_quality_ok(text):
                continue

            topic = _extract_topic_keywords(text)
            if topic and _ocr_quality_ok(topic, min_ratio=0.85):
                question = f"What does {display_name} say about {topic}?"
            else:
                question = rng.choice(_ARCHIVE_HADITH_Q_TEMPLATES).format(book=display_name)

            # Keep answer to a reasonable length
            answer_text = text[:2000].rsplit(' ', 1)[0] if len(text) > 2000 else text
            answer = f"From {display_name}:\n\n{answer_text}"

            pairs.append({
                'instruction': question,
                'input': '',
                'output': answer,
                'metadata': {
                    'source': f'archive.org/{fname}',
                    'category': category,
                },
            })

    logger.info('archive hadith books: generated %d pairs total', len(pairs))
    return pairs


# ─────────────────────────────────────────────────────────────────
# 3. CLASSICAL BOOKS (Seerah, Tazkiyah, Aqeedah, History)
# ─────────────────────────────────────────────────────────────────

_CLASSICAL_META = {
    'seerah_ibn_hisham':            ('Seerah Ibn Hisham (Life of the Prophet ﷺ)', 'seerah'),
    'seerah_ibn_hisham_abridged':   ('Seerah Ibn Hisham (Abridged)', 'seerah'),
    'madarij_al_salikin':           ('Madarij al-Salikin by Ibn al-Qayyim', 'tazkiyah'),
    'tabaqat_ibn_sad':              ('Kitab al-Tabaqat al-Kabir by Ibn Sa\'d', 'biographies'),
    'ihya_mysteries_of_purity':     ("Ihya Ulum al-Din: Mysteries of Purity by Al-Ghazali", 'tazkiyah'),
    'ihya_poverty_abstinence':      ('Ihya Ulum al-Din: On Poverty and Abstinence by Al-Ghazali', 'tazkiyah'),
    'ihya_mysteries_zakat_fasting': ('Ihya Ulum al-Din: Mysteries of Charity and Fasting by Al-Ghazali', 'tazkiyah'),
    'early_days_ibn_kathir':        ('The Early Days (Al-Bidayah) by Ibn Kathir', 'history'),
    'battles_of_the_prophet_ibn_kathir': ('The Battles of the Prophet ﷺ by Ibn Kathir', 'seerah'),
    'aqeedah_tahawiyyah':           ('Al-Aqeedah al-Tahawiyyah by Imam al-Tahawi', 'aqeedah'),
    'kitab_al_tawhid':              ('Kitab al-Tawhid by Muhammad ibn Abd al-Wahhab', 'aqeedah'),
    'aspects_days_of_ignorance':    ('Aspects of the Days of Ignorance by Ibn Abd al-Wahhab', 'aqeedah'),
    'bulugh_al_maram_classical':    ('Bulugh al-Maram by Ibn Hajar al-Asqalani', 'hadith_fiqh'),
    'shamail_khulasa':              ('Khulasat al-Shamail (Shamail al-Muhammadiyya)', 'seerah'),
    'hisn_al_muslim_classical':     ('Hisn al-Muslim (Fortress of the Muslim)', 'dua'),
}

_CLASSICAL_Q_BY_CATEGORY = {
    'seerah': [
        "What does {book} describe about the life of the Prophet ﷺ?",
        "Share a passage from {book} about the Prophet's ﷺ life.",
        "What historical account does {book} provide?",
    ],
    'tazkiyah': [
        "What spiritual guidance does {book} offer?",
        "What does {book} teach about purification of the soul?",
        "Share Islamic wisdom from {book}.",
    ],
    'aqeedah': [
        "What does {book} state about Islamic belief?",
        "Explain a point of aqeedah from {book}.",
        "What creedal teaching is found in {book}?",
    ],
    'history': [
        "What historical event does {book} describe?",
        "What does {book} recount about early Islamic history?",
        "Share a passage from {book} about Islamic history.",
    ],
    'biographies': [
        "What does {book} say about the Companions of the Prophet ﷺ?",
        "Share a biographical account from {book}.",
        "What does {book} record about early Muslims?",
    ],
    'hadith_fiqh': [
        "What ruling does {book} address?",
        "What Islamic legal guidance is in {book}?",
        "Share a passage from {book} about Islamic jurisprudence.",
    ],
    'dua': [
        "What supplication or dhikr does {book} mention?",
        "What invocation is recorded in {book}?",
        "Share a dua from {book}.",
    ],
}
_DEFAULT_CLASSICAL_Q = [
    "What does {book} discuss?",
    "Share a passage from the Islamic book {book}.",
    "What Islamic teaching is found in {book}?",
]


def generate_classical_pairs(rng: random.Random,
                              max_sections: int = 150) -> list[dict]:
    pairs = []
    for fname, (display_name, category) in _CLASSICAL_META.items():
        path = _CLASSICAL_DIR / f'{fname}.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        sections = data.get('sections', [])
        logger.info('classical %s: %d sections', fname, len(sections))

        good = [s for s in sections if len(s.get('text', '')) > 250]
        sampled = rng.sample(good, min(max_sections, len(good)))
        templates = _CLASSICAL_Q_BY_CATEGORY.get(category, _DEFAULT_CLASSICAL_Q)

        for sec in sampled:
            text = sec.get('text', '').strip()
            text = re.sub(r'\s{2,}', ' ', text)
            if len(text) < 200 or not _ocr_quality_ok(text):
                continue

            topic = _extract_topic_keywords(text)
            if topic and _ocr_quality_ok(topic, min_ratio=0.85) and rng.random() < 0.5:
                question = f"What does {display_name} say about {topic}?"
            else:
                question = rng.choice(templates).format(book=display_name)

            answer_text = text[:2200].rsplit(' ', 1)[0] if len(text) > 2200 else text
            answer = f"From {display_name}:\n\n{answer_text}"

            pairs.append({
                'instruction': question,
                'input': '',
                'output': answer,
                'metadata': {
                    'source': f'archive.org/{fname}',
                    'category': category,
                },
            })

    logger.info('classical books: generated %d pairs total', len(pairs))
    return pairs


# ─────────────────────────────────────────────────────────────────
# COMBINED ENTRY POINT
# ─────────────────────────────────────────────────────────────────
def generate_new_books_pairs(seed: int = 42) -> list[dict[str, Any]]:
    """Generate all new-book training pairs. Called by generate_qa_pairs.py."""
    rng = random.Random(seed)
    pairs: list[dict] = []

    pairs += generate_meeAtif_pairs(rng, max_per_chapter=2)
    pairs += generate_archive_hadith_pairs(rng, max_sections=200)
    pairs += generate_classical_pairs(rng, max_sections=150)

    logger.info('format_new_books: %d total pairs generated', len(pairs))
    return pairs


# ─────────────────────────────────────────────────────────────────
# STANDALONE RUN
# ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s  %(levelname)-7s  %(message)s',
                        stream=sys.stdout)

    pairs = generate_new_books_pairs()
    print(f'\nTotal pairs: {len(pairs)}')

    # Show breakdown by source
    from collections import Counter
    sources = Counter(p['metadata']['source'] for p in pairs)
    print('\nBreakdown by source:')
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f'  {count:5d}  {src}')

    # Show 3 random samples
    print('\n── 3 random samples ──────────────────────')
    for p in random.sample(pairs, min(3, len(pairs))):
        print(f"Q: {p['instruction'][:100]}")
        print(f"A: {p['output'][:250]}")
        print()
