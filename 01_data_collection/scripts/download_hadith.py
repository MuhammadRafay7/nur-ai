#!/usr/bin/env python3
"""
Download all Hadith collections + 99 Names of Allah.

Collections downloaded (English + Arabic merged):
  - Sahih Bukhari        → raw/hadith/bukhari.json
  - Sahih Muslim         → raw/hadith/muslim.json
  - Sunan Abu Dawud      → raw/hadith/abu_dawud.json
  - Jami at-Tirmidhi     → raw/hadith/tirmidhi.json
  - Sunan Ibn Majah      → raw/hadith/ibn_majah.json
  - Riyad as-Salihin     → raw/hadith/riyad_us_salihin.json

Supplementary:
  - 99 Names of Allah    → raw/supplementary/asmaul_husna.json

Source: https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/

Usage:
    python download_hadith.py
    python download_hadith.py --output-dir /custom/path
    python download_hadith.py --collections bukhari muslim
    python download_hadith.py --help
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp
from tqdm import tqdm

# ─── Constants ────────────────────────────────────────────────────────────────

CDN_BASE: str = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
GH_RAW_BASE: str = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"

MAX_RETRIES: int = 3
RETRY_BACKOFF_BASE: float = 2.0
REQUEST_DELAY: float = 0.5
TIMEOUT_SECONDS: int = 180         # Large files can take time

DEFAULT_HADITH_DIR: Path = Path(__file__).parent.parent / "raw" / "hadith"
DEFAULT_SUPP_DIR: Path = Path(__file__).parent.parent / "raw" / "supplementary"
LOG_DIR: Path = Path(__file__).parent.parent / "logs"

# Each entry: (api_name, output_filename, display_name, expected_min_count)
# For api_name, CDN URL = {CDN_BASE}/{lang}-{api_name}.json
# Fallback URL    = {GH_RAW_BASE}/{lang}-{api_name}.json
COLLECTIONS: list[tuple[str, str, str, int]] = [
    ("bukhari",          "bukhari.json",          "Sahih Bukhari",        5000),
    ("muslim",           "muslim.json",            "Sahih Muslim",         5000),
    ("abudawud",         "abu_dawud.json",         "Sunan Abu Dawud",      4000),
    ("tirmidhi",         "tirmidhi.json",          "Jami at-Tirmidhi",     2000),
    ("ibnmajah",         "ibn_majah.json",         "Sunan Ibn Majah",      3000),
    ("riyadussalihin",   "riyad_us_salihin.json",  "Riyad as-Salihin",     1000),
]

# Default hadith grade when not explicitly available in source data
DEFAULT_GRADE: str = "See source"


# ─── 99 Names of Allah (static authoritative data) ────────────────────────────

ASMAUL_HUSNA: list[dict[str, str]] = [
    {"number": 1,  "arabic": "ٱللَّٰه",        "transliteration": "Allah",       "meaning": "The Greatest Name / God",              "explanation": "The proper name of God in Islam, encompassing all divine attributes."},
    {"number": 2,  "arabic": "ٱلرَّحْمَٰن",    "transliteration": "Ar-Rahman",   "meaning": "The Most Gracious",                     "explanation": "The One who has abundant mercy for all of creation in this world."},
    {"number": 3,  "arabic": "ٱلرَّحِيم",      "transliteration": "Ar-Rahim",    "meaning": "The Most Merciful",                     "explanation": "The One who has special mercy for the believers in the Hereafter."},
    {"number": 4,  "arabic": "ٱلْمَلِك",       "transliteration": "Al-Malik",    "meaning": "The King / Sovereign",                  "explanation": "The One who has dominion over all things, the absolute ruler."},
    {"number": 5,  "arabic": "ٱلْقُدُّوس",    "transliteration": "Al-Quddus",   "meaning": "The Most Pure / Holy",                  "explanation": "The One who is free from all imperfections and deficiencies."},
    {"number": 6,  "arabic": "ٱلسَّلَام",      "transliteration": "As-Salam",    "meaning": "The Source of Peace",                   "explanation": "The One who is free from every imperfection, and grants peace."},
    {"number": 7,  "arabic": "ٱلْمُؤْمِن",    "transliteration": "Al-Mumin",    "meaning": "The Guardian of Faith",                 "explanation": "The One who bestows security and affirms His servants' faith."},
    {"number": 8,  "arabic": "ٱلْمُهَيْمِن",  "transliteration": "Al-Muhaymin", "meaning": "The Overseer / Guardian",               "explanation": "The One who watches over and protects all things."},
    {"number": 9,  "arabic": "ٱلْعَزِيز",     "transliteration": "Al-Aziz",     "meaning": "The Almighty",                          "explanation": "The One who is mighty and cannot be overcome by anything."},
    {"number": 10, "arabic": "ٱلْجَبَّار",    "transliteration": "Al-Jabbar",   "meaning": "The Compeller",                         "explanation": "The One who compels creation according to His will; He repairs what is broken."},
    {"number": 11, "arabic": "ٱلْمُتَكَبِّر", "transliteration": "Al-Mutakabbir","meaning": "The Supreme",                          "explanation": "The One who is supremely great; all greatness belongs to Him alone."},
    {"number": 12, "arabic": "ٱلْخَالِق",     "transliteration": "Al-Khaliq",   "meaning": "The Creator",                           "explanation": "The One who brings everything from non-existence into existence."},
    {"number": 13, "arabic": "ٱلْبَارِئ",     "transliteration": "Al-Bari",     "meaning": "The Originator",                        "explanation": "The One who creates without any prior model or example."},
    {"number": 14, "arabic": "ٱلْمُصَوِّر",   "transliteration": "Al-Musawwir", "meaning": "The Fashioner",                         "explanation": "The One who gives shape and form to all things in creation."},
    {"number": 15, "arabic": "ٱلْغَفَّار",    "transliteration": "Al-Ghaffar",  "meaning": "The Repeatedly Forgiving",              "explanation": "The One who forgives sins repeatedly, no matter how many times."},
    {"number": 16, "arabic": "ٱلْقَهَّار",    "transliteration": "Al-Qahhar",   "meaning": "The Subduer",                           "explanation": "The One who subdues and dominates all things with His power."},
    {"number": 17, "arabic": "ٱلْوَهَّاب",    "transliteration": "Al-Wahhab",   "meaning": "The Bestower",                          "explanation": "The One who gives freely and unconditionally without expectation."},
    {"number": 18, "arabic": "ٱلرَّزَّاق",    "transliteration": "Ar-Razzaq",   "meaning": "The Provider",                          "explanation": "The One who provides sustenance to all creatures continuously."},
    {"number": 19, "arabic": "ٱلْفَتَّاح",    "transliteration": "Al-Fattah",   "meaning": "The Opener",                            "explanation": "The One who opens doors of mercy, sustenance, and solutions."},
    {"number": 20, "arabic": "ٱلْعَلِيم",     "transliteration": "Al-Alim",     "meaning": "The All-Knowing",                       "explanation": "The One whose knowledge encompasses all things, seen and unseen."},
    {"number": 21, "arabic": "ٱلْقَابِض",     "transliteration": "Al-Qabid",    "meaning": "The Withholder",                        "explanation": "The One who withholds sustenance or souls according to His wisdom."},
    {"number": 22, "arabic": "ٱلْبَاسِط",     "transliteration": "Al-Basit",    "meaning": "The Expander",                          "explanation": "The One who expands provision and mercy as He wills."},
    {"number": 23, "arabic": "ٱلْخَافِض",     "transliteration": "Al-Khafid",   "meaning": "The Reducer",                           "explanation": "The One who lowers and humbles the arrogant and the unjust."},
    {"number": 24, "arabic": "ٱلرَّافِع",     "transliteration": "Ar-Rafi",     "meaning": "The Exalter",                           "explanation": "The One who raises the ranks of the believers and the righteous."},
    {"number": 25, "arabic": "ٱلْمُعِزّ",     "transliteration": "Al-Muizz",    "meaning": "The Honourer",                          "explanation": "The One who grants honour and dignity to whom He wills."},
    {"number": 26, "arabic": "ٱلْمُذِلّ",     "transliteration": "Al-Mudhill",  "meaning": "The Dishonourer",                       "explanation": "The One who brings disgrace upon the arrogant and rebellious."},
    {"number": 27, "arabic": "ٱلسَّمِيع",     "transliteration": "As-Sami",     "meaning": "The All-Hearing",                       "explanation": "The One who hears all sounds, public or private, loud or silent."},
    {"number": 28, "arabic": "ٱلْبَصِير",     "transliteration": "Al-Basir",    "meaning": "The All-Seeing",                        "explanation": "The One who sees all things, including what is hidden from all eyes."},
    {"number": 29, "arabic": "ٱلْحَكَم",      "transliteration": "Al-Hakam",    "meaning": "The Judge",                             "explanation": "The One who judges between creation with perfect justice."},
    {"number": 30, "arabic": "ٱلْعَدْل",      "transliteration": "Al-Adl",      "meaning": "The Just",                              "explanation": "The One who is perfectly just; He neither wrongs nor oppresses anyone."},
    {"number": 31, "arabic": "ٱللَّطِيف",     "transliteration": "Al-Latif",    "meaning": "The Subtle / Kind",                     "explanation": "The One who is kind and gentle; He knows the subtleties of all things."},
    {"number": 32, "arabic": "ٱلْخَبِير",     "transliteration": "Al-Khabir",   "meaning": "The All-Aware",                         "explanation": "The One who is informed of all inner secrets and hidden matters."},
    {"number": 33, "arabic": "ٱلْحَلِيم",     "transliteration": "Al-Halim",    "meaning": "The Forbearing",                        "explanation": "The One who delays punishment and does not hasten to punish the sinner."},
    {"number": 34, "arabic": "ٱلْعَظِيم",     "transliteration": "Al-Azim",     "meaning": "The Magnificent",                       "explanation": "The One who is supremely great in all of His attributes and actions."},
    {"number": 35, "arabic": "ٱلْغَفُور",     "transliteration": "Al-Ghafur",   "meaning": "The Forgiving",                         "explanation": "The One who forgives and covers sins entirely without punishing."},
    {"number": 36, "arabic": "ٱلشَّكُور",     "transliteration": "Ash-Shakur",  "meaning": "The Appreciative",                      "explanation": "The One who rewards greatly even for small deeds of His servants."},
    {"number": 37, "arabic": "ٱلْعَلِيّ",     "transliteration": "Al-Ali",      "meaning": "The Most High",                         "explanation": "The One who is exalted above all of creation in every way."},
    {"number": 38, "arabic": "ٱلْكَبِير",     "transliteration": "Al-Kabir",    "meaning": "The Greatest",                          "explanation": "The One who is greater than all things in attributes and power."},
    {"number": 39, "arabic": "ٱلْحَفِيظ",     "transliteration": "Al-Hafiz",    "meaning": "The Preserver",                         "explanation": "The One who preserves all things and guards them from destruction."},
    {"number": 40, "arabic": "ٱلْمُقِيت",     "transliteration": "Al-Muqit",    "meaning": "The Sustainer",                         "explanation": "The One who nourishes and sustains all of creation."},
    {"number": 41, "arabic": "ٱلْحَسِيب",     "transliteration": "Al-Hasib",    "meaning": "The Reckoner",                          "explanation": "The One who is sufficient and takes account of all deeds."},
    {"number": 42, "arabic": "ٱلْجَلِيل",     "transliteration": "Al-Jalil",    "meaning": "The Majestic",                          "explanation": "The One who is majestic and possessing attributes of perfect majesty."},
    {"number": 43, "arabic": "ٱلْكَرِيم",     "transliteration": "Al-Karim",    "meaning": "The Most Generous",                     "explanation": "The One who is generous without limit and gives without being asked."},
    {"number": 44, "arabic": "ٱلرَّقِيب",     "transliteration": "Ar-Raqib",    "meaning": "The Watchful",                          "explanation": "The One who watches over all things without lapse or oversight."},
    {"number": 45, "arabic": "ٱلْمُجِيب",     "transliteration": "Al-Mujib",    "meaning": "The Responsive",                        "explanation": "The One who responds to every dua and need of His servants."},
    {"number": 46, "arabic": "ٱلْوَاسِع",     "transliteration": "Al-Wasi",     "meaning": "The All-Encompassing",                  "explanation": "The One whose knowledge, mercy, and provision are boundless."},
    {"number": 47, "arabic": "ٱلْحَكِيم",     "transliteration": "Al-Hakim",    "meaning": "The All-Wise",                          "explanation": "The One who acts with perfect wisdom in all His decrees."},
    {"number": 48, "arabic": "ٱلْوَدُود",     "transliteration": "Al-Wadud",    "meaning": "The Loving",                            "explanation": "The One who loves His believing servants with profound love."},
    {"number": 49, "arabic": "ٱلْمَجِيد",     "transliteration": "Al-Majid",    "meaning": "The Glorious",                          "explanation": "The One who is glorious in His essence, attributes, and actions."},
    {"number": 50, "arabic": "ٱلْبَاعِث",     "transliteration": "Al-Baith",    "meaning": "The Resurrector",                       "explanation": "The One who will resurrect all of creation on the Day of Judgment."},
    {"number": 51, "arabic": "ٱلشَّهِيد",     "transliteration": "Ash-Shahid",  "meaning": "The Witness",                           "explanation": "The One who witnesses all things openly and secretly."},
    {"number": 52, "arabic": "ٱلْحَقّ",       "transliteration": "Al-Haqq",     "meaning": "The Truth",                             "explanation": "The One whose existence and attributes are absolutely true and certain."},
    {"number": 53, "arabic": "ٱلْوَكِيل",     "transliteration": "Al-Wakil",    "meaning": "The Trustee",                           "explanation": "The One who is the perfect trustee and guardian of all affairs."},
    {"number": 54, "arabic": "ٱلْقَوِيّ",     "transliteration": "Al-Qawiyy",   "meaning": "The All-Powerful",                      "explanation": "The One whose power is absolute and cannot be overcome."},
    {"number": 55, "arabic": "ٱلْمَتِين",     "transliteration": "Al-Matin",    "meaning": "The Firm / Strong",                     "explanation": "The One who is extremely strong and steadfast; His power never weakens."},
    {"number": 56, "arabic": "ٱلْوَلِيّ",     "transliteration": "Al-Waliyy",   "meaning": "The Protecting Friend",                 "explanation": "The One who protects and supports the believers."},
    {"number": 57, "arabic": "ٱلْحَمِيد",     "transliteration": "Al-Hamid",    "meaning": "The Praiseworthy",                      "explanation": "The One who is deserving of all praise in every situation."},
    {"number": 58, "arabic": "ٱلْمُحْصِي",    "transliteration": "Al-Muhsi",    "meaning": "The Counter",                           "explanation": "The One who counts and records all things without omission."},
    {"number": 59, "arabic": "ٱلْمُبْدِئ",    "transliteration": "Al-Mubdi",    "meaning": "The Originator",                        "explanation": "The One who begins creation from nothing."},
    {"number": 60, "arabic": "ٱلْمُعِيد",     "transliteration": "Al-Muid",     "meaning": "The Restorer",                          "explanation": "The One who restores creation after its end on the Day of Judgment."},
    {"number": 61, "arabic": "ٱلْمُحْيِي",    "transliteration": "Al-Muhyi",    "meaning": "The Giver of Life",                     "explanation": "The One who grants life to all living things."},
    {"number": 62, "arabic": "ٱلْمُمِيت",     "transliteration": "Al-Mumit",    "meaning": "The Taker of Life",                     "explanation": "The One who causes death according to His decree."},
    {"number": 63, "arabic": "ٱلْحَيّ",       "transliteration": "Al-Hayy",     "meaning": "The Ever-Living",                       "explanation": "The One who is eternally alive and will never die."},
    {"number": 64, "arabic": "ٱلْقَيُّوم",    "transliteration": "Al-Qayyum",   "meaning": "The Self-Subsisting",                   "explanation": "The One who sustains Himself and upon whom all of creation depends."},
    {"number": 65, "arabic": "ٱلْوَاجِد",     "transliteration": "Al-Wajid",    "meaning": "The Finder",                            "explanation": "The One who finds what He wills with ease; He lacks nothing."},
    {"number": 66, "arabic": "ٱلْمَاجِد",     "transliteration": "Al-Majid",    "meaning": "The Noble",                             "explanation": "The One who is noble in His character and deeds."},
    {"number": 67, "arabic": "ٱلْوَاحِد",     "transliteration": "Al-Wahid",    "meaning": "The One",                               "explanation": "The One who is singular and unique; there is no partner or equal."},
    {"number": 68, "arabic": "ٱلْأَحَد",      "transliteration": "Al-Ahad",     "meaning": "The Unique",                            "explanation": "The One who is absolutely unique with no resemblance to anything."},
    {"number": 69, "arabic": "ٱلصَّمَد",      "transliteration": "As-Samad",    "meaning": "The Eternal Refuge",                    "explanation": "The One upon whom all of creation depends for all their needs."},
    {"number": 70, "arabic": "ٱلْقَادِر",     "transliteration": "Al-Qadir",    "meaning": "The Omnipotent",                        "explanation": "The One who has power over all things without limitation."},
    {"number": 71, "arabic": "ٱلْمُقْتَدِر",  "transliteration": "Al-Muqtadir", "meaning": "The All-Determiner",                    "explanation": "The One who determines and controls all things perfectly."},
    {"number": 72, "arabic": "ٱلْمُقَدِّم",   "transliteration": "Al-Muqaddim", "meaning": "The Expediter",                         "explanation": "The One who puts things forward and advances them as He wills."},
    {"number": 73, "arabic": "ٱلْمُؤَخِّر",   "transliteration": "Al-Muakhkhir","meaning": "The Delayer",                           "explanation": "The One who delays things and puts them back as He wills."},
    {"number": 74, "arabic": "ٱلْأَوَّل",     "transliteration": "Al-Awwal",    "meaning": "The First",                             "explanation": "The One who is first; there was nothing before Him."},
    {"number": 75, "arabic": "ٱلْآخِر",       "transliteration": "Al-Akhir",    "meaning": "The Last",                              "explanation": "The One who is last; there will be nothing after Him."},
    {"number": 76, "arabic": "ٱلظَّاهِر",     "transliteration": "Az-Zahir",    "meaning": "The Manifest",                          "explanation": "The One who is apparent through His signs and creation."},
    {"number": 77, "arabic": "ٱلْبَاطِن",     "transliteration": "Al-Batin",    "meaning": "The Hidden",                            "explanation": "The One who is hidden in His essence from all perception."},
    {"number": 78, "arabic": "ٱلْوَالِي",     "transliteration": "Al-Wali",     "meaning": "The Governor",                          "explanation": "The One who governs all of creation according to His wisdom."},
    {"number": 79, "arabic": "ٱلْمُتَعَالِ",  "transliteration": "Al-Mutaali",  "meaning": "The Most Exalted",                      "explanation": "The One who is supremely exalted above all things and all creation."},
    {"number": 80, "arabic": "ٱلْبَرّ",       "transliteration": "Al-Barr",     "meaning": "The Source of Goodness",                "explanation": "The One who is full of goodness and benevolence toward His creation."},
    {"number": 81, "arabic": "ٱلتَّوَّاب",    "transliteration": "At-Tawwab",   "meaning": "The Acceptor of Repentance",            "explanation": "The One who accepts repentance repeatedly from His servants."},
    {"number": 82, "arabic": "ٱلْمُنْتَقِم",  "transliteration": "Al-Muntaqim", "meaning": "The Avenger",                           "explanation": "The One who punishes those who transgress and oppress others."},
    {"number": 83, "arabic": "ٱلْعَفُوّ",     "transliteration": "Al-Afuww",    "meaning": "The Pardoner",                          "explanation": "The One who pardons sins and erases them completely."},
    {"number": 84, "arabic": "ٱلرَّءُوف",     "transliteration": "Ar-Rauf",     "meaning": "The Most Kind",                         "explanation": "The One who is extremely kind and tender-hearted toward His servants."},
    {"number": 85, "arabic": "مَالِكُ ٱلْمُلْك","transliteration": "Malik-ul-Mulk","meaning": "Owner of All Sovereignty",           "explanation": "The One who owns all kingdoms and authority without any partner."},
    {"number": 86, "arabic": "ذُو ٱلْجَلَالِ وَٱلْإِكْرَام","transliteration": "Dhul-Jalali wal-Ikram","meaning": "Lord of Majesty and Bounty","explanation": "The One who possesses both great majesty and perfect generosity."},
    {"number": 87, "arabic": "ٱلْمُقْسِط",    "transliteration": "Al-Muqsit",   "meaning": "The Equitable",                         "explanation": "The One who acts with perfect equity and fairness in all matters."},
    {"number": 88, "arabic": "ٱلْجَامِع",     "transliteration": "Al-Jami",     "meaning": "The Gatherer",                          "explanation": "The One who will gather all of creation on the Day of Judgment."},
    {"number": 89, "arabic": "ٱلْغَنِيّ",     "transliteration": "Al-Ghani",    "meaning": "The Self-Sufficient",                   "explanation": "The One who is free from all needs and dependencies."},
    {"number": 90, "arabic": "ٱلْمُغْنِي",    "transliteration": "Al-Mughni",   "meaning": "The Enricher",                          "explanation": "The One who enriches and makes His servants free of need."},
    {"number": 91, "arabic": "ٱلْمَانِع",     "transliteration": "Al-Mani",     "meaning": "The Withholder",                        "explanation": "The One who withholds what He wills according to His wisdom."},
    {"number": 92, "arabic": "ٱلضَّارّ",      "transliteration": "Ad-Darr",     "meaning": "The Distressor",                        "explanation": "The One who afflicts with harm whomever He wills by His wisdom."},
    {"number": 93, "arabic": "ٱلنَّافِع",     "transliteration": "An-Nafi",     "meaning": "The Benefiter",                         "explanation": "The One who brings benefit to whomever He wills by His grace."},
    {"number": 94, "arabic": "ٱلنُّور",       "transliteration": "An-Nur",      "meaning": "The Light",                             "explanation": "The One who illuminates the heavens and earth and all of creation."},
    {"number": 95, "arabic": "ٱلْهَادِي",     "transliteration": "Al-Hadi",     "meaning": "The Guide",                             "explanation": "The One who guides His servants to the straight path."},
    {"number": 96, "arabic": "ٱلْبَدِيع",     "transliteration": "Al-Badi",     "meaning": "The Incomparable Originator",           "explanation": "The One who creates things that have no prior precedent."},
    {"number": 97, "arabic": "ٱلْبَاقِي",     "transliteration": "Al-Baqi",     "meaning": "The Ever-Enduring",                     "explanation": "The One who is eternal and will never cease to exist."},
    {"number": 98, "arabic": "ٱلْوَارِث",     "transliteration": "Al-Warith",   "meaning": "The Inheritor",                         "explanation": "The One who remains after all of creation perishes; He inherits all."},
    {"number": 99, "arabic": "ٱلرَّشِيد",     "transliteration": "Ar-Rashid",   "meaning": "The Guide to the Right Path",           "explanation": "The One who guides all things to their ultimate purpose with wisdom."},
]


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    """Configure file + console logging.

    Args:
        log_dir: Directory where the log file will be written.
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"download_hadith_{timestamp}.log"

    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("download_hadith")
    logger.info("Log file: %s", log_file)
    return logger


