"""
Helper module: generate Q&A training pairs from Quran data.

Imported by generate_qa_pairs.py — not run directly.
"""

from __future__ import annotations

import random
from typing import Any

# ─── Question templates per category ─────────────────────────────────────────

_DIRECT_VERSE_QUESTIONS: list[str] = [
    "What does Allah ﷻ say in Surah {name} ({num}:{ayah})?",
    "What is the meaning of Quran {num}:{ayah} (Surah {name})?",
    "Please share Surah {name}, Ayah {ayah} with its translation.",
    "Recite and explain verse {ayah} of Surah {name} (Surah {num}).",
    "What does the Quran say in Surah {name}, verse {ayah}?",
]

_RECITATION_QUESTIONS: list[str] = [
    "What is the Arabic text and English translation of Quran {num}:{ayah}?",
    "Share the Arabic of Surah {name}, Ayah {ayah} with its meaning.",
    "Give me the Arabic recitation and meaning of Quran {num}:{ayah} ({name}).",
]

_REFLECTION_QUESTIONS: list[str] = [
    "What lesson can Muslims reflect upon in Quran {num}:{ayah} (Surah {name})?",
    "How should a believer apply the teaching of Surah {name}, verse {ayah} in daily life?",
    "What does Surah {name} verse {ayah} teach us about our relationship with Allah ﷻ?",
]

_STUDY_QUESTIONS: list[str] = [
    "Explain Surah {name} Ayah {ayah} in detail with commentary.",
    "Provide a detailed explanation of Quran {num}:{ayah} from Surah {name}.",
    "What do scholars say about the meaning of Surah {name}, verse {ayah}?",
]

_SURAH_OVERVIEW_QUESTIONS: list[str] = [
    "What is the theme and significance of Surah {name} in the Quran?",
    "Give a brief overview of Surah {name} (Surah {num}).",
    "What topics does Surah {name} cover?",
]

_TOPIC_QURAN_QUESTIONS: list[str] = [
    "What does the Quran say about {topic}?",
    "What guidance does Allah ﷻ give about {topic} in the Quran?",
    "How does the Quran address the subject of {topic}?",
    "What does Allah ﷻ teach us about {topic}?",
]

# ─── Topic keyword taxonomy ───────────────────────────────────────────────────

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "prayer (Salah)":            ["pray", "prayer", "salah", "prostrat", "bow", "worship", "sajda", "rukoo", "qiyam"],
    "fasting (Sawm)":            ["fast", "fasting", "sawm", "ramadan", "hunger", "thirst", "abstain"],
    "charity (Zakat/Sadaqah)":   ["zakat", "charity", "alms", "give", "spend", "poor", "sadaqah", "tithe"],
    "Hajj and pilgrimage":       ["hajj", "pilgrimage", "kaaba", "mecca", "ihram", "circumambulat", "tawaf"],
    "patience (Sabr)":           ["patient", "patience", "persever", "endur", "sabr", "hardship", "trial", "tribulation"],
    "gratitude (Shukr)":         ["grateful", "gratitude", "thank", "shukr", "bless", "favor"],
    "repentance (Tawbah)":       ["repent", "tawbah", "forgiv", "sin", "turn to allah", "seek forgiveness"],
    "the Day of Judgment":       ["judgment", "resurrect", "reckoning", "hereafter", "day of", "account", "qiyamah"],
    "Paradise (Jannah)":         ["paradise", "jannah", "garden", "reward", "bliss", "rivers beneath"],
    "Hellfire (Jahannam)":       ["hellfire", "hell", "jahannam", "punish", "torment", "fire", "blazing"],
    "seeking knowledge":         ["knowledge", "learn", "wisdom", "understand", "seek", "ilm", "scholar"],
    "honesty and truthfulness":  ["honest", "truth", "truthful", "lie", "false", "sincere", "trust"],
    "parents and family":        ["parent", "mother", "father", "kin", "kinship", "womb", "family", "relative"],
    "justice (Adl)":             ["just", "justice", "fair", "equity", "balance", "oppress", "wrong"],
    "faith (Iman)":              ["believ", "faith", "iman", "trust", "tawakkul", "certain", "doubt"],
    "taqwa (God-consciousness)": ["taqwa", "pious", "righteous", "conscious", "fear allah", "god-fearing"],
    "death and the afterlife":   ["death", "die", "soul", "grave", "afterlife", "funeral", "akhirah"],
    "angels":                    ["angel", "angels", "jibril", "gabriel", "celestial being"],
    "the Prophets":              ["prophet", "messenger", "noah", "ibrahim", "moses", "jesus", "muhammad", "rasul"],
    "the Quran and revelation":  ["quran", "book", "recit", "revelation", "surah", "ayah", "scripture"],
    "marriage and family":       ["marriage", "nikah", "spouse", "husband", "wife", "wed"],
    "business and trade":        ["trade", "business", "transaction", "riba", "interest", "contract", "market"],
    "food and drink (halal)":    ["eat", "food", "drink", "halal", "haram", "forbid", "permitt", "swine", "intoxicant"],
    "purification (Taharah)":    ["pure", "purif", "clean", "taharah", "wudu", "ghusl", "wash"],
    "the unity of Allah (Tawhid)": ["one", "alone", "no partner", "associate", "shirk", "monothe", "tawhid"],
    "the creation":              ["creat", "heaven", "earth", "sky", "universe", "signs of allah", "sun", "moon"],
    "dhikr and remembrance":     ["rememb", "dhikr", "mention", "glorif", "praise allah", "subhanallah"],
    "brotherhood and unity":     ["brother", "unity", "ummah", "together", "community", "bond"],
    "humility and pride":        ["humble", "humility", "arrogant", "pride", "boast", "vain", "modest"],
    "charity to the needy":      ["orphan", "needy", "poor", "widows", "traveler", "feed"],
}


