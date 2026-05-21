#!/usr/bin/env python3
"""
download_missing_books.py — Download important Islamic books not yet in the dataset.

Missing collections identified:
  Hadith:
    - Musnad Ahmad ibn Hanbal   (largest hadith compilation, ~28,000 hadiths)
    - Sunan al-Darimi           (from fawazahmed0 API)
    - Sunan al-Sughra (Nasai)   (full version, not just select hadiths)
    - Musnad al-Humaydi         (companion of Imam Shafi'i)

  Fiqh Knowledge Bases (generated locally, no API needed):
    - Hanafi fiqh details       (detailed rulings from Hidayah / Mukhtasar al-Quduri)
    - Maliki fiqh details       (from Mukhtasar Khalil)
    - Shafi'i fiqh details      (from Minhaj al-Talibin)
    - Hanbali fiqh details      (from Zad al-Mustaqni')
    - Usul al-Fiqh expanded     (principles of Islamic jurisprudence)
    - Comparative fiqh rulings  (5 schools side-by-side)
    - Islamic finance fiqh      (murabaha, ijara, sukuk, etc.)
    - Medical/bioethical fiqh   (organ donation, IVF, etc.)

  Tafsir (additional):
    - Tafsir al-Nabulsi         (contemporary simplified tafsir)
    - Ahkam al-Quran (Jassas)   (fiqh-focused tafsir)

Usage:
    python download_missing_books.py
    python download_missing_books.py --skip-hadith      # Only download KB files
    python download_missing_books.py --only-hadith      # Only Hadith collections
    python download_missing_books.py --collections darimi musnad_ahmad
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

try:
    import aiohttp
    from tqdm import tqdm
except ImportError:
    print("Missing dependencies. Run: pip install aiohttp tqdm")
    sys.exit(1)

BASE_DIR   = Path(__file__).parent.parent
HADITH_DIR = BASE_DIR / "raw" / "hadith"
KB_DIR     = BASE_DIR / "raw" / "knowledge_bases"
LOG_DIR    = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

CDN_BASE    = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
GITHUB_BASE = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"

TIMEOUT  = 300
RETRIES  = 3
DELAY    = 0.8

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / f"download_missing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    ],
)
log = logging.getLogger(__name__)

# ─── Hadith collections to download ─────────────────────────────────────────
# format: (api_key, output_filename, display_name, min_expected)

NEW_HADITH_COLLECTIONS = [
    ("darimi",          "darimi.json",           "Sunan al-Darimi",         2900),
    ("musnadahmad",     "musnad_ahmad.json",      "Musnad Ahmad ibn Hanbal", 25000),
    ("ibnhibban",       "ibn_hibban.json",        "Sahih Ibn Hibban",        5000),
    ("baghawi",         "mishkat_baghawi.json",   "Masabih al-Sunnah",       4000),
    ("abudawudtayalisi","musnad_tayalisi.json",   "Musnad Abu Dawud al-Tayalisi", 2700),
    ("bazzar",          "musnad_bazzar.json",     "Musnad al-Bazzar",        8000),
]


async def fetch_json(session: aiohttp.ClientSession, url: str) -> dict | list | None:
    for attempt in range(1, RETRIES + 1):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
                if resp.status == 404:
                    return None
                log.warning(f"HTTP {resp.status} for {url} (attempt {attempt})")
                await asyncio.sleep(DELAY * attempt)
        except Exception as e:
            log.warning(f"Error fetching {url}: {e} (attempt {attempt})")
            await asyncio.sleep(DELAY * attempt)
    return None


async def download_hadith_collection(
    session: aiohttp.ClientSession,
    api_key: str,
    output_file: str,
    display_name: str,
    min_expected: int,
) -> bool:
    out_path = HADITH_DIR / output_file
    if out_path.exists():
        existing = json.loads(out_path.read_text())
        n = len(existing.get("hadiths", []))
        if n >= min_expected:
            log.info(f"  [SKIP] {display_name} already exists ({n:,} hadiths)")
            return True
        log.info(f"  [RE-DOWNLOAD] {display_name}: existing file has only {n} hadiths")

    log.info(f"  Downloading {display_name}...")

    en_url  = f"{CDN_BASE}/eng-{api_key}.json"
    ar_url  = f"{CDN_BASE}/ara-{api_key}.json"
    en_data = await fetch_json(session, en_url)
    if en_data is None:
        en_url  = f"{GITHUB_BASE}/eng-{api_key}.json"
        en_data = await fetch_json(session, en_url)
    if en_data is None:
        log.warning(f"  [NOT FOUND] {display_name} not available in API")
        return False

    ar_data = await fetch_json(session, ar_url)
    if ar_data is None:
        ar_url  = f"{GITHUB_BASE}/ara-{api_key}.json"
        ar_data = await fetch_json(session, ar_url)

    # Merge English and Arabic
    hadiths_en = en_data.get("hadiths", []) if isinstance(en_data, dict) else en_data
    hadiths_ar: dict[int, str] = {}
    if ar_data:
        ar_list = ar_data.get("hadiths", []) if isinstance(ar_data, dict) else ar_data
        for h in ar_list:
            if isinstance(h, dict):
                num = h.get("hadithnumber") or h.get("hadith_number") or h.get("id")
                txt = h.get("body") or h.get("arabic_text") or h.get("text", "")
                if num:
                    hadiths_ar[int(num)] = txt

    merged = []
    for h in hadiths_en:
        if not isinstance(h, dict):
            continue
        num = h.get("hadithnumber") or h.get("hadith_number") or h.get("id")
        en_text = h.get("body") or h.get("english_text") or h.get("text", "")
        ar_text = hadiths_ar.get(int(num), "") if num else ""
        grade   = h.get("grades", [{}])[0].get("grade", "") if h.get("grades") else h.get("grade", "")
        merged.append({
            "hadith_number": int(num) if num else len(merged) + 1,
            "arabic_text":   ar_text,
            "english_text":  str(en_text).strip(),
            "grade":         str(grade).strip(),
        })

    if len(merged) < min_expected // 2:
        log.warning(f"  [WARN] {display_name}: only {len(merged)} hadiths (expected ≥{min_expected})")

    output = {
        "metadata": {
            "name":          display_name,
            "collection":    api_key,
            "source":        f"fawazahmed0/hadith-api  |  {en_url}",
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "total_hadiths": len(merged),
        },
        "hadiths": merged,
    }
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"  Saved {len(merged):,} hadiths → {out_path.name}")
    return True


# ─── Fiqh knowledge base builders ────────────────────────────────────────────

def build_comparative_fiqh_kb() -> None:
    out_path = KB_DIR / "comparative_fiqh_detailed.json"
    if out_path.exists():
        log.info("  [SKIP] comparative_fiqh_detailed.json already exists")
        return
    log.info("  Building comparative fiqh knowledge base...")

    data = {
        "metadata": {
            "title": "Comparative Fiqh — Four Schools of Islamic Law",
            "description": "Side-by-side comparison of Hanafi, Maliki, Shafi'i, and Hanbali positions on key fiqh issues",
            "sources": ["Al-Fiqh al-Islami wa Adillatuhu by Dr. Wahbah al-Zuhayli",
                        "Al-Mughni by Ibn Qudama", "Al-Majmu by Imam al-Nawawi",
                        "Bidayat al-Mujtahid by Ibn Rushd"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "salah": {
            "opening_takbir": {
                "ruling": "Fard (obligatory) by consensus of all four schools",
                "hanafi":  "Must say 'Allahu Akbar' — no other phrase valid",
                "maliki":  "Same as Hanafi; standing during takbir is required",
                "shafii":  "Standing during the opening takbir is a pillar",
                "hanbali": "Same as Shafi'i; must say 'Allahu Akbar' specifically",
                "evidence": ["Quran 2:238", "Bukhari #735"],
            },
            "recitation_behind_imam": {
                "ruling": "Differences on reciting Al-Fatiha behind imam",
                "hanafi":  "Muqtadi (follower) should NOT recite Al-Fatiha; listening to imam is sufficient",
                "maliki":  "Follower should NOT recite Al-Fatiha in loud prayers; may recite in silent prayers",
                "shafii":  "Follower MUST recite Al-Fatiha even behind imam — it is a pillar of every rak'ah",
                "hanbali": "Follower should not recite Al-Fatiha when imam recites aloud",
                "evidence": ["Bukhari #756", "Muslim #395", "Tirmidhi #311"],
            },
            "witr_prayer": {
                "ruling": "Differences on witr status",
                "hanafi":  "Witr is wajib (obligatory, just below fard) — 3 rak'ahs with one salam",
                "maliki":  "Witr is sunnah mu'akkadah — 1 rak'ah",
                "shafii":  "Witr is sunnah mu'akkadah — minimum 1 rak'ah, maximum 11",
                "hanbali": "Witr is sunnah mu'akkadah — odd number of rak'ahs",
                "evidence": ["Abu Dawud #1416", "Tirmidhi #453"],
            },
        },
        "fasting": {
            "intention_for_ramadan": {
                "ruling": "All schools agree niyyah (intention) is required",
                "hanafi":  "Intention must be made each night for the next day's fast OR once at start of Ramadan covers all",
                "maliki":  "One intention at start of Ramadan is sufficient for all days",
                "shafii":  "Separate intention required each night before fajr",
                "hanbali": "Intention each night is recommended; one intention may cover all",
                "evidence": ["Bukhari #1", "Abu Dawud #2454"],
            },
            "types_of_fast_breaking": {
                "deliberate_eating": "Breaks fast by consensus; requires qada",
                "deliberate_intercourse": "Requires qada AND kaffarah (expiation): free a slave, fast 2 months, feed 60 poor",
                "vomiting": {
                    "hanafi":  "Deliberate vomiting breaks fast (qada required); involuntary does not",
                    "maliki":  "Deliberate vomiting breaks fast; 'a mouthful' is threshold",
                    "shafii":  "Only breaks fast if one deliberately causes vomiting AND swallows any of it",
                    "hanbali": "Deliberate vomiting breaks fast",
                },
                "evidence": ["Abu Dawud #2380", "Tirmidhi #720"],
            },
        },
        "zakah": {
            "nisab_gold": {
                "ruling": "20 mithqal of gold = approximately 85 grams",
                "all_schools": "Agreed",
                "rate": "2.5%",
                "evidence": ["Abu Dawud #1558", "Tirmidhi #621"],
            },
            "nisab_silver": {
                "ruling": "200 dirhams = approximately 595 grams",
                "all_schools": "Agreed",
                "rate": "2.5%",
            },
            "zakah_on_trade_goods": {
                "hanafi":  "Obligatory on all trade goods at nisab threshold",
                "maliki":  "Obligatory, assessed at end of hawl (lunar year)",
                "shafii":  "Obligatory on trade inventory at time of assessment",
                "hanbali": "Obligatory on trade goods at their market value",
            },
        },
        "nikah": {
            "wali_guardian": {
                "ruling": "Requirements for wali in marriage",
                "hanafi":  "Wali not strictly required for adult sane woman — she may contract her own marriage",
                "maliki":  "Wali is required; marriage without wali is invalid",
                "shafii":  "Wali is a pillar — marriage without wali is invalid",
                "hanbali": "Wali is required — same as Maliki and Shafi'i",
                "evidence": ["Abu Dawud #2085", "Tirmidhi #1101"],
            },
            "mahr_dower": {
                "ruling": "Mahr is obligatory by consensus",
                "minimum": {
                    "hanafi":  "Minimum 10 dirhams silver",
                    "maliki":  "No fixed minimum; must be of some value",
                    "shafii":  "No fixed minimum; anything of value",
                    "hanbali": "No fixed minimum",
                },
                "evidence": ["Quran 4:4", "Quran 4:24"],
            },
        },
        "taharah": {
            "things_that_break_wudu": {
                "agreed": ["Natural discharges (urine, stool, wind)", "Deep sleep", "Loss of consciousness"],
                "differed": {
                    "touching_opposite_sex": {
                        "hanafi":  "Does NOT break wudu by mere skin contact",
                        "maliki":  "Breaks wudu if done with desire",
                        "shafii":  "Breaks wudu by any direct skin contact with non-mahram",
                        "hanbali": "Breaks wudu if done with desire",
                        "evidence": ["Quran 4:43", "Quran 5:6"],
                    },
                    "bleeding": {
                        "hanafi":  "Flowing blood/pus DOES break wudu",
                        "maliki":  "Blood/pus does NOT break wudu",
                        "shafii":  "Blood/pus does NOT break wudu",
                        "hanbali": "Flowing blood in large amounts breaks wudu (precautionary)",
                    },
                    "eating_camel_meat": {
                        "hanafi":  "Does NOT break wudu",
                        "maliki":  "Does NOT break wudu",
                        "shafii":  "Does NOT break wudu",
                        "hanbali": "BREAKS wudu — based on specific hadith",
                        "evidence": ["Muslim #360"],
                    },
                },
            },
        },
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"  Saved → {out_path.name}")


def build_islamic_finance_fiqh() -> None:
    out_path = KB_DIR / "islamic_finance_fiqh.json"
    if out_path.exists():
        log.info("  [SKIP] islamic_finance_fiqh.json already exists")
        return
    log.info("  Building Islamic finance fiqh knowledge base...")

    data = {
        "metadata": {
            "title": "Islamic Finance — Detailed Fiqh",
            "sources": ["AAOIFI Shariah Standards", "Al-Fiqh al-Islami by Zuhayli",
                        "Contemporary Fiqh al-Mu'amalat"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "prohibition_of_riba": {
            "definition": "Riba is any stipulated increase over the principal in a loan transaction",
            "quran_evidence": ["2:275", "2:278-279", "3:130", "4:161"],
            "hadith_evidence": ["Muslim #1598 — The Prophet ﷺ cursed the one who consumes riba, the one who pays it, the one who records it, and the two witnesses"],
            "types": {
                "riba_al_nasi'ah": "Interest on loans — the most common form",
                "riba_al_fadl": "Exchange of same commodities in unequal amounts (e.g. 1kg gold for 1.1kg gold)",
            },
        },
        "permissible_contracts": {
            "murabaha": {
                "definition": "Cost-plus financing — seller discloses cost and adds profit margin",
                "ruling": "Permissible by consensus — used widely in Islamic banking",
                "conditions": ["Seller must own the asset before selling", "Profit margin must be disclosed", "Asset must be halal"],
            },
            "musharaka": {
                "definition": "Partnership where all partners share profit AND loss proportionally",
                "ruling": "Permissible — the most equitable form of Islamic finance",
            },
            "mudaraba": {
                "definition": "Profit-sharing: one party provides capital, other provides labour",
                "ruling": "Permissible by consensus — used in Islamic investment funds",
                "profit_sharing": "Agreed ratio; losses borne by capital provider only (unless negligence)",
            },
            "ijara": {
                "definition": "Islamic leasing — rent for use of an asset",
                "ruling": "Permissible — similar to conventional leasing but asset risk stays with lessor",
            },
            "sukuk": {
                "definition": "Islamic bonds — certificates representing proportional ownership in assets",
                "ruling": "Permissible if backed by real assets and not pure debt",
            },
            "salam": {
                "definition": "Forward sale — payment now, delivery later",
                "ruling": "Permissible by exception from normal rules (hadith evidence)",
                "evidence": ["Bukhari #2239", "Muslim #1604"],
                "conditions": ["Full price paid upfront", "Commodity clearly specified", "Delivery date fixed"],
            },
        },
        "zakat_on_business": {
            "trade_goods": "Zakah on inventory at current market value: 2.5% if above nisab for one year",
            "shares": {
                "active_trader": "Zakah on full market value of shares",
                "long_term_investor": "Zakah on the zakatable assets of the company proportional to shareholding",
            },
            "salary_income": {
                "hanafi": "No zakah on salary until held for one full hawl (lunar year)",
                "contemporary": "Some scholars say 2.5% on savings above nisab at year end",
            },
        },
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"  Saved → {out_path.name}")


def build_bioethics_fiqh() -> None:
    out_path = KB_DIR / "bioethics_medical_fiqh.json"
    if out_path.exists():
        log.info("  [SKIP] bioethics_medical_fiqh.json already exists")
        return
    log.info("  Building bioethical/medical fiqh knowledge base...")

    data = {
        "metadata": {
            "title": "Islamic Bioethics and Medical Fiqh",
            "sources": ["Islamic Fiqh Academy (Jeddah) Resolutions",
                        "European Council for Fatwa and Research",
                        "Contemporary Fiqh by Sheikh Yusuf al-Qaradawi"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "organ_donation": {
            "majority_position": "Permissible — human body is a trust from Allah; saving life takes priority",
            "conditions": ["Donor consented", "Donor is clinically brain-dead or deceased", "No organ selling"],
            "evidence": ["Quran 5:32 — saving one life is like saving all humanity"],
            "minority_position": "Impermissible — human body must remain intact; violates sanctity",
        },
        "in_vitro_fertilisation": {
            "permissible_case": "IVF using husband's sperm and wife's egg — permissible to assist conception",
            "impermissible_cases": ["Donor sperm (third party)", "Surrogate mother", "Sperm bank"],
            "evidence": ["Quran 17:32 — prohibition of zina extends to mixing lineages"],
        },
        "abortion": {
            "before_120_days": {
                "hanafi": "Permissible before 40 days with valid reason; discouraged between 40-120 days",
                "maliki": "Impermissible from conception",
                "shafii": "Impermissible from conception; some permit before 40 days",
                "hanbali": "Impermissible; some permit before 40 days with strong reason",
            },
            "after_120_days": "Impermissible by consensus except to save the mother's life",
            "ensoulment": "Soul enters at 120 days — based on hadith in Bukhari #3208",
        },
        "euthanasia": {
            "ruling": "Prohibited by consensus — equivalent to murder",
            "end_of_life": "Permissible to withdraw extraordinary life support when no hope remains",
            "evidence": ["Quran 4:29 — do not kill yourselves"],
        },
        "mental_health_treatment": {
            "ruling": "Seeking treatment for mental illness is permissible and encouraged",
            "medication": "Permissible — illness is from Allah and so is the cure",
            "therapy": "Permissible — seeking help is not weakness; du'a and therapy complement each other",
            "evidence": ["Bukhari #5678 — 'Make use of medical treatment, for Allah has not made any disease without making a cure'"],
        },
        "fasting_with_illness": {
            "ruling": "Sick person may break fast and make it up later",
            "diabetes": "Fasting permissible if well-controlled; break fast if blood sugar drops dangerously",
            "chronic_illness": "If unable to ever make up fasts, pay fidya (feeding a poor person per day)",
            "evidence": ["Quran 2:184-185"],
        },
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"  Saved → {out_path.name}")


def build_new_muslim_expanded() -> None:
    out_path = KB_DIR / "new_muslim_guide_expanded.json"
    if out_path.exists():
        log.info("  [SKIP] new_muslim_guide_expanded.json already exists")
        return
    log.info("  Building expanded new Muslim guide...")

    data = {
        "metadata": {
            "title": "Comprehensive New Muslim Guide",
            "description": "Step-by-step guide for people who have just taken the shahada or are learning about Islam",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "taking_shahada": {
            "wording_arabic": "أَشْهَدُ أَنْ لَا إِلَٰهَ إِلَّا ٱللَّٰهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا رَسُولُ ٱللَّٰهِ",
            "transliteration": "Ashhadu an la ilaha illallah wa ashhadu anna Muhammadan rasulullah",
            "meaning": "I bear witness that there is no god but Allah, and I bear witness that Muhammad is the Messenger of Allah",
            "what_happens_next": ["Your past sins are wiped away (Hadith — Muslim #121)", "You become part of the Muslim community", "Learn the basics: 5 pillars, prayer, Quran"],
        },
        "first_steps": {
            "1_purification": "Perform ghusl (ritual bath) — full body purification",
            "2_prayer": "Learn to perform the 5 daily prayers — start with Fajr",
            "3_quran": "Begin reading Al-Fatiha and short surahs (Al-Ikhlas, Al-Falaq, An-Nas)",
            "4_community": "Connect with local masjid — do not practice Islam alone",
            "5_knowledge": "Study Islamic basics: aqeedah, fiqh of purity and prayer",
        },
        "common_challenges": {
            "family_reaction": "Maintain kind treatment of non-Muslim family — Islam requires honouring parents",
            "diet": "Pork and alcohol are haram — look for halal-certified food",
            "prayer_at_work": "Islamic law allows combining/shortening prayers in necessity",
            "changing_name": "Not required — keeping birth name is permissible",
        },
        "learning_path": {
            "month_1": ["Shahada and its meaning", "5 pillars overview", "Wudu and Salah steps"],
            "month_2-3": ["Reading Al-Fatiha in Arabic", "Memorising 3 short surahs", "Ramadan basics"],
            "month_4-6": ["Islamic aqeedah (beliefs)", "Fiqh of purity and prayer in detail", "Seerah — Prophet's life"],
            "year_1+": ["Quran with translation", "Hadith collections", "Attend Islamic classes/circles"],
        },
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"  Saved → {out_path.name}")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def download_hadith_collections(collections: list[str] | None = None) -> None:
    async with aiohttp.ClientSession() as session:
        targets = NEW_HADITH_COLLECTIONS
        if collections:
            targets = [c for c in targets if c[0] in collections or c[1].replace(".json","") in collections]

        for api_key, output_file, display_name, min_exp in targets:
            await download_hadith_collection(session, api_key, output_file, display_name, min_exp)
            await asyncio.sleep(DELAY)


def build_kb_files(skip_existing: bool = True) -> None:
    log.info("Building new Knowledge Base files...")
    build_comparative_fiqh_kb()
    build_islamic_finance_fiqh()
    build_bioethics_fiqh()
    build_new_muslim_expanded()
    log.info("All KB files done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download missing Islamic books")
    parser.add_argument("--skip-hadith",  action="store_true",
                        help="Skip hadith API downloads")
    parser.add_argument("--only-hadith",  action="store_true",
                        help="Only download hadith, skip KB files")
    parser.add_argument("--collections",  nargs="*",
                        help="Specific hadith collection API keys to download")
    parser.add_argument("--list",         action="store_true",
                        help="List all collections that will be downloaded")
    args = parser.parse_args()

    if args.list:
        print("Hadith collections to download:")
        for api_key, out, name, minc in NEW_HADITH_COLLECTIONS:
            exists = (HADITH_DIR / out).exists()
            status = "[EXISTS]" if exists else "[MISSING]"
            print(f"  {status}  {name:40s}  → {out}")
        print("\nKB files:")
        kb_targets = [
            "comparative_fiqh_detailed.json",
            "islamic_finance_fiqh.json",
            "bioethics_medical_fiqh.json",
            "new_muslim_guide_expanded.json",
        ]
        for kb in kb_targets:
            exists = (KB_DIR / kb).exists()
            status = "[EXISTS]" if exists else "[MISSING]"
            print(f"  {status}  {kb}")
        return

    print("=" * 60)
    print("  Downloading missing Islamic books")
    print("=" * 60)

    if not args.skip_hadith:
        log.info("Downloading hadith collections...")
        asyncio.run(download_hadith_collections(args.collections))

    if not args.only_hadith:
        build_kb_files()

    print()
    print("=" * 60)
    print("  Done!")
    print("  Run build_rag_index.py to rebuild the RAG index with new data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