# ─── HTTP helper ──────────────────────────────────────────────────────────────

async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    logger: logging.Logger,
    fallback_url: str | None = None,
) -> dict[str, Any]:
    """Fetch a URL and return parsed JSON with retry + fallback URL support.

    Tries primary URL up to MAX_RETRIES times.
    On 403/404, immediately tries fallback_url if provided.

    Args:
        session: Active aiohttp client session.
        url: Primary URL to request.
        logger: Logger instance.
        fallback_url: Optional URL to try if primary fails with 403/404.

    Returns:
        Parsed JSON response as a dict.

    Raises:
        RuntimeError: If all URLs and retries are exhausted.
    """
    urls_to_try = [url] + ([fallback_url] if fallback_url else [])

    for try_url in urls_to_try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    try_url,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status in (403, 404):
                        logger.warning("HTTP %d for %s — trying next URL", resp.status, try_url)
                        break  # break inner loop → try next URL
                    resp.raise_for_status()
                    await asyncio.sleep(REQUEST_DELAY)
                    return await resp.json(content_type=None)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt == MAX_RETRIES:
                    logger.warning("All %d retries failed for %s: %s", MAX_RETRIES, try_url, exc)
                    break  # try next URL
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning("Attempt %d/%d failed: %s — retrying in %.1fs",
                               attempt, MAX_RETRIES, exc, wait)
                await asyncio.sleep(wait)

    raise RuntimeError(f"Failed to fetch {url} (tried all URLs/retries)")


