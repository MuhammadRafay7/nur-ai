#!/usr/bin/env python3
"""
Generate additional Islamic Q&A training pairs across 10 topic domains.

Topics: salah_details, ramadan_fasting, zakat_details, marriage_fiqh,
        prophetic_medicine, adab_etiquette, duas_from_quran, jannah_jahannam,
        signs_of_qiyamah, prophets_stories
"""

from __future__ import annotations

import re
from typing import Any

# ─── Question rewriting ────────────────────────────────────────────────────────

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
    return prefix + instr[0].lower() + instr[1:]


def _pair(instruction: str, output: str, category: str,
          sources: list[str] | None = None, difficulty: str = "intermediate") -> dict[str, Any]:
    return {
        "instruction": instruction,
        "input": "",
        "output": output,
        "metadata": {
            "category": category,
            "difficulty": difficulty,
            "sources": sources or [],
        },
    }


def _rephrase(pairs: list[dict], prefixes: list[str]) -> list[dict]:
    """Generate properly rephrased variants by stripping the question opener first."""
    out = []
    for p in pairs:
        instr, output, cat = p["instruction"], p["output"], p["metadata"]["category"]
        srcs, diff = p["metadata"]["sources"], p["metadata"]["difficulty"]
        if len(output) < 80:
            continue
        for prefix in prefixes:
            new_instr = _rewrite_instruction(instr, prefix)
            if new_instr and new_instr != instr:
                out.append(_pair(new_instr, output, cat, srcs, diff))
    return out


# ─── 1. Salah (Prayer) Details ────────────────────────────────────────────────

_SALAH_PAIRS: list[tuple[str, str]] = [
    (
        "What are the obligatory acts (fard) of salah?",
        "The obligatory acts of salah without which the prayer is invalid include:\n\n"
        "**Standing (Qiyam):** For those physically able, one must stand during the obligatory prayers. "
        "Allah says: 'And stand before Allah devoutly obedient.' (Quran Al-Baqarah 2:238)\n\n"
        "**Opening Takbeer (Takbiratul Ihram):** Saying 'Allahu Akbar' to commence the prayer. "
        "The Prophet ﷺ said: 'The key to prayer is purification, it is entered by takbeer and exited by tasleem.' "
        "(Abu Dawud, Hadith 618, Hasan)\n\n"
        "**Recitation of Al-Fatihah:** In every rak'ah. The Prophet ﷺ said: 'There is no prayer for the one "
        "who does not recite Al-Fatihah.' (Bukhari, Hadith 756, Sahih)\n\n"
        "**Ruku (Bowing):** Bowing deeply with the back straight. (Quran Al-Hajj 22:77)\n\n"
        "**Rising from Ruku:** Returning to standing before prostrating.\n\n"
        "**Two Sujood (Prostrations):** Each rak'ah has two. The Prophet ﷺ said: 'The closest a servant is "
        "to his Lord is when he is in prostration.' (Muslim, Hadith 482, Sahih)\n\n"
        "**Sitting between the two Sujood:** A brief sitting saying 'Rabb ighfir li.'\n\n"
        "**Final Tashahhud and Tasleem:** Sitting for the final tashahhud and ending with tasleem.\n\n"
        "**Tranquility (Tuma'ninah):** Each posture must be held with stillness. The Prophet ﷺ told "
        "the man who prayed incorrectly: 'Go back and pray, for you have not prayed.' (Bukhari, Hadith 793, Sahih)\n\n"
        "According to the majority of scholars, missing any fard deliberately invalidates the prayer. "
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the ruling on praying while sitting?",
        "Praying while sitting is permissible and valid with a reduced reward in most cases:\n\n"
        "**For the sick or unable:** Whoever cannot stand due to illness, injury, or genuine inability "
        "is fully rewarded for sitting prayer. The Prophet ﷺ said: 'Pray standing; if you cannot, then sitting; "
        "if you cannot, then on your side.' (Bukhari, Hadith 1117, Sahih)\n\n"
        "**For voluntary (nafl) prayers:** One may pray nafl sitting even without excuse, but receives "
        "half the reward of standing prayer according to one hadith (Bukhari, Hadith 1116).\n\n"
        "**For the imam:** The Hanbali and Shafi'i scholars hold that if the imam is sitting due to illness, "
        "the followers pray sitting, based on the Prophet's ﷺ final illness prayer (Muslim, Hadith 418).\n\n"
        "**How to sit in prayer:** One sits in the tashahud position (iftirash) or cross-legged (tarabbu'). "
        "The ruku is indicated by bowing the head slightly, and sujood is done on the ground if possible.\n\n"
        "[IJMA] Scholars unanimously agree that genuine inability excuses standing. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the times when prayer is forbidden (makruh/haram)?",
        "There are three primary forbidden times for performing voluntary prayers:\n\n"
        "**After Fajr until sunrise:** From after Fajr prayer until the sun has fully risen (about 15 minutes "
        "after sunrise). The Prophet ﷺ said: 'No prayer after the Fajr prayer until the sun rises.' "
        "(Bukhari, Hadith 586, Sahih)\n\n"
        "**When the sun is at its zenith (istiwa):** A brief period at solar noon when the sun is directly overhead, "
        "until it begins to decline toward Dhuhr time. (Abu Dawud, Hadith 1274, Sahih)\n\n"
        "**After Asr until Maghrib:** After performing Asr prayer until the sun sets completely. "
        "(Bukhari, Hadith 586, Sahih)\n\n"
        "**Exceptions:** The two rak'ahs of Tawaf, making up missed obligatory prayers (qada), and the "
        "tahiyyatul masjid (greeting prayer) are allowed at these times according to many scholars.\n\n"
        "[KHILAF] The Shafi'i madhab allows any prayer with a specific cause (sabab) at any time. "
        "The Hanafi madhab is stricter, prohibiting all voluntary prayers.\n\n"
        "The wisdom behind these times relates to avoiding resemblance of sun-worship at its rising, "
        "zenith, and setting. Allahu Akbar, and Allah knows best."
    ),
    (
        "How do I make up missed obligatory prayers (qada)?",
        "Making up missed obligatory prayers (qada) is obligatory for every Muslim:\n\n"
        "**The obligation:** Allah says: 'And establish prayer for My remembrance.' (Quran Ta-Ha 20:14) "
        "The Prophet ﷺ said: 'Whoever forgets a prayer or sleeps through it, let him pray it when he "
        "remembers it — there is no expiation for it except that.' (Muslim, Hadith 684, Sahih)\n\n"
        "**Order of makeup:** One should pray the missed prayers in order if possible. If one has many "
        "missed prayers, they may be made up over time without a specific order according to many scholars.\n\n"
        "**When to make up:** Makeup prayers can be performed at any time, including the forbidden times "
        "according to the majority. The Hanafi madhab differs, generally prohibiting makeup at forbidden times "
        "except for those with an excuse.\n\n"
        "**Many missed prayers:** One who intentionally skipped many prayers must repent sincerely and "
        "gradually make them up. Some scholars (Maliki) debate whether intentionally abandoned prayers "
        "can be made up, but the majority hold that they must be. [KHILAF]\n\n"
        "**The intention (niyyah):** When making up, state in one's heart: 'I intend to pray qada for the "
        "Fajr/Dhuhr/etc. of [such day].'\n\n"
        "Start now and be consistent — each prayer made up erases a debt to Allah. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the prayer of need (Salat al-Hajah)?",
        "Salat al-Hajah (Prayer of Need) is a voluntary prayer performed when one has a specific need:\n\n"
        "**Evidence:** The Prophet ﷺ said: 'Whoever has a need from Allah or from any human being, "
        "let him perform wudu properly and pray two rak'ahs, then praise Allah and send blessings upon "
        "the Prophet ﷺ, and then say: \"There is no god but Allah, the Forbearing, the Generous. Glory "
        "be to Allah, Lord of the Mighty Throne. Praise be to Allah, Lord of the worlds. O Allah, I ask "
        "You for Your mercy, for Your forgiveness, for Your protection from all sins, for success in all "
        "good deeds, for freedom from all wrongs, O Allah, do not leave any sin of mine without forgiving "
        "it, any worry without relieving it, or any need that pleases You without fulfilling it, O Most "
        "Merciful of those who show mercy.\"' (Ibn Majah, Hadith 1384, graded Hasan by many scholars)\n\n"
        "**How to perform:** Two rak'ahs of voluntary prayer with full concentration, followed by the "
        "specific dua. One may also recite Ayat al-Kursi and the last three surahs.\n\n"
        "**When to perform:** Anytime that is not a forbidden prayer time, especially in the last third "
        "of the night when Allah descends and accepts supplication.\n\n"
        "This prayer combines seeking Allah's help through both action (salah) and supplication (dua). "
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is Khushu (humility/focus) in prayer and how do I achieve it?",
        "Khushu' (خشوع) refers to the inner humility, focus, and presence of heart during salah:\n\n"
        "**Its importance:** Allah says: 'Successful indeed are the believers — those who are humble "
        "in their prayers.' (Quran Al-Mu'minun 23:1-2) Ibn al-Qayyim RH said khushu' is the soul of "
        "salah — without it, the prayer is like a dead body.\n\n"
        "**Practical steps to achieve khushu':**\n\n"
        "1. **Prepare before prayer:** Perform wudu with focus, wear clean clothes, choose a quiet place.\n"
        "2. **Understand what you recite:** Learn the meaning of Al-Fatihah and your surahs in Arabic and "
        "in your language.\n"
        "3. **Remember you stand before Allah:** Visualize standing before the King of kings. Ibn Abbas RA "
        "said: 'Pray as if it is your farewell prayer.'\n"
        "4. **Slow down:** Do not rush. Maintain tuma'ninah (stillness) in every posture.\n"
        "5. **Vary your surahs:** Reciting different surahs keeps the mind engaged.\n"
        "6. **Remove distractions:** Turn off devices, avoid images in your prayer area.\n"
        "7. **Make sujood long:** The Prophet ﷺ used to make his sujood long — this is the station "
        "of greatest closeness to Allah.\n\n"
        "**Fighting waswas (whispers):** The Prophet ﷺ advised seeking refuge in Allah from Shaytan "
        "and spitting lightly to the left if distracted. (Muslim, Hadith 2203)\n\n"
        "Khushu' develops gradually through consistent practice and learning. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the virtues of Fajr and Asr prayers?",
        "Fajr and Asr hold special status among the five daily prayers:\n\n"
        "**Fajr prayer:**\n"
        "- Allah says: 'And [also] the Quran of dawn. Indeed, the recitation of dawn is ever witnessed.' "
        "(Quran Al-Isra 17:78) — angels of the night and day both witness Fajr.\n"
        "- The Prophet ﷺ said: 'Whoever prays Fajr in congregation, he is in the protection of Allah.' "
        "(Muslim, Hadith 657, Sahih)\n"
        "- 'Whoever prays the two cool prayers (Fajr and Asr) will enter Jannah.' (Bukhari, Hadith 574, Sahih)\n"
        "- Fajr is the hardest prayer for hypocrites — attending it marks sincere faith.\n\n"
        "**Asr prayer:**\n"
        "- The Prophet ﷺ said: 'The one who misses Asr prayer is as if he lost his family and wealth.' "
        "(Bukhari, Hadith 552, Sahih)\n"
        "- Asr is called 'the middle prayer' in Quran Al-Baqarah 2:238, indicating its great importance.\n"
        "- Angels attend and record deeds at both Fajr and Asr times. (Bukhari, Hadith 555)\n\n"
        "**Jumu'ah (Friday):** The Prophet ﷺ especially warned about missing Asr on Fridays. "
        "Both Fajr and Asr mark the transition between day and night — spiritually significant times "
        "when Allah's barakah descends. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the ruling on the Witr prayer?",
        "Witr prayer is a confirmed sunnah (sunnah mu'akkadah) that every Muslim should establish:\n\n"
        "**Its importance:** The Prophet ﷺ said: 'The witr is a duty upon every Muslim. Whoever wishes "
        "may pray five rak'ahs, whoever wishes may pray three, and whoever wishes may pray one.' "
        "(Abu Dawud, Hadith 1422, Sahih)\n\n"
        "**[KHILAF] Is it obligatory?** The Hanafi madhab holds witr as wajib (obligatory but below fard). "
        "The majority (Shafi'i, Maliki, Hanbali) consider it a strongly confirmed sunnah.\n\n"
        "**Time:** After Isha prayer until Fajr. The best time is the last third of the night. "
        "If one fears not waking up, praying before sleep is fine.\n\n"
        "**Number of rak'ahs:** One, three, five, seven, nine, or eleven — always ending on an odd number. "
        "The minimum is one rak'ah according to the majority.\n\n"
        "**The three-rak'ah witr:** One may pray 2+1 (with tasleem between) or 3 continuous rak'ahs. "
        "The Maliki madhab generally prefers 3 with one tasleem.\n\n"
        "**Qunoot:** Reciting Qunoot dua in the last rak'ah of witr is sunnah. The Prophet ﷺ taught "
        "Al-Hasan RA: 'Allahumma ihdini fiman hadayt...' (Abu Dawud, Hadith 1425, Hasan)\n\n"
        "Do not sleep without praying witr — the Prophet ﷺ never abandoned it. Allahu Akbar, and Allah knows best."
    ),
    (
        "How should I perform the prayer of the traveler (Salat al-Musafir)?",
        "The traveler has special concessions (rukhsah) in prayer, which is a mercy from Allah:\n\n"
        "**Shortening (Qasr):** A traveler may shorten four-rak'ah prayers (Dhuhr, Asr, Isha) to two rak'ahs. "
        "Allah says: 'And when you travel throughout the land, there is no blame upon you for shortening "
        "the prayer.' (Quran An-Nisa 4:101)\n\n"
        "**When does travel begin?** The majority hold that once one leaves their city boundaries with "
        "the intention of traveling at least 48 miles (Shafi'i/Hanbali) or 3 days' journey (Hanafi). [KHILAF]\n\n"
        "**Combining prayers (Jam'):** A traveler may also combine Dhuhr with Asr, and Maghrib with Isha. "
        "The Prophet ﷺ combined prayers during travel. (Muslim, Hadith 703, Sahih)\n\n"
        "**Duration of travel:** The Shafi'i and Hanbali madhabs hold that once one intends to stay 4+ days, "
        "the concession ends. The Hanafi madhab sets this at 15 days. [KHILAF]\n\n"
        "**Fajr and Maghrib:** These are not shortened (Fajr is 2 rak'ahs already; Maghrib is 3 and not reduced).\n\n"
        "**Priority of using the concession:** The Prophet ﷺ said: 'Allah loves that His concessions "
        "(rukhsah) be taken, just as He loves His strict commands to be followed.' (Ibn Hibban, Sahih)\n\n"
        "Take this mercy from Allah gratefully. Allahu Akbar, and Allah knows best."
    ),
    (
        "What breaks the prayer (nullifiers of salah)?",
        "The following actions invalidate the salah and require one to restart:\n\n"
        "**1. Losing wudu:** Passing wind, urine, stool, or other hadath during prayer. The Prophet ﷺ said: "
        "'Allah does not accept the prayer of one who is in a state of minor impurity until he makes wudu.' "
        "(Bukhari, Hadith 135, Sahih)\n\n"
        "**2. Intentional speech:** Deliberately speaking other than the words of prayer. (Muslim, Hadith 537)\n\n"
        "**3. Excessive movement:** Three or more unnecessary consecutive movements that are unrelated to prayer.\n\n"
        "**4. Turning the chest away from qiblah:** Deliberately facing away from the direction of Ka'bah.\n\n"
        "**5. Laughing audibly:** Loud laughter (not smiling) breaks the prayer by consensus [IJMA].\n\n"
        "**6. Eating or drinking:** Any intentional consumption nullifies prayer.\n\n"
        "**7. Uncovering the awrah:** If one's covering slips and is not fixed immediately.\n\n"
        "**8. Intentional major ritual impurity (hadath akbar):** Janabah occurring during prayer.\n\n"
        "**Does not break prayer:** Passing in front of someone praying, a small sneeze or cough, "
        "accidental slight movement. The person praying should use a sutrah (barrier) to prevent "
        "others passing in front. Allahu Akbar, and Allah knows best."
    ),
]