def extract_topic(text: str) -> str | None:
    """Find the first matching Islamic topic in a text string.

    Args:
        text: English text (verse translation or hadith).

    Returns:
        Topic label string, or None if no topic matched.
    """
    lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return topic
    return None


# ─── Answer formatters ────────────────────────────────────────────────────────

def format_verse_answer(
    surah_name: str,
    surah_num: int,
    ayah_num: int,
    arabic: str,
    english: str,
    tafsir: str = "",
) -> str:
    """Build a complete, formatted answer for a Quranic verse.

    Args:
        surah_name: Surah name in English (e.g. 'Al-Baqarah').
        surah_num: Surah number (1–114).
        ayah_num: Ayah number within the surah.
        arabic: Arabic text of the verse.
        english: English translation.
        tafsir: Optional Ibn Kathir commentary.

    Returns:
        Formatted multi-line answer string.
    """
    parts: list[str] = [
        f"Allah ﷻ says in Surah {surah_name} ({surah_num}:{ayah_num}):\n",
        arabic,
        f'\nTranslation (Sahih International):\n"{english}"',
    ]
    if tafsir and len(tafsir.strip()) > 50:
        # Truncate very long tafsir for training (keep first 600 chars)
        tafsir_short = tafsir.strip()
        if len(tafsir_short) > 600:
            tafsir_short = tafsir_short[:600].rsplit(" ", 1)[0] + "..."
        parts.append(f"\nIbn Kathir explains:\n{tafsir_short}")
    return "\n".join(parts)


def format_surah_overview_answer(surah: dict[str, Any]) -> str:
    """Build a surah overview answer using the first ayah as an example.

    Args:
        surah: Surah dict from quran_full.json.

    Returns:
        Formatted multi-line overview string.
    """
    name = surah.get("name_english", "")
    num = surah.get("surah_number", "")
    transliteration = surah.get("name_transliteration", name)
    revelation = surah.get("revelation_type", "").capitalize()
    ayah_count = surah.get("ayah_count", 0)
    ayahs = surah.get("ayahs", [])

    rev_location = "Makkah" if revelation.lower() in ("mecca", "meccan", "makkah", "makki") else "Madinah"

    lines: list[str] = [
        f"Surah {transliteration} ({name}), Surah {num} of the Quran, is a "
        f"{revelation} surah revealed in {rev_location}, consisting of {ayah_count} ayahs.\n",
    ]

    if ayahs:
        first = ayahs[0]
        lines.append(
            f"The surah begins with Allah ﷻ saying ({num}:1):\n\n"
            f"{first.get('arabic_text', '')}\n\n"
            f'"{first.get("english_translation", "")}"'
        )

    if ayah_count > 1 and len(ayahs) >= ayah_count:
        last = ayahs[-1]
        lines.append(
            f"\nThe surah concludes ({num}:{ayah_count}):\n\n"
            f"{last.get('arabic_text', '')}\n\n"
            f'"{last.get("english_translation", "")}"'
        )

    return "\n".join(lines)


# ─── Pair generators ──────────────────────────────────────────────────────────