# ─── Collection downloader ────────────────────────────────────────────────────

async def download_collection(
    session: aiohttp.ClientSession,
    api_name: str,
    output_filename: str,
    display_name: str,
    expected_min: int,
    output_dir: Path,
    logger: logging.Logger,
) -> int:
    """Download one Hadith collection (English + Arabic) and save as merged JSON.

    Args:
        session: Active aiohttp client session.
        api_name: Name used in the CDN URL (e.g. 'bukhari').
        output_filename: Filename to save (e.g. 'bukhari.json').
        display_name: Human-readable collection name for logging.
        expected_min: Minimum expected hadith count for validation warning.
        output_dir: Directory to save the output file.
        logger: Logger instance.

    Returns:
        Number of hadiths saved.
    """
    eng_url = f"{CDN_BASE}/eng-{api_name}.json"
    ara_url = f"{CDN_BASE}/ara-{api_name}.json"

    logger.info("Downloading %s...", display_name)

    # Build fallback GitHub raw URLs for large files that CDN may block
    eng_fallback = f"{GH_RAW_BASE}/eng-{api_name}.json"
    ara_fallback = f"{GH_RAW_BASE}/ara-{api_name}.json"

    # Fetch English and Arabic in parallel (each with fallback)
    eng_task = fetch_json(session, eng_url, logger, fallback_url=eng_fallback)
    ara_task = fetch_json(session, ara_url, logger, fallback_url=ara_fallback)
    eng_data, ara_data = await asyncio.gather(eng_task, ara_task)

    # Build Arabic lookup: hadith_number → arabic_text
    ara_lookup: dict[int, str] = {}
    for h in ara_data.get("hadiths", []):
        num = h.get("hadithnumber")
        if num is not None:
            ara_lookup[int(num)] = h.get("text", "")

    # Merge English + Arabic
    hadiths: list[dict[str, Any]] = []
    for h in eng_data.get("hadiths", []):
        num = h.get("hadithnumber")
        if num is None:
            continue
        num = int(num)

        hadiths.append({
            "hadith_number": num,
            "arabic_text": ara_lookup.get(num, ""),
            "english_text": h.get("text", ""),
            "grade": h.get("grades", [{}])[0].get("grade", DEFAULT_GRADE)
                     if h.get("grades") else DEFAULT_GRADE,
        })

    # Sort by hadith_number for deterministic output
    hadiths.sort(key=lambda x: x["hadith_number"])

    # Build output document
    meta_raw = eng_data.get("metadata", {})
    output: dict[str, Any] = {
        "metadata": {
            "name": display_name,
            "collection": api_name,
            "source": "cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "total_hadiths": len(hadiths),
            "original_metadata": meta_raw,
        },
        "hadiths": hadiths,
    }

    out_file = output_dir / output_filename
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    size_mb = out_file.stat().st_size / (1024 * 1024)
    logger.info("%s: %d hadiths saved → %s (%.1f MB)", display_name, len(hadiths), out_file.name, size_mb)

    if len(hadiths) < expected_min:
        logger.warning("%s: got %d hadiths but expected >= %d — check source",
                       display_name, len(hadiths), expected_min)

    return len(hadiths)


