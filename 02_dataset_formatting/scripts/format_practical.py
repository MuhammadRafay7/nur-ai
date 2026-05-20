"""
format_practical.py
-------------------
Generates Q&A training pairs for practical how-to / step-by-step Islamic questions.

Topics covered:
  1. Wudu (Ablution)
  2. Ghusl (Full Bath)
  3. Tayammum (Dry Ablution)
  4. Salah (Prayer) — step by step from Takbir to Salam
  5. Fasting (Sawm / Ramadan)
  6. Zakat — who pays, nisab, how to calculate, recipients
  7. Hajj — arkan in order with descriptions
  8. Umrah — arkan: Ihram, Tawaf, Sa'i, Halq/Taqsir

Data sources:
  - 01_data_collection/raw/knowledge_bases/taharah_fiqh.json
  - 01_data_collection/raw/knowledge_bases/ibadah_salah_zakat_fasting_hajj.json
"""

from __future__ import annotations

import json
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
KB_DIR = (
    Path(__file__).parent.parent.parent
    / "01_data_collection"
    / "raw"
    / "knowledge_bases"
)

TAHARAH_FILE = KB_DIR / "taharah_fiqh.json"
IBADAH_FILE  = KB_DIR / "ibadah_salah_zakat_fasting_hajj.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _make_pair(question: str, answer: str, topic: str) -> dict:
    return {
        "instruction": question,
        "input":    "",
        "output":    answer,
        "metadata": {
            "category": "practical",
            "topic": topic,
        },
    }


def _shuffle_questions(templates: list[str], rng: random.Random) -> list[str]:
    """Return a shuffled copy of the question list."""
    out = templates[:]
    rng.shuffle(out)
    return out


# ---------------------------------------------------------------------------
# Answer builders — one per topic
# ---------------------------------------------------------------------------

def _build_wudu_answer(data: dict) -> str:
    wudu = data["wudu"]

    fard_lines = "\n".join(
        f"{i+1}. {item['act']} — {item['detail']}"
        for i, item in enumerate(wudu["fard_acts"])
    )

    sunnah_lines = "\n".join(f"• {s}" for s in wudu["sunnahs"])

    nullifier_lines = "\n".join(
        f"• {n['nullifier']}" for n in wudu["nullifiers"]
    )

    return (
        "**How to Perform Wudu (Ablution) — Step by Step**\n\n"
        "**Ruling:** Fard — required for Salah, touching the Mushaf, and Tawaf. "
        "Obligatory upon every Muslim who is in a state of minor ritual impurity (hadath asghar).\n\n"
        "**Prerequisites:**\n"
        "• Intention (Niyyah) — made in the heart before beginning\n"
        "• Access to pure water (ma' tahir)\n"
        "• Removal of anything blocking water from reaching the skin "
        "(e.g. nail polish, thick grease, wax)\n\n"
        "**Step-by-Step Method (Fard Acts):**\n"
        f"{fard_lines}\n\n"
        "**Sunnah Enhancements (Recommended Acts):**\n"
        f"{sunnah_lines}\n\n"
        "**What Invalidates Wudu:**\n"
        f"{nullifier_lines}\n\n"
        "**Supporting Evidence:**\n"
        "Allah says: *'O you who believe! When you rise for prayer, wash your faces "
        "and your hands up to the elbows, wipe your heads, and wash your feet to the ankles.'* "
        "(Quran 5:6)\n"
        "The Prophet ﷺ said: *'Woe to the heels from Hellfire!'* (Sahih Muslim 241) — "
        "warning those who miss the back of their heels.\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Missing the back of the heels when washing the feet\n"
        "• Not including the elbows when washing the arms\n"
        "• Breaking the sequence (tartib) — face must come before arms, head before feet\n"
        "• Allowing a long gap between each limb (breaks continuity / muwalat)\n"
        "• Wearing nail polish or rings that prevent water reaching the skin\n"
        "• Washing each part only once (sunnah is three times each)"
    )