def generate_direct_verse_pairs(
    quran_data: dict[str, Any],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate one Q&A pair per Quranic ayah (direct reference questions).

    Args:
        quran_data: Parsed quran_full.json dict.
        rng: Seeded random instance for reproducibility.

    Returns:
        List of Q&A pair dicts.
    """
    pairs: list[dict[str, Any]] = []

    for surah in quran_data.get("surahs", []):
        s_num = surah["surah_number"]
        s_name = surah.get("name_english", f"Surah {s_num}")
        s_name_t = surah.get("name_transliteration", s_name)

        for ayah in surah.get("ayahs", []):
            a_num = ayah["ayah_number"]
            arabic = ayah.get("arabic_text", "")
            english = ayah.get("english_translation", "")
            tafsir = ayah.get("tafsir_ibn_kathir", "")

            if not arabic or not english:
                continue

            template = rng.choice(_DIRECT_VERSE_QUESTIONS)
            question = template.format(name=s_name_t, num=s_num, ayah=a_num)
            answer = format_verse_answer(s_name_t, s_num, a_num, arabic, english, tafsir)

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "metadata": {
                    "category": "quran_direct",
                    "sources": [f"quran:{s_num}:{a_num}"],
                },
            })

    return pairs


def generate_surah_overview_pairs(
    quran_data: dict[str, Any],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate surah overview Q&A pairs (3 variants per surah).

    Args:
        quran_data: Parsed quran_full.json dict.
        rng: Seeded random instance.

    Returns:
        List of Q&A pair dicts.
    """
    pairs: list[dict[str, Any]] = []

    for surah in quran_data.get("surahs", []):
        s_num = surah["surah_number"]
        s_name = surah.get("name_transliteration", surah.get("name_english", f"Surah {s_num}"))
        answer = format_surah_overview_answer(surah)

        for template in rng.sample(_SURAH_OVERVIEW_QUESTIONS, min(3, len(_SURAH_OVERVIEW_QUESTIONS))):
            question = template.format(name=s_name, num=s_num)
            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "metadata": {
                    "category": "surah_meaning",
                    "sources": [f"quran:{s_num}:overview"],
                },
            })

    return pairs


def generate_topic_quran_pairs(
    quran_data: dict[str, Any],
    rng: random.Random,
    max_per_topic: int = 5,
) -> list[dict[str, Any]]:
    """Generate topic-based Quran Q&A pairs by grouping related ayahs.

    For each topic, finds ayahs matching topic keywords and combines up to 3
    related verses into one comprehensive answer.

    Args:
        quran_data: Parsed quran_full.json dict.
        rng: Seeded random instance.
        max_per_topic: Maximum Q&A pairs to generate per topic.

    Returns:
        List of Q&A pair dicts.
    """
    # Build flat list of all ayahs with metadata
    all_ayahs: list[dict[str, Any]] = []
    for surah in quran_data.get("surahs", []):
        s_num = surah["surah_number"]
        s_name = surah.get("name_transliteration", surah.get("name_english", ""))
        for ayah in surah.get("ayahs", []):
            if ayah.get("arabic_text") and ayah.get("english_translation"):
                all_ayahs.append({
                    **ayah,
                    "surah_number": s_num,
                    "surah_name": s_name,
                })

    pairs: list[dict[str, Any]] = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        # Find ayahs matching this topic
        matching = [
            a for a in all_ayahs
            if any(kw in a.get("english_translation", "").lower() for kw in keywords)
        ]
        if not matching:
            continue

        rng.shuffle(matching)
        # Generate up to max_per_topic pairs, each using 1–3 ayahs
        for i in range(min(max_per_topic, len(matching))):
            # Build answer from 1-2 most relevant ayahs
            chunk = matching[i : i + 2]
            answer_parts: list[str] = [
                f"Regarding {topic}, the Quran mentions the following:\n"
            ]
            source_keys: list[str] = []
            for a in chunk:
                vk = f"quran:{a['surah_number']}:{a['ayah_number']}"
                source_keys.append(vk)
                answer_parts.append(
                    format_verse_answer(
                        a["surah_name"],
                        a["surah_number"],
                        a["ayah_number"],
                        a["arabic_text"],
                        a["english_translation"],
                        a.get("tafsir_ibn_kathir", ""),
                    )
                )

            template = rng.choice(_TOPIC_QURAN_QUESTIONS)
            question = template.format(topic=topic)
            pairs.append({
                "instruction": question,
                "input": "",
                "output": "\n\n---\n\n".join(answer_parts[1:]),
                "metadata": {
                    "category": "quran_topic",
                    "sources": source_keys,
                },
            })

    return pairs