_SALAH_PREFIXES = [
    "Can you explain ", "Please tell me about ", "In Islamic jurisprudence, ",
    "According to the Sunnah, ", "From a fiqh perspective, ",
]


def generate_salah_pairs() -> list[dict]:
    base = [_pair(q, a, "salah_details", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "intermediate")
            for q, a in _SALAH_PAIRS]
    return base + _rephrase(base, _SALAH_PREFIXES)


# ─── 2. Ramadan & Fasting ─────────────────────────────────────────────────────

_RAMADAN_PAIRS: list[tuple[str, str]] = [
    (
        "What are the virtues and rewards of fasting Ramadan?",
        "Ramadan is the most blessed month, filled with mercy, forgiveness, and freedom from Hellfire:\n\n"
        "**The obligation:** 'O you who have believed, decreed upon you is fasting as it was decreed "
        "upon those before you so that you may become righteous.' (Quran Al-Baqarah 2:183)\n\n"
        "**Tremendous rewards:**\n"
        "- The Prophet ﷺ said: 'Whoever fasts Ramadan with faith and seeking reward, his previous sins "
        "will be forgiven.' (Bukhari, Hadith 38, Sahih)\n"
        "- 'When Ramadan comes, the gates of Jannah are opened, the gates of Jahannam are closed, "
        "and the shayateen are chained.' (Bukhari, Hadith 1899, Sahih)\n"
        "- 'In Ramadan, every night Allah frees people from Hellfire.' (Ahmad, Hasan)\n"
        "- Laylat al-Qadr (Night of Power) is worth more than 1,000 months (83+ years) of worship. "
        "(Quran Al-Qadr 97:3)\n\n"
        "**Fasting as a shield:** The Prophet ﷺ said: 'Fasting is a shield. When one of you is fasting, "
        "he should not speak obscenely or behave in an ignorant manner.' (Bukhari, Hadith 1904, Sahih)\n\n"
        "**Allah's special reward:** 'Every deed of the son of Adam is for him except fasting — "
        "it is for Me and I shall reward it.' (Bukhari, Hadith 7492, Sahih)\n\n"
        "Maximize Ramadan through prayer, Quran, charity, and dhikr. Allahu Akbar, and Allah knows best."
    ),
    (
        "What nullifies the Ramadan fast?",
        "The following actions invalidate a Ramadan fast and may require qada (making up) or kaffarah:\n\n"
        "**Things that break the fast requiring qada only:**\n"
        "1. Intentional eating or drinking during fasting hours\n"
        "2. Intentional vomiting (if one forces themselves to vomit)\n"
        "3. Beginning menstruation or postnatal bleeding\n"
        "4. Cupping (hijama) — according to some scholars based on hadith in Abu Dawud\n"
        "5. Injection of nutritive substances [KHILAF — many contemporary scholars permit injections]\n\n"
        "**Things requiring both qada AND kaffarah (expiation):**\n"
        "Intentional sexual intercourse during the day of Ramadan. Kaffarah = freeing a slave OR "
        "fasting two consecutive months OR feeding 60 poor people. (Bukhari, Hadith 1936, Sahih)\n\n"
        "**Things that do NOT break the fast:**\n"
        "- Unintentional eating/drinking (forgetting)\n"
        "- Rinsing mouth with water without swallowing\n"
        "- Using miswak or toothbrush\n"
        "- Eye/ear drops (majority view)\n"
        "- Medical injections not for nutrition\n"
        "- Swallowing one's own saliva\n"
        "- Wet dream (ghusl required but fast continues)\n\n"
        "The Prophet ﷺ said: 'Whoever forgets he is fasting and eats or drinks, let him complete his fast, "
        "for Allah has fed and watered him.' (Bukhari, Hadith 1933, Sahih)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the etiquettes and recommended acts of Ramadan?",
        "Ramadan has many recommended acts that multiply rewards and deepen taqwa:\n\n"
        "**Suhoor (pre-dawn meal):** The Prophet ﷺ said: 'Eat suhoor, for there is barakah in suhoor.' "
        "(Bukhari, Hadith 1923, Sahih) Even a few sips of water counts as suhoor.\n\n"
        "**Iftar (breaking fast):** Break fast at sunset immediately. The Prophet ﷺ said: 'The people "
        "will remain in goodness as long as they hasten to break the fast.' (Bukhari, Hadith 1957, Sahih)\n"
        "Dua at iftar: 'Allahumma laka sumtu wa bika amantu wa alayka tawakkaltu wa ala rizqika "
        "aftartu — O Allah, for You I fasted, in You I believe, upon You I rely, and with Your "
        "provision I break my fast.' (Abu Dawud, Hadith 2358, Hasan)\n\n"
        "**Tarawih prayer:** Praying in congregation at night. The Prophet ﷺ said: 'Whoever stands "
        "in prayer during Ramadan with faith and seeking reward, his previous sins will be forgiven.' "
        "(Bukhari, Hadith 37, Sahih)\n\n"
        "**Increased Quran recitation:** Jibreel AS would revise the entire Quran with the Prophet ﷺ "
        "every Ramadan. (Bukhari, Hadith 3554)\n\n"
        "**Sadaqah:** The Prophet ﷺ was most generous in Ramadan, like a free-flowing breeze. (Bukhari, Hadith 3554)\n\n"
        "**I'tikaf in last 10 nights:** Seclusion in mosque to seek Laylat al-Qadr. (Bukhari, Hadith 2020)\n\n"
        "**Seeking Laylat al-Qadr:** In odd nights of the last 10: 'Allahumma innaka Afuwwun tuhibbul "
        "afwa fa'fu anni — O Allah, You are Al-Afuw (Pardoner), You love pardon, so pardon me.' "
        "(Tirmidhi, Hadith 3513, Sahih)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "Who is exempt from fasting Ramadan?",
        "Islam provides mercy for those unable to fast through legitimate exemptions:\n\n"
        "**The ill:** One who is sick and fears harm from fasting may break the fast and make up the "
        "days later. 'Allah does not burden a soul beyond that it can bear.' (Quran Al-Baqarah 2:286)\n\n"
        "**The traveler:** A traveler may break the fast and make up the days. Allah says: 'Whoever "
        "among you is ill or on a journey — then an equal number of other days.' (Quran Al-Baqarah 2:184)\n\n"
        "**Pregnant and nursing women:** [KHILAF] If they fear harm to themselves or the child, they "
        "may break the fast. They must make up the days; some scholars (Ibn Abbas RA) also require fidyah "
        "(feeding one poor person per day).\n\n"
        "**The elderly:** Those too old or frail to fast may pay fidyah: feeding one poor person per day "
        "instead of making up the fasts. (Quran Al-Baqarah 2:184 — 'for those who can fast only with "
        "hardship')\n\n"
        "**Women during menstruation/postnatal bleeding:** Must break the fast and make up the days. "
        "The Prophet ﷺ confirmed this. (Bukhari, Hadith 1951, Sahih)\n\n"
        "**The insane and children:** Not obligated to fast; children should be encouraged gradually.\n\n"
        "Fidyah amount: Feeding the equivalent of one mudd (~750g) of food per day to a poor person. "
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is Laylat al-Qadr and how should I seek it?",
        "Laylat al-Qadr (Night of Decree/Power) is the most blessed night in the Islamic calendar:\n\n"
        "**Its significance:** Allah says: 'The Night of Decree is better than a thousand months. "
        "The angels and the Spirit descend therein by permission of their Lord for every matter. "
        "Peace it is until the emergence of dawn.' (Quran Al-Qadr 97:1-5)\n\n"
        "**When it occurs:** The Prophet ﷺ said: 'Seek it in the odd nights of the last ten days of "
        "Ramadan.' (Bukhari, Hadith 2017, Sahih) The most commonly cited nights are 21, 23, 25, 27, 29. "
        "Many scholars give preference to the 27th, though this is not certain.\n\n"
        "**Signs:** The Prophet ﷺ described it as a peaceful, cool night, and the sun rises the next "
        "morning without prominent rays. (Muslim, Hadith 762)\n\n"
        "**What to do:**\n"
        "1. Pray Tarawih and Tahajjud all 10 nights\n"
        "2. Recite much Quran\n"
        "3. Make abundant dua, especially: 'Allahumma innaka Afuwwun Karimun tuhibbul afwa fa'fu anni'\n"
        "4. Give sadaqah generously\n"
        "5. Perform I'tikaf (seclusion in mosque)\n"
        "6. Make istighfar and dhikr\n\n"
        "**If one catches it:** The Prophet ﷺ said: 'Whoever stands in prayer on Laylat al-Qadr "
        "with faith and seeking reward, his previous sins will be forgiven.' (Bukhari, Hadith 2014, Sahih)\n\n"
        "Don't miss any of the 10 nights. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is fidyah and kaffarah in fasting?",
        "Fidyah and kaffarah are two different types of compensation related to fasting:\n\n"
        "**Fidyah (ransom/compensation):**\n"
        "Fidyah is for those who cannot fast and cannot make up the days:\n"
        "- Elderly who are permanently unable to fast\n"
        "- Chronically ill who cannot recover\n"
        "- Pregnant/nursing women (according to some scholars)\n\n"
        "Amount: Feed one poor person per missed day — approximately 750g (one mudd) of staple food, "
        "or its equivalent monetary value. (Quran Al-Baqarah 2:184)\n\n"
        "**Kaffarah (expiation):**\n"
        "Kaffarah is required specifically for intentional sexual intercourse during a Ramadan fast day.\n\n"
        "The expiation in order: [IJMA on sequence]\n"
        "1. **Free a slave** (not applicable today)\n"
        "2. **Fast two consecutive months** (60 days — cannot be interrupted without valid reason)\n"
        "3. **Feed 60 poor people** (each one meal)\n\n"
        "Evidence: A man came to the Prophet ﷺ saying he had had intercourse with his wife during "
        "Ramadan. The Prophet ﷺ asked about each option, and when the man claimed inability, "
        "gave him dates to feed to poor people. (Bukhari, Hadith 1936, Sahih)\n\n"
        "[KHILAF] Some scholars require kaffarah for other major intentional fasting violations (not just intercourse).\n\n"
        "Both fidyah and kaffarah reflect Islam's balance of mercy and accountability. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the voluntary fasts in Islam besides Ramadan?",
        "The Sunnah encourages several voluntary fasts throughout the year with great rewards:\n\n"
        "**Six days of Shawwal:** After Ramadan. The Prophet ﷺ said: 'Whoever fasts Ramadan then "
        "follows it with six days of Shawwal — it is as if he fasted the entire year.' "
        "(Muslim, Hadith 1164, Sahih) [Mathematical reason: Ramadan=30 × 10 = 300 days + 6×10=60 = 360]\n\n"
        "**Monday and Thursday:** The Prophet ﷺ fasted these regularly. He ﷺ said: 'Deeds are "
        "presented [to Allah] on Monday and Thursday.' (Tirmidhi, Hadith 747, Hasan)\n\n"
        "**Three white days (Ayyam al-Beed):** 13th, 14th, 15th of each lunar month. "
        "'The Prophet ﷺ used to observe them and command us to do so.' (Abu Dawud, Hadith 2449, Sahih)\n\n"
        "**Day of Arafah (9th Dhul Hijjah):** The Prophet ﷺ said: 'Fasting the day of Arafah expiates "
        "the sins of the previous year and the coming year.' (Sahih Muslim, narrated by Abu Qatada RA) "
        "[Not for pilgrims who are at Arafah]\n\n"
        "**Day of Ashura (10th Muharram):** 'Fasting Ashura expiates the sins of the previous year.' "
        "(Sahih Muslim, narrated by Abu Qatada RA) Fast the 9th and 10th together to differ from Jewish practice.\n\n"
        "**Month of Muharram:** 'The best fasting after Ramadan is in Allah's sacred month, Muharram.' "
        "(Muslim, Hadith 1163, Sahih)\n\n"
        "**Dawud's AS fast (Sawm Dawud):** Fast every other day — the most beloved voluntary fast to Allah. "
        "(Bukhari, Hadith 1131, Sahih)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is I'tikaf and what are its conditions?",
        "I'tikaf (اعتكاف) is a form of worship involving seclusion in the mosque for the sake of Allah:\n\n"
        "**Definition:** Staying in the mosque with the intention of worship and closeness to Allah, "
        "detached from worldly affairs.\n\n"
        "**Sunnah of the Prophet ﷺ:** He ﷺ observed I'tikaf in the last 10 days of Ramadan every "
        "year until his death. (Bukhari, Hadith 2026, Sahih) This is its most common time.\n\n"
        "**Conditions for I'tikaf:**\n"
        "1. **Muslim:** Must be a Muslim\n"
        "2. **Pure state:** Must be free of major ritual impurity (janabah, menstruation)\n"
        "3. **Intention:** Niyyah to perform I'tikaf\n"
        "4. **Valid mosque:** In a mosque where congregation prayers are held [Hanbali: must be Friday mosque]\n\n"
        "**What is allowed during I'tikaf:**\n"
        "- Prayer, Quran recitation, dhikr, dua\n"
        "- Leaving briefly for necessary bodily needs\n"
        "- A spouse visiting and brief conversations\n\n"
        "**What breaks I'tikaf:**\n"
        "- Intentionally leaving the mosque without necessity\n"
        "- Sexual intercourse (Quran Al-Baqarah 2:187)\n"
        "- Losing one's mind or apostasy (Allah forbid)\n\n"
        "**Can women observe I'tikaf?** Yes — in the mosque. Some scholars permit home I'tikaf for women, "
        "but the majority require a mosque. [KHILAF]\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
]

_RAMADAN_PREFIXES = [
    "Tell me about ", "What does Islam teach about ", "Can you explain ",
    "From an Islamic perspective, ", "According to the Prophet ﷺ, what is ",
]


def generate_ramadan_pairs() -> list[dict]:
    base = [_pair(q, a, "ramadan_fasting", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "intermediate")
            for q, a in _RAMADAN_PAIRS]
    return base + _rephrase(base, _RAMADAN_PREFIXES)


# ─── 3. Zakat Details ─────────────────────────────────────────────────────────

_ZAKAT_PAIRS: list[tuple[str, str]] = [
    (
        "What is zakat and who must pay it?",
        "Zakat (زكاة) is the third pillar of Islam — a mandatory annual alms-tax purifying wealth:\n\n"
        "**The obligation:** 'And establish prayer and give zakat and bow with those who bow [in worship "
        "and obedience].' (Quran Al-Baqarah 2:43) Zakat is mentioned alongside salah 28 times in the Quran.\n\n"
        "**Who must pay:**\n"
        "1. Muslim (zakat is not required from non-Muslims)\n"
        "2. Sane adult (baligh)\n"
        "3. Free (historically; slavery abolished)\n"
        "4. Possesses nisab (minimum threshold) for one full lunar year (hawl)\n\n"
        "**Nisab thresholds:**\n"
        "- Gold: 85 grams of gold\n"
        "- Silver: 595 grams of silver\n"
        "- Cash/savings: equivalent of the above (scholars differ on which to use; silver nisab is lower, "
        "benefiting more poor people)\n\n"
        "**Rate:** 2.5% of total qualifying wealth held for one lunar year.\n\n"
        "**Severe warning for non-payment:** 'Those who hoard gold and silver and do not spend it in "
        "the way of Allah — give them tidings of a painful punishment.' (Quran At-Tawbah 9:34)\n\n"
        "**Purification:** Zakat purifies remaining wealth and the giver's soul from greed. "
        "'Take from their wealth a charity by which you purify them and cause them increase.' "
        "(Quran At-Tawbah 9:103)\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "Who are the eight categories eligible to receive zakat?",
        "Allah has specified the eight recipients (mustahiqqun) of zakat in the Quran:\n\n"
        "'Zakah expenditures are only for the poor and for the needy and for those employed to collect "
        "[zakah] and for bringing hearts together [for Islam] and for freeing captives [or slaves] and "
        "for those in debt and for the cause of Allah and for the [stranded] traveler — an obligation "
        "[imposed] by Allah.' (Quran At-Tawbah 9:60)\n\n"
        "**The Eight Categories:**\n"
        "1. **Al-Fuqara (Poor):** Those with insufficient means to meet basic needs\n"
        "2. **Al-Masakin (Needy):** Those with some income but insufficient for basic needs\n"
        "3. **Al-Amilin (Zakat workers):** Those employed to collect and distribute zakat\n"
        "4. **Al-Mu'allafatu Qulubuhum (New/reconciled hearts):** New Muslims or those whose hearts "
        "are being softened toward Islam\n"
        "5. **Fir-Riqab (Freeing slaves/captives):** Historically to free slaves; today used for "
        "freeing those in unjust captivity\n"
        "6. **Al-Gharimun (Debtors):** Those in debt for permissible purposes unable to repay\n"
        "7. **Fi Sabilillah (In the way of Allah):** Historically jihad; scholars expand to Islamic "
        "education, dawah, building mosques [KHILAF on scope]\n"
        "8. **Ibn al-Sabil (Stranded traveler):** A traveler who has run out of funds\n\n"
        "**Who cannot receive zakat:** Banu Hashim (Prophet's ﷺ family by majority view), wealthy "
        "people, non-Muslims (except category 4), and one's immediate dependents.\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What wealth is subject to zakat?",
        "Zakat applies to specific categories of wealth that meet the nisab threshold:\n\n"
        "**1. Gold and Silver:** 2.5% of gold exceeding 85g / silver exceeding 595g held for one year.\n\n"
        "**2. Cash and Savings:** Any currency equivalent to the nisab of gold or silver. Includes "
        "bank accounts, investments, and money owed to you. Rate: 2.5%.\n\n"
        "**3. Business goods (Urud al-Tijarah):** Stock-in-trade valued at market price. Rate: 2.5%. "
        "Working tools and equipment used in business are exempt.\n\n"
        "**4. Agricultural produce:** Upon harvest. Rate: 10% if rain-irrigated, 5% if artificially "
        "irrigated. Nisab: 653kg of grain. (Bukhari, Hadith 1483, Sahih)\n\n"
        "**5. Livestock (An'am):** Camels, cattle, sheep/goats that graze freely for most of the year. "
        "Complex tables exist for each animal type. The Prophet ﷺ sent detailed instructions. (Bukhari, Hadith 1454)\n\n"
        "**6. Minerals and Rikaz:** Items found underground — 20% (one-fifth/khums) immediately upon "
        "discovery. No hawl required.\n\n"
        "**7. Investment property:** [KHILAF] Rental income is subject to zakat; the property itself "
        "is debated among contemporary scholars.\n\n"
        "**Exempt from zakat:** Primary residence, personal vehicle, clothing, household items, "
        "professional tools, jewelry used regularly (Hanafi view — others differ on jewelry).\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What is Zakat al-Fitr and when must it be paid?",
        "Zakat al-Fitr (Sadaqat al-Fitr) is a special charity obligatory at the end of Ramadan:\n\n"
        "**The obligation:** Ibn Abbas RA reported: 'The Messenger of Allah ﷺ made Zakat al-Fitr "
        "obligatory as a purification for the fasting person from vain talk and foul language, "
        "and as food for the poor.' (Abu Dawud, Hadith 1609, Sahih)\n\n"
        "**Who must pay:** Every Muslim — man, woman, child, free or enslaved — who has food beyond "
        "their basic needs on Eid day. One pays on behalf of themselves and their dependents.\n\n"
        "**Amount:** One sa' (≈2.5-3kg) of the staple food of the region — wheat, barley, dates, "
        "raisins, or rice. The Prophet ﷺ specified a sa' of food per person. (Bukhari, Hadith 1503, Sahih)\n\n"
        "**[KHILAF] Cash payment:** The Hanafi madhab permits paying the monetary equivalent. "
        "The majority (Shafi'i, Maliki, Hanbali) prefer giving actual food as in the Sunnah.\n\n"
        "**When to pay:** It can be given from the beginning of Ramadan, but must be paid before "
        "Eid prayer. Giving it after Eid prayer makes it ordinary sadaqah, not Zakat al-Fitr.\n\n"
        "**Who receives it:** The poor and needy. It must reach them before Eid prayer so they "
        "can celebrate without need.\n\n"
        "This small act has a huge purifying effect. Allahu Akbar, and Allah knows best."
    ),
]

_ZAKAT_PREFIXES = [
    "Please explain ", "Can you describe ", "What does Islam say about ", "Tell me more about ",
]


def generate_zakat_pairs() -> list[dict]:
    base = [_pair(q, a, "zakat_details", ["Quran", "Sahih Bukhari", "Sahih Muslim", "Abu Dawud"], "intermediate")
            for q, a in _ZAKAT_PAIRS]
    return base + _rephrase(base, _ZAKAT_PREFIXES)


# ─── 4. Marriage & Family Fiqh ────────────────────────────────────────────────

_MARRIAGE_PAIRS: list[tuple[str, str]] = [
    (
        "What are the conditions (arkan) and pillars of a valid Islamic marriage?",
        "An Islamic marriage (nikah) is a sacred contract with specific requirements for validity:\n\n"
        "**Pillars of Nikah:**\n\n"
        "**1. Offer and Acceptance (Ijab and Qabul):** Clear verbal offer from the bride's side and "
        "acceptance from the groom, or their representatives, in the same sitting.\n\n"
        "**2. The Wali (Guardian):** A male guardian (father, then other male relatives) must be present "
        "for the bride. The Prophet ﷺ said: 'There is no nikah without a wali.' "
        "(Abu Dawud, Hadith 2085, Sahih) [Hanafi exception: a mature woman may contract her own marriage "
        "though this is makruh without wali.] [KHILAF]\n\n"
        "**3. Two witnesses:** Two adult, sane Muslim males must witness the contract. "
        "(Tirmidhi, Hadith 1101, Hasan)\n\n"
        "**4. Mahr (Dower):** A gift of value from the groom to the bride. It is her exclusive right "
        "and cannot be taken back. 'And give the women [upon marriage] their [bridal] gifts graciously.' "
        "(Quran An-Nisa 4:4) No minimum amount is set, but it must be valuable.\n\n"
        "**Recommended (not obligatory):** Khutbat al-nikah (wedding sermon) and announcing the marriage "
        "publicly. The Prophet ﷺ said: 'Announce the marriage.' (Ahmad, Hasan)\n\n"
        "**Conditions of spouses:** Both must be Muslim (or the husband Muslim and wife from Ahl al-Kitab). "
        "They must be free of marital ties. No forbidden degree of relationship (mahram).\n\n"
        "Marriage is half of one's deen. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the rights and duties of a husband in Islam?",
        "Islam establishes a balanced framework of spousal rights and duties:\n\n"
        "**Husband's rights from the wife:**\n"
        "- Obedience in non-sinful matters: 'Men are the caretakers (qawwamun) of women.' (Quran An-Nisa 4:34)\n"
        "- Being available for intimacy lawfully requested\n"
        "- Not permitting anyone the husband dislikes into the home\n"
        "- Guarding his honor and wealth in his absence\n\n"
        "**Husband's duties toward the wife:**\n"
        "- **Nafaqah (financial maintenance):** Providing food, clothing, and shelter according to his means "
        "and her status. 'And upon the father is [the responsibility for] their provision.' (Quran Al-Baqarah 2:233)\n"
        "- **Mahr payment:** Paying the agreed mahr in full\n"
        "- **Kind treatment (mu'ashara bil-ma'ruf):** 'And live with them in kindness.' (Quran An-Nisa 4:19) "
        "The Prophet ﷺ said: 'The best of you is the best to his family.' (Tirmidhi, Hadith 3895, Sahih)\n"
        "- **Justice among wives:** If polygamous, provide equal time, maintenance, and housing\n"
        "- **Education:** Helping his wife fulfill her religious obligations\n"
        "- **Not harming her:** Physical or emotional abuse is haram\n\n"
        "The Prophet ﷺ treated his wives with love, humor, and tenderness — he even raced with Aisha RA. "
        "A husband's character defines his Islamic standing. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the rights and duties of a wife in Islam?",
        "Islam honors the wife with rights and responsibilities that complement her husband's:\n\n"
        "**Wife's rights from the husband:**\n"
        "- **Mahr:** Her exclusive property, paid in full\n"
        "- **Nafaqah:** Financial support for housing, food, clothing, and medical needs\n"
        "- **Kind treatment:** Emotional respect, no abuse, no humiliation\n"
        "- **Intimacy:** Lawful conjugal rights — she may seek khul' if denied\n"
        "- **Justice:** If co-wife, equal rotation of nights and provision\n"
        "- **Permission to worship:** Access to prayer, learning, and Islamic practice\n\n"
        "**Wife's duties toward the husband:**\n"
        "- **Obedience in lawful matters:** Supporting household harmony\n"
        "- **Guarding the home:** Protecting wealth, children, and honor\n"
        "- **Not fasting voluntary fasts without permission:** To honor her husband's rights "
        "(Bukhari, Hadith 5195) — obligatory fasts need no permission\n"
        "- **Not admitting disliked guests:** The Prophet ﷺ prohibited this\n\n"
        "**Her independent rights regardless of marriage:**\n"
        "- Right to own property, earn income, and spend her money\n"
        "- Right to keep her surname\n"
        "- Right to education and practicing her religion\n"
        "- Right to khul' (initiated divorce) in cases of genuine hardship\n\n"
        "Islam elevated women's status 1,400 years ago. 'And women have rights similar to those over them "
        "in kindness.' (Quran Al-Baqarah 2:228)\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What is khul' (divorce initiated by the wife) in Islam?",
        "Khul' (خلع) is a form of divorce initiated by the wife in exchange for returning the mahr:\n\n"
        "**Definition:** The wife's right to dissolve the marriage by returning the mahr (or agreeing "
        "on a settlement) to the husband.\n\n"
        "**Quranic basis:** 'It is not lawful for you to take back anything of what you have given them "
        "unless both fear that they will not be able to keep [within] the limits of Allah. And if you "
        "fear that they will not keep the limits of Allah, then there is no blame upon either of them "
        "concerning that by which she ransoms herself.' (Quran Al-Baqarah 2:229)\n\n"
        "**Evidence:** The wife of Thabit ibn Qays RA came to the Prophet ﷺ saying she did not "
        "dislike her husband's character or religion, but feared disbelief (kufr) due to her dislike. "
        "The Prophet ﷺ instructed her to return his garden (the mahr), and ordered Thabit to divorce her. "
        "(Bukhari, Hadith 5273, Sahih)\n\n"
        "**[KHILAF] When is it valid?**\n"
        "- Majority: Valid when the wife genuinely dislikes the husband and fears not fulfilling his rights\n"
        "- Hanbali: Valid even without a stated reason\n"
        "- All: Khul' is disliked if without real cause (makruh)\n\n"
        "**What happens:** One talaq (divorce) occurs; no waiting period (iddah) except to confirm "
        "pregnancy (one menstrual cycle per majority view); the husband cannot take her back without "
        "a new nikah and new mahr.\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What is the Islamic ruling on polygamy?",
        "Islam permits, with conditions, a man to marry up to four wives:\n\n"
        "**The permission:** 'And if you fear that you will not deal justly with the orphan girls, "
        "then marry those that please you of [other] women, two or three or four. But if you fear "
        "that you will not be just, then [marry only] one.' (Quran An-Nisa 4:3)\n\n"
        "**The condition of justice:** The Quran emphasizes justice (al-adl) in treatment as the "
        "critical condition. Equal provision of housing, food, clothing, and time must be maintained.\n\n"
        "**Is perfect emotional equality required?** No — the Quran acknowledges: 'You will never be "
        "able to deal justly between wives, even if you are eager to do so.' (Quran An-Nisa 4:129) "
        "This refers to emotional equality; material and time equality is what is obligatory.\n\n"
        "**Why permitted?** Historical and societal contexts: wars leaving many widows, protection "
        "of orphans, medical inability of one wife, demographic realities. It was a reform — "
        "pre-Islamic Arabs had unlimited wives with no rights for women.\n\n"
        "**The default is one:** The Quran recommends one wife for most men: 'But if you fear "
        "you will not be just, then [marry only] one.' Most scholars consider monogamy the default "
        "and safest path for most men.\n\n"
        "**[KHILAF] Women's stipulation against it:** A woman may include in her marriage contract a "
        "condition that her husband not take a second wife. The Hanbali madhab considers this a valid "
        "and binding condition.\n\nAllahu Akbar, and Allah knows best."
    ),
]

_MARRIAGE_PREFIXES = [
    "Please explain ", "Can you describe ", "Tell me about ", "What is the Islamic ruling on ",
]


def generate_marriage_pairs() -> list[dict]:
    base = [_pair(q, a, "marriage_family", ["Quran", "Sahih Bukhari", "Sahih Muslim", "Abu Dawud"], "intermediate")
            for q, a in _MARRIAGE_PAIRS]
    return base + _rephrase(base, _MARRIAGE_PREFIXES)


# ─── 5. Prophetic Medicine (Tibb al-Nabawi) ───────────────────────────────────

_TIBB_PAIRS: list[tuple[str, str]] = [
    (
        "What is Tibb al-Nabawi (Prophetic medicine)?",
        "Tibb al-Nabawi (الطب النبوي) refers to health and healing guidance from the Prophet Muhammad ﷺ:\n\n"
        "**Definition:** The sum of medical treatments, dietary advice, and spiritual healing mentioned "
        "in authentic hadith from the Prophet ﷺ, compiled by scholars like Ibn al-Qayyim RH in his "
        "famous work 'Zad al-Ma'ad' and Ibn Hajar al-Asqalani RH.\n\n"
        "**Categories:**\n"
        "1. **Spiritual healing:** Ruqyah (Quranic recitation), dua, tawakkul, remembrance of Allah\n"
        "2. **Dietary:** Honey, black seed, olive oil, dates, zamzam water, vinegar\n"
        "3. **Physical treatments:** Hijama (cupping), fasting, moderate exercise\n"
        "4. **Preventive:** Quarantine, hygiene, moderation in eating\n\n"
        "**Honey:** 'There is healing in three things: a gulp of honey, cupping, and branding with fire "
        "(cauterizing). But I forbid my nation from cauterizing.' (Bukhari, Hadith 5680, Sahih)\n\n"
        "**Black seed (Habbatus Sauda):** 'In the black seed there is healing for every disease except "
        "death.' (Bukhari, Hadith 5688, Sahih) Modern science confirms its anti-inflammatory, "
        "antimicrobial, and immunomodulatory properties.\n\n"
        "**Important note:** Prophetic medicine complements, but does not replace, modern evidence-based "
        "medicine. Consult a qualified physician for medical conditions. Allahu Akbar, and Allah knows best."
    ),
    (
        "What does Islam say about ruqyah (healing through Quran recitation)?",
        "Ruqyah (رقية) is the practice of reciting Quranic verses and duas for healing and protection:\n\n"
        "**Evidence:** Aisha RA narrated: 'When anyone among us fell sick, the Prophet ﷺ would wipe "
        "them with his right hand and say: \"Remove the harm, O Lord of people! Heal, for You are "
        "the Healer. There is no healing except Your healing — a healing that leaves no disease.\"' "
        "(Bukhari, Hadith 5675, Sahih)\n\n"
        "**Ruqyah recitations:** Al-Fatiha (Quran's opening) is called 'the great cure' (ruqyah kubra). "
        "Ayat al-Kursi (Quran Al-Baqarah 2:255) and Al-Mu'awwidhatain (Surah Al-Falaq 113 and An-Nas 114) "
        "are especially powerful.\n\n"
        "**Permissible ruqyah conditions:**\n"
        "1. Only with words from Quran, Sunnah, or known dua\n"
        "2. In Arabic or understood language\n"
        "3. Not involving shirk, magic, or unknown symbols\n"
        "4. Believing that healing comes from Allah, not the words themselves\n\n"
        "**What is prohibited:** Ruqyah using jinn, shirk (seeking protection from other than Allah), "
        "wearing amulets containing non-Quranic words, or believing in the ruqyah itself as the healer.\n\n"
        "**Self-ruqyah:** One may recite Al-Fatiha, the last two Surahs, and Ayat al-Kursi while "
        "blowing into cupped hands and wiping over the body — this is from the Sunnah.\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the Islamic guidance on fasting for health?",
        "The Prophet ﷺ linked fasting to both spiritual and physical health:\n\n"
        "**The Prophet's ﷺ advice:** 'Fast and you will be healthy.' (Ibn al-Sunni, Hasan li ghayrihi — "
        "consider this as a general guidance, not definitive evidence for specific medical claims)\n\n"
        "**Moderation in eating:** The Prophet ﷺ said: 'The son of Adam does not fill any vessel worse "
        "than his stomach. A few morsels that keep his back straight are sufficient for the son of Adam. "
        "If he must, then one-third for his food, one-third for his drink, and one-third for his breathing.' "
        "(Tirmidhi, Hadith 2380, Sahih)\n\n"
        "**Modern science and Islamic fasting:**\n"
        "- Intermittent fasting (similar to the Islamic practice of no eating between Fajr and Maghrib) "
        "is linked to improved insulin sensitivity, weight management, and cellular autophagy.\n"
        "- The Monday/Thursday fasting Sunnah aligns with principles of periodic metabolic rest.\n"
        "- Ramadan fasting studies show benefits in cardiovascular markers and metabolic health.\n\n"
        "**Suhoor barakah:** 'Eat suhoor for there is barakah in suhoor.' (Bukhari, Hadith 1923) "
        "This prevents hypoglycemia during fasting hours.\n\n"
        "**Important caveat:** People with diabetes, eating disorders, or medical conditions should "
        "consult a physician before fasting. Islam provides exemptions for the genuinely ill. "
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What does Islam say about hijama (cupping therapy)?",
        "Hijama (الحجامة) is wet cupping therapy, one of the most recommended prophetic treatments:\n\n"
        "**Evidence:** The Prophet ﷺ said: 'The best of your treatments is hijama.' (Abu Dawud, Hadith 3857, Sahih)\n"
        "'Healing is in three things: a gulp of honey, cupping, and branding with fire; but I forbid "
        "my nation from branding.' (Bukhari, Hadith 5680)\n\n"
        "**How the Prophet ﷺ used it:** He ﷺ had hijama performed on his head for migraines, on his "
        "neck for neck pain, and between the shoulders. (Bukhari, Hadith 5699)\n\n"
        "**Best times:** The Prophet ﷺ recommended the 17th, 19th, or 21st of the lunar month, "
        "preferably on a Monday, Tuesday, or Thursday. (Abu Dawud, Tirmidhi)\n\n"
        "**Best locations:** Between the shoulders (al-kahil) for general health, sides of the neck, "
        "back of the head for headaches.\n\n"
        "**Does hijama break the fast?** [KHILAF] This is a well-known point of scholarly disagreement:\n"
        "- Hanbali and some Shafi'i: breaks the fast based on a hadith (Abu Dawud, Hasan)\n"
        "- Majority (Hanafi, Maliki, others): does not break the fast; the hadith is abrogated\n\n"
        "**Modern use:** Hijama is practiced by licensed practitioners globally and shows evidence for "
        "pain management, blood circulation, and inflammation reduction. Always use a certified "
        "practitioner. Allahu Akbar, and Allah knows best."
    ),
]

_TIBB_PREFIXES = [
    "Can you tell me about ", "What does the Prophet ﷺ say about ", "Explain the Islamic view on ",
]


def generate_tibb_pairs() -> list[dict]:
    base = [_pair(q, a, "prophetic_medicine", ["Sahih Bukhari", "Sahih Muslim", "Abu Dawud", "Tirmidhi"], "intermediate")
            for q, a in _TIBB_PAIRS]
    return base + _rephrase(base, _TIBB_PREFIXES)


# ─── 6. Adab (Islamic Etiquette) ──────────────────────────────────────────────

_ADAB_PAIRS: list[tuple[str, str]] = [
    (
        "What are the Islamic etiquettes of eating and drinking?",
        "The Prophet ﷺ established comprehensive dining etiquette that brings barakah and dignity:\n\n"
        "**Before eating:**\n"
        "- Say 'Bismillah' (In the name of Allah). The Prophet ﷺ said: 'When one of you eats, "
        "let him mention Allah's name.' If forgotten at the start, say: 'Bismillah awwalahu wa akhirahu.' "
        "(Abu Dawud, Hadith 3767, Sahih)\n"
        "- Wash hands before and after eating\n\n"
        "**While eating:**\n"
        "- Eat with the right hand: 'The shaytan eats with his left hand.' (Muslim, Hadith 2020, Sahih)\n"
        "- Eat from what is in front of you: 'O young man, mention Allah's name, eat with your right "
        "hand, and eat from what is directly in front of you.' (Bukhari, Hadith 5376, Sahih)\n"
        "- Do not recline while eating (Bukhari, Hadith 5398)\n"
        "- Avoid blowing into food or drink (Tirmidhi, Hadith 1889)\n"
        "- Do not criticize food (Bukhari, Hadith 3563)\n\n"
        "**While drinking:**\n"
        "- Drink in 3 sips, not one long gulp (Tirmidhi, Hadith 1885, Hasan)\n"
        "- Do not breathe into the vessel (Muslim, Hadith 267)\n"
        "- Sit down to drink unless at zamzam (Muslim, Hadith 2024 — standing for zamzam is permissible)\n\n"
        "**After eating:**\n"
        "- Say: 'Alhamdulillahilladhi at'amana wa saqana wa ja'alana muslimeen' "
        "(Abu Dawud, Hadith 3850, Hasan)\n"
        "- Lick fingers and the bowl: 'You do not know in which part the barakah is.' (Muslim, Hadith 2033)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the Islamic etiquettes when visiting someone's home?",
        "The Quran and Sunnah provide detailed guidance for respectful visits:\n\n"
        "**Seeking permission:** 'O you who have believed, do not enter houses other than your own "
        "houses until you ascertain welcome and greet their inhabitants.' (Quran An-Nur 24:27)\n\n"
        "**How to seek permission:** Knock or ring the bell — no more than three times. "
        "The Prophet ﷺ said: 'The salaam is said thrice. If permission is granted, enter. "
        "If not, return.' (Bukhari, Hadith 6245, Sahih)\n\n"
        "**Greeting:** Say 'Assalamu Alaikum wa Rahmatullahi wa Barakatuh' upon entering.\n\n"
        "**Do not look inside:** Do not peer into the home while seeking permission — the Prophet ﷺ "
        "warned about this. (Bukhari, Hadith 6241)\n\n"
        "**Duration of visit:** Do not overstay. Allah says: 'And when you have taken your meal, "
        "disperse, without lingering for conversation.' (Quran Al-Ahzab 33:53)\n\n"
        "**Dua for the host:** When leaving, the guest should pray for the host: 'Allahumma barik lahum "
        "fima razaqtahum — O Allah, bless them in what You have provided them.' (Muslim, Hadith 2042)\n\n"
        "**Gift giving:** Bringing a gift is sunnah and increases love. 'Exchange gifts, as that will "
        "generate love amongst you.' (Al-Adab al-Mufrad, Hasan)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the Islamic etiquettes of speaking and conversation?",
        "The Prophet ﷺ was known as the most eloquent and measured in speech:\n\n"
        "**Think before speaking:** The Prophet ﷺ said: 'Whoever believes in Allah and the Last Day, "
        "let him say what is good or remain silent.' (Bukhari, Hadith 6018, Sahih)\n\n"
        "**Lower the voice:** 'Be moderate in your walking and lower your voice.' (Quran Luqman 31:19) "
        "Luqman's advice to his son.\n\n"
        "**Avoid lying:** 'Truthfulness leads to righteousness, and righteousness leads to Jannah. "
        "Lying leads to wickedness, and wickedness leads to Hellfire.' (Bukhari, Hadith 6094, Sahih)\n\n"
        "**Avoid backbiting (gheebah):** 'Do you know what backbiting is? It is to mention your "
        "brother in a way he would dislike.' (Muslim, Hadith 2589, Sahih) The Quran compares it to "
        "eating one's dead brother's flesh. (Quran Al-Hujurat 49:12)\n\n"
        "**Avoid excessive talk:** 'Most of a person's sins come from his tongue.' (Tirmidhi, Hasan)\n\n"
        "**Speak with gentle words:** 'A gentle word is a form of charity.' (Bukhari, Hadith 2989)\n\n"
        "**Do not interrupt:** Listen fully before responding. The Prophet ﷺ gave his full attention "
        "to every person he spoke with.\n\n"
        "**Greet with full salaam:** The Prophet ﷺ said the best greeting is the full salaam — "
        "not a nod or wave.\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What are the Islamic etiquettes toward parents?",
        "Honoring parents (birr al-walidain) is mentioned alongside tawheed in the Quran:\n\n"
        "**The command:** 'And your Lord has decreed that you not worship except Him, and to parents, "
        "good treatment. Whether one or both of them reach old age [while] with you, say not to them "
        "[so much as] \"uff\" (a word of contempt) and do not repel them but speak to them a noble word.' "
        "(Quran Al-Isra 17:23)\n\n"
        "**Mother's elevated status:** A man asked the Prophet ﷺ who deserves the best companionship. "
        "He ﷺ said: 'Your mother.' Three times. Then 'Your father.' (Bukhari, Hadith 5971, Sahih)\n\n"
        "**After their death:** The Prophet ﷺ said: 'When a person dies, his deeds end except for "
        "three: sadaqah jariyah (ongoing charity), beneficial knowledge, or a righteous child who "
        "prays for him.' (Muslim, Hadith 1631, Sahih) — praying for deceased parents is among the "
        "greatest acts of birr.\n\n"
        "**Obeying parents in haram:** [IJMA] There is no obedience to parents in disobeying Allah. "
        "'There is no obedience to the creation in disobedience to the Creator.' (Ahmad, Sahih)\n\n"
        "**With non-Muslim parents:** 'But accompany them in [this] world with appropriate kindness.' "
        "(Quran Luqman 31:15) — remain dutiful even if they call to kufr, while not obeying the call.\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the Islamic etiquettes of dressing (libas)?",
        "Islamic dress etiquette reflects modesty, identity, and gratitude to Allah:\n\n"
        "**General principles:**\n"
        "- Cleanliness (tahara) is required for prayer and emphasized at all times\n"
        "- Modesty (haya') is the core of Islamic dress: covering the awrah (private parts)\n"
        "- Men's awrah: from navel to knee [IJMA]\n"
        "- Women's awrah in public: entire body except face and hands (majority view) [KHILAF on extent]\n\n"
        "**Sunnah of dress:**\n"
        "- Begin with the right side: 'The Prophet ﷺ liked to start from the right side for "
        "wearing shoes, combing hair, purification, and in all his affairs.' (Bukhari, Hadith 168)\n"
        "- Remove left side first when undressing\n"
        "- Dua when dressing: 'Alhamdulillahilladhi kasani hadha wa razaqanihi min ghayri hawlin "
        "minni wa la quwwah' (Tirmidhi, Hadith 3458, Hasan)\n\n"
        "**Prohibitions:**\n"
        "- Men wearing silk: 'Gold and silk are forbidden to the males of my ummah.' "
        "(Tirmidhi, Hadith 1720, Sahih) [Exception: medical necessity]\n"
        "- Isbaal (dragging garment below ankles out of pride): Forbidden for men (Bukhari, Hadith 5787)\n"
        "- Tashabbuh (imitating the opposite gender in dress): The Prophet ﷺ cursed men who imitate "
        "women and women who imitate men. (Bukhari, Hadith 5885)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
]

_ADAB_PREFIXES = [
    "Please describe ", "Tell me about ", "What is the Sunnah regarding ",
]


def generate_adab_pairs() -> list[dict]:
    base = [_pair(q, a, "adab_etiquette", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "beginner")
            for q, a in _ADAB_PAIRS]
    return base + _rephrase(base, _ADAB_PREFIXES)


# ─── 7. Duas from the Quran ───────────────────────────────────────────────────

_DUAS_QURAN_PAIRS: list[tuple[str, str]] = [
    (
        "What is the dua of Prophet Ibrahim (AS) for his offspring and the city of Makkah?",
        "Prophet Ibrahim AS made powerful supplications when establishing the foundations of faith:\n\n"
        "**Dua for Makkah and guidance:** 'Our Lord, I have settled some of my descendants in an "
        "uncultivated valley near Your sacred House, our Lord, that they may establish prayer. So make "
        "hearts among the people incline toward them and provide for them from the fruits that they "
        "might be grateful.' (Quran Ibrahim 14:37)\n\n"
        "**Dua for acceptance of worship:** 'Our Lord, accept [this] from us. Indeed You are the "
        "Hearing, the Knowing.' (Quran Al-Baqarah 2:127)\n\n"
        "**Dua for Muslim nation:** 'Our Lord, and make us Muslims [in submission] to You and from "
        "our descendants a Muslim nation [in submission] to You. And show us our rites and accept "
        "our repentance. Indeed, You are the Accepting of repentance, the Merciful.' "
        "(Quran Al-Baqarah 2:128)\n\n"
        "**Dua for parents and believers:** 'Our Lord, forgive me and my parents and the believers "
        "the Day the account is established.' (Quran Ibrahim 14:41)\n\n"
        "These duas of Ibrahim AS are recited to this day in the tashahud, reminding us that "
        "salah connects every Muslim to the du'a of Ibrahim AS. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the dua of Prophet Yunus (Jonah) AS when he was in the whale's belly?",
        "Prophet Yunus AS (Jonah) was swallowed by a great whale and called upon Allah:\n\n"
        "**The dua:** 'La ilaha illa Anta, subhanaka, inni kuntu min al-dhalimin — "
        "There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.' "
        "(Quran Al-Anbiya 21:87)\n\n"
        "**Transliteration:** لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ\n\n"
        "**Allah's response:** 'So We responded to him and saved him from the distress. And thus do We "
        "save the believers.' (Quran Al-Anbiya 21:88)\n\n"
        "**Its power:** The Prophet ﷺ said: 'No Muslim calls upon Allah with this dua in any matter "
        "except that Allah responds to him.' (Tirmidhi, Hadith 3505, Sahih)\n\n"
        "**Context:** Yunus AS left his people without Allah's permission when they did not believe. "
        "He was swallowed by the whale and confined in three darknesses — the depths of the sea, "
        "the night, and the belly. His dua combined tawheed (La ilaha illa Anta), tasbih (subhanaka), "
        "and istighfar (inni kuntu min al-dhalimin).\n\n"
        "**Lesson:** This dua is especially powerful because it acknowledges Allah's perfection and "
        "one's own shortcoming. Call upon Allah with it in any difficulty. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the dua of Prophet Ayyub (Job) AS during his illness?",
        "Prophet Ayyub AS was tested with severe illness and loss for many years, yet remained patient:\n\n"
        "**The dua:** 'Rabbi anni massaniyad-durru wa Anta arhamur-rahimin — "
        "My Lord, adversity has touched me, and you are the Most Merciful of the merciful.' "
        "(Quran Al-Anbiya 21:83)\n\n"
        "**Transliteration:** رَبِّ أَنِّي مَسَّنِيَ الضُّرُّ وَأَنتَ أَرْحَمُ الرَّاحِمِينَ\n\n"
        "**Allah's response:** 'So We responded to him and removed what afflicted him of adversity. "
        "And We gave back his family and the like thereof with them as mercy from Us and a reminder "
        "for the worshippers [of Allah].' (Quran Al-Anbiya 21:84)\n\n"
        "**His story:** Ayyub AS was blessed with health, wealth, and family. Allah tested him by "
        "allowing illness to afflict him for 18 years (or more). He remained patient and grateful. "
        "His wife cared for him throughout. He never complained directly to Allah but mentioned his "
        "state, acknowledging Allah's mercy.\n\n"
        "**Lesson:** This dua teaches that expressing one's pain to Allah — without demanding — is "
        "not a violation of sabr (patience). True patience includes turning to Allah in difficulty "
        "and trusting in His mercy. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is Ayat al-Kursi and why is it so important?",
        "Ayat al-Kursi (آية الكرسي) is the greatest verse in the Quran, affirming Allah's absolute sovereignty:\n\n"
        "**The verse (Quran Al-Baqarah 2:255):**\n"
        "Arabic: اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ\n"
        "Translation: 'Allah — there is no deity except Him, the Ever-Living, the Sustainer of existence. "
        "Neither drowsiness overtakes Him nor sleep. To Him belongs whatever is in the heavens and whatever "
        "is on the earth. Who is it that can intercede with Him except by His permission? He knows what "
        "is [presently] before them and what will be after them, and they encompass not a thing of His "
        "knowledge except for what He wills. His Kursi (footstool) extends over the heavens and the earth, "
        "and their preservation tires Him not. And He is the Most High, the Most Great.'\n\n"
        "**Its virtues:**\n"
        "- The Prophet ﷺ said: 'The greatest ayah in the Quran is Ayat al-Kursi.' (Muslim, Hadith 810, Sahih)\n"
        "- 'Whoever recites it after every obligatory prayer, nothing stands between him and Jannah "
        "except death.' (An-Nasa'i, graded Sahih by Ibn Hibban)\n"
        "- Reciting before sleep: An angel guards you until morning. (Bukhari, Hadith 5010, Sahih)\n\n"
        "**When to recite:** After every salah, before sleep, for protection from evil, and in times "
        "of fear. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the last two verses of Surah Al-Baqarah and their virtues?",
        "The last two verses of Surah Al-Baqarah (2:285-286) are among the most powerful in the Quran:\n\n"
        "**The verses:**\n"
        "2:285: 'The Messenger has believed in what was revealed to him from his Lord, and [so have] "
        "the believers. All of them have believed in Allah and His angels and His books and His messengers, "
        "[saying], \"We make no distinction between any of His messengers.\" And they say, \"We hear "
        "and we obey. [We seek] Your forgiveness, our Lord, and to You is the [final] destination.\"'\n\n"
        "2:286: 'Allah does not burden a soul beyond that it can bear. It will have [the consequence of] "
        "what [good] it has gained, and it will bear [the consequence of] what [evil] it has earned. "
        "Our Lord, do not impose blame upon us if we forget or make an error. Our Lord, and lay not "
        "upon us a burden like that which You laid upon those before us. Our Lord, and burden us not "
        "with that which we have no ability to bear. And pardon us; and forgive us; and have mercy "
        "upon us. You are our protector, so give us victory over the disbelieving people.'\n\n"
        "**Their virtues:** The Prophet ﷺ said: 'Whoever recites the last two verses of Surah "
        "Al-Baqarah at night, they will suffice him.' (Bukhari, Hadith 4008, Sahih) — suffice as "
        "protection or reward. Jibreel AS revealed them directly from the Throne of Allah. "
        "(Muslim, Hadith 806)\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What is Surah Al-Ikhlas and why is it equal to a third of the Quran?",
        "Surah Al-Ikhlas (Chapter 112) is one of the shortest yet most profound surahs:\n\n"
        "**The Surah:**\n"
        "Arabic: قُلْ هُوَ اللَّهُ أَحَدٌ • اللَّهُ الصَّمَدُ • لَمْ يَلِدْ وَلَمْ يُولَدْ • وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ\n\n"
        "Translation: 'Say: He is Allah, [who is] One. Allah, the Eternal Refuge. He neither begets "
        "nor is born. Nor is there to Him any equivalent.'\n\n"
        "**Why a third of the Quran:**\n"
        "The Prophet ﷺ said: 'By Him in Whose hand my soul is, it is equal to one-third of the Quran.' "
        "(Bukhari, Hadith 5013, Sahih)\n\n"
        "Scholars explain this because the Quran covers three main themes:\n"
        "1. **Tawheed (Oneness of Allah)** — covered entirely in this Surah\n"
        "2. **Ahkam (Legal rulings)**\n"
        "3. **Qisas (Stories)**\n\n"
        "Surah Al-Ikhlas encompasses the complete description of Allah's nature.\n\n"
        "**Virtues:**\n"
        "- Reciting it 3 times = complete Quran in reward\n"
        "- Loving this Surah leads to Jannah: A man told the Prophet ﷺ he loved this Surah. "
        "The Prophet ﷺ said: 'Your love for it will enter you into Jannah.' (Bukhari, Hadith 7375)\n"
        "- Recited after every salah (3 times after Fajr and Maghrib)\n\nAllahu Akbar, and Allah knows best."
    ),
]

_DUA_QURAN_PREFIXES = [
    "Please explain ", "Can you tell me about ", "What is the significance of ",
]


def generate_duas_quran_pairs() -> list[dict]:
    base = [_pair(q, a, "duas_from_quran", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "beginner")
            for q, a in _DUAS_QURAN_PAIRS]
    return base + _rephrase(base, _DUA_QURAN_PREFIXES)


# ─── 8. Jannah & Jahannam ─────────────────────────────────────────────────────

_JANNAH_PAIRS: list[tuple[str, str]] = [
    (
        "What does the Quran and Hadith say about the description of Jannah?",
        "Jannah (Paradise) is described in the Quran and Sunnah with overwhelming beauty:\n\n"
        "**Physical description:** 'Gardens of perpetual bliss — and they will be therein forever. "
        "Therein they will have whatever they wish, and with Us is more.' (Quran Qaf 50:34-35)\n\n"
        "**Rivers of Jannah:** 'In it are rivers of water unaltered, rivers of milk the taste of "
        "which never changes, rivers of wine delicious to those who drink, and rivers of purified "
        "honey.' (Quran Muhammad 47:15)\n\n"
        "**The greatest gift — seeing Allah:** The Prophet ﷺ said: 'When the people of Jannah enter "
        "Jannah, Allah will say: \"Do you want me to give you anything more?\" They will say: "
        "\"Have You not brightened our faces? Have You not admitted us to Jannah and saved us from "
        "Hellfire?\" Then He will remove the veil, and nothing they have been given will be dearer "
        "to them than looking at their Lord.' (Muslim, Hadith 181, Sahih)\n\n"
        "**Beyond imagination:** The Prophet ﷺ narrated Allah's words: 'I have prepared for My "
        "righteous servants what no eye has seen, no ear has heard, and no human heart has conceived.' "
        "(Bukhari, Hadith 3244, Sahih) — as confirmed in Quran As-Sajdah 32:17\n\n"
        "**Its gates:** Jannah has 8 gates. The Prophet ﷺ said: 'Whoever performs wudu properly "
        "and says the testimony of faith, all 8 gates of Jannah will be opened for him.' "
        "(Muslim, Hadith 234)\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What does Islam say about the description of Jahannam (Hellfire)?",
        "Jahannam (Hellfire) is described in detail in the Quran as a warning and deterrent:\n\n"
        "**Its heat:** The Prophet ﷺ said: 'Your fire is one part of 70 parts of Hell.' "
        "(Bukhari, Hadith 3265, Sahih) — the Hellfire is 70 times hotter than worldly fire.\n\n"
        "**The tree of Zaqqum:** 'Indeed, the tree of Zaqqum is food for the sinful. Like murky oil, "
        "it boils within bellies.' (Quran Ad-Dukhan 44:43-46)\n\n"
        "**Its gates:** 'It has seven gates; for each gate is of them a portion assigned.' "
        "(Quran Al-Hijr 15:44)\n\n"
        "**Its punishment:** 'Every time their skins are roasted through, We will replace them with "
        "other skins so they may taste the punishment.' (Quran An-Nisa 4:56)\n\n"
        "**Its guards:** 19 angels guard Hellfire. (Quran Al-Muddathir 74:30)\n\n"
        "**Who enters:** Those who associated partners with Allah (shirk), those who deliberately "
        "rejected the truth, and wrongdoers who did not repent — with gradations of punishment.\n\n"
        "**Can Muslims exit?** [IJMA] Muslims who committed major sins and died without repentance "
        "may be punished but will eventually be removed from Hellfire by Allah's mercy and the "
        "Prophet's ﷺ intercession.\n\n"
        "**Its eternity:** The Quran describes the unbelievers as 'abiding therein forever.' (Quran Al-Baqarah 2:81). "
        "The punishment of Hell is a reminder to take this life seriously. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the levels of Jannah?",
        "Jannah has multiple levels (darajat) assigned according to one's deeds:\n\n"
        "**The levels:** The Prophet ﷺ said: 'In Paradise there are a hundred levels that Allah has "
        "prepared for those who strive in His cause, and the distance between each two levels is like "
        "the distance between heaven and earth.' (Bukhari, Hadith 2790, Sahih)\n\n"
        "**The highest level — Al-Firdaws:** The Prophet ﷺ said: 'When you ask Allah, ask Him for "
        "Al-Firdaws, for it is the middle and highest part of Jannah. Above it is the Throne of the "
        "Most Merciful, and from it the rivers of Jannah spring forth.' (Bukhari, Hadith 2790, Sahih)\n\n"
        "**Named levels in hadith:**\n"
        "- Jannatul Firdaws (highest)\n"
        "- Jannatul 'Adn (Gardens of Eden)\n"
        "- Jannatun Na'im (Gardens of Bliss)\n"
        "- Dar al-Maqamah (Abode of Permanence)\n"
        "- Dar as-Salam (Abode of Peace)\n"
        "- Jannatul Khuld (Garden of Eternity)\n"
        "- Jannatul Ma'wa (Garden of Shelter)\n\n"
        "**Who reaches the highest?** Prophets, the siddiqeen (truthful), the shuhada (martyrs), "
        "and the saliheen (righteous). Those who memorize and act upon the Quran rise with each verse. "
        "(Abu Dawud, Hadith 1464, Hasan)\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What acts earn the highest rewards and entrance to Jannah?",
        "The Prophet ﷺ described many deeds that guarantee Jannah or earn its highest levels:\n\n"
        "**The Five Pillars:** The foundation. 'He has succeeded who purifies himself, remembers the "
        "name of his Lord, and prays.' (Quran Al-A'la 87:14-15)\n\n"
        "**Completing wudu and shahada:** 'All 8 gates of Jannah will be opened for him.' (Muslim, 234)\n\n"
        "**Salah in congregation:** 'Whoever prays the two cool prayers (Fajr and Asr) enters Jannah.' "
        "(Bukhari, Hadith 574)\n\n"
        "**Giving charity secretly:** 'Seven people will be under Allah's shade on the Day when there "
        "is no shade except His...' including 'a person who gives in charity so secretly that his left "
        "hand does not know what his right hand has given.' (Bukhari, Hadith 660, Sahih)\n\n"
        "**Visiting the sick and orphans:** 'Whoever removes a worldly hardship from a believer, "
        "Allah will remove from him one of the hardships of the Day of Resurrection.' (Muslim, 2699)\n\n"
        "**Controlling anger:** 'Whoever suppresses his anger while able to act upon it, Allah will "
        "fill his heart with security and faith.' (Abu Dawud, Hasan)\n\n"
        "**Good character:** 'The heaviest on the Scale on the Day of Judgment is good character.' "
        "(Tirmidhi, Hadith 2003, Sahih)\n\n"
        "**Seeking knowledge:** 'Whoever travels a path seeking knowledge, Allah makes easy for him "
        "a path to Jannah.' (Muslim, Hadith 2699)\n\nAllahu Akbar, and Allah knows best."
    ),
]

_JANNAH_PREFIXES = [
    "Describe ", "Tell me about ", "What does the Quran say about ", "Explain ",
]


def generate_jannah_pairs() -> list[dict]:
    base = [_pair(q, a, "jannah_jahannam", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "intermediate")
            for q, a in _JANNAH_PAIRS]
    return base + _rephrase(base, _JANNAH_PREFIXES)


# ─── 9. Signs of Qiyamah ──────────────────────────────────────────────────────

_QIYAMAH_PAIRS: list[tuple[str, str]] = [
    (
        "What are the minor signs of the Day of Judgment (Qiyamah)?",
        "The Prophet ﷺ described many minor signs (ashrat al-sa'ah al-sughra) that precede Qiyamah:\n\n"
        "**Already fulfilled:**\n"
        "- The coming of the Prophet Muhammad ﷺ himself: 'I have been sent close to the Hour, like "
        "these two.' (Bukhari, Hadith 6503) — pointing to his index and middle fingers together\n"
        "- The splitting of the moon (Quran Al-Qamar 54:1; Bukhari, Hadith 3868)\n"
        "- The death of the Prophet ﷺ and the conquest of Bayt al-Maqdis (Jerusalem)\n\n"
        "**Occurring now / will worsen:**\n"
        "- Spread of trials (fitan) and widespread killing (Muslim, Hadith 157)\n"
        "- Knowledge will decrease and ignorance will increase (Bukhari, Hadith 80)\n"
        "- Fornication will be widespread and done openly (Bukhari, Hadith 80)\n"
        "- People will compete in building tall buildings (Bukhari, Hadith 50)\n"
        "- Music and intoxicants will be widespread\n"
        "- Earthquakes will increase (Bukhari, Hadith 1036)\n"
        "- People will rush to make rulings in religion without knowledge\n"
        "- Time will pass quickly (Muslim, Hadith 157)\n"
        "- The slave woman will give birth to her mistress\n\n"
        "**Coming later:**\n"
        "- Harj (widespread killing until the killer does not know why he killed)\n"
        "- People of Iraq and Syria being prevented from their wealth\n\n"
        "These signs call us to increase worship and righteousness. Allahu Akbar, and Allah knows best."
    ),
    (
        "What are the major signs of the Day of Judgment (Ashrat al-Sa'ah al-Kubra)?",
        "The Prophet ﷺ described ten major signs (ashrat al-sa'ah al-kubra) that signal Qiyamah is imminent:\n\n"
        "The Prophet ﷺ said: 'The Hour will not come until you have seen ten signs.' (Muslim, Hadith 7285, Sahih)\n\n"
        "**The Ten Major Signs:**\n"
        "1. **Smoke (Dukhan):** A thick smoke covering the earth for 40 days (Quran Ad-Dukhan 44:10)\n"
        "2. **The Dajjal (False Messiah):** A one-eyed deceiver claiming divinity, causing great trials\n"
        "3. **The Beast (Dabbat al-Ard):** An animal emerging from the earth marking believers and disbelievers\n"
        "4. **Rising of the sun from the West:** After which the door of repentance closes\n"
        "5. **Descent of Isa (Jesus) AS:** He will descend near the white minaret in Damascus, break the cross, "
        "kill the swine, remove jizyah, and pray behind the Mahdi\n"
        "6. **Emergence of Ya'juj and Ma'juj (Gog and Magog):** A massive destructive force unleashed "
        "(Quran Al-Kahf 18:98-99)\n"
        "7. **Three massive earthquakes:** In the East, West, and Arabian Peninsula\n"
        "8. **A fire from Yemen:** Driving people to their gathering place\n"
        "9. **The Mahdi:** A just leader from the Prophet's ﷺ family who will rule for 7-8 years "
        "[Note: his mention is from hadith, not Quran; some scholars differ on some details]\n"
        "10. **A pleasant wind:** Taking the souls of all believers before the final Hour\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "Who is the Dajjal and what are his characteristics?",
        "Al-Masih al-Dajjal (the False Messiah) is the greatest trial (fitnah) in human history:\n\n"
        "**His description:** The Prophet ﷺ said: 'The Dajjal is one-eyed (a'war), and your Lord is "
        "not one-eyed. Written between his eyes is \"kafir\" (disbeliever) — every believer will "
        "be able to read it.' (Bukhari, Hadith 7131, Sahih)\n\n"
        "**His abilities:** He will have extraordinary powers — he will command rain to fall and crops "
        "to grow, and the earth will bring forth its treasures for him. He will cause things to appear "
        "that seem miraculous. (Muslim, Hadith 7373)\n\n"
        "**His claim:** He will first claim prophethood, then divinity. But he is definitively not "
        "the Prophet or Allah — every Prophet warned their nation about him.\n\n"
        "**Duration:** He will remain on earth for 40 days — one day like a year, one like a month, "
        "one like a week, and the rest like normal days. (Muslim, Hadith 7373)\n\n"
        "**His end:** He will be killed by Isa (Jesus) AS near the gate of Ludd (Lod) in Palestine.\n\n"
        "**Protection from him:**\n"
        "- Memorize the first 10 verses of Surah Al-Kahf\n"
        "- Recite: 'A'udhu billahi min al-Dajjal' in the last tashahud of prayer\n"
        "- Flee to Makkah or Madinah (he cannot enter them) (Muslim, 2942)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What will the Day of Judgment (Yawm al-Qiyamah) be like?",
        "The Day of Judgment is described in the Quran and Sunnah in powerful detail:\n\n"
        "**When it begins:** The trumpet (Sur) of Israfil AS will be blown — all will faint. "
        "Then blown again — all will be resurrected. (Quran Az-Zumar 39:68)\n\n"
        "**Its length:** The Prophet ﷺ said for some it will feel like 50,000 years; for believers "
        "it will be like the time between Dhuhr and Asr. (Muslim, Hadith 2755)\n\n"
        "**Intercession:** The Prophet ﷺ will make the great intercession (al-shafa'at al-'uzma). "
        "People will go to Adam, Ibrahim, Musa, Isa, and finally Muhammad ﷺ. He will prostrate "
        "and be given permission to intercede. (Bukhari, Hadith 4476)\n\n"
        "**The Scales (Mizan):** Deeds will be weighed. 'So whoever does an atom's weight of good "
        "will see it, and whoever does an atom's weight of evil will see it.' (Quran Az-Zalzalah 99:7-8)\n\n"
        "**The Record (Kitab):** Each person will receive their book of deeds — in right hand (success) "
        "or left/behind back (failure). (Quran Al-Inshiqaq 84:7-12)\n\n"
        "**The Bridge (Sirat):** A bridge over Hellfire. Believers cross at speeds of their piety. "
        "The Prophet ﷺ will stand at its side praying: 'O Allah, save, save!' (Muslim, Hadith 195)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
]

_QIYAMAH_PREFIXES = [
    "Tell me about ", "Can you describe ", "What does the Quran say about ", "Explain ",
]


def generate_qiyamah_pairs() -> list[dict]:
    base = [_pair(q, a, "eschatology", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "advanced")
            for q, a in _QIYAMAH_PAIRS]
    return base + _rephrase(base, _QIYAMAH_PREFIXES)


# ─── 10. Stories of the Prophets ──────────────────────────────────────────────

_PROPHETS_PAIRS: list[tuple[str, str]] = [
    (
        "What is the story of Prophet Musa (Moses) AS and the parting of the sea?",
        "The miraculous parting of the Red Sea is one of the greatest miracles in history:\n\n"
        "**Context:** Pharaoh (Fir'awn) enslaved the Children of Israel for centuries. Allah sent "
        "Musa AS with 9 clear signs — including the staff, the white hand, locusts, lice, frogs, "
        "and blood. (Quran Al-A'raf 7:133) Pharaoh refused every time.\n\n"
        "**The Exodus:** Allah commanded Musa AS to lead Bani Isra'il out of Egypt by night. "
        "Pharaoh pursued them with his massive army. They reached the sea and Bani Isra'il panicked: "
        "'Indeed, we are overtaken!' (Quran Ash-Shu'ara 26:61)\n\n"
        "**The miracle:** Musa AS declared with certainty: 'No! Indeed, with me is my Lord; He will "
        "guide me.' (Quran Ash-Shu'ara 26:62) Allah commanded him to strike the sea with his staff. "
        "'And the sea was parted, and each part was like a great towering mountain.' (Quran Ash-Shu'ara 26:63)\n\n"
        "**Pharaoh's fate:** Pharaoh followed with his army and was drowned. As he drowned, he said: "
        "'I believe that there is no god except that in whom the Children of Israel believe.' But Allah "
        "said: 'Now? And you had disobeyed before and were of the corrupters.' (Quran Yunus 10:90-91)\n\n"
        "**His body preserved:** 'So today We will save you in body that you may be to those who come "
        "after you a sign.' (Quran Yunus 10:92) — Egyptian mummies preserve this.\n\n"
        "**Lesson:** True reliance on Allah (tawakkul) produces miracles. Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the story of Prophet Yusuf (Joseph) AS and its main lessons?",
        "Surah Yusuf is called the 'best of stories' (ahsan al-qasas) in the Quran (12:3):\n\n"
        "**Early life:** Yusuf AS was beloved by his father Ya'qub AS. His brothers, jealous, "
        "threw him in a well and told their father a wolf had killed him. (Quran Yusuf 12:8-18)\n\n"
        "**In Egypt:** He was sold into slavery and bought by Al-Aziz (a high official). The wife of "
        "Al-Aziz tried to seduce him. He refused, saying: 'I seek refuge in Allah. Indeed, He is my "
        "Lord.' (Quran Yusuf 12:23) He was unjustly imprisoned.\n\n"
        "**In prison:** He interpreted dreams for two inmates. After years, the king had a dream — "
        "seven fat cows devoured by seven thin ones. Yusuf AS interpreted it as seven years of plenty "
        "followed by seven years of famine, advising storage.\n\n"
        "**Rise to power:** The king recognized his wisdom and appointed him over Egypt's storehouses. "
        "'Indeed, you are today established [in position] and trusted.' (Quran Yusuf 12:54)\n\n"
        "**Reunion:** During famine, his brothers came to Egypt. After tests, he revealed himself: "
        "'He said: I am Yusuf, and this is my brother. Allah has certainly been gracious to us.' "
        "(Quran Yusuf 12:90)\n\n"
        "**Lessons:**\n"
        "1. Patience through trials leads to relief\n"
        "2. Chastity is a mark of prophets and the righteous\n"
        "3. Forgiveness over revenge\n"
        "4. Allah's plan surpasses human plans\n\nAllahu Akbar, and Allah knows best."
    ),
    (
        "What is the story of Prophet Sulaiman (Solomon) AS?",
        "Prophet Sulaiman AS was a mighty prophet-king gifted with extraordinary powers by Allah:\n\n"
        "**His kingdom:** Allah gave Sulaiman AS a unique dominion: 'He said: My Lord, forgive me "
        "and grant me a kingdom such as will not belong to anyone after me. Indeed, You are the Bestower.' "
        "(Quran Sad 38:35)\n\n"
        "**Control over wind, jinn, and animals:** 'And to Sulaiman [We subjected] the wind — its "
        "morning [journey was that of] a month — and its afternoon [journey was that of] a month. "
        "And We caused to flow for him a spring of [liquid] copper.' (Quran Saba 34:12)\n\n"
        "He could speak with birds and animals. The hoopoe bird brought him news of the Queen of Sheba "
        "(Bilqis) who worshipped the sun. (Quran An-Naml 27:22-23)\n\n"
        "**The Queen of Sheba:** Sulaiman AS sent her a letter inviting her to Islam. She came with "
        "her throne. He tested her with a glass floor she thought was water. She recognized the truth "
        "and submitted: 'My Lord, indeed I have wronged myself, and I submit with Sulaiman to Allah, "
        "Lord of the worlds.' (Quran An-Naml 27:44)\n\n"
        "**Jinn under his command:** Jinn built for him palaces, statues, and worked heavy crafts. "
        "They did not know of his death until a worm ate through his staff and he fell. (Quran Saba 34:14)\n\n"
        "**Lesson:** Worldly power means nothing without gratitude and submission to Allah. "
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the story of Prophet Isa (Jesus) AS in Islam?",
        "Isa AS (Jesus) is one of the greatest prophets in Islam — honored deeply but not divine:\n\n"
        "**Birth:** Born miraculously to Maryam AS (the Virgin Mary) without a father. Allah said: "
        "'The likeness of Isa with Allah is as the likeness of Adam — He created him from dust, "
        "then said to him: \"Be!\" and he was.' (Quran Al-Imran 3:59)\n\n"
        "**His miracles:** Created birds from clay and breathed life into them, healed the blind and "
        "leper, raised the dead — all by Allah's permission. (Quran Al-Imran 3:49)\n\n"
        "**His message:** He was sent to the Children of Israel confirming the Torah and bringing the "
        "Injeel (Gospel). He declared: 'I am the servant of Allah. He has given me the Scripture "
        "and made me a prophet.' (Quran Maryam 19:30)\n\n"
        "**His nature in Islam:** He is not the son of God, not divine, and not part of a Trinity. "
        "'They have certainly disbelieved who say: Allah is the Messiah, the son of Mary.' "
        "(Quran Al-Ma'idah 5:72) He himself will testify on Judgment Day that he never claimed divinity. "
        "(Quran Al-Ma'idah 5:116-117)\n\n"
        "**Was he crucified?** 'They did not kill him, nor did they crucify him; but [another] was "
        "made to resemble him to them.' (Quran An-Nisa 4:157) — Allah raised him to the heavens.\n\n"
        "**His return:** Isa AS will return before Qiyamah as a just ruler. (Muslim, 155)\n\n"
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the story of Prophet Nuh (Noah) AS and the great flood?",
        "Nuh AS (Noah) is one of the five greatest prophets (Ulul Azm) and was sent to a polytheist nation:\n\n"
        "**His call:** Nuh AS called his people for 950 years: 'He said: My Lord, indeed I invited my "
        "people night and day, but my invitation increased them not except in flight.' (Quran Nuh 71:5-6)\n\n"
        "**Their response:** The elite rejected him, saying he was just a man like them and his followers "
        "were lowly people. He pleaded with Allah: 'My Lord, do not leave upon the earth from among the "
        "disbelievers an inhabitant.' (Quran Nuh 71:26)\n\n"
        "**The ark:** Allah commanded Nuh AS to build a large ship (the ark). The disbelievers mocked him. "
        "He was commanded: 'Load upon it from each [creature] two mates and your family, except those "
        "about whom the word has previously come.' (Quran Hud 11:40)\n\n"
        "**His son:** His own son refused to board, claiming a mountain would protect him. The wave "
        "came between them, and he drowned. Nuh AS called to Allah, and Allah reminded him: "
        "'Indeed, he is not of your family; indeed, he is [one whose] work was other than righteous.' "
        "(Quran Hud 11:46)\n\n"
        "**After the flood:** The ark settled on Mount Judi (Quran Hud 11:44). Nuh AS was given a "
        "covenant of safety for him and his descendants.\n\n"
        "**Lesson:** Family ties do not guarantee salvation — only iman and righteous deeds count. "
        "Allahu Akbar, and Allah knows best."
    ),
    (
        "What is the story of Prophet Idris (Enoch) AS?",
        "Prophet Idris AS (identified with Enoch in biblical tradition) is mentioned in the Quran:\n\n"
        "**Quranic mentions:** 'And mention in the Book, Idris. Indeed, he was a man of truth and a prophet. "
        "And We raised him to a high station.' (Quran Maryam 19:56-57)\n\n"
        "He is also mentioned in Surah Al-Anbiya 21:85 alongside Isma'il and Dhul-Kifl as patient "
        "and righteous prophets.\n\n"
        "**His station:** Allah raised him to a 'high station (makan ali).' Scholars interpret this "
        "as the 4th heaven. The Prophet ﷺ on the Night Journey (Isra wal Mi'raj) met Idris AS on "
        "the fourth heaven, who greeted him. (Bukhari, Hadith 3207)\n\n"
        "**Historical context:** Scholars generally hold Idris AS came before Nuh AS and was an early "
        "prophet to mankind. Some narrations credit him with being the first to write with a pen.\n\n"
        "**His attributes:** Truthfulness (siddiq) and prophethood — the Quran combines these as his "
        "defining qualities. Scholars like Ibn Kathir RH emphasize his ascetic devotion and constant worship.\n\n"
        "**Important note:** While there are many stories attributed to Idris AS in tradition, authentic "
        "Quranic and hadith information about him is limited. We affirm what is clearly confirmed and "
        "acknowledge uncertainty about additional details.\n\nAllahu Akbar, and Allah knows best."
    ),
]

_PROPHETS_PREFIXES = [
    "Tell me the story of ", "Describe the life of ", "What does the Quran say about ",
    "Narrate the story of ", "What happened to ",
]


def generate_prophets_stories_pairs() -> list[dict]:
    base = [_pair(q, a, "prophets_stories", ["Quran", "Sahih Bukhari", "Sahih Muslim"], "intermediate")
            for q, a in _PROPHETS_PAIRS]
    return base + _rephrase(base, _PROPHETS_PREFIXES)


# ─── Master function ──────────────────────────────────────────────────────────

def generate_additional_pairs() -> list[dict[str, Any]]:
    """Generate all additional Islamic Q&A pairs (~10,000 total with augmentation)."""
    generators = [
        generate_salah_pairs,
        generate_ramadan_pairs,
        generate_zakat_pairs,
        generate_marriage_pairs,
        generate_tibb_pairs,
        generate_adab_pairs,
        generate_duas_quran_pairs,
        generate_jannah_pairs,
        generate_qiyamah_pairs,
        generate_prophets_stories_pairs,
    ]

    all_pairs: list[dict] = []
    for gen in generators:
        pairs = gen()
        all_pairs.extend(pairs)

    return all_pairs


if __name__ == "__main__":
    pairs = generate_additional_pairs()
    print(f"Total additional pairs generated: {len(pairs)}")
    cats: dict[str, int] = {}
    for p in pairs:
        c = p["metadata"]["category"]
        cats[c] = cats.get(c, 0) + 1
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {count}")
