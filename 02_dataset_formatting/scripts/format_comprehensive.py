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
        arabic = v.get("arabic", "")
        translation = v.get("translation", "")
        name = v.get("surah_name", "")
        lines.append(
            f"📖 Surah {name} ({ref}):\n{arabic}\n\"{translation}\""
        )
    if not lines:
        return ""
    return "**Quranic Evidence:**\n\n" + "\n\n".join(lines)


def _build_hadith_section(hadiths: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for h in hadiths[:3]:
        collection = h.get("collection", "")
        book = h.get("book", "")
        number = h.get("number", "")
        narrator = h.get("narrator", "")
        text = h.get("text", "")
        grade = h.get("grade", "Sahih")

        num_str = f" (Hadith {number})" if number else ""
        book_str = f" — {book}" if book else ""
        narr_str = f" — Narrated by {narrator}" if narrator else ""
        header = f"📚 {collection}{book_str}{num_str}{narr_str} (Grade: {grade}):"
        lines.append(f'{header}\n"{text}"')
    if not lines:
        return ""
    return "**Hadith Evidence:**\n\n" + "\n\n".join(lines)


def _build_fiqh_section(fiqh: dict[str, Any]) -> str:
    if not fiqh:
        return ""
    consensus = fiqh.get("consensus", "")
    ruling = fiqh.get("ruling", "")
    details = fiqh.get("details", "")
    hanafi = fiqh.get("hanafi", "")
    maliki = fiqh.get("maliki", "")
    shafi = fiqh.get("shafi", "")
    hanbali = fiqh.get("hanbali", "")

    lines: list[str] = ["**Fiqh Rulings:**\n"]
    if consensus == "IJMA":
        lines.append("[IJMA] All four madhabs are in agreement.")
    elif consensus == "KHILAF":
        lines.append("[KHILAF] Scholars hold differing opinions.")
    if ruling:
        lines.append(f"\nGeneral ruling: {ruling}")
    if details:
        lines.append(f"\n{details}")
    madhabs = [
        ("Hanafi", hanafi),
        ("Maliki", maliki),
        ("Shafi'i", shafi),
        ("Hanbali", hanbali),
    ]
    for name, pos in madhabs:
        if pos:
            lines.append(f"\n• **{name}:** {pos}")
    return "\n".join(lines)


def _build_answer(
    topic: dict[str, Any],
    ans_type: str,
    quran_lookup: dict[str, Any],
) -> str:
    title = topic.get("title", "")
    explanation = topic.get("explanation", "")
    quran_refs = topic.get("quran_refs", [])
    hadiths = topic.get("hadith", [])
    fiqh = topic.get("fiqh", {})
    summary = topic.get("summary", "")
    conditions = topic.get("conditions", "")
    misconceptions = topic.get("misconceptions", "")

    q_section = _build_quran_section(quran_refs, quran_lookup)
    h_section = _build_hadith_section(hadiths)
    f_section = _build_fiqh_section(fiqh)

    # ── 1. Comprehensive — all 5 sections ────────────────────────────────────
    if ans_type == "comprehensive":
        parts: list[str] = []
        if explanation:
            parts.append(f"**{title}**\n\n{explanation}")
        if q_section:
            parts.append(q_section)
        if h_section:
            parts.append(h_section)
        if f_section:
            parts.append(f_section)
        if summary:
            parts.append(f"**Summary:**\n{summary}")
        return "\n\n".join(parts) + CONSULT_FOOTER

    # ── 2. Quran-focused ─────────────────────────────────────────────────────
    elif ans_type == "quran":
        if not q_section:
            return ""
        intro = explanation.split(".")[0] + "." if "." in explanation else explanation[:200]
        return f"Regarding **{title}**, the Quran provides clear guidance:\n\n{intro}\n\n{q_section}"

    # ── 3. Hadith-focused ────────────────────────────────────────────────────
    elif ans_type == "hadith":
        if not h_section:
            return ""
        return f"The Prophet ﷺ provided important guidance on **{title}**:\n\n{h_section}"

    # ── 4. Fiqh-focused ──────────────────────────────────────────────────────
    elif ans_type == "fiqh":
        if not f_section:
            return ""
        return (
            f"Regarding the Islamic legal ruling on **{title}**:\n\n"
            f"{f_section}" + CONSULT_FOOTER
        )

    # ── 5. Importance ────────────────────────────────────────────────────────
    elif ans_type == "importance":
        parts = [f"**Why {title} is Important in Islam**\n\n{explanation}"]
        if q_section:
            parts.append(q_section)
        if h_section:
            parts.append(h_section)
        if summary:
            parts.append(f"**In Summary:**\n{summary}")
        return "\n\n".join(parts)

    # ── 6. Combined evidence (Quran + Hadith) ────────────────────────────────
    elif ans_type == "evidence":
        parts = [f"**Islamic Evidence for {title}:**"]
        if q_section:
            parts.append(q_section)
        if h_section:
            parts.append(h_section)
        if not q_section and not h_section:
            return ""
        return "\n\n".join(parts)

    # ── 7. Application ───────────────────────────────────────────────────────
    elif ans_type == "application":
        practical = topic.get("practical", "")
        parts = [f"**Practicing {title} as a Muslim:**\n\n{explanation}"]
        if practical:
            parts.append(f"**Practical Steps:**\n{practical}")
        elif summary:
            parts.append(f"**Key Points:**\n{summary}")
        return "\n\n".join(parts) + CONSULT_FOOTER

    # ── 8. Brief summary ─────────────────────────────────────────────────────
    elif ans_type == "brief":
        if summary:
            core = f"**{title}:** {summary}"
        else:
            core = explanation[:400]
        if q_section:
            core += f"\n\n{q_section}"
        return core

    # ── 9. Definition ────────────────────────────────────────────────────────
    elif ans_type == "definition":
        arabic = topic.get("arabic", "")
        arabic_str = f" ({arabic})" if arabic else ""
        intro = explanation[:500] if len(explanation) > 500 else explanation
        return f"**{title}{arabic_str}**\n\n{intro}"

    # ── 10. Ruling ───────────────────────────────────────────────────────────
    elif ans_type == "ruling":
        ruling = fiqh.get("ruling", "")
        parts = [f"**Islamic Ruling on {title}:**\n\n{ruling or explanation[:300]}"]
        if f_section:
            parts.append(f_section)
        if q_section:
            parts.append(q_section)
        if h_section:
            parts.append(h_section)
        return "\n\n".join(parts) + CONSULT_FOOTER

    # ── 11. Conditions ───────────────────────────────────────────────────────
    elif ans_type == "conditions":
        if not conditions:
            return ""
        parts = [f"**Conditions and Requirements for {title}:**\n\n{conditions}"]
        if f_section:
            parts.append(f_section)
        return "\n\n".join(parts) + CONSULT_FOOTER

    # ── 12. Misconception ────────────────────────────────────────────────────
    elif ans_type == "misconception":
        if not misconceptions:
            return ""
        parts = [
            f"**Clarifying Misconceptions about {title}:**\n\n{misconceptions}",
        ]
        if q_section:
            parts.append(q_section)
        if h_section:
            parts.append(h_section)
        return "\n\n".join(parts)

    return ""


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
                    "arabic": ayah.get("arabic_text", ""),
                    "translation": ayah.get("english_translation", ""),
                    "surah_name": s_name,
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