def _build_ghusl_answer(data: dict) -> str:
    ghusl = data["ghusl"]

    causes_lines = "\n".join(
        f"• {c['cause']}" for c in ghusl["obligatory_causes"]
    )

    fard_lines = "\n".join(
        f"• {act}" for act in ghusl["fard_acts"]
    )

    steps = "\n".join(ghusl["sunnah_method"])

    return (
        "**How to Perform Ghusl (Full Ritual Bath) — Step by Step**\n\n"
        "**Ruling:** Fard (obligatory) when triggered by any of the causes below. "
        "Obligatory upon every Muslim who is in a state of major ritual impurity (janabah).\n\n"
        "**When Ghusl Becomes Obligatory:**\n"
        f"{causes_lines}\n\n"
        "**Prerequisites (Minimum Fard Acts — Ghusl is Valid With These Alone):**\n"
        f"{fard_lines}\n\n"
        "**Step-by-Step Sunnah Method (Complete and Recommended):**\n"
        f"{steps}\n\n"
        "**What Invalidates Ghusl / Makes It Insufficient:**\n"
        "• Any area of the body not reached by water (even a fingernail-sized patch)\n"
        "• Nail polish, wax, or thick substances blocking water from the skin\n"
        "• Not removing braids if water cannot penetrate to the roots (women: roots must be wet)\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said: *'When a man sits between the four parts of a woman and "
        "the two circumcised parts meet, ghusl becomes obligatory.'* (Sahih Bukhari 291)\n"
        "Allah says: *'If you are in a state of janabah, purify yourselves.'* (Quran 5:6)\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Forgetting to wash inside the navel\n"
        "• Not ensuring water reaches under the armpits and between the buttocks\n"
        "• Women with braided hair: the roots must be wet, but undoing the braid is not required "
        "if water reaches the roots\n"
        "• Thinking wudu must be performed separately after ghusl — ghusl includes wudu "
        "(though some scholars recommend performing wudu first as in the sunnah method)"
    )


def _build_tayammum_answer(data: dict) -> str:
    tayammum = data["tayammum"]

    conditions_lines = "\n".join(f"• {c}" for c in tayammum["conditions"])
    steps = "\n".join(tayammum["method"])
    nullifiers = "\n".join(f"• {n}" for n in tayammum["nullifiers"])

    return (
        "**How to Perform Tayammum (Dry Ablution) — Step by Step**\n\n"
        "**Ruling:** A valid substitute for wudu and ghusl when water cannot be used. "
        "It is a concession (rukhsah) from Allah for situations where water is unavailable or harmful.\n\n"
        "**When Tayammum Is Permitted:**\n"
        f"{conditions_lines}\n\n"
        "**Prerequisites:**\n"
        "• Pure earth, dust, sand, or any surface of the ground (stone, clay, etc.)\n"
        "• Intention (Niyyah) in the heart\n\n"
        "**Step-by-Step Method:**\n"
        f"{steps}\n\n"
        "**What Invalidates Tayammum:**\n"
        f"{nullifiers}\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said: *'The (clean) earth has been made a place of prostration "
        "and a means of purification for me.'* (Sahih Bukhari 338)\n"
        "Allah says: *'...and if you find no water, then seek clean earth and wipe your "
        "faces and hands with it.'* (Quran 4:43)\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Striking the earth more than once (one strike for both face and hands is sufficient)\n"
        "• Using a surface that is not pure earth/dust (e.g. a painted wall may not qualify)\n"
        "• Performing tayammum when water is actually accessible nearby\n"
        "• Not making a fresh tayammum when the reason for the original one no longer applies "
        "(e.g. water becomes available)"
    )