# ─── 99 Names saver ───────────────────────────────────────────────────────────

def save_asmaul_husna(output_dir: Path, logger: logging.Logger) -> None:
    """Save 99 Names of Allah to asmaul_husna.json.

    Args:
        output_dir: Directory to save the output file.
        logger: Logger instance.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    document: dict[str, Any] = {
        "metadata": {
            "source": "Islamic scholarly tradition",
            "reference": "Sahih Bukhari 6410, Sahih Muslim 2677",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_names": len(ASMAUL_HUSNA),
        },
        "names": ASMAUL_HUSNA,
    }

    out_file = output_dir / "asmaul_husna.json"
    out_file.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("99 Names of Allah saved → %s (%d names)", out_file, len(ASMAUL_HUSNA))


# ─── Main orchestrator ────────────────────────────────────────────────────────

async def download_all(
    hadith_dir: Path,
    supp_dir: Path,
    selected_collections: list[str],
    logger: logging.Logger,
) -> None:
    """Download all Hadith collections and supplementary data.

    Args:
        hadith_dir: Output directory for hadith JSON files.
        supp_dir: Output directory for supplementary JSON files.
        selected_collections: List of api_name values to download.
            Pass empty list to download all.
        logger: Logger instance.
    """
    hadith_dir.mkdir(parents=True, exist_ok=True)
    supp_dir.mkdir(parents=True, exist_ok=True)

    # Filter collections if user specified a subset
    to_download = [
        c for c in COLLECTIONS
        if not selected_collections or c[0] in selected_collections
    ]

    if not to_download:
        logger.error("No collections matched. Valid names: %s",
                     [c[0] for c in COLLECTIONS])
        sys.exit(1)

    connector = aiohttp.TCPConnector(limit=3)
    async with aiohttp.ClientSession(connector=connector) as session:
        total_hadiths = 0
        failed_collections: list[str] = []

        for api_name, filename, display_name, expected_min in tqdm(to_download, desc="Collections"):
            try:
                count = await download_collection(
                    session, api_name, filename, display_name,
                    expected_min, hadith_dir, logger,
                )
                total_hadiths += count
            except RuntimeError as exc:
                logger.error("SKIPPED %s: %s", display_name, exc)
                failed_collections.append(display_name)

    # Save 99 Names regardless of any collection failures
    save_asmaul_husna(supp_dir, logger)

    logger.info("=" * 50)
    logger.info("Total hadiths downloaded: %d", total_hadiths)
    if failed_collections:
        logger.warning("Failed collections (%d): %s", len(failed_collections),
                       ", ".join(failed_collections))
        logger.warning("Re-run with --collections %s to retry failed ones",
                       " ".join(c[0] for c in COLLECTIONS
                                if c[2] in failed_collections))
    else:
        logger.info("All collections downloaded successfully")
    logger.info("Collections saved to: %s", hadith_dir)
    logger.info("Supplementary data saved to: %s", supp_dir)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Download Hadith collections + 99 Names of Allah.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_hadith.py
  python download_hadith.py --collections bukhari muslim
  python download_hadith.py --hadith-dir /data/hadith
  python download_hadith.py --help

Available collections:
  bukhari, muslim, abudawud, tirmidhi, ibnmajah, riyadussalihin
        """,
    )
    parser.add_argument(
        "--hadith-dir",
        type=Path,
        default=DEFAULT_HADITH_DIR,
        help=f"Output dir for hadith JSONs (default: {DEFAULT_HADITH_DIR})",
    )
    parser.add_argument(
        "--supp-dir",
        type=Path,
        default=DEFAULT_SUPP_DIR,
        help=f"Output dir for supplementary JSONs (default: {DEFAULT_SUPP_DIR})",
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        default=[],
        metavar="NAME",
        help="Download only these collections (default: all)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point: parse args, setup logging, run async download."""
    args = parse_args()
    logger = setup_logging(LOG_DIR, args.log_level)

    logger.info("=" * 60)
    logger.info("Hadith Download — starting")
    logger.info("Hadith dir : %s", args.hadith_dir)
    logger.info("Supp dir   : %s", args.supp_dir)
    logger.info("Collections: %s", args.collections or "all")
    logger.info("=" * 60)

    start = time.monotonic()
    try:
        asyncio.run(download_all(args.hadith_dir, args.supp_dir, args.collections, logger))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Download failed: %s", exc)
        sys.exit(1)

    elapsed = time.monotonic() - start
    logger.info("Completed in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
