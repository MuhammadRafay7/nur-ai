#!/usr/bin/env python3
"""
Generate comprehensive 5-section Q&A pairs from comprehensive_topics.json.

Every answer follows the exact format:
  1. Detailed Explanation
  2. Quranic Evidence  — Arabic + translation + reference
  3. Hadith Evidence   — Collection — Book (Hadith N) — Narrator — Grade — Text
  4. Fiqh Rulings      — 4 madhabs with [IJMA] / [KHILAF] markers
  5. Summary

Produces ~60 pairs per topic × 100 topics = 6,000+ pairs.

Question types (12 × 5 templates = 60 per topic):
  comprehensive, quran, hadith, fiqh, importance, evidence,
  application, brief, definition, ruling, conditions, misconception
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_comprehensive")

CONSULT_FOOTER = (
    "\n\n*For complex personal situations, consult a qualified Islamic scholar "
    "who can consider all relevant circumstances.*"
)

# ─── Question templates (12 types × 5 = 60 per topic) ─────────────────────────

_Q: dict[str, list[str]] = {
    "comprehensive": [
        "What does Islam say about {title}? Provide a detailed explanation with Quran, hadith, and fiqh rulings.",
        "Explain {title} in Islam comprehensively — including Quranic evidence, hadith, and the rulings of the four madhabs.",
        "Give me a full Islamic explanation of {title} with evidence and scholarly rulings.",
        "I want to learn about {title} from an Islamic perspective. Include Quran, hadith, and fiqh.",
        "What is the Islamic position on {title}? Provide Quranic verses, hadiths, and each madhab's ruling.",
    ],
    "quran": [
        "What does the Quran say about {title}?",
        "Are there Quranic verses about {title}? What do they say?",
        "What does Allah ﷻ say about {title} in the Quran?",
        "Give me Quranic evidence about {title}.",
        "Which ayahs of the Quran address {title}?",
    ],
    "hadith": [
        "What did the Prophet ﷺ say about {title}?",
        "Are there authentic hadiths about {title}?",
        "What does the Sunnah of the Prophet ﷺ teach about {title}?",
        "Give me hadith evidence for {title}.",
        "What did the Prophet Muhammad ﷺ teach about {title}?",
    ],
    "fiqh": [
        "What is the fiqh ruling on {title}? What do the four madhabs say?",
        "What is the Islamic legal ruling on {title}?",
        "Do all Islamic scholars agree on {title}? What do the madhabs say?",
        "Explain the scholarly positions on {title} according to the four madhabs.",
        "What is the ruling of the Hanafi, Maliki, Shafi'i, and Hanbali madhabs on {title}?",
    ],
    "importance": [
        "Why is {title} important in Islam?",
        "What is the significance of {title} for Muslims?",
        "Why does Islam emphasize {title}?",
        "What are the benefits of {title} in Islam?",
        "How does {title} benefit a Muslim's spiritual and daily life?",
    ],
    "evidence": [
        "Give me dalil (evidence) for {title} from both Quran and Sunnah.",
        "What are the Islamic proofs for {title} from Quran and hadith?",
        "Prove {title} using both Quran and hadith.",
        "What do the Quran and Sunnah say about {title}?",
        "Give me Quranic and hadith references for {title}.",
    ],
    "application": [
        "How should a Muslim practice {title} in daily life?",
        "What practical steps should a Muslim take regarding {title}?",
        "How can I implement {title} as a Muslim?",
        "What does Islam require a Muslim to do regarding {title}?",
        "Give practical Islamic guidance on {title}.",
    ],
    "brief": [
        "Briefly explain {title} in Islam.",
        "Give me a short Islamic explanation of {title}.",
        "What is {title} in simple Islamic terms?",
        "Summarize the Islamic view on {title} in a few sentences.",
        "In brief, what does Islam say about {title}?",
    ],
    "definition": [
        "What is {title} ({arabic}) in Islam?",
        "Define {title} from an Islamic perspective.",
        "What does the term {title} mean in Islamic teaching?",
        "Explain the concept of {title} in Islam.",
        "What is the meaning and significance of {title} in Islam?",
    ],
    "ruling": [
        "Is {title} obligatory, recommended, or forbidden in Islam?",
        "What is the Islamic ruling on {title}? Is it fard, sunnah, or something else?",
        "Is {title} obligatory upon all Muslims?",
        "What is the status of {title} in Islamic law (Sharia)?",
        "Is {title} a religious obligation in Islam?",
    ],
    "conditions": [
        "What are the conditions and requirements for {title} in Islam?",
        "What must a Muslim fulfill for {title} to be valid?",
        "What are the pillars and conditions of {title} according to Islamic law?",
        "What invalidates {title} in Islam?",
        "What are the prerequisites for {title} in Islamic jurisprudence?",
    ],
    "misconception": [
        "What are common misunderstandings about {title} in Islam?",
        "How does Islam clarify misconceptions about {title}?",
        "What does Islam actually teach about {title} versus common misconceptions?",
        "Are there widespread myths about {title} that Islam corrects?",
        "What should Muslims know to avoid misconceptions about {title}?",
    ],
}


# ─── Answer section builders ──────────────────────────────────────────────────

def _build_quran_section(quran_refs: list[str], quran_lookup: dict[str, Any]) -> str:
    lines: list[str] = []
    for ref in quran_refs[:3]:
        v = quran_lookup.get(ref)
        if not v:
            continue
        arabic      = v.get("arabic", "")
        translation = v.get("translation", "")
        name        = v.get("surah_name", "")
        translit    = v.get("transliteration", "")
        entry = f"Surah {name} ({ref}):\n{arabic}"
        if translit:
            entry += f"\nTransliteration: {translit}"
        entry += f'\nTranslation: "{translation}"'
        lines.append(entry)
    if not lines:
        return ""
    return "**Quranic Evidence:**\n\n" + "\n\n".join(lines)


def _build_hadith_section(hadiths: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for h in hadiths[:3]:
        collection = h.get("collection", "")
        book       = h.get("book", "")
        number     = h.get("number", "")
        narrator   = h.get("narrator", "")
        text       = h.get("text", "")
        arabic     = h.get("arabic", "")
        grade      = h.get("grade", "Sahih")

        num_str  = f", Hadith {number}" if number else ""
        book_str = f" — {book}" if book else ""
        ref_line = f"({collection}{book_str}{num_str}) — Grade: {grade}"

        entry = f'The Prophet \u00f7 said: "{text}"\n{ref_line}'
        if narrator:
            entry = f'The Prophet \u00f7 said: "{text}"\nNarrated by: {narrator}\n{ref_line}'
        if arabic:
            entry = f"{arabic}\n{entry}"
        lines.append(entry)
    if not lines:
        return ""
    return "**Hadith Evidence:**\n\n" + "\n\n".join(lines)


def _build_fiqh_section(fiqh: dict[str, Any]) -> str:
    if not fiqh:
        return ""
    consensus = fiqh.get("consensus", "")
    ruling    = fiqh.get("ruling", "")
    details   = fiqh.get("details", "")
    hanafi    = fiqh.get("hanafi", "")
    maliki    = fiqh.get("maliki", "")
    shafi     = fiqh.get("shafi", "")
    hanbali   = fiqh.get("hanbali", "")

    lines: list[str] = ["**Scholarly Rulings (Madhabs):**\n"]
    if consensus == "IJMA":
        lines.append("All four madhabs are in agreement (Ijma).")
    elif consensus == "KHILAF":
        lines.append("Scholars hold differing opinions (Ikhtilaf).")
    if ruling:
        lines.append(f"\nGeneral ruling: {ruling}")
    if details:
        lines.append(f"\n{details}")
    for school, pos in [("Hanafi", hanafi), ("Maliki", maliki), ("Shafi'i", shafi), ("Hanbali", hanbali)]:
        if pos:
            lines.append(f"\n\u2022 **{school}:** {pos}")
    return "\n".join(lines)


def _build_answer(
    topic: dict[str, Any],
    ans_type: str,
    quran_lookup: dict[str, Any],
) -> str:
    """Build a unified 5-section answer for any question type.

    Structure (every answer):
      1. Explanation — in the light of Quran and Hadith
      2. Quranic Evidence — Arabic + transliteration + reference + translation
      3. Hadith Evidence — text + collection + number + grade
      4. Scholarly Rulings — 4 madhabs
      5. Conclusion
    """
    title          = topic.get("title", "")
    explanation    = topic.get("explanation", "")
    quran_refs     = topic.get("quran_refs", [])
    hadiths        = topic.get("hadith", [])
    fiqh           = topic.get("fiqh", {})
    summary        = topic.get("summary", "")
    conditions     = topic.get("conditions", "")
    misconceptions = topic.get("misconceptions", "")
    practical      = topic.get("practical", "")
    arabic_name    = topic.get("arabic", "")

    q_section = _build_quran_section(quran_refs, quran_lookup)
    h_section = _build_hadith_section(hadiths)
    f_section = _build_fiqh_section(fiqh)

    # ── Opening paragraph varies by question type ─────────────────────────────
    if ans_type == "definition":
        arabic_str = f" ({arabic_name})" if arabic_name else ""
        opening = f"**{title}{arabic_str}**\n\n{explanation}"
    elif ans_type == "conditions":
        body = conditions if conditions else explanation
        opening = f"**Conditions and Requirements for {title}:**\n\n{body}"
    elif ans_type == "misconception":
        body = misconceptions if misconceptions else explanation
        opening = f"**Clarifying Misconceptions about {title}:**\n\n{body}"
    elif ans_type == "application":
        body = explanation
        if practical:
            body += f"\n\n**Practical Steps:**\n{practical}"
        opening = f"**Practicing {title} as a Muslim:**\n\n{body}"
    elif ans_type == "importance":
        opening = f"**The Importance of {title} in Islam:**\n\n{explanation}"
    elif ans_type == "ruling":
        ruling = fiqh.get("ruling", "")
        opening = f"**Islamic Ruling on {title}:**\n\n{ruling or explanation}"
    elif ans_type == "brief":
        opening = f"**{title}:**\n\n{summary or explanation[:400]}"
    else:
        # comprehensive, quran, hadith, fiqh, evidence
        opening = f"**{title}**\n\n{explanation}"

    # ── Assemble the full 5-section structure ─────────────────────────────────
    parts: list[str] = [opening]
    if q_section:
        parts.append(q_section)
    if h_section:
        parts.append(h_section)
    if f_section:
        parts.append(f_section)
    if summary:
        parts.append(f"**Conclusion:**\n{summary}")

    result = "\n\n".join(filter(None, parts))
    if fiqh or ans_type in ("comprehensive", "fiqh", "ruling", "conditions"):
        result += CONSULT_FOOTER
    return result


# ─── Main generator ───────────────────────────────────────────────────────────

def generate_comprehensive_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    """Generate 5,000+ comprehensive 5-section Q&A pairs.

    Loads comprehensive_topics.json from kb_dir, resolves Quran references
    from quran_full.json, and produces 60 pairs per topic across 12 question
    types × 5 templates.

    Args:
        kb_dir: Knowledge bases directory containing comprehensive_topics.json.

    Returns:
        List of Q&A pair dicts.
    """
    topics_path = kb_dir / "comprehensive_topics.json"
    if not topics_path.exists():
        logger.warning("comprehensive_topics.json not found — skipping")
        return []

    data = json.loads(topics_path.read_text(encoding="utf-8"))
    topics: list[dict[str, Any]] = data.get("topics", [])

    # Build Quran lookup: "S:A" → {arabic, translation, surah_name}
    quran_lookup: dict[str, Any] = {}
    quran_path = kb_dir.parent / "quran" / "quran_full.json"
    if quran_path.exists():
        qdata = json.loads(quran_path.read_text(encoding="utf-8"))
        for surah in qdata.get("surahs", []):
            s_num = surah["surah_number"]
            s_name = surah.get("name_transliteration", surah.get("name_english", ""))
            for ayah in surah.get("ayahs", []):
                key = f"{s_num}:{ayah['ayah_number']}"
                quran_lookup[key] = {
                    "arabic":          ayah.get("arabic_text", ""),
                    "translation":     ayah.get("english_translation", ""),
                    "surah_name":      s_name,
                    "transliteration": ayah.get("transliteration", ""),
                }
        logger.info("Quran lookup built: %d verses", len(quran_lookup))
    else:
        logger.warning("quran_full.json not found — Quran text will be missing from comprehensive pairs")

    pairs: list[dict[str, Any]] = []

    for topic in topics:
        topic_id = topic.get("id", "unknown")
        title = topic.get("title", topic_id)
        arabic = topic.get("arabic", title)
        category = topic.get("category", "comprehensive")

        for ans_type, templates in _Q.items():
            answer = _build_answer(topic, ans_type, quran_lookup)
            if not answer or len(answer.strip()) < 80:
                continue

            for template in templates:
                question = template.format(title=title, arabic=arabic)
                pairs.append({
                    "instruction": question,
                    "input": "",
                    "output": answer,
                    "metadata": {
                        "category": f"comprehensive",
                        "sub_category": category,
                        "topic_id": topic_id,
                        "answer_type": ans_type,
                        "sources": (
                            topic.get("quran_refs", [])
                            + [h.get("collection", "") for h in topic.get("hadith", [])]
                        ),
                    },
                })

    logger.info("Comprehensive pairs generated: %d", len(pairs))
    return pairs
