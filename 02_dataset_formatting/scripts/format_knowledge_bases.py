#!/usr/bin/env python3
"""
Generate Q&A training pairs from all knowledge base JSON files.

Covers topics 16–278 from the expanded dataset plan:
  - Tajweed rules          → tajweed_rules.json
  - Hadith sciences        → hadith_sciences.json
  - Usul al-Fiqh           → usul_al_fiqh.json
  - 4 Madhabs comparative  → madhab_comparative.json
  - Prophets in Islam      → prophets_in_islam.json
  - Aqeedah                → aqeedah.json
  - Eschatology            → eschatology.json
  - Ibadah (Salah/Zakat/Fasting/Hajj) → ibadah_salah_zakat_fasting_hajj.json
  - Family law & Inheritance → family_law_inheritance.json
  - Quran sciences         → quran_sciences.json
  - Contemporary fiqh      → contemporary_issues_fiqh.json
  - Fabricated hadith      → fabricated_hadith.json (for refusal training)
  - Duas and adhkar        → duas_and_adhkar.json
  - Sahabah biographies    → sahabah_biographies.json
  - Akhlaq and ethics      → akhlaq_ethics.json
  - Diseases of the heart  → diseases_of_heart.json
  - Scholars biographies   → scholars_biographies.json
  - Seerah al-Nabawiyyah   → seerah_nabawiyyah.json
  - Halal and haram food   → halal_haram_food.json
  - Comparative religion   → comparative_religion_dawah.json
  - Taharah (purification) → taharah_fiqh.json

Usage:
    python format_knowledge_bases.py
    python format_knowledge_bases.py --kb-dir /custom/knowledge_bases
    python format_knowledge_bases.py --output-dir /custom/output
"""

from __future__ import annotations

import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_knowledge_bases")

# ─── Paths ────────────────────────────────────────────────────────────────────

DEFAULT_KB_DIR: Path = (
    Path(__file__).parent.parent.parent
    / "01_data_collection" / "raw" / "knowledge_bases"
)
DEFAULT_OUTPUT_DIR: Path = Path(__file__).parent.parent / "formatted_output" / "knowledge_bases"