def _build_salah_answer(data: dict) -> str:
    salah = data["salah"]

    conditions = "\n".join(f"• {c}" for c in salah["conditions_for_validity"])
    pillars     = "\n".join(
        f"{i+1}. {p}" for i, p in enumerate(salah["pillars_arkan"])
    )
    invalidators = "\n".join(f"• {inv}" for inv in salah["invalidators"])

    return (
        "**How to Perform Salah (Prayer) — Step by Step**\n\n"
        "**Ruling:** Fard Ayn (individually obligatory) on every Muslim, five times daily. "
        "Quran 2:43, 4:103.\n\n"
        "**Prerequisites (Conditions for Validity):**\n"
        f"{conditions}\n\n"
        "**Step-by-Step Method — The Pillars (Arkan) of Salah:**\n"
        "1. **Opening Takbir** — Raise both hands to the earlobes and say *'Allahu Akbar'*. "
        "This marks the entry into prayer. (Bukhari 756)\n"
        "2. **Standing (Qiyam)** — Stand upright facing the Qiblah. "
        "Those unable to stand may sit or lie down.\n"
        "3. **Recite Al-Fatiha** — Recite Surah Al-Fatiha in every rak'ah. "
        "Then recite any additional surah in the first two rak'ahs. (Bukhari 756, Muslim 394)\n"
        "4. **Ruku' (Bowing)** — Say *'Allahu Akbar'*, bow with the back flat, "
        "hands on knees. Recite *'Subhana Rabbiyal-Azim'* (at least once). "
        "Maintain stillness (tuma'ninah).\n"
        "5. **Rising from Ruku'** — Return to standing, saying "
        "*'Sami'Allahu liman hamidah'* (Imam/alone), then *'Rabbana lakal-hamd'*.\n"
        "6. **First Sajdah (Prostration)** — Say *'Allahu Akbar'*, go down to the ground "
        "on seven bones: forehead + nose, two palms, two knees, tips of both feet. "
        "Recite *'Subhana Rabbiyal-A'la'*. Maintain stillness.\n"
        "7. **Sitting between the two Sajdahs** — Rise saying *'Allahu Akbar'*, sit briefly, "
        "say *'Rabbighfir li'*, then go down for the second sajdah.\n"
        "8. **Second Sajdah** — Same as the first. This completes one rak'ah.\n"
        "9. **Tashahhud** — After the 2nd rak'ah (and final rak'ah): sit and recite the "
        "Tashahhud: *'At-tahiyyatu lillahi was-salawatu wat-tayyibat...'*. "
        "In the final sitting, add the Salawat Ibrahimiyyah.\n"
        "10. **Final Tasleem** — Turn the head to the right saying "
        "*'Assalamu Alaykum wa Rahmatullah'*, then to the left. "
        "This exits the prayer.\n\n"
        "**What Invalidates Salah:**\n"
        f"{invalidators}\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said: *'Pray as you have seen me pray.'* (Sahih Bukhari 631)\n"
        "He also said about one who prayed quickly without stillness: "
        "*'Go back and pray, for you have not prayed.'* (Bukhari 793) — emphasising tuma'ninah.\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Not achieving stillness (tuma'ninah) in ruku' and sujud — this is a pillar\n"
        "• Lifting the feet from the ground during sujud\n"
        "• Reciting Al-Fatiha too quickly without meaning\n"
        "• Not fully completing the rising from ruku' before going down to sujud\n"
        "• Speaking during the prayer (invalidates it unless by mistake)"
    )


