#!/usr/bin/env python3
"""
Generate Q&A training pairs for list/names type questions.

The model learns to answer "Names of Prophet's wives", "List all prophets",
"Names of the 10 promised paradise", "What are the pillars of Islam?" with a
clean numbered-list format.

Data sources:
  - prophets_in_islam.json      (prophets list, aqeedah_basis.qualities_of_all_prophets)
  - sahabah_biographies.json    (rightly_guided_caliphs, ten_promised_paradise,
                                  female_companions_sahabiyyat)
  - ibadah_salah_zakat_fasting_hajj.json  (salah.five_daily_prayers, salah.pillars_arkan,
                                            hajj.pillars_arkan_of_hajj)

Hard-coded lists used:
  - 11 wives of the Prophet ﷺ (Ummahatul Mu'minin) in order
  - 5 Pillars of Islam
  - 6 Pillars of Iman
  - Arkan of Wudu

Entry point:
    generate_lists_pairs(seed=42) -> list[dict]
    Each dict: {instruction, input, output, metadata}
    metadata: {category: "lists", sub_category: "...", topic: "..."}

Usage:
    python format_lists.py
    python format_lists.py --output /custom/output/lists_pairs.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("format_lists")

# ─── Paths ────────────────────────────────────────────────────────────────────

KB_DIR: Path = (
    Path(__file__).parent.parent.parent
    / "01_data_collection" / "raw" / "knowledge_bases"
)

DEFAULT_OUTPUT: Path = (
    Path(__file__).parent.parent
    / "formatted_output" / "lists_pairs.json"
)

# ─── Question templates ────────────────────────────────────────────────────────

PROPHETS_TEMPLATES = [
    "What are the names of all prophets mentioned in the Quran?",
    "List the 25 prophets in Islam.",
    "Who are the prophets of Islam?",
    "Name all the prophets mentioned in the Quran with their Arabic names.",
    "Can you list all 25 prophets of Islam?",
    "What are the names of all the Quran's prophets?",
    "Give me a complete list of the prophets mentioned in the Quran.",
    "How many prophets are mentioned in the Quran and what are their names?",
    "Which prophets are mentioned by name in the Quran?",
    "I want to know all the names of the prophets Allah mentions in the Quran.",
    "List all Anbiya of Islam from Adam to Muhammad ﷺ.",
    "What are the 25 names of prophets from the Quran?",
]

ULUL_AZM_TEMPLATES = [
    "Who are the Ulul Azm (prophets of great determination)?",
    "Name the 5 greatest prophets in Islam.",
    "What does Ulul Azm mean and who are they?",
    "Who are the five Ulul Azm prophets?",
    "Which prophets are considered Ulul Azm in Islam?",
    "List the prophets of strong will and determination in Islam.",
    "Who are the mightiest prophets in Islam?",
    "What is the meaning of Ulul Azm and which prophets hold this rank?",
    "Name the five messengers who showed the greatest perseverance.",
    "Which Quranic verse mentions the Ulul Azm prophets?",
    "Who are the prophets called Ulul Azm in Quran 46:35?",
]

WIVES_TEMPLATES = [
    "What are the names of the Prophet's ﷺ wives?",
    "Who were the Mothers of the Believers?",
    "How many wives did the Prophet ﷺ have and what were their names?",
    "Name the wives of Prophet Muhammad ﷺ.",
    "List the Ummahatul Mu'minin.",
    "Who are the Mothers of the Believers (Ummahatul Mu'minin)?",
    "Can you name all the wives of the Prophet Muhammad ﷺ?",
    "What were the names of the Prophet's ﷺ blessed wives?",
    "List all 11 wives of Prophet Muhammad ﷺ with their descriptions.",
    "Who did the Prophet ﷺ marry and in what order?",
    "What does Ummahatul Mu'minin mean and who are they?",
    "Name the wives of the Prophet ﷺ who are called Mothers of the Believers.",
]

CALIPHS_TEMPLATES = [
    "Who are the four rightly guided caliphs?",
    "Name the Khulafa Rashidun with their periods of rule.",
    "Who were the successors of the Prophet ﷺ?",
    "List the four rightly guided caliphs of Islam.",
    "Who are the Khulafa Rashidun?",
    "Name the first four caliphs of Islam.",
    "Who led the Muslim community after the Prophet ﷺ passed away?",
    "What are the names of the four rightly guided successors of the Prophet ﷺ?",
    "List the Khulafa Rashidun with their titles and length of rule.",
    "Who were the four caliphs mentioned in the hadith about following their Sunnah?",
    "After Prophet Muhammad ﷺ, who were the four guided leaders of Islam?",
    "Name the four Caliphs of Islam in order.",
]

TEN_PARADISE_TEMPLATES = [
    "Who are the ten companions promised paradise?",
    "Name the Ashra Mubasshara.",
    "Which companions were promised Jannah by the Prophet ﷺ?",
    "List the ten companions guaranteed paradise.",
    "Who are the Al-Asharatu al-Mubashsharun?",
    "Name the 10 Sahabah promised Jannah.",
    "Which ten companions did the Prophet ﷺ name as being guaranteed paradise?",
    "What are the names of the ten blessed companions promised Jannah?",
    "Who are the Ashra Mubasshara and what is the source for this?",
    "List the ten companions the Prophet ﷺ specifically guaranteed paradise to in one hadith.",
    "Name all the companions promised paradise by name in one hadith.",
    "Who are the ten promised Jannah and what is notable about each?",
]

FIVE_PILLARS_TEMPLATES = [
    "What are the 5 pillars of Islam?",
    "List the pillars of Islam.",
    "What are the arkan of Islam?",
    "Name the five pillars of Islam.",
    "What are the fundamental obligations in Islam?",
    "Can you explain the five pillars of Islam?",
    "What are the five foundations of Islamic practice?",
    "List the five obligatory acts every Muslim must perform.",
    "What are the five arkan al-Islam with their Arabic names?",
    "Explain each of the five pillars of Islam.",
    "A new Muslim wants to know the five pillars of Islam — what are they?",
    "What is the hadith basis for the five pillars of Islam?",
]

SIX_IMAN_TEMPLATES = [
    "What are the 6 pillars of Iman?",
    "List the pillars of faith in Islam.",
    "What must a Muslim believe in according to Islam?",
    "Name the six pillars of Iman.",
    "What are the arkan of Iman?",
    "What are the six articles of faith in Islam?",
    "List the six things every Muslim is required to believe in.",
    "What does Islamic Iman (faith) require one to believe in?",
    "Explain the six pillars of Iman with Arabic terms.",
    "What are the six things mentioned in the Hadith of Jibril about Iman?",
    "List the six beliefs that define a Muslim's faith.",
    "What are the six pillars of faith (arkan al-iman) in Islam?",
]

FIVE_PRAYERS_TEMPLATES = [
    "What are the 5 daily prayers and their times?",
    "Name the five obligatory prayers in Islam with their rak'ahs.",
    "List the salah times and rak'ahs.",
    "What are the names of the five daily prayers?",
    "How many rak'ahs does each daily prayer have?",
    "List the fard prayers in Islam with their timings.",
    "What are the five obligatory salah and when are they prayed?",
    "Can you list all five daily prayers with their times and number of rak'ahs?",
    "What is the time for each of the five daily prayers?",
    "Name each salah, its timing, and how many rak'ahs it has.",
    "What are the timings and rak'ahs of the five fard salah?",
    "List the five daily prayers in Islam from Fajr to Isha.",
]

HAJJ_PILLARS_TEMPLATES = [
    "What are the pillars (arkan) of Hajj?",
    "List the obligatory acts of Hajj.",
    "What are the rukn of Hajj?",
    "Name the pillars of Hajj.",
    "What are the arkan al-Hajj?",
    "Which acts are considered pillars of Hajj that cannot be skipped?",
    "List the four pillars of Hajj.",
    "What are the essential pillars of the Hajj pilgrimage?",
    "What are the arkan of Hajj and why can they not be compensated with dam?",
    "Explain the pillars of Hajj.",
    "What are the four acts of Hajj that are considered fard rukn?",
    "List the pillars of Hajj with their Quranic references.",
]

# ─── Hard-coded data ────────────────────────────────────────────────────────────

# The 11 wives of the Prophet ﷺ (Ummahatul Mu'minin) in order
PROPHET_WIVES: list[dict[str, str]] = [
    {
        "name": "Khadijah bint Khuwaylid",
        "arabic": "خديجة بنت خويلد",
        "note": "First wife; first Muslim; mother of all the Prophet's ﷺ children except Ibrahim; married him for 25 years until her death",
    },
    {
        "name": "Sawda bint Zam'a",
        "arabic": "سودة بنت زمعة",
        "note": "Widow who had emigrated to Abyssinia; the Prophet ﷺ married her after Khadijah's death",
    },
    {
        "name": "Aisha bint Abi Bakr",
        "arabic": "عائشة بنت أبي بكر",
        "note": "Daughter of Abu Bakr; greatest female scholar of Islam; narrated ~2210 hadith; the Prophet ﷺ said 'Learn half your religion from Aisha'",
    },
    {
        "name": "Hafsa bint Umar",
        "arabic": "حفصة بنت عمر",
        "note": "Daughter of Umar ibn al-Khattab; widow of a Badr martyr; the original copy of the Quran was entrusted to her",
    },
    {
        "name": "Zaynab bint Khuzayma",
        "arabic": "زينب بنت خزيمة",
        "note": "Known as Umm al-Masakin (Mother of the Poor) for her great charity; died about two or three months after her marriage",
    },
    {
        "name": "Umm Salama (Hind bint Abi Umayyah)",
        "arabic": "أم سلمة",
        "note": "Among the first to emigrate to Abyssinia; last surviving wife of the Prophet ﷺ; a great transmitter of hadith",
    },
    {
        "name": "Zaynab bint Jahsh",
        "arabic": "زينب بنت جحش",
        "note": "Cousin of the Prophet ﷺ; her marriage was ordained by Allah in the Quran (33:37) to abolish a pre-Islamic custom",
    },
    {
        "name": "Juwayriya bint al-Harith",
        "arabic": "جويرية بنت الحارث",
        "note": "From the Banu Mustaliq tribe; her marriage led to the freeing of many captives",
    },
    {
        "name": "Umm Habiba (Ramlah bint Abi Sufyan)",
        "arabic": "أم حبيبة",
        "note": "Daughter of Abu Sufyan; emigrated to Abyssinia; the Negus arranged her marriage to the Prophet ﷺ on his behalf",
    },
    {
        "name": "Safiyya bint Huyayy",
        "arabic": "صفية بنت حيي",
        "note": "From the Banu Nadir tribe; descendant of Harun (Aaron) ﷺ; married after the Battle of Khaybar",
    },
    {
        "name": "Maymuna bint al-Harith",
        "arabic": "ميمونة بنت الحارث",
        "note": "Last woman the Prophet ﷺ married; known for her piety and generosity; the only wife the Prophet ﷺ married while in ihram (disputed — majority say it was after exiting ihram)",
    },
]

# Five Pillars of Islam
FIVE_PILLARS: list[dict[str, str]] = [
    {
        "name": "Shahada",
        "arabic": "الشهادة",
        "description": "Testimony of faith — 'There is no god but Allah and Muhammad ﷺ is His Messenger'; the foundation of all Islam",
    },
    {
        "name": "Salah",
        "arabic": "الصلاة",
        "description": "Five daily prayers — Fajr, Dhuhr, Asr, Maghrib, and Isha; obligatory for every Muslim (Quran 2:43)",
    },
    {
        "name": "Zakat",
        "arabic": "الزكاة",
        "description": "Obligatory charity — 2.5% of savings above the nisab threshold given annually to the eight categories in Quran 9:60",
    },
    {
        "name": "Sawm",
        "arabic": "الصوم",
        "description": "Fasting the month of Ramadan — abstaining from food, drink, and intimacy from Fajr to sunset (Quran 2:183–185)",
    },
    {
        "name": "Hajj",
        "arabic": "الحج",
        "description": "Pilgrimage to Makkah — obligatory once in a lifetime for those who have the means and ability (Quran 3:97)",
    },
]

# Six Pillars of Iman
SIX_IMAN: list[dict[str, str]] = [
    {
        "name": "Belief in Allah",
        "arabic": "الإيمان بالله",
        "description": "Belief in the existence and oneness of Allah (Tawhid) — His names, attributes, and absolute lordship",
    },
    {
        "name": "Belief in the Angels",
        "arabic": "الإيمان بالملائكة",
        "description": "Belief in the angels created from light who obey Allah without question and carry out His commands",
    },
    {
        "name": "Belief in the Books",
        "arabic": "الإيمان بالكتب",
        "description": "Belief in all scriptures Allah revealed — including the Tawrah, Zabur, Injeel, and the final Quran (preserved and complete)",
    },
    {
        "name": "Belief in the Prophets",
        "arabic": "الإيمان بالرسل",
        "description": "Belief in all prophets sent by Allah — from Adam ﷺ to the seal of prophets, Muhammad ﷺ — without distinction (Quran 2:285)",
    },
    {
        "name": "Belief in the Day of Judgment",
        "arabic": "الإيمان باليوم الآخر",
        "description": "Belief in the Last Day — resurrection, the Reckoning, paradise (Jannah) and hellfire (Jahannam)",
    },
    {
        "name": "Belief in Divine Decree (Qadar)",
        "arabic": "الإيمان بالقدر",
        "description": "Belief that all good and bad is from Allah's knowledge and decree — and that striving and supplication are themselves part of that decree (Hadith Jibril — Muslim 8)",
    },
]

# Ulul Azm — the 5 prophets of great determination
ULUL_AZM: list[dict[str, str]] = [
    {
        "name": "Nuh (Noah)",
        "arabic": "نُوح",
        "description": "Called his people for 950 years without giving up; first Rasul sent to humanity; survived the Great Flood by Allah's command (Quran 29:14, 71:1-28)",
    },
    {
        "name": "Ibrahim (Abraham)",
        "arabic": "إِبْرَاهِيم",
        "description": "Khalilullah (Friend of Allah); thrown into fire for rejecting idols; commanded to sacrifice his son and both submitted; built the Ka'bah (Quran 2:124, 37:83-113)",
    },
    {
        "name": "Musa (Moses)",
        "arabic": "مُوسَى",
        "description": "Kalimullah (Spoke directly with Allah); confronted Pharaoh, parted the sea, received the Torah at Mount Sinai; most mentioned prophet in the Quran",
    },
    {
        "name": "Isa (Jesus)",
        "arabic": "عِيسَى",
        "description": "Ruhullah (Spirit from Allah); born of a virgin; performed great miracles by Allah's permission; raised to heaven by Allah and will return before the Day of Judgment",
    },
    {
        "name": "Muhammad ﷺ",
        "arabic": "مُحَمَّد",
        "description": "Khatam al-Nabiyyin (Seal of the Prophets); Habibullah (Beloved of Allah); sent as a mercy to all worlds (Quran 21:107); his message is final and universal",
    },
]

# ─── Loaders ───────────────────────────────────────────────────────────────────


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_prophets_data() -> dict[str, Any]:
    return _load_json(KB_DIR / "prophets_in_islam.json")


def load_sahabah_data() -> dict[str, Any]:
    return _load_json(KB_DIR / "sahabah_biographies.json")


def load_ibadah_data() -> dict[str, Any]:
    return _load_json(KB_DIR / "ibadah_salah_zakat_fasting_hajj.json")


# ─── Answer builders ───────────────────────────────────────────────────────────

def _numbered_list(
    items: list[dict[str, str]],
    name_key: str = "name",
    arabic_key: str | None = "arabic",
    desc_key: str | None = "description",
) -> str:
    """Build a numbered list string from a list of dicts."""
    lines: list[str] = []
    for i, item in enumerate(items, 1):
        name = item.get(name_key, "")
        arabic = item.get(arabic_key, "") if arabic_key else ""
        desc = item.get(desc_key, "") if desc_key else ""

        if arabic and desc:
            lines.append(f"{i}. **{name}** ({arabic}) — {desc}")
        elif arabic:
            lines.append(f"{i}. **{name}** ({arabic})")
        elif desc:
            lines.append(f"{i}. **{name}** — {desc}")
        else:
            lines.append(f"{i}. **{name}**")
    return "\n".join(lines)


def build_prophets_answer(data: dict[str, Any]) -> str:
    prophets = data["prophets"]
    intro = (
        "Islam recognizes 25 prophets mentioned by name in the Quran. "
        "We are required to believe in all of them without distinction (Quran 2:136, 2:285). "
        "The total number of prophets sent by Allah is 124,000 according to hadith (Musnad Ahmad 22342), "
        "but only these 25 are named in the Quran."
    )
    items: list[str] = []
    for p in prophets:
        num = p["number"]
        name_en = p["name_english"]
        name_ar = p.get("name_arabic", "")
        title = p.get("title", "")
        title_part = f" — {title}" if title else ""
        items.append(f"{num}. **{name_en}** ({name_ar}){title_part}")

    note = (
        "**Note:** Belief in all prophets is the 4th pillar of Iman. "
        "All prophets shared five qualities: Siddiq (Truthful), Amanah (Trustworthy), "
        "Tabligh (Conveying), Fatanah (Intelligence), and Ismah (Protection from major sin)."
    )
    return f"**The 25 Prophets Mentioned in the Quran**\n\n{intro}\n\n" + "\n".join(items) + f"\n\n{note}"


def build_ulul_azm_answer() -> str:
    intro = (
        "Ulul Azm (أُولُو الْعَزْم) means 'those possessing strong will and firm determination.' "
        "These are the five greatest prophets, mentioned in the Quran (46:35) as those who showed "
        "the most extraordinary patience and perseverance in conveying Allah's message."
    )
    body = _numbered_list(ULUL_AZM, name_key="name", arabic_key="arabic", desc_key="description")
    note = (
        "**Note:** The Prophet ﷺ is the greatest of all prophets and the last. "
        "On the Day of Judgment, the intercession (shafa'ah al-uzma) will be given to Prophet Muhammad ﷺ. "
        "All Muslims must love and honor all five of these noble messengers."
    )
    return f"**Ulul Azm — The Five Prophets of Great Determination**\n\n{intro}\n\n{body}\n\n{note}"


def build_wives_answer(female_companions: list[dict[str, Any]]) -> str:
    intro = (
        "The Prophet Muhammad ﷺ had 11 wives in total. They are honored with the title "
        "Ummahatul Mu'minin (أُمَّهَاتُ الْمُؤْمِنِين — Mothers of the Believers) as designated "
        "by Allah in the Quran (33:6). Muslims are obligated to respect and love them all."
    )
    items: list[str] = []
    for i, wife in enumerate(PROPHET_WIVES, 1):
        name = wife["name"]
        arabic = wife["arabic"]
        note = wife["note"]
        items.append(f"{i}. **{name}** ({arabic}) — {note}")

    closing_note = (
        "**Note:** Khadijah RA and Aisha RA are especially prominent — Khadijah was the first Muslim "
        "and supported the Prophet ﷺ unconditionally, while Aisha transmitted half the private Sunnah "
        "of the Prophet's ﷺ household. All 11 are guaranteed Paradise as Mothers of the Believers."
    )
    return (
        f"**The Wives of the Prophet ﷺ (Ummahatul Mu'minin)**\n\n{intro}\n\n"
        + "\n".join(items)
        + f"\n\n{closing_note}"
    )


def build_caliphs_answer(caliphs: list[dict[str, Any]]) -> str:
    intro = (
        "The Khulafa Rashidun (الْخُلَفَاءُ الرَّاشِدُون — Rightly Guided Caliphs) are the four "
        "companions who led the Muslim community after the Prophet ﷺ passed away. "
        "The Prophet ﷺ said: 'Hold fast to my Sunnah and the Sunnah of the Rightly Guided Caliphs after me' "
        "(Abu Dawud 4607, Tirmidhi 2676 — Sahih)."
    )
    items: list[str] = []
    for i, caliph in enumerate(caliphs, 1):
        name = caliph["name"]
        arabic = caliph.get("arabic", "")
        title = caliph.get("title", "")
        caliphate = caliph.get("caliphate", "")
        desc = f"{title}; caliphate: {caliphate}" if title and caliphate else (title or caliphate)
        if arabic:
            items.append(f"{i}. **{name}** ({arabic}) — {desc}")
        else:
            items.append(f"{i}. **{name}** — {desc}")

    note = (
        "**Note:** The Sunni position affirms this order of succession as correct and blessed. "
        "Quran 9:100 praises all the Companions. We hold all four in love and highest respect."
    )
    return (
        f"**The Four Rightly Guided Caliphs (Khulafa Rashidun)**\n\n{intro}\n\n"
        + "\n".join(items)
        + f"\n\n{note}"
    )


def build_ten_paradise_answer(ten_data: dict[str, Any]) -> str:
    intro = (
        "Al-Asharatu al-Mubashsharun (الْعَشَرَةُ الْمُبَشَّرُون — The Ten Given Glad Tidings) are "
        "the ten companions whom the Prophet ﷺ named in a single hadith as being promised Paradise. "
        "Source: Abu Dawud 4649, Tirmidhi 3748 — Sahih."
    )
    the_ten: list[str] = ten_data.get("the_ten", [])
    individual_notes: list[dict] = ten_data.get("individual_notes", [])
    notes_map: dict[str, str] = {n["name"]: n.get("distinction", "") for n in individual_notes}

    # Titles for the first four (from rightly_guided_caliphs titles)
    titles_map: dict[str, str] = {
        "Abu Bakr as-Siddiq": "As-Siddiq (The Truthful Confirmer) — 1st Caliph",
        "Umar ibn al-Khattab": "Al-Faruq (The Distinguisher of Truth from Falsehood) — 2nd Caliph",
        "Uthman ibn Affan": "Dhul Nurayn (Possessor of Two Lights) — 3rd Caliph",
        "Ali ibn Abi Talib": "Asadullah (Lion of Allah) — 4th Caliph",
    }

    items: list[str] = []
    for i, name in enumerate(the_ten, 1):
        if name in titles_map:
            desc = titles_map[name]
        elif name in notes_map and notes_map[name]:
            desc = notes_map[name]
        else:
            desc = "Among the greatest companions of the Prophet ﷺ"
        items.append(f"{i}. **{name}** — {desc}")

    note = (
        "**Note:** This list comes from a single hadith in which the Prophet ﷺ named all ten together. "
        "There are other companions individually promised paradise in other narrations (e.g. Bilal RA, "
        "Khadijah RA), but these ten are promised in this specific well-known hadith."
    )
    return (
        f"**The Ten Companions Promised Paradise (Ashra Mubasshara)**\n\n{intro}\n\n"
        + "\n".join(items)
        + f"\n\n{note}"
    )


def build_five_pillars_answer() -> str:
    intro = (
        "The five pillars of Islam (أَرْكَانُ الْإِسْلَام) are the foundational acts of worship "
        "that every Muslim must observe. They are derived from the famous Hadith of Jibril "
        "(Muslim 8) and Bukhari 8: 'Islam is built on five things.'"
    )
    body = _numbered_list(FIVE_PILLARS, name_key="name", arabic_key="arabic", desc_key="description")
    note = (
        "**Note:** These are the structural pillars — neglecting the Shahada makes one a non-Muslim; "
        "neglecting the others (without denial) is a major sin. "
        "Together they form the complete framework of a Muslim's life."
    )
    return f"**The Five Pillars of Islam (Arkan al-Islam)**\n\n{intro}\n\n{body}\n\n{note}"


def build_six_iman_answer() -> str:
    intro = (
        "The six pillars of Iman (أَرْكَانُ الْإِيمَان — pillars of faith) are what every Muslim "
        "must believe in the heart. They come from the Hadith of Jibril when he asked the Prophet ﷺ "
        "about Iman — Sahih Muslim 8."
    )
    body = _numbered_list(SIX_IMAN, name_key="name", arabic_key="arabic", desc_key="description")
    note = (
        "**Note:** Denying any one of the six pillars takes a person outside the fold of Islam. "
        "Belief in Qadar (divine decree) includes both good and bad — meaning everything happens "
        "by Allah's knowledge and will, while humans still have free will and responsibility."
    )
    return f"**The Six Pillars of Iman (Arkan al-Iman)**\n\n{intro}\n\n{body}\n\n{note}"


def build_five_prayers_answer(prayers: list[dict[str, Any]]) -> str:
    intro = (
        "The five daily prayers (الصَّلَوَاتُ الْخَمْس) are the second pillar of Islam and "
        "obligatory (fard) on every Muslim. The Prophet ﷺ said they are the pillar of the religion "
        "(Tirmidhi 2616). They were prescribed during the Night Journey (Al-Isra wal-Mi'raj)."
    )
    items: list[str] = []
    for i, prayer in enumerate(prayers, 1):
        name = prayer["name"]
        rakats = prayer["rakats"]
        time_start = prayer.get("time_start", "")
        time_end = prayer.get("time_end", "")
        desc = f"{rakats} rak'ahs; time: {time_start} to {time_end}"
        items.append(f"{i}. **{name}** — {desc}")

    note = (
        "**Note:** These five prayers combine to a total of 17 fard rak'ahs daily. "
        "The Prophet ﷺ said: 'The first thing a person will be asked about on the Day of Judgment "
        "is their salah. If it is good, the rest of their deeds will be good.' (Abu Dawud 864, Sahih)"
    )
    return (
        f"**The Five Daily Prayers (Al-Salawat al-Khams)**\n\n{intro}\n\n"
        + "\n".join(items)
        + f"\n\n{note}"
    )


def build_hajj_pillars_answer(hajj_data: dict[str, Any]) -> str:
    intro = (
        "The arkan (أَرْكَان — pillars) of Hajj are the essential acts without which the Hajj is "
        "not valid and cannot be compensated by a penalty (dam). Missing any rukn invalidates the "
        "entire Hajj. They are agreed upon by the majority of scholars."
    )
    arkan: list[str] = hajj_data.get("pillars_arkan_of_hajj", [])
    items: list[str] = []
    for i, rukn in enumerate(arkan, 1):
        # Split reference from the main text if present (format: "Text — Reference")
        if " — " in rukn:
            main, ref = rukn.split(" — ", 1)
            items.append(f"{i}. **{main.strip()}** — {ref.strip()}")
        else:
            items.append(f"{i}. **{rukn.strip()}**")

    note = (
        "**Note:** The most important pillar is Wuquf at Arafah — the Prophet ﷺ said: "
        "'Hajj is Arafah' (Tirmidhi 889, Sahih). Missing Arafah invalidates the entire Hajj. "
        "The wajibat (obligatory but not arkan) acts, such as staying at Muzdalifah and stoning "
        "the Jamaraat, can be compensated with a sacrifice (dam) if missed."
    )
    return (
        f"**The Pillars of Hajj (Arkan al-Hajj)**\n\n{intro}\n\n"
        + "\n".join(items)
        + f"\n\n{note}"
    )


# ─── Pair generators ───────────────────────────────────────────────────────────

def _make_pair(
    instruction: str,
    output: str,
    sub_category: str,
    topic: str,
) -> dict[str, Any]:
    return {
        "instruction": instruction,
        "input": "",
        "output": output,
        "metadata": {
            "category": "lists",
            "sub_category": sub_category,
            "topic": topic,
        },
    }


def gen_prophets_pairs(
    prophets_data: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    answer = build_prophets_answer(prophets_data)
    pairs = [_make_pair(t, answer, "prophets", "25 prophets in the Quran") for t in templates]
    return pairs


def gen_ulul_azm_pairs(
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    answer = build_ulul_azm_answer()
    return [_make_pair(t, answer, "ulul_azm", "Ulul Azm — 5 greatest prophets") for t in templates]


def gen_wives_pairs(
    sahabah_data: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    female_companions = sahabah_data.get("female_companions_sahabiyyat", [])
    answer = build_wives_answer(female_companions)
    return [_make_pair(t, answer, "wives", "Ummahatul Mu'minin — Mothers of the Believers") for t in templates]


def gen_caliphs_pairs(
    sahabah_data: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    caliphs = sahabah_data.get("rightly_guided_caliphs", [])
    answer = build_caliphs_answer(caliphs)
    return [_make_pair(t, answer, "caliphs", "Khulafa Rashidun — Four Rightly Guided Caliphs") for t in templates]


def gen_ten_paradise_pairs(
    sahabah_data: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    ten_data = sahabah_data.get("ten_promised_paradise", {})
    answer = build_ten_paradise_answer(ten_data)
    return [_make_pair(t, answer, "ten_paradise", "Ashra Mubasshara — Ten Promised Paradise") for t in templates]


def gen_five_pillars_pairs(
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    answer = build_five_pillars_answer()
    return [_make_pair(t, answer, "pillars", "Five Pillars of Islam") for t in templates]


def gen_six_iman_pairs(
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    answer = build_six_iman_answer()
    return [_make_pair(t, answer, "iman", "Six Pillars of Iman") for t in templates]


def gen_five_prayers_pairs(
    ibadah_data: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    prayers = ibadah_data["salah"]["five_daily_prayers"]
    answer = build_five_prayers_answer(prayers)
    return [_make_pair(t, answer, "salah", "Five Daily Prayers") for t in templates]


def gen_hajj_pillars_pairs(
    ibadah_data: dict[str, Any],
    rng: random.Random,
    templates: list[str],
) -> list[dict[str, Any]]:
    hajj_data = ibadah_data["hajj"]
    answer = build_hajj_pillars_answer(hajj_data)
    return [_make_pair(t, answer, "hajj", "Pillars (Arkan) of Hajj") for t in templates]


# ─── Entry point ───────────────────────────────────────────────────────────────

def generate_lists_pairs(seed: int = 42) -> list[dict[str, Any]]:
    """
    Generate Q&A training pairs for list/names type questions.

    Returns a list of dicts each with keys:
        instruction, input, output, metadata
    where metadata contains:
        category: "lists"
        sub_category: one of "prophets" / "wives" / "caliphs" / "ten_paradise" /
                              "pillars" / "iman" / "salah" / "hajj"
        topic: descriptive string
    """
    rng = random.Random(seed)

    # Load source data
    prophets_data = load_prophets_data()
    sahabah_data = load_sahabah_data()
    ibadah_data = load_ibadah_data()

    all_pairs: list[dict[str, Any]] = []

    # 1. 25 Prophets of Islam
    all_pairs.extend(gen_prophets_pairs(prophets_data, rng, PROPHETS_TEMPLATES))

    # 2. Ulul Azm — 5 Greatest Prophets
    all_pairs.extend(gen_ulul_azm_pairs(rng, ULUL_AZM_TEMPLATES))

    # 3. Prophet's Wives (Ummahatul Mu'minin)
    all_pairs.extend(gen_wives_pairs(sahabah_data, rng, WIVES_TEMPLATES))

    # 4. Four Rightly Guided Caliphs (Khulafa Rashidun)
    all_pairs.extend(gen_caliphs_pairs(sahabah_data, rng, CALIPHS_TEMPLATES))

    # 5. Ten Companions Promised Paradise (Ashra Mubasshara)
    all_pairs.extend(gen_ten_paradise_pairs(sahabah_data, rng, TEN_PARADISE_TEMPLATES))

    # 6. Five Pillars of Islam
    all_pairs.extend(gen_five_pillars_pairs(rng, FIVE_PILLARS_TEMPLATES))

    # 7. Six Pillars of Iman
    all_pairs.extend(gen_six_iman_pairs(rng, SIX_IMAN_TEMPLATES))

    # 8. Five Daily Prayers
    all_pairs.extend(gen_five_prayers_pairs(ibadah_data, rng, FIVE_PRAYERS_TEMPLATES))

    # 9. Pillars of Hajj
    all_pairs.extend(gen_hajj_pillars_pairs(ibadah_data, rng, HAJJ_PILLARS_TEMPLATES))

    logger.info("Generated %d list Q&A pairs total.", len(all_pairs))
    return all_pairs


# ─── CLI ───────────────────────────────────────────────────────────────────────

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate list/names Q&A training pairs for the Islamic AI model."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the output JSON file (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: %(default)s)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: %(default)s)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: %(default)s)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s | %(name)s | %(message)s",
        stream=sys.stderr,
    )

    pairs = generate_lists_pairs(seed=args.seed)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": {
            "title": "Islamic Lists Q&A Training Pairs",
            "description": (
                "Training pairs teaching the model to answer list/names questions "
                "with a clean numbered-list format."
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "seed": args.seed,
            "total_pairs": len(pairs),
            "categories": [
                "prophets",
                "ulul_azm",
                "wives",
                "caliphs",
                "ten_paradise",
                "pillars",
                "iman",
                "salah",
                "hajj",
            ],
        },
        "pairs": pairs,
    }

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=args.indent)

    print(f"Wrote {len(pairs)} pairs → {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