CONSULT_SCHOLAR_FOOTER = (
    "\n\n*Note: For your specific situation, please consult a qualified Islamic scholar "
    "who can consider all relevant circumstances.*"
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_pair(
    instruction: str,
    output: str,
    category: str,
    sources: list[str] | None = None,
    madhab: str = "All",
    consult_scholar: bool = False,
) -> dict[str, Any]:
    if consult_scholar:
        output = output + CONSULT_SCHOLAR_FOOTER
    return {
        "instruction": instruction.strip(),
        "input": "",
        "output": output.strip(),
        "metadata": {
            "category": category,
            "sources": sources or [],
            "madhab": madhab,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _load(kb_dir: Path, filename: str) -> dict[str, Any]:
    path = kb_dir / filename
    if not path.exists():
        logger.warning("Knowledge base not found: %s", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ─── Tajweed pairs ────────────────────────────────────────────────────────────

def generate_tajweed_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "tajweed_rules.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Noon Sakinah / Tanween rules
    for rule in data.get("noon_sakinah_tanween", {}).get("rules", []):
        name = rule.get("name", "")
        definition = rule.get("definition", "")
        letters = ", ".join(rule.get("letters", []))
        example = rule.get("example_arabic", "")
        example_exp = rule.get("example_explanation", "")

        pairs.append(_make_pair(
            f"What is {name} in Tajweed?",
            f"**{name}** ({rule.get('arabic', '')})\n\n"
            f"{definition}\n\n"
            f"**Letters:** {letters}\n\n"
            f"**Example:** {example} — {example_exp}\n\n"
            f"**Duration:** {rule.get('duration', '')}",
            "tajweed",
            sources=["Tuhfat al-Atfal", "Al-Jazariyyah"],
        ))

        if "subcategories" in rule:
            for sub in rule["subcategories"]:
                pairs.append(_make_pair(
                    f"What is {sub.get('name', '')} in Tajweed? How does it differ?",
                    f"**{sub.get('name', '')}** ({sub.get('arabic', '')})\n\n"
                    f"{sub.get('definition', '')}\n\n"
                    f"**Letters:** {', '.join(sub.get('letters', []))}\n\n"
                    f"**Example:** {sub.get('example_arabic', '')} — {sub.get('example_explanation', '')}",
                    "tajweed",
                ))

    # Madd rules
    for rule in data.get("madd", {}).get("rules", []):
        pairs.append(_make_pair(
            f"What is {rule.get('name', '')}?",
            f"**{rule.get('name', '')}** ({rule.get('arabic', '')})\n\n"
            f"{rule.get('definition', '')}\n\n"
            f"**Duration:** {rule.get('duration', '')} counts\n\n"
            f"**Example:** {rule.get('example_arabic', '')} (Surah {rule.get('example_verse', '')})",
            "tajweed",
        ))

    # Qalqalah
    q = data.get("qalqalah", {})
    if q:
        pairs.append(_make_pair(
            "What is Qalqalah in Tajweed? What are its letters and levels?",
            f"**Qalqalah** ({q.get('arabic', '')})\n\n"
            f"{q.get('definition', '')}\n\n"
            f"**Letters:** {', '.join(q.get('letters', []))} — Mnemonic: {q.get('mnemonic', '')}\n\n"
            "**Levels:**\n"
            + "\n".join(
                f"- **{lv.get('name')}:** {lv.get('condition')} — e.g., {lv.get('example')}"
                for lv in q.get("levels", [])
            ),
            "tajweed",
        ))

    # Makharij overview
    pairs.append(_make_pair(
        "What are the Makhaarij al-Huruf (articulation points) in Arabic Tajweed?",
        "The **Makhaarij al-Huruf** are the 17 points from which Arabic letters originate:\n\n"
        "1. **Al-Jawf** (empty space) — long vowel letters (Alif, Waw, Ya when madd)\n"
        "2. **Al-Halq** (throat) — 3 sub-points:\n"
        "   - Deepest: ء and ه\n"
        "   - Middle: ع and ح\n"
        "   - Nearest: غ and خ\n"
        "3. **Al-Lisan** (tongue) — 10 sub-points covering ق, ك, ج, ش, ي, ض, ل, ن, ر, ط, د, ت, ظ, ذ, ث, ز, س, ص\n"
        "4. **Al-Shafatayn** (two lips) — ب, م, و, ف\n"
        "5. **Al-Khayshum** (nasal passage) — source of ghunna for ن and م",
        "tajweed",
        sources=["Al-Jazariyyah"],
    ))

    logger.info("Tajweed: %d pairs", len(pairs))
    return pairs


# ─── Hadith Sciences pairs ────────────────────────────────────────────────────

def generate_hadith_sciences_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "hadith_sciences.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Authenticity classifications
    for cls in data.get("classifications_by_authenticity", []):
        name = cls.get("name", "")
        arabic = cls.get("arabic", "")
        definition = cls.get("definition", "")
        conditions = cls.get("conditions", [])

        pairs.append(_make_pair(
            f"What is {name} hadith? What are its conditions?",
            f"**{name}** ({arabic})\n\n"
            f"{definition}\n\n"
            + (
                "**Conditions:**\n" + "\n".join(f"- {c}" for c in conditions)
                if conditions else ""
            )
            + f"\n\n**Ruling:** {cls.get('ruling', '')}",
            "hadith_sciences",
            sources=["Muqaddimah Ibn al-Salah", "Nukhbat al-Fikr"],
        ))

        # Sub-categories
        for sub in cls.get("subcategories", []):
            pairs.append(_make_pair(
                f"What is {sub.get('name', '')} hadith?",
                f"**{sub.get('name', '')}** ({sub.get('arabic', '')})\n\n"
                f"{sub.get('definition', '')}",
                "hadith_sciences",
            ))

    # Chain classifications
    for cls in data.get("classifications_by_chain", []):
        pairs.append(_make_pair(
            f"What is {cls.get('name', '')} hadith?",
            f"**{cls.get('name', '')}** ({cls.get('arabic', '')})\n\n"
            f"{cls.get('definition', '')}\n\n"
            f"**Certainty:** {cls.get('certainty', '')}",
            "hadith_sciences",
        ))

    # Rijal grading
    rg = data.get("rijal_grading", {})
    if rg:
        pairs.append(_make_pair(
            "What is Ilm al-Jarh wal-Ta'dil? How are hadith narrators graded?",
            f"**{rg.get('name', '')}**\n\n"
            f"{rg.get('description', '')}\n\n"
            "**Grades of Trustworthiness (Ta'dil):**\n"
            + "\n".join(
                f"- Grade {g['grade']}: {g['term']} — {g['meaning']}"
                for g in rg.get("ta_dil_grades", [])
            )
            + "\n\n**Grades of Weakness/Rejection (Jarh):**\n"
            + "\n".join(
                f"- Grade {g['grade']}: {g['term']} — {g['meaning']}"
                for g in rg.get("jarh_grades", [])
            ),
            "hadith_sciences",
            sources=["Taqrib al-Tahdhib — Ibn Hajar"],
        ))

    # Hadith Qudsi
    hq = data.get("hadith_qudsi", {})
    if hq:
        pairs.append(_make_pair(
            "What is Hadith Qudsi? How does it differ from the Quran and regular hadith?",
            f"**{hq.get('name', '')}** ({hq.get('arabic', '')})\n\n"
            f"**Definition:** {hq.get('definition', '')}\n\n"
            "**Differences from the Quran:**\n"
            + "\n".join(f"- {d}" for d in hq.get("difference_from_quran", [])),
            "hadith_sciences",
        ))

    # Major collections timeline
    pairs.append(_make_pair(
        "What are the major hadith collections and when were they compiled?",
        "The major hadith collections compiled in order:\n\n"
        "- **Muwatta Imam Malik** (~150 AH) — first major collection; ~1720 hadiths\n"
        "- **Musnad Imam Ahmad** (~240 AH) — ~27,000 hadiths\n"
        "- **Sahih al-Bukhari** (256 AH) — ~7563 hadiths (with repetition); considered most authentic\n"
        "- **Sahih Muslim** (261 AH) — ~7500 hadiths; second most authentic\n"
        "- **Sunan Abu Dawud** (275 AH) — ~5274 hadiths; focus on fiqh\n"
        "- **Jami al-Tirmidhi** (279 AH) — ~3956 hadiths; introduces Sahih/Hasan/Da'if grading\n"
        "- **Sunan Ibn Majah** (273 AH) — ~4341 hadiths\n"
        "- **Sunan al-Nasai** (303 AH) — ~5766 hadiths; known for critical approach\n\n"
        "Together: Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasai, and Ibn Majah form the **Kutub al-Sittah** (Six Books).",
        "hadith_sciences",
    ))

    logger.info("Hadith sciences: %d pairs", len(pairs))
    return pairs


# ─── Usul al-Fiqh pairs ───────────────────────────────────────────────────────

def generate_usul_fiqh_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "usul_al_fiqh.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Primary sources
    for source in data.get("primary_sources", []):
        pairs.append(_make_pair(
            f"What is the role of {source.get('name', '')} in Islamic law?",
            f"**{source.get('name', '')}** — Rank {source.get('rank', '')} source\n\n"
            f"{source.get('definition', '')}\n\n"
            f"**Authority:** {source.get('authority', '')}",
            "usul_al_fiqh",
        ))

    # Secondary sources
    for source in data.get("secondary_sources", []):
        pairs.append(_make_pair(
            f"What is {source.get('name', '')} in Islamic legal theory?",
            f"**{source.get('name', '')}** ({source.get('arabic', '')})\n\n"
            f"{source.get('definition', '')}\n\n"
            + (f"**School:** {source.get('school', '')}\n\n" if source.get("school") else "")
            + (
                "**Conditions:**\n" + "\n".join(f"- {c}" for c in source.get("conditions", []))
                if source.get("conditions") else ""
            )
            + (f"\n\n**Example:** {source.get('example', '')}" if source.get("example") else ""),
            "usul_al_fiqh",
        ))

    # Legal categories
    cats = data.get("categories_of_rulings", {}).get("categories", [])
    for cat in cats:
        pairs.append(_make_pair(
            f"What does {cat.get('name', '').split('(')[0].strip()} mean in Islamic fiqh?",
            f"**{cat.get('name', '')}** ({cat.get('arabic', '')})\n\n"
            f"{cat.get('definition', '')}\n\n"
            f"**Reward/Punishment:** {cat.get('reward_punishment', cat.get('reward_punishment', 'See definition'))}\n\n"
            + (
                "**Examples:** " + ", ".join(cat.get("examples", []))
                if cat.get("examples") else ""
            ),
            "usul_al_fiqh",
        ))

    # Maqasid
    maqasid = data.get("maqasid_al_shariah", {})
    pairs.append(_make_pair(
        "What are the Maqasid al-Shariah (Objectives of Islamic Law)?",
        f"**{maqasid.get('name', '')}**\n\n"
        f"{maqasid.get('definition', '')}\n\n"
        "The five necessities (Daruriyyat):\n\n"
        + "\n".join(
            f"{n.get('rank')}. **{n.get('necessity', '')}** ({n.get('arabic', '')})\n"
            f"   - Protected by: {n.get('positive', '')}\n"
            f"   - Safeguarded by: {n.get('negative_protection', '')}"
            for n in maqasid.get("five_necessities", [])
        ),
        "usul_al_fiqh",
        sources=["Al-Muwafaqat — Imam al-Shatibi"],
    ))

    # Legal maxims
    for maxim in data.get("legal_maxims", []):
        pairs.append(_make_pair(
            f"What is the Islamic legal maxim '{maxim.get('transliteration', '')}'?",
            f"**{maxim.get('maxim', '')}**\n\n"
            f"*'{maxim.get('translation', '')}'*\n\n"
            f"**Basis:** {maxim.get('basis', '')}\n\n"
            f"**Application:** {maxim.get('application', '')}",
            "usul_al_fiqh",
        ))

    logger.info("Usul al-Fiqh: %d pairs", len(pairs))
    return pairs


# ─── Madhab comparative pairs ─────────────────────────────────────────────────

def generate_madhab_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "madhab_comparative.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Madhab profiles
    for m in data.get("madhab_profiles", []):
        pairs.append(_make_pair(
            f"Who founded the {m.get('name', '')} school of thought and what is its methodology?",
            f"**The {m.get('name', '')} Madhab**\n\n"
            f"**Founder:** Imam {m.get('founder', '')} ({m.get('founder_dates', '')})\n"
            f"**Founded in:** {m.get('founded_in', '')}\n\n"
            f"**Methodology:** {m.get('methodology', '')}\n\n"
            f"**Key Principles:**\n" + "\n".join(f"- {p}" for p in m.get("key_principles", []))
            + f"\n\n**Prevalent today in:** {m.get('geographic_prevalence', '')}",
            "madhab_comparative",
        ))

    # Comparative rulings
    for ruling in data.get("comparative_rulings", []):
        topic = ruling.get("topic", "")
        question = ruling.get("question", "")
        madhabs = ruling.get("rulings", {})

        answer = f"**{topic}**\n\n{question}\n\n"
        for madhab_name, position in madhabs.items():
            answer += f"**{madhab_name}:** {position}\n\n"
        if ruling.get("basis"):
            answer += f"**Scholarly Basis:** {ruling.get('basis', '')}"
        if ruling.get("consensus"):
            answer += f"\n\n**Consensus:** {ruling.get('consensus', '')}"

        pairs.append(_make_pair(
            question,
            answer,
            "madhab_comparative",
            sources=["Al-Fiqh ala al-Madhahib al-Arba'ah"],
        ))

        # Also ask "what do the four madhabs say about X?"
        pairs.append(_make_pair(
            f"What do the four madhabs say about {topic.lower().split('—')[0].strip()}?",
            answer,
            "madhab_comparative",
        ))

    logger.info("Madhab comparative: %d pairs", len(pairs))
    return pairs


# ─── Prophets pairs ───────────────────────────────────────────────────────────

def generate_prophets_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "prophets_in_islam.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    for prophet in data.get("prophets", []):
        name_en = prophet.get("name_english", "")
        name_ar = prophet.get("name_arabic", "")
        title = prophet.get("title", "")
        events = prophet.get("key_events", [])
        lessons = prophet.get("lessons", [])
        refs = prophet.get("quran_references", [])
        sent_to = prophet.get("sent_to", "")
        miracles = prophet.get("miracles", [])
        dua = prophet.get("dua", "")
        children = prophet.get("children", [])

        body = f"**Prophet {name_en} ﷺ** ({name_ar})"
        if title:
            body += f"\n**Title:** {title}"
        if sent_to:
            body += f"\n**Sent to:** {sent_to}"
        if refs:
            body += f"\n**Quranic references:** {', '.join(refs)}"
        if events:
            body += "\n\n**Key Events:**\n" + "\n".join(f"- {e}" for e in events)
        if miracles:
            body += "\n\n**Miracles:**\n" + "\n".join(f"- {m}" for m in miracles)
        if dua:
            body += f"\n\n**Famous Dua:** {dua}"
        if children:
            body += f"\n\n**Children:** {', '.join(children)}"
        if lessons:
            body += "\n\n**Lessons:**\n" + "\n".join(f"- {l}" for l in lessons)

        pairs.append(_make_pair(
            f"Who was Prophet {name_en} ﷺ and what is his story in Islam?",
            body, "prophets_stories",
            sources=refs,
        ))

        pairs.append(_make_pair(
            f"What does the Quran say about Prophet {name_en} ﷺ?",
            body, "prophets_stories",
            sources=refs,
        ))

        if events:
            pairs.append(_make_pair(
                f"What were the major events in the life of Prophet {name_en} ﷺ?",
                f"**Major events in the life of Prophet {name_en} ﷺ:**\n\n"
                + "\n".join(f"- {e}" for e in events),
                "prophets_stories", sources=refs,
            ))

        if lessons:
            pairs.append(_make_pair(
                f"What lessons can Muslims learn from the story of Prophet {name_en} ﷺ?",
                f"**Lessons from the story of Prophet {name_en} ﷺ:**\n\n"
                + "\n".join(f"- {l}" for l in lessons),
                "prophets_stories",
            ))

    # General aqeedah question
    basis = data.get("aqeedah_basis", {})
    pairs.append(_make_pair(
        "How many prophets were sent by Allah? Who are the 25 mentioned in the Quran?",
        f"{basis.get('belief_in_prophets', '')}\n\n"
        "**Total prophets:** ~124,000 (Musnad Ahmad) with ~315 Messengers among them.\n\n"
        "**25 prophets mentioned by name in the Quran:**\n"
        + ", ".join(
            f"{p.get('name_english', '')} ({p.get('name_arabic', '')})"
            for p in data.get("prophets", [])
        ),
        "prophets_stories",
        sources=["Quran 2:136", "Musnad Ahmad 22342"],
    ))

    logger.info("Prophets: %d pairs", len(pairs))
    return pairs


# ─── Aqeedah pairs ────────────────────────────────────────────────────────────

def generate_aqeedah_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "aqeedah.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    for pillar in data.get("six_pillars_of_iman", []):
        pairs.append(_make_pair(
            f"What is the {pillar.get('pillar', '')}{'st' if pillar.get('pillar') == 1 else 'nd' if pillar.get('pillar') == 2 else 'rd' if pillar.get('pillar') == 3 else 'th'} pillar of Iman (faith) in Islam?",
            f"**Pillar {pillar.get('pillar', '')}: {pillar.get('name', '')}**\n\n"
            f"Quranic Reference: {pillar.get('quran_reference', '')}\n\n"
            + "\n".join(f"- {item}" for item in pillar.get("includes", pillar.get("four_levels", []))),
            "aqeedah",
            sources=[pillar.get("quran_reference", ""), pillar.get("hadith_reference", "")],
        ))

    # Attributes
    attrs = data.get("attributes_of_allah", {})
    if attrs:
        pairs.append(_make_pair(
            "What is the Sunni approach to Allah's attributes? What is Tashbih and Ta'til?",
            f"{attrs.get('description', '')}\n\n"
            f"**Approach:** {attrs.get('ashari_maturidi_approach', '')}\n\n"
            "The **20 necessary attributes** of Allah include:\n"
            + "\n".join(
                f"- **{a.get('name', '')}** ({a.get('arabic', '')}): {a.get('meaning', '')}"
                for a in attrs.get("twenty_necessary_attributes", [])[:10]
            )
            + "\n\n...and more.",
            "aqeedah",
        ))

    # Shirk
    shirk = data.get("shirk", {})
    if shirk:
        for t in shirk.get("types", []):
            pairs.append(_make_pair(
                f"What is {t.get('type', '')} in Islam?",
                f"**{t.get('type', '')}**\n\n"
                f"{t.get('definition', '')}\n\n"
                + ("**Examples:**\n" + "\n".join(f"- {e}" for e in t.get("examples", []))
                   if t.get("examples") else ""),
                "aqeedah",
                sources=["Quran 4:48"],
            ))

    # Qadar
    qadar = data.get("qadar_free_will", {})
    if qadar:
        pairs.append(_make_pair(
            "How does Islam reconcile predestination (qadar) with human free will?",
            "Islam affirms BOTH divine predestination and human free will:\n\n"
            "**The four levels of Qadar:**\n"
            + "\n".join(
                f"- **{lv.get('name', '')}:** {lv.get('definition', '')}"
                for lv in data.get("six_pillars_of_iman", [{}])[5].get("four_levels", [])
            )
            + "\n\n**Free will:** Humans have genuine choice in their actions. Allah's foreknowledge does not compel — "
            "it is like knowing what someone will choose without forcing them.\n\n"
            "**Deviant positions:** The Qadariyyah denied divine foreknowledge; the Jabariyyah denied human free will. "
            "Sunni aqeedah affirms both truths without contradiction.",
            "aqeedah",
            sources=["Sahih Muslim 2643", "Quran 54:49"],
        ))

    logger.info("Aqeedah: %d pairs", len(pairs))
    return pairs


# ─── Eschatology pairs ────────────────────────────────────────────────────────

def generate_eschatology_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "eschatology.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Death and grave
    grave = data.get("death_and_grave", {})
    pairs.append(_make_pair(
        "What happens when a person dies in Islam? What is the punishment of the grave?",
        "**Death and What Follows in Islam:**\n\n"
        "**At death:** The Angel of Death takes the soul — gently for believers, painfully for disbelievers (Quran 32:11)\n\n"
        "**Questioning in the Grave:** Two angels (Munkar and Nakir) ask:\n"
        "1. Who is your Lord?\n2. What is your religion?\n3. Who is this man (about the Prophet ﷺ)?\n\n"
        "**Believer's result:** Grave expanded, window to Paradise opened\n"
        "**Disbeliever's result:** Grave constricted, window to Hellfire opened\n\n"
        "**Barzakh:** The period between death and resurrection — real punishment or bliss occurs here (Quran 40:46)\n\n"
        "**Protection from grave punishment:** Regular recitation of Surah al-Mulk (67) — Tirmidhi 2890",
        "eschatology",
        sources=["Sahih Bukhari 1338", "Sahih Muslim 2870", "Quran 32:11"],
    ))

    # Major signs
    for sign in data.get("major_signs", {}).get("signs", []):
        pairs.append(_make_pair(
            f"What is Al-Dajjal/the {sign.get('sign', '')} in Islamic eschatology?",
            f"**{sign.get('sign', '')}** (Major Sign #{sign.get('order', '')})\n\n"
            + "\n".join(f"- {d}" for d in sign.get("details", []))
            + (f"\n\n**Protection:** {sign.get('how_to_protect', '')}" if sign.get("how_to_protect") else ""),
            "eschatology",
            sources=[sign.get("quran_reference", ""), sign.get("hadith", "")],
        ))

    # Paradise and Hellfire
    for realm, key, question in [
        ("paradise", "paradise", "What is Paradise (Jannah) like in Islam?"),
        ("hellfire", "hellfire", "What is Hellfire (Jahannam) like in Islam?"),
    ]:
        realm_data = data.get(key, {})
        if realm_data:
            descriptions = realm_data.get("descriptions", [])
            levels = realm_data.get("levels", [])
            pairs.append(_make_pair(
                question,
                f"**{realm.capitalize()} in Islam:**\n\n"
                "**Levels:**\n"
                + "\n".join(
                    f"- {lv.get('name', lv.get('level', ''))}: {lv.get('description', lv.get('for', ''))}"
                    for lv in levels
                )
                + "\n\n**Descriptions from Quran and Hadith:**\n"
                + "\n".join(f"- {d}" for d in descriptions),
                "eschatology",
            ))

    # Day of Judgment
    doj = data.get("day_of_judgment", {})
    if doj:
        pairs.append(_make_pair(
            "What will happen on the Day of Judgment according to Islam?",
            "**The Day of Judgment (Yawm al-Qiyamah):**\n\n"
            "**Known by many names:** " + ", ".join(n.get("name", "") for n in doj.get("names", [])) + "\n\n"
            "**Sequence of events:**\n"
            "1. Two blows of the Trumpet (Sur) — first kills all; second resurrects all (39:68)\n"
            "2. Resurrection — all gathered on a flat white plain (Bukhari 3447)\n"
            "3. The Scale (Mizan) weighs deeds (21:47)\n"
            "4. The Record (Kitab) — given in right or left hand (17:13-14)\n"
            "5. The Bridge (Sirat) — all cross over Hellfire at speeds matching deeds\n"
            "6. Intercession (Shafa'ah) — the Prophet ﷺ intercedes (Bukhari 4712)\n"
            "7. Final entry into Paradise or Hellfire\n\n"
            "**The Great Intercession:** When all are waiting for judgment, people will ask Adam, Nuh, Ibrahim, Musa, Isa — each will say 'not me.' Only Muhammad ﷺ will accept and intercede (Bukhari 4712).",
            "eschatology",
            sources=["Quran 39:68", "Sahih Bukhari 4712", "Sahih Muslim 183"],
        ))

    logger.info("Eschatology: %d pairs", len(pairs))
    return pairs


# ─── Ibadah pairs ─────────────────────────────────────────────────────────────

def generate_ibadah_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "ibadah_salah_zakat_fasting_hajj.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    salah = data.get("salah", {})
    # Five daily prayers
    prayers = salah.get("five_daily_prayers", [])
    if prayers:
        pairs.append(_make_pair(
            "What are the five daily prayers in Islam and their times?",
            "**The Five Daily Prayers (Salawat al-Khams):**\n\n"
            + "\n".join(
                f"- **{p['name']}:** {p['rakats']} rak'ahs | "
                f"Time: {p['time_start']} to {p['time_end']}"
                for p in prayers
            )
            + "\n\nThese are Fard Ayn (obligatory on every Muslim) — Quran 2:43, 4:103.",
            "salah",
            sources=["Quran 2:43", "Quran 4:103"],
        ))

    # Pillars of salah
    pillars = salah.get("pillars_arkan", [])
    if pillars:
        pairs.append(_make_pair(
            "What are the pillars (arkan) of Salah? What makes a prayer valid?",
            "**Pillars of Salah (must all be present for prayer to be valid):**\n\n"
            + "\n".join(f"- {p}" for p in pillars),
            "salah",
            sources=["Sahih Bukhari 756", "Sahih Muslim 394"],
        ))

    # Sunnah prayers
    for sp in salah.get("sunnah_prayers", []):
        pairs.append(_make_pair(
            f"What is {sp.get('name', '')} prayer? When and how is it performed?",
            f"**{sp.get('name', '')}**\n\n"
            f"{sp.get('details', '')}\n\n"
            + (f"**Time:** {sp.get('time', '')}\n" if sp.get("time") else "")
            + (f"**Reference:** {sp.get('reference', '')}" if sp.get("reference") else ""),
            "salah",
        ))

    # Zakat
    zakat = data.get("zakat", {})
    if zakat:
        pairs.append(_make_pair(
            "What are the conditions for Zakat to become obligatory?",
            f"**Zakat becomes obligatory when:**\n\n"
            + "\n".join(f"- {c}" for c in zakat.get("conditions", []))
            + f"\n\n**Rate:** 2.5% of the total wealth above nisab\n\n"
            "**Nisab thresholds:**\n"
            f"- Gold: {zakat.get('nisab_thresholds', {}).get('gold', {}).get('amount', '')} at 2.5%\n"
            f"- Silver: {zakat.get('nisab_thresholds', {}).get('silver', {}).get('amount', '')} at 2.5%",
            "zakat",
            sources=["Quran 9:60", "Abu Dawud 1558"],
        ))

        # Eight categories
        cats = zakat.get("eight_categories_of_recipients", {})
        if cats:
            pairs.append(_make_pair(
                "Who are the eligible recipients of Zakat according to the Quran?",
                f"Allah ﷻ specified eight categories of Zakat recipients in Quran {cats.get('quran_reference', '9:60')}:\n\n"
                + "\n".join(
                    f"{i+1}. **{c.get('name', '')}** ({c.get('arabic', '')}): {c.get('definition', '')}"
                    for i, c in enumerate(cats.get("categories", []))
                ),
                "zakat",
                sources=["Quran 9:60"],
            ))

    # Fasting
    fasting = data.get("fasting", {})
    if fasting:
        pairs.append(_make_pair(
            "What invalidates the fast in Ramadan? What breaks the fast?",
            "**Things that invalidate the Ramadan fast:**\n\n"
            "**Requiring makeup AND kaffarah (expiation):**\n"
            "- Intentional sexual intercourse during daytime\n"
            "- Kaffarah: Free a slave, OR fast 2 consecutive months, OR feed 60 poor people (Bukhari 1936)\n\n"
            "**Requiring makeup only:**\n"
            + "\n".join(f"- {item}" for item in fasting.get("invalidators_requiring_makeup_only", []))
            + "\n\n**Does NOT break the fast:**\n"
            + "\n".join(f"- {item}" for item in fasting.get("does_not_break_fast", [])[:6]),
            "fasting",
            sources=["Sahih Bukhari 1933", "Sahih Bukhari 1936"],
        ))

        for vf in fasting.get("voluntary_fasts", []):
            pairs.append(_make_pair(
                f"What is the reward for fasting {vf.get('name', '')}?",
                f"**Fasting {vf.get('name', '')}:**\n\n"
                f"**Reward:** {vf.get('reward', vf.get('reason', vf.get('description', '')))}\n\n"
                + (f"**Reference:** {vf.get('reference', '')}" if vf.get("reference") else ""),
                "fasting",
                sources=[vf.get("reference", "")],
            ))

    # Hajj
    hajj = data.get("hajj", {})
    if hajj:
        pairs.append(_make_pair(
            "What are the pillars of Hajj? What are the essential acts without which Hajj is invalid?",
            "**Pillars (Arkan) of Hajj — without these, Hajj is invalid:**\n\n"
            + "\n".join(f"- {p}" for p in hajj.get("pillars_arkan_of_hajj", []))
            + "\n\n**Most important:** The standing at Arafah — 'Hajj is Arafah' (Tirmidhi 889, Sahih)\n"
            "Missing Arafah means missing Hajj entirely.",
            "hajj",
            sources=["Quran 2:197", "Tirmidhi 889"],
        ))

        pairs.append(_make_pair(
            "What is the step-by-step sequence of Hajj?",
            "**Hajj Step-by-Step:**\n\n"
            + "\n".join(f"- {step}" for step in hajj.get("steps_in_order", [])),
            "hajj",
        ))

    logger.info("Ibadah: %d pairs", len(pairs))
    return pairs


# ─── Family law pairs ─────────────────────────────────────────────────────────

def generate_family_law_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "family_law_inheritance.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Nikah
    nikah = data.get("nikah", {})
    if nikah:
        pairs.append(_make_pair(
            "What are the conditions and pillars of a valid Islamic marriage (nikah)?",
            f"**Islamic Marriage (Nikah):**\n\n{nikah.get('definition', '')}\n\n"
            f"**Pillars:**\n" + "\n".join(f"- {p}" for p in nikah.get("pillars", []))
            + "\n\n**Conditions:**\n"
            + "\n".join(f"- **{k}:** {v}" for k, v in nikah.get("conditions", {}).items())
            + f"\n\n**Prophetic encouragement:** {nikah.get('hadith', '')}",
            "family_law",
            sources=["Sahih Bukhari 5066", "Quran 4:4"],
        ))

        pairs.append(_make_pair(
            "Who is prohibited to marry in Islam?",
            "**Permanently prohibited marriages in Islam (Quran 4:22-24):**\n\n"
            + "\n".join(f"- {p}" for p in nikah.get("prohibited_marriages", [])),
            "family_law",
            sources=["Quran 4:22-24"],
        ))

    # Divorce
    divorce = data.get("divorce", {})
    if divorce:
        for dtype in divorce.get("types", []):
            pairs.append(_make_pair(
                f"What is {dtype.get('name', '')} in Islam?",
                f"**{dtype.get('name', '')}**\n\n"
                f"{dtype.get('definition', '')}\n\n"
                + (f"**Process:** {dtype.get('process', '')}\n" if dtype.get("process") else "")
                + (f"**Ruling:** {dtype.get('ruling', '')}\n" if dtype.get("ruling") else ""),
                "family_law",
                consult_scholar=True,
            ))

        iddat = divorce.get("iddat", {})
        if iddat:
            pairs.append(_make_pair(
                "What is the iddat (waiting period) after divorce or death?",
                f"**Iddat (Waiting Period):**\n\n{iddat.get('purpose', '')}\n\n"
                "**Duration by situation:**\n"
                + "\n".join(
                    f"- **{p.get('situation', '')}:** {p.get('duration', '')}"
                    for p in iddat.get("periods", [])
                ),
                "family_law",
                sources=["Quran 2:228", "Quran 2:234", "Quran 65:4"],
            ))

    # Inheritance
    faraid = data.get("inheritance_faraid", {})
    if faraid:
        pairs.append(_make_pair(
            "What are the fixed inheritance shares in Islam according to the Quran?",
            "**Fixed Inheritance Shares (Fara'id) — Quran 4:11-12 and 4:176:**\n\n"
            + "\n".join(
                f"**{s.get('share', '')}:** {', '.join(s.get('recipients', []))}"
                for s in faraid.get("fixed_shares_quran", [])
            )
            + "\n\n**After fixed shares:** Remainder goes to Asabah (residual heirs — sons first, then father, brothers, etc.)",
            "family_law",
            sources=["Quran 4:11-12", "Quran 4:176"],
        ))

        # Practical example
        ex = faraid.get("practical_example", {})
        if ex:
            pairs.append(_make_pair(
                "Can you give an example of how Islamic inheritance is calculated?",
                f"**{ex.get('scenario', '')}**\n\n"
                "**Calculation:**\n"
                + "\n".join(
                    f"- {k}: {v}"
                    for k, v in ex.get("calculation", {}).items()
                ),
                "family_law",
            ))

    logger.info("Family law: %d pairs", len(pairs))
    return pairs


# ─── Contemporary fiqh pairs ──────────────────────────────────────────────────

def generate_contemporary_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "contemporary_issues_fiqh.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    for section_key in ["financial", "technology", "bioethics", "living_as_minority"]:
        for issue in data.get(section_key, []):
            topic = issue.get("topic", "")
            question = issue.get("question", "") or f"What is the Islamic ruling on {topic}?"
            ruling = issue.get("ruling", "")
            majority = issue.get("majority_ruling", "")

            body = f"**{topic}**\n\n"
            if ruling:
                body += f"**Ruling:** {ruling}\n\n"
            if majority:
                body += f"**Majority ruling:** {majority}\n\n"

            for pos_key in ["position_1", "position_2"]:
                pos = issue.get(pos_key, {})
                if pos:
                    body += f"**Position ({pos.get('ruling', pos_key)}):** {pos.get('definition', pos.get('scholars', ''))}\n"
                    if pos.get("conditions"):
                        body += "Conditions: " + "; ".join(pos.get("conditions", [])) + "\n"
                    body += "\n"

            for list_key in ["conditions", "permitted", "haram_uses", "principles"]:
                lst = issue.get(list_key, [])
                if lst:
                    body += f"**{list_key.replace('_', ' ').title()}:**\n" + "\n".join(f"- {item}" for item in lst) + "\n\n"

            if issue.get("recommendation"):
                body += f"**Recommendation:** {issue.get('recommendation', '')}"

            pairs.append(_make_pair(
                question or f"What is the Islamic ruling on {topic}?",
                body,
                f"contemporary_fiqh",
                consult_scholar=bool(issue.get("consult_scholar", section_key in ["bioethics", "financial"])),
            ))

    logger.info("Contemporary fiqh: %d pairs", len(pairs))
    return pairs


# ─── Fabricated hadith refusal pairs ──────────────────────────────────────────

def generate_fabricated_refusal_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "fabricated_hadith.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    for entry in data.get("fabricated_hadith", []):
        circulated = entry.get("circulated_text", "")
        status = entry.get("status", "")
        verdict = entry.get("scholarly_verdict", "")
        correct = entry.get("correct_teaching", "")
        auth = entry.get("authentic_version", "")

        if "AUTHENTIC" in status:
            # Confirmed authentic — still create a pair clarifying it is authentic
            pairs.append(_make_pair(
                f"Is this a real hadith: '{circulated[:80]}'?",
                f"**Status: {status}**\n\n"
                f"{entry.get('authentic_confirmation', '')}\n\n"
                f"**Scholarly verdict:** {verdict}",
                "refusal",
                sources=["Hadith sciences verification"],
            ))
        else:
            # Fabricated/weak — create a clear refusal pair
            pairs.append(_make_pair(
                f"Is this a hadith of the Prophet ﷺ: '{circulated[:100]}'?",
                f"**This is NOT an authentic hadith from the Prophet ﷺ.**\n\n"
                f"**Status:** {status}\n\n"
                f"**Scholarly verdict:** {verdict}\n\n"
                + (f"**Correct Islamic teaching on this topic:** {correct}" if correct else "")
                + (f"\n\n**Authentic version:** {auth}" if auth else ""),
                "refusal",
                sources=["Al-Mawdu'at — Ibn al-Jawzi", "Silsilat al-Da'ifah — al-Albani"],
            ))

    logger.info("Fabricated hadith refusals: %d pairs", len(pairs))
    return pairs


# ─── Quran sciences pairs ─────────────────────────────────────────────────────

def generate_quran_sciences_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "quran_sciences.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    # Revelation
    rev = data.get("revelation", {})
    first = rev.get("first_revelation", {})
    if first:
        pairs.append(_make_pair(
            "When and where was the first revelation of the Quran?",
            f"**First Revelation:**\n\n"
            f"- **Surah:** {first.get('surah', '')} ({first.get('verses', '')})\n"
            f"- **Location:** {first.get('location', '')}\n"
            f"- **Date:** {first.get('date', '')}\n"
            f"- **How:** {first.get('how', '')}\n\n"
            f"**First words revealed:** {first.get('first_words', '')}",
            "quran_sciences",
            sources=[first.get("reference", "Bukhari 4953")],
        ))

    # Makki/Madani
    mm = data.get("makki_madani", {})
    if mm:
        pairs.append(_make_pair(
            "What is the difference between Makki and Madani surahs?",
            f"**Makki Surahs:** {mm.get('definition', {}).get('makki', '')}\n"
            f"**Madani Surahs:** {mm.get('definition', {}).get('madani', '')}\n\n"
            "**Characteristics of Makki surahs:**\n"
            + "\n".join(f"- {c}" for c in mm.get("characteristics", {}).get("makki_surahs", []))
            + "\n\n**Characteristics of Madani surahs:**\n"
            + "\n".join(f"- {c}" for c in mm.get("characteristics", {}).get("madani_surahs", [])),
            "quran_sciences",
        ))

    # Preservation
    pres = data.get("preservation", {})
    if pres:
        pairs.append(_make_pair(
            "How was the Quran preserved and compiled into book form?",
            f"**Allah's Guarantee:** Quran 15:9 — '{pres.get('divine_guarantee', '')}'\n\n"
            "**Preservation:**\n"
            "- Memorized by hundreds of Companions during the Prophet's ﷺ lifetime\n"
            "- Written on palm leaves, bones, and stones\n\n"
            "**Compilation:**\n"
            + "\n".join(
                f"- **{c.get('period', '')}:** {c.get('reason', '')} → {c.get('result', '')}"
                for c in pres.get("compilation", [])
            ),
            "quran_sciences",
            sources=["Quran 15:9", "Sahih Bukhari 4986"],
        ))

    # Nasikh/Mansukh
    nm = data.get("nasikh_mansukh", {})
    if nm:
        pairs.append(_make_pair(
            "What is Nasikh and Mansukh in Quranic sciences? Give examples.",
            f"**{nm.get('name', '')}**\n\n"
            f"{nm.get('definition', '')}\n\n"
            "**Famous examples:**\n"
            + "\n".join(
                f"- **{e.get('ruling', '')}:** Originally {e.get('original', '')} → Abrogated by {e.get('abrogated_by', e.get('stages', [''])[- 1])}"
                for e in nm.get("famous_examples", [])
            ),
            "quran_sciences",
        ))

    # I'jaz
    ijaz = data.get("ijaz", {})
    if ijaz:
        pairs.append(_make_pair(
            "What is the I'jaz al-Quran (miracle of the Quran)?",
            f"**{ijaz.get('name', '')}**\n\n"
            f"{ijaz.get('definition', '')}\n\n"
            f"**Quranic Challenge:** {ijaz.get('quranic_challenge', '')}\n\n"
            "**Types of Miracles:**\n"
            + "\n".join(
                f"- **{t.get('type', '')}:** {t.get('description', '')}"
                for t in ijaz.get("types", [])
            ),
            "quran_sciences",
            sources=["Quran 2:23"],
        ))

    logger.info("Quran sciences: %d pairs", len(pairs))
    return pairs


# ─── Duas and adhkar pairs ────────────────────────────────────────────────────

def generate_duas_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "duas_and_adhkar.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    def _dua_entry(dua: dict[str, Any]) -> str:
        parts = []
        if dua.get("arabic"):
            parts.append(f"**Arabic:** {dua['arabic']}")
        if dua.get("transliteration"):
            parts.append(f"**Transliteration:** {dua['transliteration']}")
        if dua.get("translation"):
            parts.append(f"**Translation:** {dua['translation']}")
        if dua.get("reward"):
            parts.append(f"**Reward/Virtue:** {dua['reward']}")
        if dua.get("source"):
            parts.append(f"**Source:** {dua['source']}")
        return "\n".join(parts)

    # Morning adhkar
    morning = data.get("morning_adhkar", [])
    if morning:
        pairs.append(_make_pair(
            "What are the morning adhkar (morning remembrances) a Muslim should recite?",
            "**Morning Adhkar — Authenticated Supplications:**\n\n"
            + "\n\n---\n".join(
                f"**{d.get('occasion', '')}**\n{_dua_entry(d)}"
                for d in morning[:4]
            ),
            "duas_adhkar",
            sources=["Sahih Bukhari", "Sunan Abu Dawud"],
        ))

        # Sayyid al-Istighfar deserves its own pair
        for d in morning:
            if "Sayyid" in d.get("occasion", "") or "Istighfar" in d.get("occasion", ""):
                pairs.append(_make_pair(
                    "What is Sayyid al-Istighfar (the Master Supplication for Forgiveness)?",
                    f"**Sayyid al-Istighfar — {d.get('occasion', '')}**\n\n"
                    f"{_dua_entry(d)}",
                    "duas_adhkar",
                    sources=[d.get("source", "Bukhari 6306")],
                ))

    # Post-prayer adhkar
    post_prayer = data.get("post_prayer_adhkar", [])
    if post_prayer:
        pairs.append(_make_pair(
            "What should a Muslim say after each obligatory prayer?",
            "**Post-Prayer Adhkar:**\n\n"
            + "\n\n".join(
                f"**{d.get('occasion', '')}**\n{_dua_entry(d)}"
                for d in post_prayer[:3]
            ),
            "duas_adhkar",
            sources=["Sahih Muslim 597"],
        ))

    # Daily occasions
    for dua in data.get("daily_occasions", []):
        occasion = dua.get("occasion", "")
        if not occasion:
            continue
        pairs.append(_make_pair(
            f"What dua should a Muslim say when {occasion.lower()}?",
            f"**Dua for: {occasion}**\n\n{_dua_entry(dua)}"
            + (f"\n\n**Note:** {dua.get('note', '')}" if dua.get("note") else "")
            + (f"\n\n**If forgot:** {dua.get('if_forgot', '')}" if dua.get("if_forgot") else ""),
            "duas_adhkar",
            sources=[dua.get("source", "")],
        ))

    # Quranic duas
    for dua in data.get("quranic_duas", []):
        name = dua.get("name", "")
        if not name:
            continue
        pairs.append(_make_pair(
            f"What is the Quranic dua: {name}?",
            f"**{name}**\n\n{_dua_entry(dua)}",
            "duas_adhkar",
            sources=[dua.get("source", "")],
        ))

    # Special occasions
    for dua in data.get("special_occasions", []):
        occasion = dua.get("occasion", "")
        if not occasion:
            continue
        pairs.append(_make_pair(
            f"What is the dua for {occasion.lower()}?",
            f"**{occasion}**\n\n{_dua_entry(dua)}"
            + (f"\n\n**Instructions:** {dua.get('instructions', '')}" if dua.get("instructions") else ""),
            "duas_adhkar",
            sources=[dua.get("source", "")],
        ))

    # Overall Istikhara explanation
    for dua in data.get("special_occasions", []):
        if "Istikhara" in dua.get("occasion", ""):
            pairs.append(_make_pair(
                "How does one perform Salat al-Istikhara (the prayer for seeking guidance)?",
                f"**Salat al-Istikhara:**\n\n"
                f"Pray 2 rak'ah voluntary prayer, then recite this dua:\n\n"
                f"{_dua_entry(dua)}\n\n"
                f"**Instructions:** {dua.get('instructions', '')}",
                "duas_adhkar",
                sources=["Bukhari 1162"],
            ))

    # Salawat
    for salawat in data.get("salawat_on_prophet", []):
        pairs.append(_make_pair(
            "What is the Ibrahimiyyah Salawat recited in prayer?",
            f"**{salawat.get('name', '')}**\n\n{_dua_entry(salawat)}",
            "duas_adhkar",
            sources=[salawat.get("source", "Bukhari 3370")],
        ))

    # General question about Laylat al-Qadr dua
    pairs.append(_make_pair(
        "What dua should be made on Laylat al-Qadr (Night of Power)?",
        "**Aisha (RA) asked the Prophet ﷺ:** 'If I know which night is Laylat al-Qadr, what should I say?'\n\n"
        "**The Prophet ﷺ replied:**\n\n"
        "**Arabic:** اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي\n"
        "**Transliteration:** Allahumma innaka afuwwun tuhibbul-afwa fa'fu anni\n"
        "**Translation:** O Allah, You are the Pardoner and You love to pardon, so pardon me.\n\n"
        "**Source:** Tirmidhi 3513, Ibn Majah 3850 — Sahih",
        "duas_adhkar",
        sources=["Tirmidhi 3513", "Ibn Majah 3850"],
    ))

    logger.info("Duas and adhkar: %d pairs", len(pairs))
    return pairs


# ─── Sahabah biographies pairs ────────────────────────────────────────────────

def generate_sahabah_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    data = _load(kb_dir, "sahabah_biographies.json")
    if not data:
        return []
    pairs: list[dict[str, Any]] = []

    def _companion_body(companion: dict[str, Any]) -> str:
        lines = []
        if companion.get("title"):
            lines.append(f"**Title:** {companion['title']}")
        if companion.get("death"):
            lines.append(f"**Death:** {companion['death']}")
        if companion.get("acceptance_of_islam"):
            lines.append(f"**Acceptance of Islam:** {companion['acceptance_of_islam']}")
        if companion.get("distinction"):
            lines.append(f"**Distinction:** {companion['distinction']}")
        virtues = companion.get("key_virtues", [])
        if virtues:
            lines.append("**Key virtues:**\n" + "\n".join(f"- {v}" for v in virtues))
        contribs = companion.get("major_contributions", [])
        if contribs:
            lines.append("**Major contributions:**\n" + "\n".join(f"- {c}" for c in contribs))
        if companion.get("hadith_praise"):
            lines.append(f"**Prophetic praise:** {companion['hadith_praise']}")
        lessons = companion.get("lessons", [])
        if lessons:
            lines.append("**Lessons:** " + "; ".join(lessons))
        return "\n\n".join(lines)

    # Rightly Guided Caliphs
    for caliph in data.get("rightly_guided_caliphs", []):
        name = caliph.get("name", "")
        pairs.append(_make_pair(
            f"Who was {name}? What were his major contributions to Islam?",
            f"**{name} — {caliph.get('title', '')}**\n\n{_companion_body(caliph)}",
            "sahabah",
            sources=["Al-Isabah — Ibn Hajar", "Sahih Bukhari"],
        ))

    # Ten promised Paradise
    ten = data.get("ten_promised_paradise", {})
    if ten:
        pairs.append(_make_pair(
            "Who are the Ten Companions promised Paradise by the Prophet ﷺ?",
            f"**Al-Asharatu al-Mubashsharun — Ten Given Glad Tidings of Paradise**\n\n"
            f"**Source:** {ten.get('source', 'Abu Dawud 4649, Tirmidhi 3748 — Sahih')}\n\n"
            "**The Ten:**\n"
            + "\n".join(f"{i+1}. {name}" for i, name in enumerate(ten.get("the_ten", [])))
            + "\n\n**Individual notes:**\n"
            + "\n".join(
                f"- **{n.get('name', '')}:** {n.get('distinction', '')}"
                for n in ten.get("individual_notes", [])
            ),
            "sahabah",
            sources=["Abu Dawud 4649", "Tirmidhi 3748"],
        ))

    # Individual notes on some of the ten
    for note in ten.get("individual_notes", []):
        name = note.get("name", "")
        pairs.append(_make_pair(
            f"Who was {name}?",
            f"**{name} — {note.get('title', '')}**\n\n"
            f"{note.get('distinction', '')}\n\n"
            + (f"**Source:** {note.get('source', '')}" if note.get("source") else ""),
            "sahabah",
            sources=[note.get("source", "")],
        ))

    # Major companions
    for companion in data.get("major_companions", []):
        name = companion.get("name", "")
        pairs.append(_make_pair(
            f"Who was {name} among the Companions of the Prophet ﷺ?",
            f"**{name}** — {companion.get('title', '') or companion.get('distinction', '')[:60]}\n\n"
            f"{_companion_body(companion)}",
            "sahabah",
            sources=["Al-Isabah — Ibn Hajar al-Asqalani"],
        ))

    # Female companions
    for companion in data.get("female_companions_sahabiyyat", []):
        name = companion.get("name", "")
        pairs.append(_make_pair(
            f"Who was {name}? What was her role in early Islam?",
            f"**{name} — {companion.get('title', '')}**\n\n{_companion_body(companion)}",
            "sahabah",
            sources=["Tabaqat al-Kubra — Ibn Sa'd"],
        ))

    # General Quran praise of Companions
    virtues = data.get("sahabah_virtues_general", {})
    if virtues:
        pairs.append(_make_pair(
            "What does the Quran and Sunnah say about the status of the Companions (Sahabah)?",
            f"**Quranic Praise:**\n{virtues.get('quran_praise', '')}\n\n"
            f"**The Prophet ﷺ said:** {virtues.get('hadith_on_not_insulting_them', '')}\n\n"
            f"**Sunni stance:** {virtues.get('sunni_stance', '')}",
            "sahabah",
            sources=["Quran 9:100", "Bukhari 3673", "Muslim 2540"],
        ))

    logger.info("Sahabah: %d pairs", len(pairs))
    return pairs


# ─── Master generator ─────────────────────────────────────────────────────────

def generate_akhlaq_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "akhlaq_ethics.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []
    for v in data.get("virtues", []):
        name = v.get("name", "")
        arabic = v.get("arabic", "")
        definition = v.get("definition", "")
        degrees = v.get("degrees", [])
        quran_ev = v.get("quran_evidence", "")
        hadith_ev = v.get("hadith_evidence", "")
        practical = v.get("practical_application", [])
        vice = v.get("opposite_vice", "")

        degrees_text = "\n".join(f"  {i+1}. {d}" for i, d in enumerate(degrees)) if degrees else ""
        practical_text = "\n".join(f"  • {p}" for p in practical) if practical else ""

        pairs.append(_make_pair(
            instruction=f"What is {name} ({arabic}) in Islam? How can a Muslim develop it?",
            output=(
                f"{name} ({arabic}) is one of the praised qualities of Islamic character (akhlaq).\n\n"
                f"**Definition:** {definition}\n\n"
                + (f"**Degrees of {name}:**\n{degrees_text}\n\n" if degrees_text else "")
                + (f"**Quranic Evidence:** {quran_ev}\n\n" if quran_ev else "")
                + (f"**Hadith Evidence:** {hadith_ev}\n\n" if hadith_ev else "")
                + (f"**Practical Ways to Develop {name}:**\n{practical_text}" if practical_text else "")
            ),
            category="akhlaq",
            sources=[quran_ev, hadith_ev],
        ))

        if vice:
            pairs.append(_make_pair(
                instruction=f"What does Islam say about {vice}? How does it relate to {name}?",
                output=(
                    f"Islam warns against {vice}, which is the opposite of {name} ({arabic}).\n\n"
                    f"{name} is defined as: {definition}\n\n"
                    + (f"**Quranic Warning:** {quran_ev}\n\n" if quran_ev else "")
                    + (f"**Prophetic Guidance:** {hadith_ev}\n\n" if hadith_ev else "")
                    + (
                        f"**Building {name} to overcome {vice}:**\n{practical_text}"
                        if practical_text else ""
                    )
                ),
                category="akhlaq",
            ))

    return pairs


def generate_diseases_heart_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "diseases_of_heart.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []
    for d in data.get("diseases", []):
        name = d.get("name", "")
        arabic = d.get("arabic", "")
        definition = d.get("definition", "")
        symptoms = d.get("symptoms", [])
        causes = d.get("causes", [])
        quran_ev = d.get("quran_evidence", "")
        hadith_ev = d.get("hadith_evidence", "")
        cure = d.get("cure", [])

        symptoms_text = "\n".join(f"  • {s}" for s in symptoms) if symptoms else ""
        causes_text = "\n".join(f"  • {c}" for c in causes) if causes else ""
        cure_text = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(cure)) if cure else ""

        pairs.append(_make_pair(
            instruction=f"What is {name} ({arabic}) as a disease of the heart in Islam? What are its signs and how is it cured?",
            output=(
                f"**{name} ({arabic})** is one of the spiritual diseases of the heart (amrad al-qulub).\n\n"
                f"**Definition:** {definition}\n\n"
                + (f"**Signs and Symptoms:**\n{symptoms_text}\n\n" if symptoms_text else "")
                + (f"**Causes:**\n{causes_text}\n\n" if causes_text else "")
                + (f"**Quranic Evidence:** {quran_ev}\n\n" if quran_ev else "")
                + (f"**Hadith Evidence:** {hadith_ev}\n\n" if hadith_ev else "")
                + (f"**Cure:**\n{cure_text}" if cure_text else "")
            ),
            category="tazkiyah",
            sources=[quran_ev, hadith_ev],
        ))

    return pairs


def generate_scholars_biographies_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "scholars_biographies.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []
    for s in data.get("scholars", []):
        name = s.get("name", "")
        arabic = s.get("arabic", "")
        title = s.get("title", "")
        born = s.get("born", "")
        died = s.get("died", "")
        origin = s.get("origin", "")
        madhab = s.get("madhab", "")
        specialty = s.get("specialty", "")
        key_works = s.get("key_works", [])
        contributions = s.get("contributions", [])
        quote = s.get("quote", "")

        works_text = "\n".join(f"  • {w}" for w in key_works) if key_works else ""
        contrib_text = "\n".join(f"  • {c}" for c in contributions) if contributions else ""

        pairs.append(_make_pair(
            instruction=f"Who was {name} RH? What are his major contributions to Islamic scholarship?",
            output=(
                f"**{name} RH ({arabic})** — {title}\n\n"
                f"**Born:** {born} | **Died:** {died} | **Origin:** {origin}\n"
                f"**Madhab:** {madhab} | **Specialty:** {specialty}\n\n"
                + (f"**Major Works:**\n{works_text}\n\n" if works_text else "")
                + (f"**Contributions to Islamic Knowledge:**\n{contrib_text}\n\n" if contrib_text else "")
                + (f'**Notable Quote:** "{quote}"' if quote else "")
            ),
            category="scholars",
        ))

        if key_works:
            works_list = ", ".join(key_works[:3])
            pairs.append(_make_pair(
                instruction=f"What are the major books written by {name} RH?",
                output=(
                    f"{name} RH ({arabic}), the {madhab} scholar and expert in {specialty}, "
                    f"authored numerous important works in Islamic scholarship:\n\n"
                    + (f"**Key Works:**\n{works_text}\n\n" if works_text else "")
                    + (f"**His Overall Contributions:**\n{contrib_text}" if contrib_text else "")
                ),
                category="scholars",
            ))

    return pairs


def generate_seerah_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "seerah_nabawiyyah.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []
    for e in data.get("events", []):
        title = e.get("title", "")
        year = e.get("year", "")
        location = e.get("location", "")
        description = e.get("description", "")
        key_figures = e.get("key_figures", [])
        quran_refs = e.get("quran_references", [])
        lessons = e.get("lessons", [])

        figures_text = ", ".join(key_figures) if key_figures else ""
        quran_text = "\n".join(f"  • {r}" for r in quran_refs) if quran_refs else ""
        lessons_text = "\n".join(f"  {i+1}. {l}" for i, l in enumerate(lessons)) if lessons else ""

        pairs.append(_make_pair(
            instruction=f"What happened during {title} in the Seerah of the Prophet ﷺ?",
            output=(
                f"**{title}**\n"
                + (f"*Year: {year} | Location: {location}*\n\n" if year or location else "\n")
                + f"{description}\n\n"
                + (f"**Key Figures:** {figures_text}\n\n" if figures_text else "")
                + (f"**Quranic References:**\n{quran_text}\n\n" if quran_text else "")
                + (f"**Lessons for Muslims:**\n{lessons_text}" if lessons_text else "")
            ),
            category="seerah",
            sources=quran_refs,
        ))

        if lessons:
            pairs.append(_make_pair(
                instruction=f"What Islamic lessons do Muslims learn from {title}?",
                output=(
                    f"The event of **{title}** in the Seerah of the Prophet ﷺ teaches Muslims several vital lessons:\n\n"
                    f"**Background:** {description}\n\n"
                    f"**Lessons:**\n{lessons_text}\n\n"
                    + (f"**Quranic Connection:**\n{quran_text}" if quran_text else "")
                ),
                category="seerah",
            ))

    return pairs


def generate_halal_haram_food_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "halal_haram_food.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []

    # General principles (list of strings)
    principles = data.get("general_principles", [])
    if principles:
        principles_text = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(principles))
        pairs.append(_make_pair(
            instruction="What are the general Islamic principles for determining whether food is halal or haram?",
            output=(
                "Islam provides clear principles for determining permissibility of food:\n\n"
                f"{principles_text}\n\n"
                "The Quran states: 'O mankind! Eat of that which is lawful and wholesome in the earth.' (Al-Baqarah 2:168)"
            ),
            category="halal_haram",
        ))

    # Explicitly haram items
    for item in data.get("explicitly_haram", []):
        item_name = item.get("item", "")
        arabic = item.get("arabic", "")
        evidence = item.get("evidence", "")
        includes = item.get("includes", [])
        all_madhabs = item.get("all_madhabs", False)

        includes_text = "\n".join(f"  • {inc}" for inc in includes) if includes else ""
        madhab_note = "[IJMA] All four madhabs agree on this prohibition." if all_madhabs else ""

        pairs.append(_make_pair(
            instruction=f"Is {item_name} halal or haram in Islam?",
            output=(
                f"**{item_name}** ({arabic}) is **Haram** (forbidden) in Islam.\n\n"
                f"**Evidence:** {evidence}\n\n"
                + (f"**This includes:**\n{includes_text}\n\n" if includes_text else "")
                + (f"{madhab_note}" if madhab_note else "")
            ),
            category="halal_haram",
            sources=[evidence],
        ))

    # Seafood
    seafood = data.get("seafood", {})
    if seafood:
        ruling = seafood.get("ruling", "")
        hanafi = seafood.get("hanafi_position", "")
        evidence = seafood.get("evidence", "")
        pairs.append(_make_pair(
            instruction="What is the Islamic ruling on seafood? Do all madhabs agree?",
            output=(
                f"**Seafood Ruling:** {ruling}\n\n"
                + (f"**Hanafi Position:** {hanafi}\n\n" if hanafi else "")
                + (f"**Evidence:** {evidence}\n\n" if evidence else "")
                + "[KHILAF] Scholars differ on which sea creatures are permissible beyond fish."
                + CONSULT_SCHOLAR_FOOTER
            ),
            category="halal_haram",
        ))

    # Gelatin
    gelatin = data.get("gelatin", {})
    if gelatin:
        ruling = gelatin.get("ruling", "")
        from_pork = gelatin.get("from_pork", "")
        recommendation = gelatin.get("recommendation", "")
        pairs.append(_make_pair(
            instruction="Is gelatin halal? What is the Islamic ruling on gelatin in food?",
            output=(
                f"**Gelatin Ruling:** {ruling}\n\n"
                + (f"**From pork:** {from_pork}\n\n" if from_pork else "")
                + "[KHILAF] Scholars differ on gelatin derived from non-halal animals after chemical transformation.\n\n"
                + (f"**Recommendation:** {recommendation}" if recommendation else "")
                + CONSULT_SCHOLAR_FOOTER
            ),
            category="halal_haram",
        ))

    # Contemporary questions
    for q in data.get("contemporary_questions", []):
        question = q.get("question", "")
        answer = q.get("answer", "")
        if question and answer:
            pairs.append(_make_pair(
                instruction=question,
                output=answer + CONSULT_SCHOLAR_FOOTER,
                category="halal_haram",
            ))

    return pairs


def generate_comparative_religion_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "comparative_religion_dawah.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []

    # Dawah principles
    for p in data.get("dawah_principles", []):
        principle = p[0] if isinstance(p, list) and len(p) > 0 else p.get("principle", "") if isinstance(p, dict) else ""
        arabic = p[1] if isinstance(p, list) and len(p) > 1 else p.get("arabic", "") if isinstance(p, dict) else ""
        application = p[2] if isinstance(p, list) and len(p) > 2 else p.get("application", "") if isinstance(p, dict) else ""
        if principle:
            pairs.append(_make_pair(
                instruction=f"What is the da'wah principle of '{principle}' in Islam?",
                output=(
                    f"**Da'wah Principle: {principle}**"
                    + (f" ({arabic})" if arabic else "") + "\n\n"
                    + (f"**How to apply it:** {application}" if application else "")
                ),
                category="dawah",
            ))

    # Islam vs Christianity
    for item in data.get("islam_vs_christianity", []):
        topic = item[0] if isinstance(item, list) else item.get("topic", "")
        islamic_pos = item[2] if isinstance(item, list) and len(item) > 2 else item.get("islamic_position", "")
        quran_resp = item[3] if isinstance(item, list) and len(item) > 3 else item.get("quran_response", "")
        dawah_app = item[4] if isinstance(item, list) and len(item) > 4 else item.get("dawah_approach", "")
        if topic and islamic_pos:
            pairs.append(_make_pair(
                instruction=f"What is the Islamic perspective on '{topic}' in comparison with Christianity?",
                output=(
                    f"**Islamic Position on {topic}:**\n{islamic_pos}\n\n"
                    + (f"**Quranic Evidence:** {quran_resp}\n\n" if quran_resp else "")
                    + (f"**Da'wah Approach:** {dawah_app}" if dawah_app else "")
                ),
                category="dawah",
            ))

    # Common objections to Islam
    for item in data.get("common_objections_to_islam", []):
        objection = item[0] if isinstance(item, list) else item.get("objection", "")
        response = item[1] if isinstance(item, list) and len(item) > 1 else item.get("islamic_response", "")
        if objection and response:
            pairs.append(_make_pair(
                instruction=f"How does Islam respond to the objection: '{objection}'?",
                output=(
                    f"**Objection:** {objection}\n\n"
                    f"**Islamic Response:**\n{response}"
                ),
                category="dawah",
            ))

    return pairs


def generate_taharah_pairs(kb_dir: Path) -> list[dict[str, Any]]:
    path = kb_dir / "taharah_fiqh.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs: list[dict[str, Any]] = []

    # Wudu — fard acts
    wudu = data.get("wudu", {})
    fard_acts = wudu.get("fard_acts", [])
    if fard_acts:
        acts_text = "\n".join(
            f"  {i+1}. **{a.get('act','')}** ({a.get('arabic','')})"
            + (f" — {a.get('detail','')}" if a.get('detail') else "")
            + (f" [Evidence: {a.get('evidence','')}]" if a.get('evidence') else "")
            for i, a in enumerate(fard_acts) if isinstance(a, dict)
        )
        pairs.append(_make_pair(
            instruction="What are the obligatory (fard) acts of wudu in Islam?",
            output=(
                "The obligatory acts of wudu (ablution) that must be performed for it to be valid:\n\n"
                f"{acts_text}\n\n"
                "Evidence: Quran 5:6 — 'O you who believe! When you intend to offer the prayer, "
                "wash your faces and your hands up to the elbows...'"
            ),
            category="taharah",
            sources=["Quran 5:6"],
        ))

    # Wudu — nullifiers
    nullifiers = wudu.get("nullifiers", [])
    if nullifiers:
        null_text = "\n".join(
            f"  {i+1}. **{n.get('nullifier','')}** ({n.get('arabic','')})"
            + (f"\n     {n.get('detail','')}" if n.get('detail') else "")
            + (f" [Evidence: {n.get('evidence','')}]" if n.get('evidence') else "")
            for i, n in enumerate(nullifiers) if isinstance(n, dict)
        )
        pairs.append(_make_pair(
            instruction="What actions nullify (break) wudu in Islam?",
            output=(
                "The following actions nullify wudu, requiring a new ablution before prayer:\n\n"
                f"{null_text}"
            ),
            category="taharah",
        ))

    # Ghusl — obligatory causes
    ghusl = data.get("ghusl", {})
    causes = ghusl.get("obligatory_causes", [])
    if causes:
        causes_text = "\n".join(
            f"  {i+1}. **{c.get('cause','')}** ({c.get('arabic','')})"
            + (f" [Evidence: {c.get('evidence','')}]" if c.get('evidence') else "")
            for i, c in enumerate(causes) if isinstance(c, dict)
        )
        fard_ghusl = ghusl.get("fard_acts", [])
        fard_text = "\n".join(f"  • {a}" for a in fard_ghusl) if isinstance(fard_ghusl, list) and fard_ghusl and isinstance(fard_ghusl[0], str) else ""
        pairs.append(_make_pair(
            instruction="When is ghusl (ritual bath) obligatory in Islam? What are its required acts?",
            output=(
                "**Ghusl** (ritual purification/full body wash) becomes obligatory in the following cases:\n\n"
                f"{causes_text}\n\n"
                + (f"**Obligatory Acts of Ghusl:**\n{fard_text}\n\n" if fard_text else "")
                + "Evidence: Quran 4:43, Quran 5:6"
            ),
            category="taharah",
            sources=["Quran 4:43", "Quran 5:6"],
        ))

    # Tayammum
    tayammum = data.get("tayammum", {})
    conditions = tayammum.get("conditions", [])
    method = tayammum.get("method", "")
    evidence = tayammum.get("evidence", "")
    if conditions or method:
        cond_text = "\n".join(f"  • {c}" for c in conditions) if isinstance(conditions, list) else ""
        pairs.append(_make_pair(
            instruction="What is tayammum? When is it permitted and how is it performed?",
            output=(
                "**Tayammum** is dry ablution using clean earth or dust — a concession from Allah when water is unavailable or its use is harmful.\n\n"
                + (f"**Permitted Conditions:**\n{cond_text}\n\n" if cond_text else "")
                + (f"**Method:** {method}\n\n" if method else "")
                + (f"**Evidence:** {evidence}" if evidence else "")
            ),
            category="taharah",
            sources=[evidence] if evidence else [],
        ))

    # Najasah
    najasah = data.get("najasah", {})
    heavy = najasah.get("heavy_impurities", [])
    if heavy and isinstance(heavy, list):
        heavy_text = "\n".join(
            f"  • **{n.get('item','')}** — {n.get('ruling','')}. Method: {n.get('method','')}"
            for n in heavy if isinstance(n, dict)
        )
        pairs.append(_make_pair(
            instruction="What are the major (heavy) impurities (najasah) in Islam and how are they removed?",
            output=(
                "**Najasah Ghalizah** (heavy/major impurities) require complete removal for prayer validity:\n\n"
                f"{heavy_text}\n\n"
                "These must be physically removed — purification is achieved by washing until no trace remains."
            ),
            category="taharah",
        ))

    return pairs


def generate_all(kb_dir: Path) -> list[dict[str, Any]]:
    generators = [
        generate_tajweed_pairs,
        generate_hadith_sciences_pairs,
        generate_usul_fiqh_pairs,
        generate_madhab_pairs,
        generate_prophets_pairs,
        generate_aqeedah_pairs,
        generate_eschatology_pairs,
        generate_ibadah_pairs,
        generate_family_law_pairs,
        generate_contemporary_pairs,
        generate_fabricated_refusal_pairs,
        generate_quran_sciences_pairs,
        generate_duas_pairs,
        generate_sahabah_pairs,
        generate_akhlaq_pairs,
        generate_diseases_heart_pairs,
        generate_scholars_biographies_pairs,
        generate_seerah_pairs,
        generate_halal_haram_food_pairs,
        generate_comparative_religion_pairs,
        generate_taharah_pairs,
    ]
    all_pairs: list[dict[str, Any]] = []
    for gen in generators:
        try:
            all_pairs.extend(gen(kb_dir))
        except Exception as exc:
            logger.error("Generator %s failed: %s", gen.__name__, exc)
    return all_pairs


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate Q&A pairs from knowledge base JSON files."
    )
    parser.add_argument("--kb-dir", type=Path, default=DEFAULT_KB_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    random.seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating pairs from knowledge bases in %s", args.kb_dir)
    pairs = generate_all(args.kb_dir)
    logger.info("Total pairs generated: %d", len(pairs))

    # Write to JSONL
    import jsonlines
    out_file = args.output_dir / "knowledge_base_pairs.jsonl"
    with jsonlines.open(out_file, mode="w") as writer:
        writer.write_all(pairs)

    # Summary
    from collections import Counter
    counts = Counter(p["metadata"]["category"] for p in pairs)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_pairs": len(pairs),
        "by_category": dict(counts),
        "kb_dir": str(args.kb_dir),
    }
    (args.output_dir / "knowledge_base_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    logger.info("Saved to %s", out_file)
    for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
        logger.info("  %-35s: %d", cat, count)


if __name__ == "__main__":
    main()