def _build_fasting_answer(data: dict) -> str:
    fasting = data["fasting"]

    conditions = "\n".join(f"• {c}" for c in fasting["conditions_for_obligation"])
    pillars     = "\n".join(f"• {p}" for p in fasting["pillars"])

    invalidators_kaffara = "\n".join(
        f"• {opt}" for opt in fasting["invalidators_requiring_makeup_and_kaffarah"]["kaffarah_options"]
    )
    invalidators_makeup  = "\n".join(
        f"• {inv}" for inv in fasting["invalidators_requiring_makeup_only"]
    )
    doesnt_break = "\n".join(f"• {d}" for d in fasting["does_not_break_fast"])

    return (
        "**How to Fast in Ramadan (Sawm) — Step by Step**\n\n"
        "**Ruling:** Fard Ayn (obligatory) on every adult Muslim during the month of Ramadan. "
        "Quran 2:183-185.\n\n"
        "**Who Must Fast:**\n"
        f"{conditions}\n\n"
        "**Prerequisites:**\n"
        "• Confirmed start of Ramadan (moon sighting or reliable announcement)\n"
        "• Be in a state of ritual purity by the time of Fajr (Suhoor before Fajr is recommended)\n\n"
        "**Step-by-Step Method:**\n"
        "1. **Make your intention (Niyyah)** — The night before each fasting day "
        "(before Fajr). For Ramadan: the intention for the entire month is accepted "
        "by Hanafi scholars; Shafi'i require renewing it each night.\n"
        "2. **Have Suhoor (pre-dawn meal)** — Eat and drink before Fajr (true dawn). "
        "Suhoor is a sunnah: *'Take Suhoor, for in Suhoor there is blessing.'* "
        "(Bukhari 1923)\n"
        "3. **Cease all eating, drinking, and intercourse at Fajr** — From the moment "
        "true dawn (Fajr Sadiq) appears until sunset. (Quran 2:187)\n"
        "4. **Maintain the fast throughout the day** — Refrain from all invalidators, "
        "guard the tongue and conduct: *'Whoever does not give up lying and acting "
        "upon lies, Allah has no need of his giving up food and drink.'* (Bukhari 1903)\n"
        "5. **Break the fast at sunset (Iftar)** — Hasten to break it: "
        "*'People will remain in good as long as they hasten in breaking the fast.'* "
        "(Bukhari 1957). Recommended to break with dates and water following the Prophet's sunnah.\n"
        "6. **Make up missed days** — If a day is missed for a valid reason "
        "(illness, travel, menstruation), it must be made up before the next Ramadan.\n\n"
        "**Pillars of Fasting:**\n"
        f"{pillars}\n\n"
        "**What Breaks the Fast (Requires Makeup Only):**\n"
        f"{invalidators_makeup}\n\n"
        "**What Breaks the Fast (Requires Makeup + Kaffarah):**\n"
        "• Intentional sexual intercourse during the daytime of Ramadan.\n"
        "Kaffarah options (in order):\n"
        f"{invalidators_kaffara}\n\n"
        "**What Does NOT Break the Fast:**\n"
        f"{doesnt_break}\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said: *'Whoever fasts Ramadan out of faith and seeking reward, "
        "his past sins will be forgiven.'* (Bukhari 38)\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Forgetting to make the intention the night before (especially for Shafi'i school)\n"
        "• Assuming an injection automatically breaks the fast — "
        "non-nutritive injections do not break it (majority of contemporary scholars)\n"
        "• Continuing to eat after the Fajr adhan if it is the correct time\n"
        "• Delaying Iftar beyond sunset unnecessarily"
    )


