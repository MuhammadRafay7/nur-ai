#!/usr/bin/env python3
"""
Generate Q&A training pairs from the 6 new classical Islamic books KB files:
  tafsir_books.json, fiqh_books.json, aqeedah_books.json,
  seerah_books.json, ihya_and_general_books.json, musnad_and_darimi.json
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_books_kb")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load(kb_dir: Path, filename: str) -> dict[str, Any]:
    path = kb_dir / filename
    if not path.exists():
        logger.warning("KB file not found: %s", filename)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load %s: %s", filename, exc)
        return {}

def _pair(instruction: str, output: str, source: str) -> dict[str, Any]:
    return {
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip(),
        "metadata": {"source": source, "category": "books_kb"},
    }

def _val(v: Any) -> str:
    """Flatten a value (str, list, dict) to a readable string."""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "; ".join(_val(i) for i in v if i)
    if isinstance(v, dict):
        return " — ".join(f"{k}: {_val(v2)}" for k, v2 in v.items() if v2)
    return str(v) if v else ""

# ─── Tafsir Books ─────────────────────────────────────────────────────────────

_TAFSIR_BOOKS = [
    ("tafsir_ibn_kathir",  "Tafsir Ibn Kathir",          "Ibn Kathir RH"),
    ("tafsir_al_tabari",   "Tafsir al-Tabari",           "Imam Tabari RH"),
    ("tafsir_al_qurtubi",  "Tafsir al-Qurtubi",          "Imam Qurtubi RH"),
    ("tafsir_al_jalalayn", "Tafsir al-Jalalayn",         "al-Mahalli & al-Suyuti RH"),
    ("fi_zilal_al_quran",  "Fi Zilal al-Quran",          "Sayyid Qutb RH"),
    ("maariful_quran",     "Maariful Quran",             "Mufti Muhammad Shafi RH"),
]

def _tafsir_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "tafsir_books.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Methodology overview pairs
    for entry in data.get("tafsir_methodology", []):
        name = _val(entry.get("type") or entry.get("name", ""))
        defn = _val(entry.get("definition") or entry.get("description", ""))
        ex   = _val(entry.get("examples") or entry.get("example", ""))
        if name and defn:
            out = defn
            if ex:
                out += f" Examples include: {ex}."
            pairs.append(_pair(
                f"What is {name} in Quranic tafsir?",
                out,
                "tafsir_books.json/methodology",
            ))

    # Per-book pairs
    for key, display, author in _TAFSIR_BOOKS:
        book = data.get(key, {})
        if not book:
            continue

        # Overview question
        methodology = _val(book.get("methodology", ""))
        features    = _val(book.get("features") or book.get("unique_features", []))
        strengths   = _val(book.get("strengths", ""))
        auth        = book.get("author", {})
        died        = _val(auth.get("died") or auth.get("death", ""))
        school      = _val(auth.get("school") or auth.get("madhab", ""))

        if methodology:
            out = (
                f"{display} was authored by {author}"
                + (f" (d. {died})" if died else "")
                + (f", a scholar of the {school} school" if school else "")
                + f". {methodology}"
            )
            if features:
                out += f" Its distinctive features include: {features}."
            if strengths:
                out += f" It is particularly valued for: {strengths}."
            pairs.append(_pair(
                f"What is {display} and what is its methodology?",
                out,
                f"tafsir_books.json/{key}",
            ))

        # Famous commentary pairs — fields differ per book
        for commentary in book.get("famous_commentaries", []):
            if not isinstance(commentary, dict):
                continue
            # Try various field name patterns the agent may have used
            surah = _val(
                commentary.get("surah_ayah") or commentary.get("surah") or
                commentary.get("verse") or commentary.get("ayah_ref", "")
            )
            expl = _val(
                commentary.get("ibn_kathir_commentary") or commentary.get("tabari_commentary") or
                commentary.get("qurtubi_commentary") or commentary.get("jalalayn_commentary") or
                commentary.get("qutb_commentary") or commentary.get("shafi_commentary") or
                commentary.get("commentary") or commentary.get("explanation") or
                commentary.get("key_insight", "")
            )
            topic = _val(commentary.get("topic") or commentary.get("subject", ""))
            if surah and expl:
                label = surah if surah else topic
                pairs.append(_pair(
                    f"What does {display} say about {label}?",
                    expl,
                    f"tafsir_books.json/{key}/famous_commentaries",
                ))

        # Notable quotes — may be list of strings or list of dicts
        for quote in (
            book.get("notable_quotes_from_tafsir") or
            book.get("notable_quotes") or []
        ):
            if isinstance(quote, str) and len(quote) > 20:
                pairs.append(_pair(
                    f"What is a notable quote from {display}?",
                    f'{author} in {display}: {quote}',
                    f"tafsir_books.json/{key}/quotes",
                ))
            elif isinstance(quote, dict):
                q_text = _val(quote.get("quote") or quote.get("text", ""))
                topic  = _val(quote.get("topic") or quote.get("context", ""))
                if q_text:
                    pairs.append(_pair(
                        f"What did {author} say about {topic or 'tafsir methodology'} in {display}?",
                        f'{author} in {display}: "{q_text}"',
                        f"tafsir_books.json/{key}/quotes",
                    ))

    # Comparative analysis
    for entry in data.get("comparative_analysis", []):
        if not isinstance(entry, dict):
            continue
        situation = _val(entry.get("situation") or entry.get("topic") or entry.get("use_case", ""))
        recommend = _val(entry.get("recommended") or entry.get("recommendation", ""))
        reason    = _val(entry.get("reason") or entry.get("why", ""))
        if situation and recommend:
            out = f"For {situation}, {recommend} is recommended."
            if reason:
                out += f" {reason}"
            pairs.append(_pair(
                f"Which tafsir should I use for {situation}?",
                out,
                "tafsir_books.json/comparative_analysis",
            ))

    # Key tafsir concepts
    for entry in data.get("key_tafsir_concepts", []):
        concept = _val(entry.get("concept") or entry.get("name", ""))
        arabic  = _val(entry.get("arabic", ""))
        defn    = _val(entry.get("definition") or entry.get("description", ""))
        ex      = _val(entry.get("example") or entry.get("examples", ""))
        if concept and defn:
            full = f"{concept}" + (f" (Arabic: {arabic})" if arabic else "") + f": {defn}"
            if ex:
                full += f" Example: {ex}."
            pairs.append(_pair(
                f"What is {concept} in the science of tafsir?",
                full,
                "tafsir_books.json/key_tafsir_concepts",
            ))

    return pairs

# ─── Fiqh Books ───────────────────────────────────────────────────────────────

_FIQH_MADHAB_KEYS = [
    ("hanafi_books",  "Hanafi"),
    ("maliki_books",  "Maliki"),
    ("shafii_books",  "Shafi'i"),
    ("hanbali_books", "Hanbali"),
]

def _fiqh_book_pairs(data: dict, madhab: str, book_key: str, book: dict) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    display = _val(book.get("full_title") or book.get("title") or book_key.replace("_", " ").title())
    auth    = book.get("author", {})
    died    = _val(auth.get("died") or auth.get("death", ""))
    overview = _val(book.get("overview") or book.get("description", ""))
    methodology = _val(book.get("methodology", ""))
    topics  = _val(book.get("topics_covered") or book.get("chapters", []))

    if overview or methodology:
        out = f"{display} is a foundational {madhab} fiqh text"
        if died:
            out += f" compiled by {_val(auth.get('name',''))} (d. {died})"
        out += "."
        if overview:
            out += f" {overview}"
        if methodology:
            out += f" Its methodology: {methodology}"
        if topics:
            out += f" Topics covered include: {topics}."
        pairs.append(_pair(
            f"What is {display} in {madhab} fiqh?",
            out,
            f"fiqh_books.json/{madhab}/{book_key}",
        ))

    # Sample rulings — values can be str, list[str], or dict
    rulings = book.get("sample_rulings") or book.get("rulings") or {}
    if isinstance(rulings, dict):
        for topic, ruling in rulings.items():
            r_text = _val(ruling)
            if r_text and topic not in ("title", "author", "madhab"):
                pairs.append(_pair(
                    f"What is the {madhab} ruling on {topic.replace('_',' ')} according to {display}?",
                    f"According to {display} ({madhab} school): {r_text}",
                    f"fiqh_books.json/{madhab}/{book_key}/rulings",
                ))
    elif isinstance(rulings, list):
        for ruling in rulings:
            if isinstance(ruling, dict):
                topic  = _val(ruling.get("topic") or ruling.get("chapter", ""))
                r_text = _val(ruling.get("ruling") or ruling.get("text", ""))
                if topic and r_text:
                    pairs.append(_pair(
                        f"What is the {madhab} ruling on {topic} according to {display}?",
                        r_text,
                        f"fiqh_books.json/{madhab}/{book_key}/rulings",
                    ))

    # Famous passages — may be list of strings or list of dicts
    for passage in book.get("famous_passages", []) or book.get("famous_quotes", []):
        if isinstance(passage, str) and len(passage) > 20:
            pairs.append(_pair(
                f"What is a famous passage from {display}?",
                f'{display}: "{passage}"',
                f"fiqh_books.json/{madhab}/{book_key}/passages",
            ))
        elif isinstance(passage, dict):
            topic = _val(passage.get("topic") or passage.get("subject", ""))
            text  = _val(passage.get("text") or passage.get("quote", ""))
            if text:
                pairs.append(_pair(
                    f"What does {display} state about {topic or 'Islamic law'}?",
                    f'{display}: "{text}"',
                    f"fiqh_books.json/{madhab}/{book_key}/passages",
                ))
    return pairs

def _fiqh_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "fiqh_books.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    for section_key, madhab in _FIQH_MADHAB_KEYS:
        section = data.get(section_key, {})
        if isinstance(section, dict):
            for book_key, book in section.items():
                if isinstance(book, dict):
                    pairs.extend(_fiqh_book_pairs(data, madhab, book_key, book))

    # Comparative rulings
    for ruling in data.get("comparative_rulings", []):
        issue = _val(ruling.get("issue") or ruling.get("topic", ""))
        if not issue:
            continue
        parts = []
        for m in ("Hanafi", "Maliki", "Shafi'i", "Hanbali"):
            key = m.lower().replace("'", "").replace(" ", "_")
            val = _val(ruling.get(key) or ruling.get(m, ""))
            if val:
                parts.append(f"• {m}: {val}")
        if parts:
            pairs.append(_pair(
                f"How do the four madhabs differ on {issue}?",
                f"The ruling on {issue} differs across the four schools:\n" + "\n".join(parts),
                "fiqh_books.json/comparative_rulings",
            ))

    # Usul al-fiqh books
    for book in data.get("usul_al_fiqh_books", []):
        title  = _val(book.get("title") or book.get("name", ""))
        author = _val(book.get("author", ""))
        desc   = _val(book.get("description") or book.get("overview", ""))
        if title and desc:
            pairs.append(_pair(
                f"What is {title} and what does it cover?",
                f"{title}" + (f" by {author}" if author else "") + f": {desc}",
                "fiqh_books.json/usul_al_fiqh_books",
            ))

    return pairs

# ─── Aqeedah Books ────────────────────────────────────────────────────────────

def _aqeedah_book_pairs(data: dict) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for book in data.get("classical_aqeedah_books", []):
        title  = _val(book.get("title") or book.get("name", ""))
        author = _val(book.get("author", ""))
        died   = _val(book.get("died") or book.get("death", ""))
        school = _val(book.get("theological_school") or book.get("school", ""))
        key_doc = _val(book.get("key_doctrines") or book.get("doctrines", []))
        overview = _val(book.get("overview") or book.get("description", ""))
        famous  = _val(book.get("famous_passages") or book.get("key_statements", []))

        if title and overview:
            out = f"{title}"
            if author:
                out += f" by {author}"
            if died:
                out += f" (d. {died})"
            if school:
                out += f", represents the {school} theological tradition"
            out += f". {overview}"
            if key_doc:
                out += f" Key doctrines: {key_doc}."
            pairs.append(_pair(
                f"What is {title} and what theological positions does it establish?",
                out,
                f"aqeedah_books.json/classical_aqeedah_books",
            ))

        if famous:
            pairs.append(_pair(
                f"What are some notable statements from {title}?",
                famous,
                f"aqeedah_books.json/classical_aqeedah_books",
            ))

    # Three schools
    schools = data.get("three_sunni_theological_schools", {})
    if isinstance(schools, dict):
        for school_key, school_data in schools.items():
            if not isinstance(school_data, dict):
                continue
            name = _val(school_data.get("name") or school_key)
            founders = _val(school_data.get("founders") or school_data.get("founder", ""))
            method = _val(school_data.get("methodology") or school_data.get("approach", ""))
            if name and method:
                pairs.append(_pair(
                    f"What is the {name} theological school in Islam and what is its methodology?",
                    f"The {name} school" + (f", founded by {founders}" if founders else "") + f": {method}",
                    "aqeedah_books.json/theological_schools",
                ))
    elif isinstance(schools, list):
        for school_data in schools:
            name = _val(school_data.get("name", ""))
            method = _val(school_data.get("methodology") or school_data.get("approach", ""))
            founders = _val(school_data.get("founders") or school_data.get("founder", ""))
            if name and method:
                pairs.append(_pair(
                    f"What is the {name} theological school in Islam?",
                    f"The {name} school" + (f", founded by {founders}" if founders else "") + f": {method}",
                    "aqeedah_books.json/theological_schools",
                ))

    # Key aqeedah topics
    topics = data.get("key_aqeedah_topics", {})
    if isinstance(topics, dict):
        items = topics.items()
    elif isinstance(topics, list):
        items = [(t.get("topic", ""), t) for t in topics if isinstance(t, dict)]
    else:
        items = []

    for topic_key, topic_data in items:
        if isinstance(topic_data, dict):
            name    = _val(topic_data.get("name") or topic_key)
            defn    = _val(topic_data.get("definition") or topic_data.get("description") or topic_data.get("overview", ""))
            dalil   = _val(topic_data.get("evidence") or topic_data.get("dalil", ""))
            khilaf  = _val(topic_data.get("scholarly_positions") or topic_data.get("positions", ""))
            if name and defn:
                out = defn
                if dalil:
                    out += f" Evidence: {dalil}."
                if khilaf:
                    out += f" Scholarly positions: {khilaf}."
                pairs.append(_pair(
                    f"What is the Islamic aqeedah position on {name}?",
                    out,
                    f"aqeedah_books.json/key_aqeedah_topics/{topic_key}",
                ))

    # Sample Q&A pairs already in file
    for qa in data.get("qa_sample_pairs", []):
        q = _val(qa.get("question") or qa.get("q", ""))
        a = _val(qa.get("answer") or qa.get("a", ""))
        if q and a:
            pairs.append(_pair(q, a, "aqeedah_books.json/qa_sample_pairs"))

    return pairs

def _aqeedah_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "aqeedah_books.json")
    return _aqeedah_book_pairs(data) if data else []

# ─── Seerah Books ─────────────────────────────────────────────────────────────

def _seerah_books_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "seerah_books.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Per-book pairs
    for book in data.get("seerah_books", []):
        if not isinstance(book, dict):
            continue
        title   = _val(book.get("title") or book.get("name") or book.get("full_title", ""))
        author  = _val(book.get("author", ""))
        died    = _val(book.get("date") or book.get("died") or book.get("death", ""))
        scope   = _val(book.get("scope") or book.get("overview") or book.get("description") or book.get("importance", ""))
        method  = _val(book.get("methodology", ""))
        features = _val(book.get("key_features") or book.get("key_events_covered") or book.get("features", []))
        if title and scope:
            out = f"{title}"
            if author:
                out += f" by {author}"
            if died:
                out += f" (d. {died})"
            out += f": {scope}"
            if method:
                out += f" Methodology: {method}."
            if features:
                out += f" Key features: {features}."
            pairs.append(_pair(
                f"What is {title} and why is it important in Islamic seerah?",
                out,
                "seerah_books.json/seerah_books",
            ))

    # Chronological events
    for event in data.get("seerah_chronological_events", []):
        if not isinstance(event, dict):
            continue
        period = _val(event.get("period") or event.get("phase", ""))
        details = _val(event.get("key_events") or event.get("details") or event.get("summary", ""))
        lessons = _val(event.get("lessons") or event.get("significance", ""))
        if period and details:
            out = details
            if lessons:
                out += f" Lessons: {lessons}"
            pairs.append(_pair(
                f"What happened during {period} of the Prophet's ﷺ life?",
                out,
                "seerah_books.json/chronological_events",
            ))

    # Major battles
    for battle in data.get("major_battles", []):
        if not isinstance(battle, dict):
            continue
        name    = _val(battle.get("name") or battle.get("battle", ""))
        year    = _val(battle.get("year") or battle.get("date", ""))
        bg      = _val(battle.get("background") or battle.get("cause", ""))
        events  = _val(battle.get("key_events") or battle.get("what_happened", ""))
        lessons = _val(battle.get("lessons") or battle.get("significance", ""))
        quran_  = _val(battle.get("quran_reference") or battle.get("quranic_reference", ""))
        if name:
            out = bg or events or ""
            if events and bg:
                out = f"{bg} {events}"
            if lessons:
                out += f" Key lessons: {lessons}."
            if quran_:
                out += f" Quranic reference: {quran_}."
            if out:
                pairs.append(_pair(
                    f"What happened at the Battle of {name}" + (f" ({year})" if year else "") + "?",
                    out,
                    "seerah_books.json/major_battles",
                ))

    # Companion profiles — can be dict of lists, list of dicts, etc.
    companions = data.get("key_companions", {})
    if isinstance(companions, dict):
        for val in companions.values():
            if isinstance(val, list):
                for c in val:
                    if isinstance(c, dict):
                        _add_companion_pair(pairs, c)
            elif isinstance(val, dict):
                _add_companion_pair(pairs, val)
            # skip string values (e.g. section titles)
    elif isinstance(companions, list):
        for comp in companions:
            if isinstance(comp, dict):
                _add_companion_pair(pairs, comp)

    # QA sample pairs
    for qa in data.get("qa_sample_pairs", []):
        q = _val(qa.get("question") or qa.get("q", ""))
        a = _val(qa.get("answer") or qa.get("a", ""))
        if q and a:
            pairs.append(_pair(q, a, "seerah_books.json/qa_sample_pairs"))

    return pairs

def _add_companion_pair(pairs: list, comp: dict) -> None:
    name = _val(comp.get("name", ""))
    bio  = _val(comp.get("biography") or comp.get("description") or comp.get("role", ""))
    known = _val(comp.get("known_for") or comp.get("significance", ""))
    if name and (bio or known):
        out = bio or ""
        if known:
            out += f" Known for: {known}."
        pairs.append(_pair(
            f"Who was {name} RA and what was their role in early Islam?",
            out,
            "seerah_books.json/key_companions",
        ))

# ─── Ihya & General Books ─────────────────────────────────────────────────────

def _ihya_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "ihya_and_general_books.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Ihya quarters
    ihya = data.get("ihya_ulum_al_din", {})
    if ihya:
        overview = _val(ihya.get("overview", ""))
        if overview:
            pairs.append(_pair(
                "What is Ihya Ulum al-Din by Imam Ghazali and what does it cover?",
                overview,
                "ihya_and_general_books.json/ihya_overview",
            ))

        quarter_map = {
            "quarter_1": "acts of worship (Ibadat)",
            "quarter_2": "everyday customs (Adat)",
            "quarter_3": "destructive vices (Muhlikat)",
            "quarter_4": "saving virtues (Munjiyat)",
        }
        for q_key, q_name in quarter_map.items():
            for chapter in ihya.get(q_key, []):
                ch_name = _val(chapter.get("chapter") or chapter.get("title", ""))
                teaching = _val(chapter.get("key_teaching") or chapter.get("summary", ""))
                quote    = _val(chapter.get("famous_quote") or chapter.get("quote", ""))
                if ch_name and teaching:
                    out = f"In the quarter on {q_name}, Imam Ghazali RH teaches: {teaching}"
                    if quote:
                        out += f' He wrote: "{quote}"'
                    pairs.append(_pair(
                        f"What does Imam Ghazali RH say about {ch_name} in Ihya Ulum al-Din?",
                        out,
                        f"ihya_and_general_books.json/ihya/{q_key}",
                    ))

    # Riyad as-Salihin hadiths
    riyad = data.get("riyad_as_salihin", {})
    for h in riyad.get("hadiths", []):
        num    = h.get("number", "")
        text   = _val(h.get("text", ""))
        source = _val(h.get("source", ""))
        lesson = _val(h.get("lesson", ""))
        if text and lesson:
            pairs.append(_pair(
                f"What is Hadith {num} in Riyad as-Salihin about?",
                f"{text}" + (f" — {source}" if source else "") + (f". Lesson: {lesson}" if lesson else ""),
                "ihya_and_general_books.json/riyad_as_salihin",
            ))

    # Bulugh al-Maram hadiths
    bulugh = data.get("bulugh_al_maram", {})
    for h in bulugh.get("hadiths", []):
        topic  = _val(h.get("topic", ""))
        text   = _val(h.get("text", ""))
        source = _val(h.get("source", ""))
        lesson = _val(h.get("lesson", ""))
        if topic and text:
            pairs.append(_pair(
                f"What does Bulugh al-Maram say about {topic}?",
                f"{text}" + (f" ({source})" if source else "") + (f". {lesson}" if lesson else ""),
                "ihya_and_general_books.json/bulugh_al_maram",
            ))

    # Mishkat al-Masabih
    mishkat = data.get("mishkat_al_masabih", {})
    overview = _val(mishkat.get("overview") or mishkat.get("description", ""))
    if overview:
        pairs.append(_pair(
            "What is Mishkat al-Masabih and how is it used in Islamic education?",
            overview,
            "ihya_and_general_books.json/mishkat_al_masabih",
        ))

    # Muqaddimah Ibn Khaldun
    muq = data.get("muqaddimah_ibn_khaldun", {})
    for concept in muq.get("key_concepts", []) or []:
        name = _val(concept.get("concept") or concept.get("name", ""))
        expl = _val(concept.get("explanation") or concept.get("description", ""))
        if name and expl:
            pairs.append(_pair(
                f"What is Ibn Khaldun's concept of {name}?",
                expl,
                "ihya_and_general_books.json/muqaddimah/concepts",
            ))
    overview_muq = _val(muq.get("overview") or muq.get("description", ""))
    if overview_muq:
        pairs.append(_pair(
            "What is the Muqaddimah of Ibn Khaldun and why is it significant?",
            overview_muq,
            "ihya_and_general_books.json/muqaddimah",
        ))

    return pairs

# ─── Musnad Ahmad & Darimi ────────────────────────────────────────────────────

def _musnad_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "musnad_and_darimi.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    book_map = [
        ("musnad_ahmad",      "Musnad Ahmad",        "Imam Ahmad ibn Hanbal RH"),
        ("sunan_al_darimi",   "Sunan al-Darimi",     "Imam al-Darimi RH"),
        ("sahih_ibn_hibban",  "Sahih Ibn Hibban",    "Ibn Hibban RH"),
        ("mustadrak_al_hakim","Mustadrak al-Hakim",  "Imam al-Hakim RH"),
    ]

    for key, display, author in book_map:
        book = data.get(key, {})
        if not book:
            continue

        overview    = _val(book.get("overview") or book.get("description", ""))
        methodology = _val(book.get("methodology", ""))
        auth        = book.get("author", {})
        died        = _val(auth.get("died") or auth.get("death", ""))

        if overview:
            out = f"{display}"
            if died:
                out += f" (d. {died})"
            out += f" by {author}: {overview}"
            if methodology:
                out += f" Methodology: {methodology}."
            pairs.append(_pair(
                f"What is the {display} and what makes it significant?",
                out,
                f"musnad_and_darimi.json/{key}/overview",
            ))

        for h in book.get("hadiths", []):
            narrator = _val(h.get("narrator", ""))
            text     = _val(h.get("text", ""))
            grade    = _val(h.get("grade", ""))
            topic    = _val(h.get("topic") or h.get("subject", ""))
            num      = h.get("number_approx") or h.get("number", "")
            if text and topic:
                source_str = f"{display}" + (f" #{num}" if num else "") + (f" ({grade})" if grade else "")
                pairs.append(_pair(
                    f"What does {display} say about {topic}?",
                    (f"Narrated by {narrator} RA: " if narrator else "") + text + f" — {source_str}",
                    f"musnad_and_darimi.json/{key}/hadiths",
                ))

    return pairs

# ─── Master function ──────────────────────────────────────────────────────────

def generate_books_kb_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    """Return all Q&A pairs from the 6 classical Islamic books KB files."""
    all_pairs: list[dict[str, Any]] = []

    generators = [
        ("Tafsir books",          _tafsir_pairs),
        ("Fiqh books",            _fiqh_pairs),
        ("Aqeedah books",         _aqeedah_pairs),
        ("Seerah books",          _seerah_books_pairs),
        ("Ihya & general books",  _ihya_pairs),
        ("Musnad & Darimi",       _musnad_pairs),
    ]

    for name, fn in generators:
        try:
            pairs = fn(kb_dir)
            logger.info("%-35s → %d pairs", name, len(pairs))
            all_pairs.extend(pairs)
        except Exception as exc:
            logger.warning("%s failed: %s", name, exc)

    return all_pairs
