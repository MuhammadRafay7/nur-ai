#!/usr/bin/env python3
"""
Generate Q&A training pairs from the 20 new knowledge base JSON files.

Handles: seerah, taharah, akhlaq, scholars, heart diseases, halal/haram food,
comparative religion, Islamic history, Quran stories, death/funeral, rights,
Islamic finance, new Muslim guide, Islamic psychology, tafsir key surahs,
Juz Amma tafsir, Islamic governance, Quran Arabic vocab, Islamic civilization,
battles seerah.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_new_kb")

# ─── Question rewriting ────────────────────────────────────────────────────────

# Strips the leading question word/phrase and returns the remainder, optionally
# inserting a bridge word so that prefix + remainder reads naturally.
_STRIP_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^What\s+(is|are|does|do|was|were|will|would|can|should)\s+", re.I), ""),
    (re.compile(r"^How\s+(do\s+I|do\s+we|does\s+one|can\s+I|can\s+we|can\s+one|should\s+I|should\s+we|do\s+Muslims)\s+", re.I), "how to "),
    (re.compile(r"^How\s+(is|are|was|were)\s+", re.I), ""),
    (re.compile(r"^Who\s+(is|are|was|were|will|would)\s+", re.I), ""),
    (re.compile(r"^Why\s+(is|are|does|do|did|was|were|should|would)\s+", re.I), "why "),
    (re.compile(r"^When\s+(is|are|does|do|did|was|were)\s+", re.I), "when "),
    (re.compile(r"^Which\s+(is|are|does|do|was|were)\s+", re.I), ""),
    (re.compile(r"^Is\s+(it|there|the|this|that|a|an)\s+", re.I), ""),
    (re.compile(r"^Are\s+(there|the|these|those)\s+", re.I), ""),
    (re.compile(r"^Can\s+(you|I|we|one|Muslims)\s+", re.I), ""),
]


def _rewrite_instruction(instr: str, prefix: str) -> str:
    """Rewrite a question naturally: strip its opener then prepend the new prefix."""
    if not instr:
        return instr
    for pattern, bridge in _STRIP_PATTERNS:
        m = pattern.match(instr)
        if m:
            remainder = bridge + instr[m.end():]
            if remainder:
                return prefix + remainder[0].lower() + remainder[1:]
    # Fallback: lowercase first char only
    return prefix + instr[0].lower() + instr[1:]


# ─── Question augmentation templates ──────────────────────────────────────────

_SEERAH_ALT_PREFIXES = [
    "Describe ", "Give me a detailed account of ", "Summarize the event of ",
    "In the Seerah of the Prophet ﷺ, what do we know about ",
    "From Islamic history, explain ", "What can you tell me about ",
]

_FIQH_ALT_PREFIXES = [
    "According to Islamic jurisprudence, explain ",
    "In Islam, what is the ruling regarding ",
    "What does the Sharia say about ",
    "Explain the Islamic ruling on ",
    "From a fiqh perspective, describe ",
]

_AKHLAQ_ALT_PREFIXES = [
    "From an Islamic perspective, tell me about ",
    "Explain the Islamic teaching on ",
    "What does Islam teach about ",
    "Explain the virtue of ",
    "In the Quran and Sunnah, what is said about ",
]

_GENERAL_ALT_PREFIXES = [
    "Can you explain ",
    "Please describe ",
    "In Islamic teaching, tell me about ",
    "What does Islam say about ",
    "Provide an overview of ",
]


def _augment(pairs: list[dict[str, Any]], category: str, max_per_pair: int = 2) -> list[dict[str, Any]]:
    """Generate alternative-phrasing variants for each pair to boost count."""
    if category in ("seerah",):
        alt_prefixes = _SEERAH_ALT_PREFIXES
    elif category in ("taharah", "halal_haram_food", "death_funeral", "rights_in_islam", "islamic_finance"):
        alt_prefixes = _FIQH_ALT_PREFIXES
    elif category in ("akhlaq", "diseases_of_heart", "islamic_psychology"):
        alt_prefixes = _AKHLAQ_ALT_PREFIXES
    else:
        alt_prefixes = _GENERAL_ALT_PREFIXES

    augmented: list[dict[str, Any]] = []
    for pair in pairs:
        instr = pair["instruction"]
        output = pair["output"]
        cat = pair["metadata"]["category"]
        diff = pair["metadata"]["difficulty"]
        sources = pair["metadata"]["sources"]

        if len(output) < 100:
            continue

        for prefix in alt_prefixes[:max_per_pair]:
            new_instr = _rewrite_instruction(instr, prefix)
            if new_instr and new_instr != instr:
                augmented.append(_pair(new_instr, output, cat, sources, diff))

    return augmented


# ─── Helper ────────────────────────────────────────────────────────────────────

def _pair(instruction: str, output: str, category: str,
          sources: list[str] | None = None, difficulty: str = "intermediate") -> dict[str, Any]:
    return {
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip(),
        "metadata": {
            "category": category,
            "sources": sources or [],
            "difficulty": difficulty,
        },
    }


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


# ─── Seerah al-Nabawiyyah ──────────────────────────────────────────────────────

def _gen_seerah(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "seerah_nabawiyyah.json")
    pairs: list[dict[str, Any]] = []
    events = data.get("events", [])
    for ev in events:
        title = ev.get("title", "")
        year = ev.get("year", "")
        location = ev.get("location", "")
        desc = ev.get("description", "")
        figures = ev.get("key_figures", [])
        qrefs = ev.get("quran_references", [])
        hrefs = ev.get("hadith_references", [])
        lessons = ev.get("lessons", [])
        if not title or not desc:
            continue

        quran_str = ", ".join(qrefs) if qrefs else ""
        hadith_str = ""
        if hrefs:
            h = hrefs[0]
            hadith_str = f"\n\n{h.get('text','')}\n(Source: {h.get('source','')}{', ' + h.get('number','') if h.get('number') else ''} — Grade: {h.get('grade','')})"
        figures_str = "\n".join(f"• {f}" for f in figures) if figures else ""
        lessons_str = "\n".join(f"• {l}" for l in lessons) if lessons else ""
        quran_section = f"\n\nQuranic References: {quran_str}" if quran_str else ""

        # Q1: What happened?
        pairs.append(_pair(
            f"What happened during {title} in the life of Prophet Muhammad ﷺ?",
            f"**{title}** ({year})\n\n{desc}{quran_section}{hadith_str}"
            + (f"\n\nKey Figures:\n{figures_str}" if figures_str else ""),
            "seerah", difficulty="intermediate"
        ))
        # Q2: When and where?
        if year and location:
            pairs.append(_pair(
                f"When and where did {title} occur in the Seerah of the Prophet ﷺ?",
                f"**{title}** took place in **{year}** at **{location}**.\n\n{desc[:400]}{'...' if len(desc) > 400 else ''}",
                "seerah", difficulty="basic"
            ))
        # Q3: Who were the key figures?
        if figures:
            pairs.append(_pair(
                f"Who were the key figures involved in {title}?",
                f"The key figures in **{title}** ({year}) were:\n\n{figures_str}\n\n{desc[:300]}{'...' if len(desc) > 300 else ''}",
                "seerah", difficulty="basic"
            ))
        # Q4: Lessons
        if lessons:
            pairs.append(_pair(
                f"What Islamic lessons can we learn from {title} in the Prophet's ﷺ biography?",
                f"**Lessons from {title}** ({year}):\n\n{lessons_str}\n\nContext: {desc[:300]}{'...' if len(desc) > 300 else ''}",
                "seerah", difficulty="advanced"
            ))
        # Q5: Quran reference
        if quran_str:
            pairs.append(_pair(
                f"What Quranic verses relate to {title} in the Seerah?",
                f"The following Quranic references relate to **{title}**:\n\n{quran_str}\n\n{desc[:400]}{'...' if len(desc) > 400 else ''}{hadith_str}",
                "seerah", difficulty="advanced"
            ))
        # Q6: Hadith evidence
        if hrefs and len(hrefs) > 0:
            h = hrefs[0]
            hadith_text = h.get('text','')
            hadith_source = h.get('source','')
            if hadith_text:
                pairs.append(_pair(
                    f"What hadith evidence exists about {title} in the Prophet's ﷺ biography?",
                    f"**Hadith Evidence for {title}** ({year}):\n\n{hadith_text}\n(Source: {hadith_source}, Grade: {h.get('grade','')})\n\nContext: {desc[:300]}{'...' if len(desc) > 300 else ''}",
                    "seerah", difficulty="advanced"
                ))
        # Q7: Summary/contextual
        if location:
            pairs.append(_pair(
                f"What was the significance of {title} for the early Muslim community?",
                f"**Significance of {title}** ({year}, {location}):\n\n{desc}"
                + (f"\n\nLessons:\n{lessons_str}" if lessons_str else ""),
                "seerah", difficulty="intermediate"
            ))
    return pairs


# ─── Taharah Fiqh ──────────────────────────────────────────────────────────────

def _gen_taharah(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "taharah_fiqh.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    # Wudu sunnah acts
    wudu_sunnahs = data.get("wudu", {}).get("sunnahs", [])
    if wudu_sunnahs:
        sunnahs_str = "\n".join(f"• {s}" for s in wudu_sunnahs)
        pairs.append(_pair(
            "What are the sunnah acts of wudu that increase its reward?",
            f"**Sunnah Acts of Wudu** (recommended but not obligatory):\n\n{sunnahs_str}\n\nOmitting these does not invalidate the wudu, but performing them earns extra reward.",
            "taharah", difficulty="basic"
        ))

    # General wudu overview
    wudu_overview = data.get("wudu", {})
    fard_acts = wudu_overview.get("fard_acts", [])
    if fard_acts:
        fard_list = "\n".join(f"• {a.get('act','')} ({a.get('arabic','')})" for a in fard_acts if isinstance(a, dict))
        pairs.append(_pair(
            "What are all the fard (obligatory) acts of wudu that must be performed?",
            f"**Fard Acts of Wudu** — These are obligatory; omitting any one invalidates the wudu:\n\n{fard_list}",
            "taharah", difficulty="basic"
        ))

    # Wudu fard acts
    wudu = data.get("wudu", {})
    for act_data in wudu.get("fard_acts", []):
        act = act_data.get("act", "")
        arabic = act_data.get("arabic", "")
        detail = act_data.get("detail", "")
        evidence = act_data.get("evidence", "")
        if not act:
            continue
        pairs.append(_pair(
            f"Is {act} a fard (obligatory) act of wudu in Islam?",
            f"Yes, **{act}** ({arabic}) is a **fard (obligatory)** act of wudu.\n\n{detail}\n\nEvidence: {evidence}",
            "taharah", difficulty="intermediate"
        ))
        # Additional variant
        pairs.append(_pair(
            f"Explain the wudu act of {act} ({arabic}) in detail.",
            f"**{act}** ({arabic}) — Obligatory Wudu Act:\n\n{detail}\n\nEvidence: {evidence}",
            "taharah", difficulty="intermediate"
        ))

    # Wudu nullifiers
    for null_data in wudu.get("nullifiers", []):
        nullifier = null_data.get("nullifier", "")
        detail = null_data.get("detail", "")
        evidence = null_data.get("evidence", "")
        if not nullifier:
            continue
        answer = f"**{nullifier}** is one of the nullifiers of wudu.\n\n"
        if detail:
            answer += f"{detail}\n\n"
        if evidence:
            answer += f"Evidence: {evidence}"
        pairs.append(_pair(
            f"Does {nullifier.lower()} break wudu in Islam?",
            answer.strip(),
            "taharah", difficulty="intermediate"
        ))

    # Ghusl causes
    ghusl = data.get("ghusl", {})
    for cause_data in ghusl.get("obligatory_causes", []):
        cause = cause_data.get("cause", "")
        arabic = cause_data.get("arabic", "")
        evidence = cause_data.get("evidence", "")
        if not cause:
            continue
        pairs.append(_pair(
            f"Does {cause.lower()} make ghusl obligatory in Islam?",
            f"Yes, **{cause}** ({arabic}) makes ghusl (ritual bath) **obligatory (fard)**.\n\nEvidence: {evidence}",
            "taharah", difficulty="intermediate"
        ))

    # Ghusl method
    sunnah_method = ghusl.get("sunnah_method", [])
    if sunnah_method:
        method_str = "\n".join(sunnah_method)
        pairs.append(_pair(
            "What is the correct sunnah method for performing ghusl (ritual bath) in Islam?",
            f"The complete sunnah method for ghusl is:\n\n{method_str}\n\nThe fard (minimum obligatory) acts are: intention, covering entire body with water, removing anything preventing water reaching skin.",
            "taharah", difficulty="intermediate"
        ))

    # Tayammum
    tayammum = data.get("tayammum", {})
    conditions = tayammum.get("conditions", [])
    method = tayammum.get("method", [])
    evidence = tayammum.get("evidence", "")
    if conditions:
        cond_str = "\n".join(f"• {c}" for c in conditions)
        method_str = "\n".join(method) if method else ""
        pairs.append(_pair(
            "When is tayammum (dry ablution) permissible in Islam and how is it performed?",
            f"**Tayammum** is permitted when:\n\n{cond_str}\n\n**Method:**\n{method_str}\n\nEvidence: {evidence}",
            "taharah", difficulty="intermediate"
        ))

    # Ghusl fard acts
    ghusl_fard = ghusl.get("fard_acts", [])
    if ghusl_fard:
        fard_str = "\n".join(f"• {a}" for a in ghusl_fard)
        pairs.append(_pair(
            "What are the minimum obligatory (fard) acts for a valid ghusl in Islam?",
            f"**Minimum Fard Acts of Ghusl:**\n\n{fard_str}\n\nIf these three are performed, the ghusl is valid even without the full sunnah method.",
            "taharah", difficulty="basic"
        ))

    # Tayammum nullifiers
    tayammum_nullifiers = tayammum.get("nullifiers", [])
    if tayammum_nullifiers:
        nullifiers_str = "\n".join(f"• {n}" for n in tayammum_nullifiers)
        pairs.append(_pair(
            "What nullifies tayammum (dry ablution) in Islam?",
            f"**Nullifiers of Tayammum:**\n\n{nullifiers_str}",
            "taharah", difficulty="intermediate"
        ))

    # Najasah tahir items
    najasah = data.get("najasah", {})
    tahir = najasah.get("tahir_items", [])
    if tahir:
        tahir_str = "\n".join(f"• {t}" for t in tahir)
        pairs.append(_pair(
            "What substances are considered tahir (pure) in Islam despite common misconceptions?",
            f"**Tahir (Ritually Pure) Substances:**\n\n{tahir_str}\n\nThese do not require ritual purification even if they come into contact with the body or clothing.",
            "taharah", difficulty="basic"
        ))

    # Light impurities
    light_imp = najasah.get("light_impurities", [])
    for item_data in light_imp:
        item = item_data.get("item", "")
        ruling = item_data.get("ruling", "")
        evidence = item_data.get("evidence", "")
        if item:
            pairs.append(_pair(
                f"What is the ruling on {item.lower()} — how is it treated as najasah?",
                f"**{item}** is classified as **light najasah (khafif)**.\n\nRuling: {ruling}\n\nEvidence: {evidence}",
                "taharah", difficulty="intermediate"
            ))

    # Najasah
    for item_data in najasah.get("heavy_impurities", []):
        item = item_data.get("item", "")
        ruling = item_data.get("ruling", "")
        method = item_data.get("method", "")
        evidence = item_data.get("evidence", "")
        if not item:
            continue
        answer = f"**{item}** is considered **najis (ritually impure)**.\n\nRuling: {ruling}\n"
        if method:
            answer += f"Method of purification: {method}\n"
        if evidence:
            answer += f"Evidence: {evidence}"
        pairs.append(_pair(
            f"Is {item.lower()} considered najis (impure) in Islam?",
            answer.strip(),
            "taharah", difficulty="basic"
        ))

    return pairs


# ─── Akhlaq / Ethics ───────────────────────────────────────────────────────────

def _gen_akhlaq(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "akhlaq_ethics.json")
    pairs: list[dict[str, Any]] = []
    for virtue in data.get("virtues", []):
        name = virtue.get("name", "")
        arabic = virtue.get("arabic", "")
        definition = virtue.get("definition", "")
        qevidence = virtue.get("quran_evidence", [])
        hevidence = virtue.get("hadith_evidence", [])
        practical = virtue.get("practical_application", [])
        opposite = virtue.get("opposite_vice", "")
        if not name or not definition:
            continue

        quran_str = ""
        if qevidence:
            q = qevidence[0]
            quran_str = f'\n\nQuran {q.get("ref","")}: "{q.get("text","")}"'
        hadith_str = ""
        if hevidence:
            h = hevidence[0]
            hadith_str = f'\n\n{h.get("text","")} ({h.get("source","")}{", " + h.get("number","") if h.get("number") else ""})'
        practical_str = "\n".join(f"• {p}" for p in practical) if practical else ""

        # Q1: Definition
        pairs.append(_pair(
            f"What is {name} ({arabic}) in Islam?",
            f"**{name}** ({arabic}) is a core Islamic virtue.\n\n{definition}{quran_str}{hadith_str}"
            + (f"\n\nPractical Application:\n{practical_str}" if practical_str else ""),
            "akhlaq", difficulty="basic"
        ))
        # Q2: Quran evidence
        if qevidence:
            all_quran = "\n".join(f'• {q.get("ref","")}: "{q.get("text","")}"' for q in qevidence)
            pairs.append(_pair(
                f"What does the Quran say about {name} ({arabic})?",
                f"The Quran emphasizes **{name}** ({arabic}) in multiple places:\n\n{all_quran}\n\n{definition}",
                "akhlaq", difficulty="intermediate"
            ))
        # Q3: Opposite vice
        if opposite:
            pairs.append(_pair(
                f"What is the opposite of {name} ({arabic}) in Islamic ethics?",
                f"The opposite of **{name}** is **{opposite}**.\n\n{name} is defined as: {definition}\n\nPractical ways to develop {name}:\n{practical_str}",
                "akhlaq", difficulty="basic"
            ))
        # Q4: How to develop
        if practical:
            pairs.append(_pair(
                f"How can a Muslim develop {name} ({arabic}) in their daily life?",
                f"**Practical ways to develop {name}** ({arabic}):\n\n{practical_str}\n\nThe Prophet ﷺ exemplified this virtue throughout his life. {hadith_str}",
                "akhlaq", difficulty="intermediate"
            ))
        # Q5: Hadith evidence
        if hevidence:
            all_hadith = "\n".join(
                f'• {h.get("text","")} ({h.get("source","")}{", " + h.get("number","") if h.get("number") else ""})'
                for h in hevidence
            )
            pairs.append(_pair(
                f"What hadith supports the importance of {name} ({arabic}) in Islam?",
                f"**Hadith Evidence for {name}** ({arabic}):\n\n{all_hadith}\n\nDefinition: {definition}",
                "akhlaq", difficulty="intermediate"
            ))
        # Q6: Islamic character
        pairs.append(_pair(
            f"Why is {name} ({arabic}) considered an essential part of Islamic character?",
            f"**{name}** ({arabic}) is essential to Islamic character because:\n\n{definition}"
            + (f"\n\n{quran_str}" if quran_str else "")
            + (f"\n\nPractical Application:\n{practical_str}" if practical_str else ""),
            "akhlaq", difficulty="basic"
        ))

    return pairs


# ─── Scholars Biographies ──────────────────────────────────────────────────────

def _gen_scholars(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "scholars_biographies.json")
    pairs: list[dict[str, Any]] = []
    for scholar in data.get("scholars", []):
        name = scholar.get("name", "")
        arabic = scholar.get("arabic", "")
        title = scholar.get("title", "")
        born = scholar.get("born", "")
        died = scholar.get("died", "")
        origin = scholar.get("origin", "")
        madhab = scholar.get("madhab", "")
        specialty = scholar.get("specialty", "")
        works = scholar.get("key_works", [])
        contributions = scholar.get("contributions", [])
        historical_note = scholar.get("historical_note", "")
        quote = scholar.get("quote", "")
        if not name:
            continue

        works_str = "\n".join(f"• {w}" for w in works) if works else ""
        contrib_str = "\n".join(f"• {c}" for c in contributions) if contributions else ""

        # Q1: Who was this scholar?
        pairs.append(_pair(
            f"Who was Imam {name} RH and what was his contribution to Islam?",
            f"**Imam {name} RH** ({arabic}){', known as ' + title if title else ''} was a major Islamic scholar.\n\n"
            f"Born: {born} | Died: {died} | Origin: {origin}\n"
            f"Specialty: {specialty}\n"
            + (f"Madhab: {madhab}\n" if madhab else "")
            + (f"\nMajor Works:\n{works_str}\n" if works_str else "")
            + (f"\nKey Contributions:\n{contrib_str}\n" if contrib_str else "")
            + (f"\n{historical_note}" if historical_note else ""),
            "scholars_biographies", difficulty="intermediate"
        ))
        # Q2: Key works
        if works:
            pairs.append(_pair(
                f"What are the major works/books written by Imam {name} RH?",
                f"**Imam {name} RH** ({born}–{died}) authored several landmark works:\n\n{works_str}\n\n{contrib_str}",
                "scholars_biographies", difficulty="intermediate"
            ))
        # Q3: Historical note
        if historical_note:
            pairs.append(_pair(
                f"What is notable about the life and trials of Imam {name} RH?",
                f"**Imam {name} RH** had a remarkable life:\n\n{historical_note}"
                + (f"\n\n{quote}" if quote else ""),
                "scholars_biographies", difficulty="advanced"
            ))
        # Q4: Which madhab?
        if madhab:
            pairs.append(_pair(
                f"Which madhab (school of jurisprudence) did Imam {name} RH found or represent?",
                f"**Imam {name} RH** was the founder/leading scholar of the **{madhab}** school of jurisprudence.\n\n"
                f"Born in {origin} ({born}–{died}), he specialized in {specialty}.\n\n{contrib_str}",
                "scholars_biographies", difficulty="basic"
            ))
        # Q5: Specialty
        if specialty:
            pairs.append(_pair(
                f"What was Imam {name} RH's area of expertise and specialty in Islamic sciences?",
                f"**Imam {name} RH** specialized in **{specialty}**.\n\n"
                f"Born: {born} | Died: {died} | Origin: {origin}\n\n"
                + (f"Major Contributions:\n{contrib_str}" if contrib_str else ""),
                "scholars_biographies", difficulty="intermediate"
            ))
        # Q6: Quote / wisdom
        if quote:
            pairs.append(_pair(
                f"What is a famous saying or wisdom from Imam {name} RH?",
                f"**Famous Saying of Imam {name} RH** ({born}–{died}):\n\n\"{quote}\"\n\n"
                f"Context: Imam {name} RH was a leading scholar of {specialty}.",
                "scholars_biographies", difficulty="intermediate"
            ))
    return pairs


# ─── Diseases of the Heart ─────────────────────────────────────────────────────

def _gen_heart_diseases(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "diseases_of_heart.json")
    pairs: list[dict[str, Any]] = []
    for disease in data.get("diseases", []):
        name = disease.get("name", "")
        arabic = disease.get("arabic", "")
        definition = disease.get("definition", "")
        symptoms = disease.get("symptoms", [])
        cure = disease.get("cure", [])
        qevidence = disease.get("quran_evidence", [])
        hevidence = disease.get("hadith_evidence", [])
        distinction = disease.get("distinction", "")
        if not name or not definition:
            continue

        symptoms_str = "\n".join(f"• {s}" for s in symptoms) if symptoms else ""
        cure_str = "\n".join(f"• {c}" for c in cure) if cure else ""
        quran_str = ""
        if qevidence:
            q = qevidence[0]
            quran_str = f'\nQuran {q.get("ref","")}: "{q.get("text","")}"'
        hadith_str = ""
        if hevidence:
            h = hevidence[0]
            hadith_str = f'\n{h.get("text","")} ({h.get("source","")})'

        # Q1: What is it?
        pairs.append(_pair(
            f"What is {name} ({arabic}) and why is it considered a spiritual disease in Islam?",
            f"**{name}** ({arabic}) is one of the major spiritual diseases of the heart.\n\n{definition}\n{quran_str}\n{hadith_str}"
            + (f"\n\nSymptoms:\n{symptoms_str}" if symptoms_str else ""),
            "diseases_of_heart", difficulty="intermediate"
        ))
        # Q2: Symptoms
        if symptoms:
            pairs.append(_pair(
                f"What are the signs and symptoms that a person has {name} ({arabic}) in their heart?",
                f"**Signs of {name}** ({arabic}) in the heart:\n\n{symptoms_str}\n\nDefinition: {definition}",
                "diseases_of_heart", difficulty="intermediate"
            ))
        # Q3: Cure
        if cure:
            pairs.append(_pair(
                f"How does a Muslim cure {name} ({arabic}) — what is the Islamic remedy?",
                f"**Remedies for {name}** ({arabic}):\n\n{cure_str}\n\n{definition}\n{hadith_str}"
                + (f"\n\n{distinction}" if distinction else ""),
                "diseases_of_heart", difficulty="advanced"
            ))
        # Q4: Distinction
        if distinction:
            pairs.append(_pair(
                f"What is the difference between {name} ({arabic}) and a similar concept in Islam?",
                f"**Important distinction regarding {name}** ({arabic}):\n\n{distinction}\n\nDefinition: {definition}",
                "diseases_of_heart", difficulty="advanced"
            ))
        # Q5: Quran evidence
        if qevidence:
            all_quran = "\n".join(
                f'• Quran {q.get("ref","")}: "{q.get("text","")}"' for q in qevidence
            )
            pairs.append(_pair(
                f"What does the Quran say about {name} ({arabic})?",
                f"**Quranic Evidence on {name}** ({arabic}):\n\n{all_quran}\n\nDefinition: {definition}",
                "diseases_of_heart", difficulty="intermediate"
            ))
        # Q6: How to recognize and cure
        if symptoms and cure:
            pairs.append(_pair(
                f"How do I know if I have {name} ({arabic}) and what should I do to cure it?",
                f"**{name}** ({arabic}) — Recognition and Treatment:\n\n"
                f"**Signs (Symptoms):**\n{symptoms_str}\n\n"
                f"**Islamic Treatment:**\n{cure_str}",
                "diseases_of_heart", difficulty="advanced"
            ))
    return pairs


# ─── Halal / Haram Food ────────────────────────────────────────────────────────

def _gen_halal_haram_food(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "halal_haram_food.json")
    pairs: list[dict[str, Any]] = []

    # General principles
    general = data.get("general_principles", [])
    if general:
        principles_str = "\n".join(f"• {p}" for p in general)
        pairs.append(_pair(
            "What are the general Islamic principles for determining halal and haram food?",
            f"**General Islamic Principles for Halal/Haram Food:**\n\n{principles_str}",
            "halal_haram_food", difficulty="basic"
        ))

    # Explicitly haram items
    for item_data in data.get("explicitly_haram", []):
        item = item_data.get("item", "")
        arabic = item_data.get("arabic", "")
        evidence = item_data.get("evidence", "")
        includes = item_data.get("includes", [])
        note = item_data.get("note", "")
        all_madhabs = item_data.get("all_madhabs", "")
        contemporary = item_data.get("contemporary", [])
        if not item:
            continue

        includes_str = "\n".join(f"• {i}" for i in includes) if includes else ""
        contemporary_str = "\n".join(f"• {c}" for c in contemporary) if contemporary else ""

        pairs.append(_pair(
            f"Why is {item.lower()} haram in Islam?",
            f"**{item}** ({arabic}) is explicitly **haram** in Islam.\n\nEvidence: {evidence}\n"
            + (f"\nThis includes:\n{includes_str}\n" if includes_str else "")
            + (f"\n{note}" if note else "")
            + (f"\n{all_madhabs}" if all_madhabs else "")
            + (f"\nContemporary issues:\n{contemporary_str}" if contemporary_str else ""),
            "halal_haram_food", difficulty="basic"
        ))

    # Seafood
    seafood = data.get("seafood", {})
    if seafood:
        ruling = seafood.get("ruling", "")
        hanafi = seafood.get("hanafi_position", "")
        evidence = seafood.get("evidence", "")
        pairs.append(_pair(
            "What is the Islamic ruling on seafood — is all seafood halal?",
            f"{ruling}\n\nHanafi position: {hanafi}\n\nEvidence: {evidence}",
            "halal_haram_food", difficulty="intermediate"
        ))

    # Gelatin
    gelatin = data.get("gelatin", {})
    if gelatin:
        from_pork = gelatin.get("from_pork", "")
        from_halal = gelatin.get("from_halal_slaughtered_animal", "")
        rec = gelatin.get("recommendation", "")
        pairs.append(_pair(
            "What is the Islamic ruling on gelatin — is gelatin halal or haram?",
            f"**Gelatin ruling depends on its source:**\n\n• From pork: {from_pork}\n• From halal-slaughtered animal: {from_halal}\n\n{rec}",
            "halal_haram_food", difficulty="intermediate"
        ))

    # E-numbers / additives
    additives = data.get("additives_e_numbers", [])
    if additives:
        additive_list = "\n".join(
            f"• **{a.get('code','')} ({a.get('name','')})**: Source: {a.get('source','')} — {a.get('ruling','')}"
            for a in additives
        )
        pairs.append(_pair(
            "What are the common halal/haram food additives and E-numbers Muslims should be aware of?",
            f"**Common food additives and their Islamic ruling:**\n\n{additive_list}\n\nAlways check for halal certification when in doubt.",
            "halal_haram_food", difficulty="advanced"
        ))

    # Contemporary questions
    for q_data in data.get("contemporary_questions", []):
        question = q_data.get("question", "")
        answer = q_data.get("answer", "")
        if question and answer:
            pairs.append(_pair(question, answer, "halal_haram_food", difficulty="intermediate"))

    return pairs


# ─── Comparative Religion & Da'wah ────────────────────────────────────────────

def _gen_comparative_religion(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "comparative_religion_dawah.json")
    pairs: list[dict[str, Any]] = []

    # Da'wah principles
    for principle_data in data.get("dawah_principles", []):
        principle = principle_data.get("principle", "")
        arabic = principle_data.get("arabic", "")
        application = principle_data.get("application", "")
        if principle and application:
            pairs.append(_pair(
                f"What is the Islamic principle of {principle.split('(')[0].strip()} in da'wah?",
                f"**{principle}**\n{arabic if arabic else ''}\n\n{application}",
                "comparative_religion", difficulty="intermediate"
            ))

    # Islam vs Christianity
    for topic_data in data.get("islam_vs_christianity", []):
        topic = topic_data.get("topic", "")
        islamic = topic_data.get("islamic_position", "")
        christian = topic_data.get("christian_position", "")
        quran = topic_data.get("quran_response", "")
        dawah = topic_data.get("dawah_approach", "")
        if not topic or not islamic:
            continue
        pairs.append(_pair(
            f"What is the Islamic perspective on {topic} compared to Christian belief?",
            f"**Islamic Position on {topic}:**\n\n{islamic}\n\n"
            + (f"Christian Position: {christian}\n\n" if christian else "")
            + (f"Quranic Response: {quran}\n\n" if quran else "")
            + (f"Da'wah Approach: {dawah}" if dawah else ""),
            "comparative_religion", difficulty="advanced"
        ))

    # Islam vs Atheism
    for topic_data in data.get("islam_vs_atheism", []):
        topic = topic_data.get("topic", "")
        argument = topic_data.get("argument", "")
        quran_ref = topic_data.get("quran_reference", "")
        response = topic_data.get("response_to_objection", "") or topic_data.get("dawah_note", "")
        if not topic or not argument:
            continue
        pairs.append(_pair(
            f"How does Islam respond to atheism regarding {topic.split('—')[0].strip()}?",
            f"**Islamic Response to Atheism: {topic}**\n\n{argument}\n\n"
            + (f"Quranic Support: {quran_ref}\n\n" if quran_ref else "")
            + (f"{response}" if response else ""),
            "comparative_religion", difficulty="advanced"
        ))

    # Common objections
    for obj_data in data.get("common_objections_to_islam", []):
        objection = obj_data.get("objection", "")
        response = obj_data.get("islamic_response", "")
        specific = obj_data.get("specific_refutals", [])
        historical = obj_data.get("historical_facts", [])
        if not objection or not response:
            continue
        extra = ""
        if specific:
            extra += "\n\n" + "\n".join(f"• {s}" for s in specific)
        if historical:
            extra += "\n\nHistorical Facts:\n" + "\n".join(f"• {h}" for h in historical)
        pairs.append(_pair(
            f"How do Muslims respond to the claim that '{objection}'?",
            f"**Islamic Response:**\n\n{response}{extra}",
            "comparative_religion", difficulty="advanced"
        ))
        # Second question variant
        pairs.append(_pair(
            f"What is the Islamic rebuttal to the objection: '{objection}'?",
            f"**Da'wah Response to: '{objection}'**\n\n{response}{extra}",
            "comparative_religion", difficulty="advanced"
        ))

    # Additional christianity variants
    for topic_data in data.get("islam_vs_christianity", []):
        topic = topic_data.get("topic", "")
        dawah = topic_data.get("dawah_approach", "")
        if topic and dawah:
            pairs.append(_pair(
                f"How should a Muslim approach the topic of {topic} when doing da'wah to Christians?",
                f"**Da'wah Approach for {topic}:**\n\n{dawah}",
                "comparative_religion", difficulty="advanced"
            ))

    return pairs


# ─── Islamic History ───────────────────────────────────────────────────────────

def _gen_islamic_history(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "islamic_history_timeline.json")
    pairs: list[dict[str, Any]] = []
    for period in data.get("periods", []):
        period_name = period.get("period", "")
        years = period.get("years", "")
        capital = period.get("capital", "")
        key_events = period.get("key_events", [])
        collapse = period.get("collapse", "")
        golden = period.get("golden_age", {})
        caliphs = period.get("caliphs", [])
        if not period_name:
            continue

        events_str = "\n".join(f"• {e}" for e in key_events) if key_events else ""

        pairs.append(_pair(
            f"What was the {period_name} and what were its major events?",
            f"**{period_name}** ({years})\n"
            + (f"Capital: {capital}\n" if capital else "")
            + (f"\nKey Events:\n{events_str}" if events_str else "")
            + (f"\n\n{collapse}" if collapse else ""),
            "islamic_history", difficulty="intermediate"
        ))

        # Individual caliphs
        for caliph in caliphs:
            caliph_name = caliph.get("name", "")
            reign = caliph.get("reign", "")
            caliph_events = caliph.get("key_events", [])
            character = caliph.get("character", "")
            martyrdom = caliph.get("martyrdom", "")
            if not caliph_name:
                continue
            caliph_events_str = "\n".join(f"• {e}" for e in caliph_events) if caliph_events else ""
            pairs.append(_pair(
                f"What were the major achievements and events during the caliphate of {caliph_name}?",
                f"**{caliph_name}** ruled from {reign}.\n\n"
                + (f"Key Achievements:\n{caliph_events_str}\n\n" if caliph_events_str else "")
                + (f"{character}\n\n" if character else "")
                + (f"{martyrdom}" if martyrdom else ""),
                "islamic_history", difficulty="intermediate"
            ))

        # Golden age
        if golden:
            achievements = golden.get("achievements", [])
            golden_years = golden.get("years", "")
            ach_str = "\n".join(f"• {a}" for a in achievements)
            pairs.append(_pair(
                f"What was the Islamic Golden Age during the {period_name}?",
                f"**Islamic Golden Age** ({golden_years})\n\nMajor Achievements:\n{ach_str}",
                "islamic_history", difficulty="intermediate"
            ))

        # Additional period questions
        if capital:
            pairs.append(_pair(
                f"What was the capital city of the {period_name} and what was its significance?",
                f"The capital of the **{period_name}** ({years}) was **{capital}**.\n\n"
                + (f"Key Events:\n{events_str}" if events_str else "")
                + (f"\n\n{collapse}" if collapse else ""),
                "islamic_history", difficulty="basic"
            ))
        if collapse:
            pairs.append(_pair(
                f"How did the {period_name} come to an end?",
                f"**Decline and Fall of the {period_name}** ({years}):\n\n{collapse}\n\n"
                + (f"Key Events during the period:\n{events_str}" if events_str else ""),
                "islamic_history", difficulty="intermediate"
            ))
    return pairs


# ─── Quran Stories ─────────────────────────────────────────────────────────────

def _gen_quran_stories(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "quran_stories.json")
    pairs: list[dict[str, Any]] = []
    for story in data.get("stories", []):
        prophet = story.get("prophet", "")
        surah = story.get("surah", "")
        description = story.get("allah_description", "") or story.get("mentioned_in_quran", "")
        key_events = story.get("key_events", [])
        themes = story.get("major_themes", [])
        title = story.get("title", "")
        status = story.get("status_in_islam", "")
        hadith = story.get("hadith", {})
        if not prophet:
            continue

        events_str = ""
        if key_events:
            for ev in key_events:
                if isinstance(ev, dict):
                    event = ev.get("event", "")
                    lesson = ev.get("lesson", "")
                    qref = ev.get("quran_ref", "")
                    if event:
                        events_str += f"• **{event}**"
                        if qref:
                            events_str += f" (Quran {qref})"
                        if lesson:
                            events_str += f"\n  Lesson: {lesson}"
                        events_str += "\n"
        themes_str = "\n".join(f"• {t}" for t in themes) if themes else ""
        hadith_str = ""
        if hadith and isinstance(hadith, dict):
            hadith_str = f'\n\nHadith: {hadith.get("text","")}\n({hadith.get("source","")}, {hadith.get("number","")})'

        # Q1: Story overview
        pairs.append(_pair(
            f"Tell me the story of Prophet {prophet} as mentioned in the Quran.",
            f"**The Story of Prophet {prophet}**\n"
            + (f"\n{description}\n" if description else "")
            + (f"\nSurah: {surah}\n" if surah else "")
            + (f"\n**Key Events:**\n{events_str}" if events_str else "")
            + (f"\n**Major Themes:**\n{themes_str}" if themes_str else "")
            + hadith_str,
            "quran_stories", difficulty="intermediate"
        ))
        # Q2: Themes/lessons
        if themes:
            pairs.append(_pair(
                f"What are the major themes and lessons from the story of Prophet {prophet} in the Quran?",
                f"**Themes in the Story of Prophet {prophet}:**\n\n{themes_str}\n\n{events_str}",
                "quran_stories", difficulty="advanced"
            ))
        # Q3: Status in Islam
        if status:
            pairs.append(_pair(
                f"What is the status and importance of Prophet {prophet} in Islam?",
                f"**Prophet {prophet} in Islam:**\n\n{status}"
                + (f"\n\n{description}" if description else ""),
                "quran_stories", difficulty="basic"
            ))
        # Q4: Hadith mentioning the prophet
        if hadith_str:
            pairs.append(_pair(
                f"What hadith mentions Prophet {prophet} and what does it tell us?",
                f"**Hadith about Prophet {prophet}:**\n\n{hadith_str}\n\n{description[:300] if description else ''}",
                "quran_stories", difficulty="intermediate"
            ))
        # Q5: Key event detail
        if events_str:
            pairs.append(_pair(
                f"What were the key miracles and events in the life of Prophet {prophet}?",
                f"**Key Events in the Life of Prophet {prophet}:**\n\n{events_str}"
                + (f"\n\n{themes_str}" if themes_str else ""),
                "quran_stories", difficulty="intermediate"
            ))
        # Q6: Surah/location in Quran
        if surah:
            pairs.append(_pair(
                f"In which Surah is the story of Prophet {prophet} mentioned in the Quran?",
                f"The story of Prophet {prophet} is mentioned in **{surah}**.\n\n{description[:400] if description else ''}"
                + hadith_str,
                "quran_stories", difficulty="basic"
            ))
    return pairs


# ─── Death and Funeral Rites ───────────────────────────────────────────────────

def _gen_death_funeral(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "death_funeral_rites.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    # At time of death
    at_death = data.get("at_time_of_death", {})
    if at_death:
        pairs.append(_pair(
            "What should Muslims do at the time of a person's death according to Islamic teachings?",
            f"**At the Time of Death — Islamic Guidance:**\n\n"
            f"**Talqin:** {at_death.get('talqin','')}\n\n"
            f"**Closing Eyes:** {at_death.get('closing_eyes','')}\n\n"
            f"**Covering:** {at_death.get('covering_body','')}\n\n"
            f"**Dua:** {at_death.get('dua_for_bereaved','')}",
            "death_funeral", difficulty="intermediate"
        ))

    # Ghusl al-mayyit
    ghusl = data.get("ghusl_al_mayyit", {})
    if ghusl:
        method = ghusl.get("method", [])
        method_str = "\n".join(method) if method else ""
        pairs.append(_pair(
            "How is ghusl al-mayyit (ritual washing of the deceased) performed in Islam?",
            f"**Ghusl al-Mayyit (Ritual Washing of the Deceased)**\n\n"
            f"Ruling: {ghusl.get('obligation','')}\n\n"
            f"Who performs it: {ghusl.get('who_washes','')}\n\n"
            f"Method:\n{method_str}\n\n"
            f"Special case: {ghusl.get('special_cases','')}",
            "death_funeral", difficulty="intermediate"
        ))

    # Kafan
    kafan = data.get("kafan", {})
    if kafan:
        pairs.append(_pair(
            "What is the correct Islamic way to wrap the deceased (kafan) before burial?",
            f"**Kafan (Shrouding the Deceased):**\n\n"
            f"For men: {kafan.get('male','')}\n\nFor women: {kafan.get('female','')}\n\n"
            f"Evidence: {kafan.get('evidence','')}\n\nSunnah: {kafan.get('sunnah','')}",
            "death_funeral", difficulty="intermediate"
        ))

    # Salat al-Janaza
    janaza = data.get("salat_al_janaza", {})
    if janaza:
        structure = janaza.get("structure", [])
        structure_str = "\n".join(structure) if structure else ""
        pairs.append(_pair(
            "How is the salat al-janaza (funeral prayer) performed in Islam?",
            f"**Salat al-Janaza (Funeral Prayer)**\n\nRuling: {janaza.get('ruling','')}\n\n"
            f"Structure:\n{structure_str}\n\n"
            f"Du'a for deceased:\n{janaza.get('dua_for_deceased','')}\n\n"
            f"Who leads: {janaza.get('who_leads','')}",
            "death_funeral", difficulty="intermediate"
        ))

    # Burial
    burial = data.get("burial", {})
    if burial:
        pairs.append(_pair(
            "What are the Islamic rulings and etiquette for burial of the deceased?",
            f"**Islamic Burial Guidelines:**\n\n"
            f"Speed: {burial.get('speed','')}\n\n"
            f"Direction: {burial.get('direction','')}\n\n"
            f"Grave type: {burial.get('lahd_vs_shaqq','')}\n\n"
            f"Lowering the body: {burial.get('lowering_the_body','')}\n\n"
            f"Grave mound: {burial.get('grave_mound','')}\n\n"
            f"Marker: {burial.get('grave_marker','')}",
            "death_funeral", difficulty="intermediate"
        ))

    # Visiting graves
    graves = data.get("visiting_graves", {})
    if graves:
        prohibited = graves.get("prohibited", [])
        prohibited_str = "\n".join(f"• {p}" for p in prohibited) if prohibited else ""
        pairs.append(_pair(
            "What are the Islamic guidelines for visiting graves?",
            f"Ruling: {graves.get('ruling','')}\n\n"
            f"What to say: {graves.get('what_to_say','')}\n\n"
            f"Reciting Quran: {graves.get('reciting_quran','')}\n\n"
            f"Prohibited at graves:\n{prohibited_str}",
            "death_funeral", difficulty="intermediate"
        ))

    # Taziyah (condolences)
    taziyah = data.get("taziyah_condolences", {})
    if taziyah:
        sunnah_words = taziyah.get("sunnah_words", "")
        duration = taziyah.get("duration", "")
        prohibited_cond = taziyah.get("prohibited", [])
        patience = taziyah.get("patience_sabr", "")
        prohibited_str = "\n".join(f"• {p}" for p in prohibited_cond) if prohibited_cond else ""
        pairs.append(_pair(
            "What is the Islamic etiquette for offering condolences (taziyah) to a bereaved family?",
            f"**Taziyah (Condolences) in Islam:**\n\n"
            + (f"Sunnah words: {sunnah_words}\n\n" if sunnah_words else "")
            + (f"Duration: {duration}\n\n" if duration else "")
            + (f"Patience (Sabr): {patience}\n\n" if patience else "")
            + (f"What to avoid:\n{prohibited_str}" if prohibited_str else ""),
            "death_funeral", difficulty="intermediate"
        ))

    return pairs


# ─── Rights in Islam ───────────────────────────────────────────────────────────

def _gen_rights(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "rights_in_islam.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    # Rights of Allah
    rights_allah = data.get("rights_of_allah", {})
    if rights_allah:
        desc = rights_allah.get("description", "")
        examples = rights_allah.get("examples", [])
        examples_str = "\n".join(f"• {e}" for e in examples) if examples else ""
        pairs.append(_pair(
            "What are the rights of Allah (Huquq Allah) that every Muslim must fulfill?",
            f"**Rights of Allah (Huquq Allah):**\n\n{desc}\n\n{examples_str}",
            "rights_in_islam", difficulty="basic"
        ))

    for section_key, label in [
        ("rights_of_parents", "parents"),
        ("rights_of_children", "children"),
        ("rights_of_women", "women"),
        ("rights_of_neighbors", "neighbors"),
        ("rights_of_non_muslims", "non-Muslims"),
        ("rights_of_animals", "animals"),
    ]:
        section = data.get(section_key, {})
        if not section:
            continue

        quran = section.get("quran", "")
        hadith_examples = section.get("hadith_examples", []) or ([section.get("hadith", "")] if section.get("hadith") else [])
        limits = section.get("limits", "")

        parts = []
        for k, v in section.items():
            if isinstance(v, list) and k not in ("hadith_examples",):
                parts.append(f"**{k.replace('_',' ').title()}:**\n" + "\n".join(f"• {i}" for i in v))
            elif isinstance(v, str) and k not in ("quran", "hadith"):
                parts.append(v)
        content = "\n\n".join(parts[:4])

        pairs.append(_pair(
            f"What are the rights of {label} in Islam according to the Quran and Sunnah?",
            f"**Rights of {label.title()} in Islam:**\n\n"
            + (f"Quranic Evidence: {quran}\n\n" if quran else "")
            + content
            + (f"\n\nLimits: {limits}" if limits else ""),
            "rights_in_islam", difficulty="intermediate"
        ))

    return pairs


# ─── Islamic Finance ───────────────────────────────────────────────────────────

def _gen_islamic_finance(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "islamic_finance.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    # Riba
    riba = data.get("core_prohibition", {}).get("riba", {})
    if riba:
        pairs.append(_pair(
            "What is riba (interest) and why is it strictly prohibited in Islam?",
            f"**Riba (Interest/Usury) in Islam:**\n\n{riba.get('definition','')}\n\n"
            f"Quran: {riba.get('quran','')}\n\n"
            f"Hadith: {riba.get('hadith','')}\n\n"
            f"Types: {'; '.join(riba.get('types', []))}",
            "islamic_finance", difficulty="intermediate"
        ))

    # Halal instruments
    for instrument in data.get("halal_instruments", []):
        name = instrument.get("name", "")
        arabic = instrument.get("arabic", "")
        itype = instrument.get("type", "")
        how = instrument.get("how_it_works", "")
        key = instrument.get("key_feature", "")
        use = instrument.get("contemporary_use", "")
        if not name or not how:
            continue
        pairs.append(_pair(
            f"What is {name} ({arabic}) in Islamic finance and how does it work?",
            f"**{name}** ({arabic}) — {itype}\n\nHow it works: {how}\n\nKey feature: {key}\n\nContemporary use: {use}",
            "islamic_finance", difficulty="advanced"
        ))
        pairs.append(_pair(
            f"How is {name} ({arabic}) used as a halal alternative to conventional {itype.lower() if itype else 'financial instrument'}?",
            f"**{name}** ({arabic}) is an Islamic finance instrument that provides a halal alternative.\n\n{how}\n\nKey distinguishing feature: {key}\n\nContemporary use: {use}",
            "islamic_finance", difficulty="advanced"
        ))

    # Mortgage fatwa
    mortgage = data.get("fatwa_on_mortgages", {})
    if mortgage:
        pairs.append(_pair(
            "Is a conventional mortgage halal or haram in Islam? What are the Islamic alternatives?",
            f"**Conventional Mortgage:** {mortgage.get('conventional_mortgage','')}\n\n"
            f"**Islamic Alternatives:**\n" + "\n".join(f"• {a}" for a in mortgage.get("islamic_alternatives", []))
            + f"\n\n{mortgage.get('necessity_argument','')}",
            "islamic_finance", difficulty="intermediate"
        ))

    # Zakat overview
    zakat = data.get("zakat_overview", {})
    if zakat:
        assets = zakat.get("zakatable_assets", [])
        recipients = zakat.get("zakat_recipients", [])
        assets_str = "\n".join(f"• {a}" for a in assets) if assets else ""
        recip_str = "\n".join(f"• {r}" for r in recipients) if recipients else ""
        pairs.append(_pair(
            "What is zakat and how is it calculated in Islamic finance?",
            f"**Zakat (Obligatory Alms):**\n\n{zakat.get('definition','')}\n\n"
            f"Nisab (threshold): {zakat.get('nisab','')}\n"
            f"Rate: {zakat.get('rate','')}\n\n"
            + (f"Zakatable Assets:\n{assets_str}\n\n" if assets_str else "")
            + (f"Eight Categories of Recipients (Quran 9:60):\n{recip_str}" if recip_str else ""),
            "islamic_finance", difficulty="intermediate"
        ))

        # Exempt assets
        exempt = zakat.get("exempt_assets", [])
        if exempt:
            exempt_str = "\n".join(f"• {e}" for e in exempt)
            pairs.append(_pair(
                "What assets are exempt from zakat in Islam?",
                f"**Assets Exempt from Zakat:**\n\n{exempt_str}\n\nZakat only applies to zakatable wealth above the nisab threshold held for one lunar year.",
                "islamic_finance", difficulty="intermediate"
            ))

    return pairs


# ─── New Muslim Guide ──────────────────────────────────────────────────────────

def _gen_new_muslim(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "new_muslim_guide.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    shahadah = data.get("shahadah", {})
    if shahadah:
        meaning = shahadah.get("meaning", "")
        practical = shahadah.get("what_it_means_practically", [])
        practical_str = "\n".join(f"• {p}" for p in practical) if practical else ""
        pairs.append(_pair(
            "What is the Shahadah and what does it mean to say it as a new Muslim?",
            f"**The Shahadah (Declaration of Faith):**\n\n"
            f"Arabic: {shahadah.get('arabic','')}\n"
            f"Transliteration: {shahadah.get('transliteration','')}\n"
            f"Translation: {shahadah.get('translation','')}\n\n"
            f"{meaning}\n\n{practical_str}",
            "new_muslim_guide", difficulty="basic"
        ))

    # Obligations
    for ob in data.get("immediate_obligations", []):
        obligation = ob.get("obligation", "")
        how = ob.get("how_to_start", "")
        note = ob.get("note", "")
        if obligation:
            pairs.append(_pair(
                f"As a new Muslim, what do I need to know about {obligation.split('(')[0].strip()}?",
                f"**{obligation}** — What new Muslims need to know:\n\n"
                + (how if how else note),
                "new_muslim_guide", difficulty="basic"
            ))

    # Common questions
    for qa in data.get("common_questions", []):
        q = qa.get("q", "")
        a = qa.get("a", "")
        if q and a:
            pairs.append(_pair(q, a, "new_muslim_guide", difficulty="basic"))

    # First things to learn
    first_things = data.get("first_things_to_learn", [])
    if first_things:
        things_str = "\n".join(f"• {t}" for t in first_things)
        pairs.append(_pair(
            "What should a new Muslim learn first after taking the Shahadah?",
            f"**First things to learn as a new Muslim:**\n\n{things_str}\n\n"
            f"Take it one step at a time. Allah ﷻ knows your intention and effort. The Prophet ﷺ said: 'Make things easy and do not make them difficult.' (Sahih Bukhari 69)",
            "new_muslim_guide", difficulty="basic"
        ))

    # Six Pillars of Iman
    six_pillars = data.get("six_pillars_of_iman", [])
    if six_pillars:
        pillars_str = "\n".join(f"• {p}" for p in six_pillars)
        pairs.append(_pair(
            "What are the Six Pillars of Iman (faith) in Islam?",
            f"**The Six Pillars of Iman (Faith):**\n\n{pillars_str}\n\n"
            f"These are derived from the famous hadith of Jibreel AS: '...and you believe in Allah, His angels, His books, His messengers, the Last Day, and you believe in divine decree, both the good and bad of it.' (Sahih Muslim 8)",
            "new_muslim_guide", difficulty="basic"
        ))

    # Five Pillars of Islam
    five_pillars = data.get("five_pillars_of_islam", [])
    if five_pillars:
        pillars_str = "\n".join(f"• {p}" for p in five_pillars)
        pairs.append(_pair(
            "What are the Five Pillars of Islam?",
            f"**The Five Pillars of Islam:**\n\n{pillars_str}\n\n"
            f"These are the foundational acts of worship that every Muslim must perform. The Prophet ﷺ said: 'Islam is built upon five [pillars].' (Sahih Bukhari 8, Sahih Muslim 16)",
            "new_muslim_guide", difficulty="basic"
        ))

    # Gradual approach
    gradual = data.get("gradual_approach", {})
    if gradual and isinstance(gradual, dict):
        principle = gradual.get("principle", "")
        priority = gradual.get("priority_order", [])
        hadith = gradual.get("hadith", "")
        priority_str = "\n".join(f"• {p}" for p in priority) if priority else ""
        pairs.append(_pair(
            "How should a new Muslim approach learning and practicing Islam — all at once or gradually?",
            f"**Gradual Approach to Islam for New Muslims:**\n\n{principle}\n\n"
            + (f"Priority Order:\n{priority_str}\n\n" if priority_str else "")
            + (f"Hadith Evidence: {hadith}" if hadith else ""),
            "new_muslim_guide", difficulty="basic"
        ))

    return pairs


# ─── Islamic Psychology ────────────────────────────────────────────────────────

def _gen_islamic_psychology(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "islamic_psychology.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    # General principles
    general = data.get("general_principles", [])
    if general:
        gen_str = "\n".join(f"• {p}" for p in general)
        pairs.append(_pair(
            "What are the general Islamic principles for understanding mental health?",
            f"**Islamic Principles on Mental Health:**\n\n{gen_str}",
            "islamic_psychology", difficulty="basic"
        ))

    for section_key, question_template in [
        ("anxiety_and_worry", "How does Islam address anxiety and worry?"),
        ("depression", "What does Islam say about depression and how should a Muslim cope?"),
        ("grief", "How does Islam guide Muslims through grief and loss?"),
        ("trauma_and_healing", "What is the Islamic approach to trauma and emotional healing?"),
    ]:
        section = data.get(section_key, {})
        if not section:
            continue

        parts = []
        for key, val in section.items():
            if isinstance(val, str) and len(val) > 30:
                parts.append(f"**{key.replace('_',' ').title()}:** {val}")
            elif isinstance(val, list):
                items = "\n".join(f"• {i}" for i in val)
                parts.append(f"**{key.replace('_',' ').title()}:**\n{items}")

        pairs.append(_pair(
            question_template,
            "\n\n".join(parts[:5]),
            "islamic_psychology", difficulty="intermediate"
        ))

    # Anger management
    anger = data.get("anger_management", {})
    if anger:
        guidance = anger.get("prophetic_guidance", "")
        steps = anger.get("practical_steps_from_sunnah", [])
        cause = anger.get("cause_in_islam", "")
        steps_str = "\n".join(f"• {s}" for s in steps) if steps else ""
        pairs.append(_pair(
            "How does Islam guide Muslims to control anger according to the Prophet ﷺ?",
            f"**Islamic Guidance on Anger Management:**\n\n{guidance}\n\n"
            + (f"Cause: {cause}\n\n" if cause else "")
            + (f"Practical Steps from Sunnah:\n{steps_str}" if steps_str else ""),
            "islamic_psychology", difficulty="intermediate"
        ))

    # Envy and evil eye
    envy = data.get("envy_and_evil_eye", {})
    if envy:
        evil_eye = envy.get("evil_eye_reality", "")
        protection = envy.get("protection", [])
        hasad = envy.get("envy_hasad", "")
        cure = envy.get("cure_for_hasad", "")
        prot_str = "\n".join(f"• {p}" for p in protection) if protection else ""
        pairs.append(_pair(
            "What does Islam say about the evil eye (ayn) and envy (hasad)?",
            f"**Evil Eye in Islam:**\n\n{evil_eye}\n\n"
            + (f"Protection:\n{prot_str}\n\n" if prot_str else "")
            + (f"Hasad (Envy): {hasad}\n\n" if hasad else "")
            + (f"Cure for Hasad: {cure}" if cure else ""),
            "islamic_psychology", difficulty="intermediate"
        ))

    # Self-esteem and identity
    selfesteem = data.get("self_esteem_and_identity", {})
    if selfesteem:
        perspective = selfesteem.get("islamic_perspective", "")
        comparison = selfesteem.get("comparison_trap", "")
        purpose = selfesteem.get("purpose", "")
        identity = selfesteem.get("muslim_identity", "")
        pairs.append(_pair(
            "How does Islam build self-esteem and a positive identity in Muslims?",
            f"**Islamic Perspective on Self-Esteem:**\n\n{perspective}\n\n"
            + (f"Avoiding Comparison: {comparison}\n\n" if comparison else "")
            + (f"Purpose: {purpose}\n\n" if purpose else "")
            + (f"Muslim Identity: {identity}" if identity else ""),
            "islamic_psychology", difficulty="intermediate"
        ))

    # Suicide section — special handling
    suicide = data.get("suicide_and_self_harm", {})
    if suicide:
        pairs.append(_pair(
            "What is the Islamic ruling on suicide and how should Muslims respond to someone who is suicidal?",
            f"**Islamic Perspective on Suicide:**\n\n"
            f"{suicide.get('islamic_ruling','')}\n\n"
            f"**Compassionate Approach:** {suicide.get('compassionate_approach','')}\n\n"
            f"**Hope:** {suicide.get('hope','')}\n\n"
            f"**Crisis Resources:** {suicide.get('crisis_resources','')}\n\n"
            f"*{suicide.get('note','')}*",
            "islamic_psychology", difficulty="advanced"
        ))

    return pairs


# ─── Tafsir Key Surahs ─────────────────────────────────────────────────────────

def _gen_tafsir_key_surahs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "tafsir_key_surahs.json")
    pairs: list[dict[str, Any]] = []
    for surah in data.get("surahs", []):
        number = surah.get("number", "")
        name = surah.get("name", "") or surah.get("surah", "")
        arabic_name = surah.get("arabic_name", "")
        meaning = surah.get("meaning", "")
        revelation = surah.get("revelation", "")
        ayahs_count = surah.get("ayahs", "")
        names = surah.get("names", [])
        structure = surah.get("structure", "")
        hadith_importance = surah.get("hadith_importance", "")
        themes = surah.get("themes", []) or (surah.get("four_stories", []) if surah.get("four_stories") else [])
        key_verse = surah.get("key_verse", {})
        if not name:
            continue

        names_str = ", ".join(names) if names else ""
        themes_content = ""
        if isinstance(themes, list):
            for t in themes:
                if isinstance(t, dict):
                    story = t.get("story","") or t.get("theme","")
                    lesson = t.get("lesson","")
                    ayahs = t.get("ayahs","")
                    themes_content += f"• **{story}** (verses {ayahs}): {lesson}\n"
                elif isinstance(t, str):
                    themes_content += f"• {t}\n"

        key_verse_str = ""
        if key_verse and isinstance(key_verse, dict):
            ref = key_verse.get("ref","") or key_verse.get("ayah","")
            text = key_verse.get("text","") or key_verse.get("meaning","")
            key_verse_str = f"\nKey Verse ({ref}): {text}"

        pairs.append(_pair(
            f"What is the theme and significance of Surah {name} (Surah {number}) in the Quran?",
            f"**Surah {name}** ({arabic_name}) — {meaning}\n\n"
            f"Surah #{number} | {revelation} revelation | {ayahs_count} verses\n"
            + (f"Also known as: {names_str}\n" if names_str else "")
            + (f"\n{structure}\n" if structure else "")
            + (f"\n{hadith_importance}\n" if hadith_importance else "")
            + (f"\nKey Topics:\n{themes_content}" if themes_content else "")
            + key_verse_str,
            "tafsir", difficulty="intermediate"
        ))

        # Verse-by-verse pairs
        for verse_data in surah.get("verse_by_verse", []):
            ayah = verse_data.get("ayah", "")
            arabic = verse_data.get("arabic", "")
            tafsir_text = verse_data.get("tafsir", "")
            if ayah and tafsir_text:
                pairs.append(_pair(
                    f"What is the tafsir (explanation) of Surah {name} verse {ayah}?",
                    f"**Surah {name} ({number}:{ayah})**\n\n{arabic}\n\nTafsir (Ibn Kathir):\n{tafsir_text}",
                    "tafsir", difficulty="advanced"
                ))

        # Key themes (for surahs without verse_by_verse)
        key_themes = surah.get("key_themes", [])
        if key_themes:
            themes_str = "\n".join(f"• {t}" for t in key_themes)
            pairs.append(_pair(
                f"What are the major themes covered in Surah {name} ({number})?",
                f"**Major Themes of Surah {name}** ({arabic_name}):\n\n{themes_str}",
                "tafsir", difficulty="intermediate"
            ))

        # Key ayahs
        for key_ayah in surah.get("key_ayahs", []):
            ref = key_ayah.get("ref", "")
            ayah_name = key_ayah.get("name", "")
            text = key_ayah.get("text", "")
            significance = key_ayah.get("significance", "")
            lesson = key_ayah.get("lesson", "")
            if ref and (text or significance):
                q_text = ayah_name if ayah_name else f"verse {ref}"
                pairs.append(_pair(
                    f"What is the significance of {q_text} in the Quran?",
                    f"**{ayah_name or ref}** ({ref})\n\n"
                    + (f'"{text}"\n\n' if text else "")
                    + (f"Significance: {significance}\n\n" if significance else "")
                    + (f"Lesson: {lesson}" if lesson else ""),
                    "tafsir", difficulty="intermediate"
                ))

        # Four stories (Surah Al-Kahf)
        four_stories = surah.get("four_stories", [])
        for story in four_stories:
            story_name = story.get("story", "")
            story_ayahs = story.get("ayahs", "")
            lesson = story.get("lesson", "")
            detail = story.get("detail", "")
            if story_name and lesson:
                pairs.append(_pair(
                    f"What is the story of {story_name} in Surah {name} and what is its lesson?",
                    f"**{story_name}** (Surah {name} {story_ayahs})\n\n"
                    + (f"{detail}\n\n" if detail else "")
                    + f"Lesson: {lesson}",
                    "tafsir", difficulty="intermediate"
                ))

        # Special virtue / intercession
        special_virtue = surah.get("special_virtue", "")
        intercession = surah.get("intercession_at_grave", "")
        why_friday = surah.get("why_recite_on_friday", "")
        recurring = surah.get("recurring_verse", "")
        last_ayahs = surah.get("last_three_ayahs", {})
        key_distinction = surah.get("key_distinction", "")

        if special_virtue:
            pairs.append(_pair(
                f"What is the special virtue of reciting Surah {name} every Friday?",
                f"**Special Virtue of Surah {name}:**\n\n{special_virtue}"
                + (f"\n\nWhy recite on Friday: {why_friday}" if why_friday else ""),
                "tafsir", difficulty="basic"
            ))

        if intercession:
            pairs.append(_pair(
                f"Does Surah {name} intercede for the person who recites it in the grave?",
                f"**Surah {name} and Intercession at the Grave:**\n\n{intercession}",
                "tafsir", difficulty="intermediate"
            ))

        if recurring:
            pairs.append(_pair(
                f"What is the recurring refrain in Surah {name} and what does it mean?",
                f"**Recurring Verse in Surah {name}:**\n\n{recurring}",
                "tafsir", difficulty="basic"
            ))

        if last_ayahs and isinstance(last_ayahs, dict):
            context = last_ayahs.get("context", "")
            names_of_allah = last_ayahs.get("names_of_allah_mentioned", [])
            hadith_lv = last_ayahs.get("hadith", "")
            names_str = ", ".join(names_of_allah) if names_of_allah else ""
            pairs.append(_pair(
                f"What is the significance of the last three verses of Surah {name}?",
                f"**Last Three Ayahs of Surah {name}:**\n\n"
                + (f"{context}\n\n" if context else "")
                + (f"Names of Allah mentioned: {names_str}\n\n" if names_str else "")
                + (f"Hadith: {hadith_lv}" if hadith_lv else ""),
                "tafsir", difficulty="advanced"
            ))

        if key_distinction:
            pairs.append(_pair(
                f"What makes Surah {name} unique or distinct among the surahs of the Quran?",
                f"**Key Distinction of Surah {name}:**\n\n{key_distinction}",
                "tafsir", difficulty="intermediate"
            ))

    return pairs


# ─── Juz Amma Tafsir ───────────────────────────────────────────────────────────

def _gen_juz_amma(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "juz_amma_tafsir.json")
    pairs: list[dict[str, Any]] = []
    for surah in data.get("surahs", []):
        number = surah.get("number", "")
        name = surah.get("name", "")
        arabic_name = surah.get("arabic_name", "")
        meaning = surah.get("meaning", "")
        ayahs = surah.get("ayahs", "")
        theme = surah.get("theme", "")
        context = surah.get("context", "")
        hadith = surah.get("hadith", "")
        key_verse = surah.get("key_verse", "")
        key_lesson = surah.get("key_lesson", "")
        key_fact = surah.get("key_fact", "")
        practical = surah.get("practical_importance", "")
        ruqyah = surah.get("ruqyah", "")
        if not name or not theme:
            continue

        pairs.append(_pair(
            f"What is the meaning and theme of Surah {name} (Surah {number}) in Juz Amma?",
            f"**Surah {name}** ({arabic_name}) — {meaning}\n\n"
            f"Surah #{number} | {ayahs} verses\n\n"
            f"{theme}\n"
            + (f"\nContext: {context}\n" if context else "")
            + (f"\nHadith: {hadith}\n" if hadith else "")
            + (f"\n{key_verse}\n" if key_verse else "")
            + (f"\nKey Lesson: {key_lesson}\n" if key_lesson else "")
            + (f"\nKey Fact: {key_fact}\n" if key_fact else "")
            + (f"\nPractical Importance: {practical}\n" if practical else "")
            + (f"\nRuqyah: {ruqyah}" if ruqyah else ""),
            "juz_amma_tafsir", difficulty="intermediate"
        ))

        # Special virtue questions
        if hadith:
            pairs.append(_pair(
                f"What hadith mentions the virtue of reciting Surah {name}?",
                f"**Virtue of Surah {name} ({number}):**\n\n{hadith}\n\n{theme}",
                "juz_amma_tafsir", difficulty="basic"
            ))
        # Key lesson question
        if key_lesson:
            pairs.append(_pair(
                f"What is the key lesson Muslims should take from Surah {name}?",
                f"**Key Lesson from Surah {name}** ({arabic_name} — {meaning}):\n\n{key_lesson}\n\n{theme}",
                "juz_amma_tafsir", difficulty="basic"
            ))
        # Practical importance
        if practical:
            pairs.append(_pair(
                f"How is Surah {name} practically important in a Muslim's daily life?",
                f"**Practical Importance of Surah {name}:**\n\n{practical}\n\n{theme}",
                "juz_amma_tafsir", difficulty="basic"
            ))
        # Context/occasion
        if context:
            pairs.append(_pair(
                f"What is the historical context or occasion of revelation for Surah {name}?",
                f"**Context of Revelation — Surah {name}** ({number}):\n\n{context}\n\n{theme}",
                "juz_amma_tafsir", difficulty="intermediate"
            ))
        # Key verse
        if key_verse and isinstance(key_verse, str):
            pairs.append(_pair(
                f"What is the most important verse in Surah {name}?",
                f"**Key Verse of Surah {name}** ({arabic_name}):\n\n{key_verse}\n\nTheme: {theme}",
                "juz_amma_tafsir", difficulty="intermediate"
            ))

    return pairs


# ─── Islamic Governance ────────────────────────────────────────────────────────

def _gen_governance(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "islamic_governance.json")
    pairs: list[dict[str, Any]] = []
    if not data:
        return pairs

    for principle in data.get("core_principles", []):
        pname = principle.get("principle", "")
        quran = principle.get("quran", "")
        application = principle.get("application", "")
        hadith = principle.get("hadith", "")
        examples = principle.get("historical_examples", "")
        if not pname:
            continue
        pairs.append(_pair(
            f"What is the Islamic principle of {pname.split('(')[0].strip()} in governance?",
            f"**{pname}**\n\n"
            + (f"Quran: {quran}\n\n" if quran else "")
            + (f"Application: {application}\n\n" if application else "")
            + (f"Hadith: {hadith}\n\n" if hadith else "")
            + (f"Historical Example: {examples}" if examples else ""),
            "islamic_governance", difficulty="advanced"
        ))

    caliphate = data.get("caliphate", {})
    if caliphate:
        pairs.append(_pair(
            "What is the Islamic Caliphate (Khilafah) and what does Islam teach about it?",
            f"**The Islamic Caliphate (Khilafah):**\n\n"
            f"{caliphate.get('definition','')}\n\n"
            f"Historical Reality: {caliphate.get('historical_reality','')}\n\n"
            f"Contemporary Position: {caliphate.get('contemporary_position','')}\n\n"
            f"Note: {caliphate.get('important_note','')}",
            "islamic_governance", difficulty="advanced"
        ))

    non_muslim = data.get("non_muslim_citizens", {})
    if non_muslim:
        pairs.append(_pair(
            "What rights do non-Muslims have under Islamic governance according to the Sharia?",
            f"**Rights of Non-Muslims in Islamic Governance:**\n\n"
            f"{non_muslim.get('dhimmi_rights','')}\n\n"
            f"Contemporary Application: {non_muslim.get('contemporary_relevance','')}\n\n"
            f"Jizyah Today: {non_muslim.get('jizyah_contemporary','')}",
            "islamic_governance", difficulty="advanced"
        ))

    # Islamic law sources
    law_sources = data.get("islamic_law_sources", {})
    if law_sources:
        sources = law_sources.get("sources", [])
        sources_str = "\n".join(
            f"• **{s.get('source','')}**: {s.get('description','')}" for s in sources
        ) if sources else ""
        pairs.append(_pair(
            "What are the sources of Islamic law (Usul al-Fiqh)?",
            f"**Sources of Islamic Law (Usul al-Fiqh):**\n\n{law_sources.get('usul_al_fiqh','')}\n\n{sources_str}",
            "islamic_governance", difficulty="intermediate"
        ))

    # Four madhabs
    madhabs_data = data.get("four_madhabs", {})
    if madhabs_data:
        schools = madhabs_data.get("schools", [])
        for school in schools:
            school_name = school.get("name", "")
            founder = school.get("founder", "")
            regions = school.get("regions", "")
            char = school.get("characteristic", "")
            if school_name:
                pairs.append(_pair(
                    f"What is the {school_name} madhab (school of jurisprudence) in Islam?",
                    f"**{school_name} Madhab**\n\nFounder: {founder}\nRegions: {regions}\n\n{char}\n\n{madhabs_data.get('description','')}",
                    "islamic_governance", difficulty="intermediate"
                ))

    return pairs


# ─── Quran Arabic Vocab ────────────────────────────────────────────────────────

def _gen_quran_vocab(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "quran_arabic_vocab.json")
    pairs: list[dict[str, Any]] = []

    for family in data.get("word_families", []):
        root = family.get("root", "")
        root_meaning = family.get("root_meaning", "")
        words = family.get("words", [])
        if not root or not words:
            continue
        words_summary = "\n".join(
            f"• **{w.get('word','')}** ({w.get('transliteration','')}) — {w.get('meaning','')}"
            + (f". {w.get('note','')}" if w.get('note') else "")
            for w in words
        )
        pairs.append(_pair(
            f"What Arabic words come from the root {root} ({root_meaning}) in the Quran?",
            f"**Arabic Root {root}** — meaning: {root_meaning}\n\nDerived Quranic words:\n{words_summary}",
            "quran_arabic_vocab", difficulty="intermediate"
        ))
        # Individual word pairs
        for w in words:
            word = w.get('word', '')
            trans = w.get('transliteration', '')
            wmeaning = w.get('meaning', '')
            note = w.get('note', '')
            if word and wmeaning:
                pairs.append(_pair(
                    f"What does the Quranic word '{trans}' ({word}) mean?",
                    f"**{word}** ({trans}) comes from the root **{root}** ({root_meaning}).\n\nMeaning: {wmeaning}"
                    + (f"\n\nNote: {note}" if note else ""),
                    "quran_arabic_vocab", difficulty="basic"
                ))

    # Essential phrases
    for phrase_data in data.get("essential_phrases", []):
        phrase = phrase_data.get("phrase", "")
        trans = phrase_data.get("transliteration", "")
        meaning = phrase_data.get("meaning", "")
        usage = phrase_data.get("usage", "")
        if phrase and meaning:
            pairs.append(_pair(
                f"What does '{trans}' ({phrase}) mean and when should a Muslim say it?",
                f"**{phrase}**\nTransliteration: {trans}\nMeaning: {meaning}\n\nWhen to say it: {usage}",
                "quran_arabic_vocab", difficulty="basic"
            ))

    # Numbers in Arabic
    numbers = data.get("numbers_in_arabic", [])
    if numbers:
        numbers_str = "\n".join(
            f"• **{n.get('arabic','')}** ({n.get('transliteration','')}) — {n.get('meaning','')}"
            for n in numbers
        )
        pairs.append(_pair(
            "What are the Arabic numbers and how are they used in the Quran?",
            f"**Arabic Numbers in the Quran:**\n\n{numbers_str}",
            "quran_arabic_vocab", difficulty="basic"
        ))

    # Quranic grammar basics
    grammar = data.get("quranic_grammar_basics", [])
    for gram_item in grammar:
        concept = gram_item.get("concept", "")
        explanation = gram_item.get("explanation", "")
        example = gram_item.get("example", "")
        significance = gram_item.get("quranic_significance", "")
        if concept and explanation:
            pairs.append(_pair(
                f"What is '{concept}' in Quranic Arabic grammar?",
                f"**{concept}**\n\n{explanation}"
                + (f"\n\nExample: {example}" if example else "")
                + (f"\n\nQuranic Significance: {significance}" if significance else ""),
                "quran_arabic_vocab", difficulty="advanced"
            ))

    return pairs


# ─── Islamic Civilization ─────────────────────────────────────────────────────

def _gen_civilization(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "islamic_civilization.json")
    pairs: list[dict[str, Any]] = []

    overview = data.get("golden_age_overview", {})
    if overview:
        centers = "\n".join(f"• {c}" for c in overview.get("centers", []))
        pairs.append(_pair(
            "What was the Islamic Golden Age and what were its major centers of learning?",
            f"**The Islamic Golden Age** ({overview.get('period','')})\n\n"
            f"Major Centers:\n{centers}\n\n"
            f"{overview.get('transmission_role','')}",
            "islamic_civilization", difficulty="intermediate"
        ))

    for scientist in data.get("scientists", []):
        name = scientist.get("name", "")
        lived = scientist.get("lived", "")
        field = scientist.get("field", "")
        contributions = scientist.get("contributions", [])
        if not name or not contributions:
            continue
        contrib_str = "\n".join(f"• {c}" for c in contributions)
        pairs.append(_pair(
            f"What were the major contributions of {name} to science and human knowledge?",
            f"**{name}** ({lived}) — Field: {field}\n\nContributions:\n{contrib_str}",
            "islamic_civilization", difficulty="intermediate"
        ))

    for institution in data.get("educational_institutions", []):
        inst_name = institution.get("institution", "")
        founded = institution.get("founded", "")
        significance = institution.get("significance", "")
        if inst_name:
            pairs.append(_pair(
                f"What is the significance of {inst_name.split(',')[0]} in Islamic history?",
                f"**{inst_name}**\nFounded: {founded}\n\n{significance}",
                "islamic_civilization", difficulty="intermediate"
            ))

    # Arts and architecture
    arts = data.get("arts_and_architecture", {})
    if arts and isinstance(arts, dict):
        calligraphy = arts.get("calligraphy", "")
        architecture = arts.get("architecture", {})
        geometric = arts.get("geometric_art", "")
        music = arts.get("music_and_poetry", "")

        if calligraphy:
            pairs.append(_pair(
                "What is the role of calligraphy in Islamic art and civilization?",
                f"**Islamic Calligraphy:**\n\n{calligraphy}",
                "islamic_civilization", difficulty="intermediate"
            ))

        if architecture and isinstance(architecture, dict):
            structures = architecture.get("notable_structures", [])
            elements = architecture.get("key_elements", [])
            structs_str = "\n".join(f"• {s}" for s in structures) if structures else ""
            elems_str = "\n".join(f"• {e}" for e in elements) if elements else ""
            pairs.append(_pair(
                "What are the notable examples of Islamic architecture from the Golden Age?",
                f"**Islamic Architecture:**\n\nNotable Structures:\n{structs_str}\n\nKey Architectural Elements:\n{elems_str}",
                "islamic_civilization", difficulty="intermediate"
            ))

        if geometric:
            pairs.append(_pair(
                "What is the significance of geometric art in Islamic civilization?",
                f"**Islamic Geometric Art:**\n\n{geometric}",
                "islamic_civilization", difficulty="intermediate"
            ))

    # Agricultural revolution
    agri = data.get("agricultural_revolution", {})
    if agri and isinstance(agri, dict):
        contribution = agri.get("contribution", "")
        crops = agri.get("introduced_crops", [])
        impact = agri.get("impact", "")
        crops_str = "\n".join(f"• {c}" for c in crops) if crops else ""
        if contribution or crops:
            pairs.append(_pair(
                "What was the Islamic Agricultural Revolution and its impact on world civilization?",
                f"**Islamic Agricultural Revolution:**\n\n{contribution}\n\n"
                + (f"Crops Introduced to Europe:\n{crops_str}\n\n" if crops_str else "")
                + (f"Impact: {impact}" if impact else ""),
                "islamic_civilization", difficulty="intermediate"
            ))

    return pairs


# ─── Battles Seerah ────────────────────────────────────────────────────────────

def _gen_battles(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "battles_seerah.json")
    pairs: list[dict[str, Any]] = []

    # Overview
    overview = data.get("overview", {})
    if isinstance(overview, dict):
        total = overview.get("total_military_expeditions", "")
        ghazwah = overview.get("ghazwah_definition", "")
        sariyyah = overview.get("sariyyah_definition", "")
        if total or ghazwah:
            pairs.append(_pair(
                "How many military expeditions did the Prophet ﷺ lead and what is the difference between ghazwah and sariyyah?",
                f"**Prophetic Military Expeditions:**\n\n"
                + (f"Total: {total}\n\n" if total else "")
                + (f"Ghazwah (غزوة): {ghazwah}\n\n" if ghazwah else "")
                + (f"Sariyyah (سرية): {sariyyah}" if sariyyah else ""),
                "seerah", difficulty="intermediate"
            ))

    # Seerah milestones
    milestones = data.get("seerah_milestones", {})
    if isinstance(milestones, dict):
        milestone_map = {
            "birth_and_early_life": "Tell me about the birth and early life of Prophet Muhammad ﷺ.",
            "pre_prophetic_character": "What was the character of Prophet Muhammad ﷺ before prophethood?",
            "first_revelation": "How did the first revelation come to Prophet Muhammad ﷺ?",
            "hijra_to_madinah": "What was the Hijra of Prophet Muhammad ﷺ to Madinah?",
            "farewell_sermon": "What did Prophet Muhammad ﷺ say in his farewell sermon (Khutbat al-Wada)?",
            "death_of_the_prophet": "How did Prophet Muhammad ﷺ pass away?",
        }
        for key, question in milestone_map.items():
            milestone = milestones.get(key, {})
            if not milestone or not isinstance(milestone, dict):
                continue
            content = "\n".join(f"**{k.replace('_',' ').title()}:** {v}" for k, v in milestone.items() if isinstance(v, str))
            key_points = milestone.get("key_points", [])
            if key_points:
                content += "\n\n**Key Points:**\n" + "\n".join(f"• {p}" for p in key_points)
            if content:
                pairs.append(_pair(question, content, "seerah", difficulty="intermediate"))

    for battle in data.get("battles", []):
        name = battle.get("name", "")
        arabic = battle.get("arabic", "")
        date = battle.get("date", "")
        location = battle.get("location", "")
        cause = battle.get("cause", "")
        outcome = battle.get("outcome", "")
        lessons = battle.get("lessons", [])
        key_event = battle.get("key_event", "")
        significance = battle.get("significance", "")
        divine = battle.get("divine_assistance", "")
        quran = battle.get("quran", "") or battle.get("lesson_quran", "")
        muslim_str = battle.get("muslim_strength", "")
        enemy_str = battle.get("enemy_strength", "")
        if not name:
            continue

        lessons_str = "\n".join(f"• {l}" for l in lessons) if lessons else ""

        # Q1: Overview
        pairs.append(_pair(
            f"What happened during the {name} in Islamic history?",
            f"**{name}** ({arabic})\nDate: {date} | Location: {location}\n\n"
            + (f"Forces: Muslims: {muslim_str} vs Enemy: {enemy_str}\n\n" if muslim_str else "")
            + (f"Cause: {cause}\n\n" if cause else "")
            + (f"Outcome: {outcome}\n\n" if outcome else "")
            + (f"Key Event: {key_event}\n\n" if key_event else "")
            + (f"Divine Assistance: {divine}\n\n" if divine else "")
            + (f"Significance: {significance}" if significance else ""),
            "seerah", difficulty="intermediate"
        ))
        # Q2: Lessons
        if lessons:
            pairs.append(_pair(
                f"What are the Islamic lessons from the {name}?",
                f"**Lessons from the {name}** ({date}):\n\n{lessons_str}\n\n"
                + (f"Quran: {quran}" if quran else ""),
                "seerah", difficulty="advanced"
            ))
        # Q3: Quran reference
        if quran:
            pairs.append(_pair(
                f"What Quranic verses relate to the {name}?",
                f"The {name} is referenced in the Quran:\n\n{quran}\n\nContext: {outcome or cause}",
                "seerah", difficulty="advanced"
            ))
        # Q4: Cause of battle
        if cause:
            pairs.append(_pair(
                f"What caused the {name} in the time of the Prophet ﷺ?",
                f"**Cause of the {name}** ({date}, {location}):\n\n{cause}\n\n"
                + (f"Outcome: {outcome}" if outcome else ""),
                "seerah", difficulty="intermediate"
            ))
        # Q5: Forces comparison
        if muslim_str and enemy_str:
            pairs.append(_pair(
                f"What were the military strengths of the Muslim and enemy forces in the {name}?",
                f"**Forces in the {name}** ({date}):\n\nMuslim forces: {muslim_str}\nEnemy forces: {enemy_str}\n\n"
                + (f"Outcome: {outcome}" if outcome else "")
                + (f"\n\nDivine Assistance: {divine}" if divine else ""),
                "seerah", difficulty="intermediate"
            ))

    return pairs


# ─── Master function ───────────────────────────────────────────────────────────

def generate_new_kb_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    """Generate all Q&A pairs from the 20 new knowledge base files."""
    generators = [
        ("Seerah al-Nabawiyyah",          _gen_seerah,              "seerah"),
        ("Taharah fiqh",                   _gen_taharah,             "taharah"),
        ("Akhlaq & ethics",                _gen_akhlaq,              "akhlaq"),
        ("Scholars biographies",           _gen_scholars,            "scholars_biographies"),
        ("Diseases of the heart",          _gen_heart_diseases,      "diseases_of_heart"),
        ("Halal/haram food",               _gen_halal_haram_food,    "halal_haram_food"),
        ("Comparative religion",           _gen_comparative_religion,"comparative_religion"),
        ("Islamic history",                _gen_islamic_history,     "islamic_history"),
        ("Quran stories",                  _gen_quran_stories,       "quran_stories"),
        ("Death & funeral rites",          _gen_death_funeral,       "death_funeral"),
        ("Rights in Islam",                _gen_rights,              "rights_in_islam"),
        ("Islamic finance",                _gen_islamic_finance,     "islamic_finance"),
        ("New Muslim guide",               _gen_new_muslim,          "new_muslim_guide"),
        ("Islamic psychology",             _gen_islamic_psychology,  "islamic_psychology"),
        ("Tafsir key surahs",              _gen_tafsir_key_surahs,   "tafsir"),
        ("Juz Amma tafsir",                _gen_juz_amma,            "juz_amma_tafsir"),
        ("Islamic governance",             _gen_governance,          "islamic_governance"),
        ("Quran Arabic vocabulary",        _gen_quran_vocab,         "quran_arabic_vocab"),
        ("Islamic civilization",           _gen_civilization,        "islamic_civilization"),
        ("Battles of the Prophet ﷺ",      _gen_battles,             "seerah"),
    ]

    all_pairs: list[dict[str, Any]] = []
    for description, fn, category in generators:
        try:
            pairs = fn(kb_dir)
            augmented = _augment(pairs, category, max_per_pair=4)
            total = pairs + augmented
            print(f"  {description}: {len(pairs)} pairs + {len(augmented)} augmented = {len(total)}")
            all_pairs.extend(total)
        except Exception as exc:
            logger.warning("  %s → SKIPPED (%s)", description, exc)

    return all_pairs


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    kb_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent.parent.parent / "01_data_collection" / "raw" / "knowledge_bases"
    )
    pairs = generate_new_kb_pairs(kb_path)
    print(f"\nTotal new KB pairs: {len(pairs)}")