def _build_zakat_answer(data: dict) -> str:
    zakat = data["zakat"]

    conditions  = "\n".join(f"• {c}" for c in zakat["conditions"])
    categories  = "\n".join(
        f"• **{cat['name']}** — {cat['definition']}"
        for cat in zakat["eight_categories_of_recipients"]["categories"]
    )
    zakatable   = "\n".join(f"• {w}" for w in zakat["zakatable_wealth"])
    nisab       = zakat["nisab_thresholds"]

    return (
        "**How to Pay Zakat — Complete Guide**\n\n"
        "**Ruling:** Fard (3rd Pillar of Islam) on every Muslim who meets the conditions. "
        "Quran 2:43, 9:60.\n\n"
        "**Who Must Pay Zakat:**\n"
        f"{conditions}\n\n"
        "**Prerequisites:**\n"
        "• Wealth has reached the nisab threshold\n"
        "• One full lunar year (hawl) has passed while holding that wealth\n"
        "• Sincere intention (Niyyah) when distributing\n\n"
        "**What Wealth is Zakatable:**\n"
        f"{zakatable}\n\n"
        "**Step-by-Step: How to Calculate and Pay Zakat:**\n"
        "1. **Determine your zakatable assets** — Add up all gold, silver, cash savings, "
        "business inventory, and freely grazing livestock.\n"
        "2. **Check if you have held nisab for one full lunar year (hawl)** — "
        "The wealth must have been at or above nisab for an entire lunar year.\n"
        "3. **Nisab threshold:**\n"
        f"   • Gold: {nisab['gold']['amount']} — rate: {nisab['gold']['rate']}\n"
        f"   • Silver: {nisab['silver']['amount']} — rate: {nisab['silver']['rate']}\n"
        "   • For cash savings: use the gold or silver nisab — scholars recommend "
        "whichever benefits the poor more (usually silver nisab = more inclusive).\n"
        "4. **Calculate the amount due** — Multiply total zakatable wealth by 2.5% "
        "(i.e. 1/40th).\n"
        "   Example: If you have $10,000 in savings above nisab, "
        "zakat = $10,000 × 2.5% = $250.\n"
        "5. **Distribute to the eight eligible categories** (Quran 9:60):\n"
        f"{categories}\n\n"
        "**Important Notes:**\n"
        "• Zakat cannot be given to one's direct dependants (parents, children, spouse)\n"
        "• Zakat cannot be given to Banu Hashim (the Prophet's ﷺ family) — they receive "
        "from khums\n"
        "• Zakat al-Fitr: Also obligatory before Eid al-Fitr — one sa' "
        f"({zakat['zakat_al_fitr']['amount']}) of staple food per household member\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said to Mu'adh ibn Jabal: "
        "*'Inform them that Allah has made zakat obligatory on them, taken from their "
        "wealthy and given to their poor.'* (Bukhari 1395)\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Counting the value of one's house, car, or personal items — these are not zakatable\n"
        "• Forgetting to include business inventory (this is commonly missed)\n"
        "• Not restarting the hawl (one-year countdown) when wealth drops below nisab mid-year\n"
        "• Giving zakat to ineligible recipients (e.g. building a mosque is not zakat-eligible "
        "by majority opinion)"
    )


def _build_hajj_answer(data: dict) -> str:
    hajj = data["hajj"]

    conditions   = "\n".join(f"• {c}" for c in hajj["conditions_for_obligation"])
    pillars      = "\n".join(
        f"{i+1}. {p}" for i, p in enumerate(hajj["pillars_arkan_of_hajj"])
    )
    steps        = "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(hajj["steps_in_order"])
    )
    prohibitions = "\n".join(f"• {p}" for p in hajj["ihram_prohibitions"])

    return (
        "**Hajj — The Complete Step-by-Step Guide**\n\n"
        "**Ruling:** Fard (5th Pillar of Islam) — once in a lifetime for those with means. "
        "Quran 3:97.\n\n"
        "**Who Must Perform Hajj:**\n"
        f"{conditions}\n\n"
        "**Prerequisites:**\n"
        "• Enter Ihram (ritual state of consecration) at the Miqat before entering Makkah\n"
        "• Intention for Hajj in the heart\n"
        "• Choose type: Tamattu' (recommended for non-Makkans), Ifrad, or Qiran\n\n"
        "**The Four Pillars (Arkan) of Hajj — These Cannot Be Omitted:**\n"
        f"{pillars}\n\n"
        "**Step-by-Step Sequence of Hajj:**\n"
        f"{steps}\n\n"
        "**Prohibitions While in Ihram:**\n"
        f"{prohibitions}\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said: *'Hajj is Arafah.'* (Tirmidhi 889 — Sahih) — "
        "showing that standing at Arafah is the central pillar.\n"
        "He also said: *'Whoever performs Hajj and does not commit any obscenity "
        "or transgression will return as pure as the day his mother bore him.'* "
        "(Bukhari 1521)\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Leaving Arafah before sunset — this would invalidate Hajj\n"
        "• Missing the night at Muzdalifah without a valid excuse\n"
        "• Men wearing stitched clothing while in Ihram\n"
        "• Forgetting Tawaf al-Wada' (Farewell Tawaf) before leaving Makkah — "
        "this is wajib (Bukhari 1755)\n"
        "• Rushing Tawaf al-Ifadah before returning from Arafah on 10 Dhul Hijjah"
    )