def generate_recitation_verse_pairs(
    quran_data: dict[str, Any],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate compact Arabic-focused pairs for every ayah (recitation angle).

    Answer format: Arabic text + citation reference + English translation only,
    without extended tafsir — trains the model to provide clean citations.

    Args:
        quran_data: Parsed quran_full.json dict.
        rng: Seeded random instance.

    Returns:
        List of Q&A pair dicts.
    """
    pairs: list[dict[str, Any]] = []

    for surah in quran_data.get("surahs", []):
        s_num = surah["surah_number"]
        s_name_t = surah.get("name_transliteration", surah.get("name_english", f"Surah {s_num}"))

        for ayah in surah.get("ayahs", []):
            a_num = ayah["ayah_number"]
            arabic = ayah.get("arabic_text", "")
            english = ayah.get("english_translation", "")

            if not arabic or not english:
                continue

            template = rng.choice(_RECITATION_QUESTIONS)
            question = template.format(name=s_name_t, num=s_num, ayah=a_num)
            answer = (
                f"Surah {s_name_t} ({s_num}:{a_num}):\n\n"
                f"{arabic}\n\n"
                f'Translation: "{english}"'
            )

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "metadata": {
                    "category": "quran_recitation",
                    "sources": [f"quran:{s_num}:{a_num}"],
                },
            })

    return pairs


def generate_reflection_verse_pairs(
    quran_data: dict[str, Any],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate lesson/reflection pairs for every ayah.

    Answer format: English translation first, then a brief reflection drawn
    from the first sentence of tafsir (or the translation itself when no tafsir).

    Args:
        quran_data: Parsed quran_full.json dict.
        rng: Seeded random instance.

    Returns:
        List of Q&A pair dicts.
    """
    pairs: list[dict[str, Any]] = []

    for surah in quran_data.get("surahs", []):
        s_num = surah["surah_number"]
        s_name_t = surah.get("name_transliteration", surah.get("name_english", f"Surah {s_num}"))

        for ayah in surah.get("ayahs", []):
            a_num = ayah["ayah_number"]
            arabic = ayah.get("arabic_text", "")
            english = ayah.get("english_translation", "")
            tafsir = ayah.get("tafsir_ibn_kathir", "")

            if not arabic or not english:
                continue

            if tafsir and len(tafsir.strip()) > 40:
                raw = tafsir.strip()
                first_sentence = raw.split(".")[0] + "." if "." in raw else raw[:200]
                reflection = first_sentence[:300]
            else:
                reflection = english[:200] if len(english) > 40 else english

            template = rng.choice(_REFLECTION_QUESTIONS)
            question = template.format(name=s_name_t, num=s_num, ayah=a_num)
            answer = (
                f"Allah ﷻ says in Surah {s_name_t} ({s_num}:{a_num}):\n\n"
                f"{arabic}\n\n"
                f'"{english}"\n\n'
                f"**Reflection:** {reflection}"
            )

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "metadata": {
                    "category": "quran_reflection",
                    "sources": [f"quran:{s_num}:{a_num}"],
                },
            })

    return pairs


def generate_study_verse_pairs(
    quran_data: dict[str, Any],
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Generate detailed study pairs for ayahs that have tafsir content.

    Produces pairs only when tafsir is available and substantial (> 100 chars)
    so answers are genuinely richer than direct-verse pairs.

    Args:
        quran_data: Parsed quran_full.json dict.
        rng: Seeded random instance.

    Returns:
        List of Q&A pair dicts.
    """
    pairs: list[dict[str, Any]] = []

    for surah in quran_data.get("surahs", []):
        s_num = surah["surah_number"]
        s_name_t = surah.get("name_transliteration", surah.get("name_english", f"Surah {s_num}"))

        for ayah in surah.get("ayahs", []):
            a_num = ayah["ayah_number"]
            arabic = ayah.get("arabic_text", "")
            english = ayah.get("english_translation", "")
            tafsir = ayah.get("tafsir_ibn_kathir", "")

            if not arabic or not english:
                continue
            if not tafsir or len(tafsir.strip()) < 100:
                continue

            tafsir_text = tafsir.strip()
            if len(tafsir_text) > 800:
                tafsir_text = tafsir_text[:800].rsplit(" ", 1)[0] + "..."

            template = rng.choice(_STUDY_QUESTIONS)
            question = template.format(name=s_name_t, num=s_num, ayah=a_num)
            answer = (
                f"**Surah {s_name_t} ({s_num}:{a_num})**\n\n"
                f"{arabic}\n\n"
                f'**Translation:** "{english}"\n\n'
                f"**Commentary (Ibn Kathir RH):**\n{tafsir_text}"
            )

            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "metadata": {
                    "category": "quran_study",
                    "sources": [f"quran:{s_num}:{a_num}"],
                },
            })

    return pairs