def _build_umrah_answer(data: dict) -> str:
    umrah = data["hajj"]["umrah"]

    pillars = "\n".join(
        f"{i+1}. {p}" for i, p in enumerate(umrah["pillars"])
    )

    return (
        "**Umrah (Minor Pilgrimage) — Step-by-Step Guide**\n\n"
        "**Ruling:** Fard once in a lifetime (Shafi'i, Hanbali) or Sunnah Mu'akkadah "
        "(Hanafi, Maliki). It can be performed at any time of the year except the "
        "days of Hajj.\n\n"
        "**Prerequisites:**\n"
        "• Be in a state of ritual purity (wudu)\n"
        "• Enter Ihram at or before the Miqat — failure to do so requires a dam (sacrifice)\n\n"
        "**Step-by-Step Method:**\n"
        "1. **Enter Ihram at the Miqat** — Make intention for Umrah, say *'Labbayk Allahumma "
        "Umrah'*, recite the Talbiyah: *'Labbayk Allahumma labbayk...'* Men: wear two "
        "unstitched white sheets (izar and rida'). Women: normal modest clothing. "
        "Avoid all ihram prohibitions from this point.\n"
        "2. **Arrive at Masjid al-Haram and begin Tawaf** — Perform 7 complete circuits "
        "around the Ka'bah in a counter-clockwise direction starting and ending at the "
        "Black Stone (Hajar al-Aswad). Men: perform idtiba' (right shoulder uncovered) "
        "and raml (brisk walk) in the first 3 rounds.\n"
        "3. **Pray 2 rak'ahs behind Maqam Ibrahim** — After Tawaf, pray two rak'ahs, "
        "reciting Surah Al-Kafirun in the first and Surah Al-Ikhlas in the second.\n"
        "4. **Drink Zamzam water** — It is sunnah to drink while facing the Ka'bah "
        "and making dua.\n"
        "5. **Perform Sa'i between Safa and Marwah** — Walk 7 times between the two hills "
        "(Safa to Marwah = 1, Marwah to Safa = 2, and so on until ending at Marwah on "
        "the 7th). Recite supplications. Men: jog between the two green markers.\n"
        "6. **Cut or shave the hair (Halq or Taqsir)** — Men: shave the entire head "
        "(halq, preferred) or shorten it significantly (taqsir). Women: cut a fingertip's "
        "length from the hair. This ends the state of Ihram.\n\n"
        "**The Four Pillars of Umrah:**\n"
        f"{pillars}\n\n"
        "**What Invalidates / Harms Umrah:**\n"
        "• Intentional intercourse after entering Ihram — invalidates the Umrah; "
        "must complete it and make it up\n"
        "• Leaving Ihram deliberately before completing all pillars\n"
        "• Performing Tawaf without wudu\n\n"
        "**Supporting Evidence:**\n"
        "The Prophet ﷺ said: *'From one Umrah to the next is an expiation for "
        "whatever sins come in between.'* (Bukhari 1773)\n\n"
        "**Common Mistakes to Avoid:**\n"
        "• Starting Tawaf before the Ihram (or not being in wudu for Tawaf)\n"
        "• Counting Sa'i incorrectly — remember: it ends on the 7th crossing at Marwah\n"
        "• Men not performing raml (brisk walk) in the first three rounds of Tawaf\n"
        "• Only cutting a few strands of hair — men should shorten all of it "
        "significantly (minimum: shortening all around the head)"
    )


# ---------------------------------------------------------------------------
# Question templates per topic
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, list[str]] = {
    "wudu": [
        "How do I perform Wudu (ablution)?",
        "Step by step guide to Wudu.",
        "How to do Wudu correctly in Islam?",
        "What are the steps of Wudu?",
        "Teach me how to perform Wudu.",
        "What is the correct method of Wudu?",
        "How should a Muslim perform Wudu?",
    ],
    "ghusl": [
        "How do I perform Ghusl (ritual bath)?",
        "Step by step guide to Ghusl.",
        "How to do Ghusl correctly in Islam?",
        "What are the steps of Ghusl?",
        "Teach me how to perform Ghusl.",
        "What is the correct method of Ghusl?",
        "How should a Muslim perform the full ritual bath (Ghusl)?",
    ],
    "tayammum": [
        "How do I perform Tayammum (dry ablution)?",
        "Step by step guide to Tayammum.",
        "How to do Tayammum correctly in Islam?",
        "What are the steps of Tayammum?",
        "Teach me how to perform Tayammum.",
        "What is the correct method of Tayammum?",
        "How should a Muslim perform Tayammum when there is no water?",
    ],
    "salah": [
        "How do I perform Salah (prayer)?",
        "Step by step guide to Salah.",
        "How to pray correctly in Islam?",
        "What are the steps of Salah from Takbir to Salam?",
        "Teach me how to perform the Islamic prayer.",
        "What is the correct method of Salah?",
        "How should a Muslim perform Salah?",
    ],
    "fasting": [
        "How do I fast in Ramadan?",
        "Step by step guide to fasting in Islam.",
        "How to fast correctly in Ramadan?",
        "What are the steps of fasting in Ramadan?",
        "Teach me how to fast during Ramadan.",
        "What is the correct method of fasting in Islam?",
        "How should a Muslim observe the Ramadan fast?",
    ],
    "zakat": [
        "How do I pay Zakat?",
        "Step by step guide to paying Zakat.",
        "How to calculate and pay Zakat correctly?",
        "What are the steps of paying Zakat?",
        "Teach me how to calculate my Zakat.",
        "What is the correct method of paying Zakat?",
        "How should a Muslim calculate and distribute Zakat?",
    ],
    "hajj": [
        "How do I perform Hajj?",
        "Step by step guide to Hajj.",
        "How to perform Hajj correctly in Islam?",
        "What are the steps of Hajj in order?",
        "Teach me how to perform Hajj.",
        "What is the correct method of performing Hajj?",
        "How should a Muslim perform Hajj?",
    ],
    "umrah": [
        "How do I perform Umrah?",
        "Step by step guide to Umrah.",
        "How to perform Umrah correctly in Islam?",
        "What are the steps of Umrah?",
        "Teach me how to perform Umrah.",
        "What is the correct method of Umrah?",
        "How should a Muslim perform Umrah?",
    ],
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_practical_pairs(seed: int = 42) -> list[dict]:
    """
    Generate Q&A training pairs for practical how-to Islamic questions.

    Returns a list of dicts with keys: instruction, output, metadata.
    Target: 50-80 pairs (8 topics × ~7 question templates = 56 pairs).
    """
    rng = random.Random(seed)

    taharah = _load_json(TAHARAH_FILE)
    ibadah  = _load_json(IBADAH_FILE)

    # Build answers from the actual data
    answers: dict[str, str] = {
        "wudu":     _build_wudu_answer(taharah),
        "ghusl":    _build_ghusl_answer(taharah),
        "tayammum": _build_tayammum_answer(taharah),
        "salah":    _build_salah_answer(ibadah),
        "fasting":  _build_fasting_answer(ibadah),
        "zakat":    _build_zakat_answer(ibadah),
        "hajj":     _build_hajj_answer(ibadah),
        "umrah":    _build_umrah_answer(ibadah),
    }

    pairs: list[dict] = []

    for topic, questions in TEMPLATES.items():
        shuffled = _shuffle_questions(questions, rng)
        answer   = answers[topic]
        for question in shuffled:
            pairs.append(_make_pair(question, answer, topic))

    # Final shuffle across all topics to mix them in training
    rng.shuffle(pairs)

    return pairs


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    pairs = generate_practical_pairs()
    print(f"Generated {len(pairs)} practical Q&A pairs.", file=sys.stderr)

    # Print a summary by topic
    from collections import Counter
    topic_counts: Counter = Counter(p["metadata"]["topic"] for p in pairs)
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic:12s}: {count} pairs", file=sys.stderr)

    # Dump as JSON to stdout (can be piped to a file)
    print(json.dumps(pairs, ensure_ascii=False, indent=2))
