"""
Helper module: generate Q&A training pairs for hadith-explanation questions.

Teaches the model to answer "Explain Hadith 1 from Bukhari", "What does this
hadith mean?", "What lessons can we take from this?" with a structured
explanation format — distinct from simply quoting the hadith text.

Imported by generate_qa_pairs.py — not run directly.

Entry point:
    generate_hadith_explanation_pairs(seed: int = 42) -> list[dict]
"""

from __future__ import annotations

import json
import random
import re
import unicodedata
from pathlib import Path
from typing import Any

# ─── Data paths ───────────────────────────────────────────────────────────────

_RAW_DIR: Path = Path(__file__).parent.parent.parent / "01_data_collection" / "raw"

_NAWAWI_PATH: Path = _RAW_DIR / "hadith" / "nawawi_40.json"
_QUDSI_PATH: Path = _RAW_DIR / "hadith" / "hadith_qudsi.json"
_BUKHARI_PATH: Path = _RAW_DIR / "hadith" / "bukhari.json"

# ─── Collection display names ─────────────────────────────────────────────────

_DISPLAY: dict[str, str] = {
    "nawawi_40": "40 Hadith Nawawi",
    "hadith_qudsi": "40 Hadith Qudsi",
    "bukhari": "Sahih al-Bukhari",
}

# ─── Narrator extraction ──────────────────────────────────────────────────────

# Pattern for "On the authority of X" / "Narrated X" opener
_NARRATOR_PATTERNS = [
    re.compile(
        r"^(?:On the authority of|on the authority of)\s+([A-Za-zÀ-ɏ'''\- ]+?)"
        r"(?:\s*\([^)]*\))?\s*(?:,|who said|:)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^Narrated\s+'?([A-Za-zÀ-ɏ'''\- ]+?)'?\s*(?:\([^)]*\))?\s*:",
        re.IGNORECASE,
    ),
]


def _extract_narrator(english: str) -> str:
    """Extract the narrator name from the opening of the English hadith text."""
    text = english.strip()
    for pat in _NARRATOR_PATTERNS:
        m = pat.match(text)
        if m:
            name = m.group(1).strip().rstrip(",")
            # Remove trailing "(ra)" or "(may Allah…)" fragments
            name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
            if 3 <= len(name) <= 60:
                return name
    return ""


# ─── Arabic isnad stripping (reuse pattern from format_hadith) ────────────────

_AR_ISNAD_START = re.compile(
    r"^(حَدَّثَنَا|حدثنا|أَخْبَرَنَا|اخبرنا|حَدَّثَنِي|حدثني"
    r"|أَخْبَرَنِي|اخبرني|وَحَدَّثَنَا|وحدثنا|وَأَخْبَرَنَا"
    r"|وأخبرنا|أَنْبَأَنَا|انبانا|رَوَى|روى)",
    re.UNICODE,
)
_AR_QALA = re.compile(r"قَالَ|قَالَتْ|قال|قالت", re.UNICODE)


def _strip_isnad_arabic(arabic: str) -> str:
    """Remove isnad chain from Arabic hadith text; return matn only."""
    if not arabic:
        return ""
    text = arabic.strip()
    if not _AR_ISNAD_START.match(text):
        return text
    matches = list(_AR_QALA.finditer(text))
    if not matches:
        return ""
    matn = text[matches[-1].end():].strip()
    matn = re.sub(r"^[\s:،,\-–—]+", "", matn).strip()
    return matn if len(matn) >= 20 else ""


def _clean_arabic(arabic: str) -> str:
    """Return stripped Arabic matn, or empty string if not meaningful.

    Normalises to NFC before isnad stripping because the raw JSON may use
    a different ordering of combining diacritics (e.g. shadda + fatha vs
    fatha + shadda), which would prevent regex matching without normalisation.
    """
    # Remove stray HTML tags sometimes present in the raw data
    clean = re.sub(r"<br\s*/?>", " ", arabic or "")
    clean = re.sub(r"<[^>]+>", "", clean).strip()
    # Normalise Unicode combining characters so the isnad regex matches reliably
    clean = unicodedata.normalize("NFC", clean)
    return _strip_isnad_arabic(clean)


# ─── Short-form hadith snippet for question templates ─────────────────────────

def _hadith_snippet(english: str, max_chars: int = 40) -> str:
    """Return first `max_chars` characters of the hadith text (quote-ready)."""
    text = english.strip()
    # Skip narrator opener to reach the actual teaching
    for prefix_pat in [
        r"^On the authority of [^:]+:\s*",
        r"^Also on the authority of [^:]+:\s*",
        r"^Narrated [^:]+:\s*",
    ]:
        text = re.sub(prefix_pat, "", text, flags=re.IGNORECASE).strip()
    # Now skip another level: "The Prophet ﷺ said:" / "The Messenger said:"
    text = re.sub(
        r'^(?:The (?:Prophet|Messenger)(?: of Allah)?(?: ﷺ)?\s+said[,:]?\s*["""]?)',
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    # Strip leading quotation marks
    text = text.lstrip('"\'""')
    snippet = text[:max_chars].rstrip()
    if len(text) > max_chars:
        snippet += "..."
    return snippet


# ─── Explanation derivation ───────────────────────────────────────────────────
#
# For every known hadith we pre-write a "What This Hadith Teaches", "Context",
# "Key Lessons", and "Related Principle" section.  For hadiths we have no
# pre-written entry for we fall back to an automatic derivation from keywords.

# Each entry: (teaches, context, lessons_list, related_principle)
_NAWAWI_EXPLANATIONS: dict[int, tuple[str, str, list[str], str]] = {
    1: (
        "The validity and reward of any deed in Islam hinges entirely on the sincerity "
        "of intention behind it. An action done for worldly gain or the wrong motive "
        "earns no reward with Allah, even if the outward act is correct.",
        "This hadith was reportedly said after a companion emigrated to Madinah for "
        "worldly reasons rather than for the sake of Allah. It became the first hadith "
        "in Imam Nawawi's collection because it underpins all of Islamic worship.",
        [
            "Before any act of worship, renew your intention (niyyah) sincerely for Allah.",
            "A small deed done with pure intention outweighs a large deed done for show.",
            "Riya (showing off) invalidates the spiritual reward of otherwise good deeds.",
        ],
        "This is the basis of the fiqh principle: 'Actions are judged by intentions' "
        "(al-umur bi-maqasidiha), one of the five universal maxims of Islamic law.",
    ),
    2: (
        "Islam, Iman, and Ihsan form three ascending levels of the religion. Islam is "
        "outward submission, Iman is inner conviction, and Ihsan is the highest level — "
        "worshipping Allah as though you see Him, bringing profound sincerity to every act.",
        "This hadith records the famous visit of the angel Jibreel, who appeared as an "
        "unknown man to teach the companions the foundations of their religion in a "
        "structured way. The Prophet ﷺ revealed his identity only after he left.",
        [
            "The five pillars of Islam (Shahada, Salah, Zakat, Fasting, Hajj) are the "
            "core outward practices every Muslim must fulfil.",
            "True faith requires belief in Allah, His angels, Books, Messengers, the "
            "Last Day, and divine decree (qadar).",
            "Ihsan — striving to worship as if you see Allah — is the highest spiritual "
            "goal; it turns routine acts into profound devotion.",
        ],
        "This hadith is called 'the mother of the Sunnah' because it summarises the "
        "entire religion in one conversation, just as Surah al-Fatiha summarises the Quran.",
    ),
    3: (
        "Islam is built on five foundational pillars, each representing a core act of "
        "worship. These pillars structure a Muslim's spiritual and communal life from the "
        "most basic testimony of faith to the once-in-a-lifetime pilgrimage.",
        "This hadith was recorded by the son of Umar ibn al-Khattab, one of the closest "
        "companions. It complements Hadith 2 (Jibreel's hadith) by stating the pillars "
        "directly as a building metaphor.",
        [
            "The Shahada (testimony of faith) is the entry point into Islam and the "
            "most important pillar.",
            "Prayer, Zakat, fasting, and Hajj are not optional extras but structural "
            "requirements — removing one weakens the entire building.",
            "Memorising and understanding these pillars is obligatory knowledge for "
            "every Muslim.",
        ],
        "This hadith establishes that Islam is a structured system of worship, not merely "
        "a set of personal beliefs, aligning with the Quranic command: 'Establish prayer "
        "and give Zakat.' (Al-Baqarah 2:43)",
    ),
    4: (
        "Every human being's destiny — sustenance, lifespan, deeds, and final abode — "
        "is written before birth by the angel. Yet free will and good deeds remain "
        "essential, because one may act well until the very end and be saved.",
        "Ibn Masood narrated this to show that divine decree (qadar) does not remove "
        "human responsibility. The shocking revelation that a man nearly in Paradise "
        "can end up in Hellfire (and vice versa) underlines the danger of complacency.",
        [
            "Belief in qadar (divine decree) is the sixth pillar of Iman — accepting "
            "that Allah knows and has decreed everything.",
            "Never feel secure from spiritual failure; the end of one's life can "
            "overturn an entire lifetime of good deeds if one abandons faith.",
            "Conversely, never despair: a life of sin can be redeemed by sincere "
            "repentance before death.",
        ],
        "This hadith establishes the Sunni position on predestination: decree is real "
        "and all-encompassing, yet humans are fully responsible for their choices — "
        "both truths coexist without contradiction.",
    ),
    5: (
        "Any practice introduced into the religion that has no basis in the Quran or "
        "authentic Sunnah is a rejected innovation (bid'ah). Islam is a complete "
        "revelation and requires no additions.",
        "The Prophet ﷺ said this in the context of defining the boundaries of the "
        "religion. It is paired with Hadith 1 in many scholarly works: Hadith 1 "
        "establishes that deeds need correct intention; Hadith 5 establishes they also "
        "need correct form according to revelation.",
        [
            "Innovations in worship — no matter how sincere the intention — are "
            "rejected by Allah because He completed the religion (Al-Ma'idah 5:3).",
            "The Sunnah provides the standard: if the Prophet ﷺ did not teach it as "
            "worship, it should not be treated as worship.",
            "Scholars distinguish between forbidden religious innovations (bid'ah) and "
            "permissible worldly innovations (technology, tools, etc.).",
        ],
        "This hadith is the textual foundation for protecting the Sunnah from distortion "
        "and forms the basis for scholars' rejection of newly invented religious rituals.",
    ),
    6: (
        "Lawful and unlawful matters are clear in Islam; it is the grey area of doubtful "
        "matters that tests a person's taqwa. The heart is the seat of spiritual health — "
        "when it is sound, the entire person's conduct is sound.",
        "The Prophet ﷺ used the vivid metaphor of a shepherd grazing near a protected "
        "sanctuary to explain how a person who flirts with doubtful matters will "
        "eventually cross into the forbidden. He then identifies the heart as the "
        "determining organ of all conduct.",
        [
            "Avoid doubtful matters as a protection for your religion and honour — "
            "not just what is clearly haram, but what raises uncertainty.",
            "The health of the heart directly determines the quality of all one's deeds; "
            "invest in purifying it through dhikr, reflection, and avoiding sin.",
            "Not everything that is technically permissible is spiritually beneficial — "
            "wara' (scrupulousness) is a higher station than mere legality.",
        ],
        "This hadith establishes the fiqh maxim: 'Leave that which makes you doubt "
        "for that which does not make you doubt,' and underscores the centrality of "
        "tazkiyat al-nafs (purification of the soul) in Islamic ethics.",
    ),
    7: (
        "The entire religion is encapsulated in sincere advice (naseehah). A Muslim's "
        "duty is to be genuinely well-wishing toward Allah, His Book, His Messenger, "
        "the Muslim leaders, and the Muslim community at large.",
        "A companion asked who this advice is owed to, and the Prophet ﷺ listed five "
        "recipients in order of priority: Allah first, then the revealed text, then the "
        "Prophet's person, then leadership, then the common believers.",
        [
            "Naseehah to Allah means worshipping sincerely, obeying His commands, "
            "and attributing to Him only what He deserves.",
            "Naseehah to the Muslim leaders means guiding them to good, not flattering "
            "them in sin, and sincerely praying for their rectification.",
            "Naseehah to fellow Muslims means wishing for them what you wish for "
            "yourself — the same principle as Hadith 13.",
        ],
        "This hadith condenses the social and spiritual ethics of Islam into one word: "
        "naseehah. It is the foundation of Islamic mutual accountability (hisba).",
    ),
    8: (
        "Allah commands fighting against those who resist the call to Islam until they "
        "embrace its testimony and obligations. Once they do, their lives and wealth are "
        "protected. This hadith describes the classical conditions for cessation of "
        "armed conflict in an Islamic state context.",
        "This hadith was addressed to the companions in the context of early Islamic "
        "expansion and the rules of warfare. It is understood by scholars in a "
        "political-military context, not as a command to individuals to attack neighbours.",
        [
            "The Shahada and establishment of prayer are the outward markers of entering "
            "the protected status of a Muslim in a Muslim polity.",
            "Life, property, and honour of those who affirm Islam are inviolable — "
            "except when they commit offences that carry Islamic legal penalties.",
            "Accountability ultimately rests with Allah alone, not with human beings.",
        ],
        "Scholars of usul al-fiqh cite this hadith when discussing the rights that "
        "Islam establishes for its adherents, and the limits of state authority.",
    ),
    9: (
        "Obedience to the Prophet ﷺ must be measured and reasonable. Muslims should "
        "avoid excessive questioning that burdens the community with new obligations, "
        "and should do as much good as they are capable of without overloading "
        "themselves with self-imposed hardship.",
        "The Prophet ﷺ said this after a companion's excessive question led to a ruling "
        "that became difficult to fulfil. It is a warning against introducing hardship "
        "through unnecessary interrogation of divine commands.",
        [
            "Islam is a religion of ease — do what is commanded to the best of your "
            "ability, and do not create extra restrictions on yourself.",
            "Excessive debate about religious rulings can sometimes lead to stricter "
            "outcomes; wisdom is sometimes in acceptance.",
            "What the Prophet ﷺ forbids, leave entirely; what he commands, fulfil "
            "as much as possible without creating undue hardship.",
        ],
        "This hadith is the basis for the fiqh principle: 'Hardship begets ease' "
        "(al-mashaqqah tajlib al-taysir), and for the Islamic emphasis on moderation "
        "in religious practice.",
    ),
    10: (
        "Allah is pure and accepts only what is pure. This applies equally to deeds "
        "and to sustenance. A du'a made with a heart sustained by haram income will not "
        "be answered — outward piety cannot compensate for inward corruption of what "
        "one consumes.",
        "The Prophet ﷺ described a man in the most desperate of circumstances — "
        "a dishevelled traveller with hands raised to the sky — to illustrate that "
        "even the most outwardly sincere supplication is blocked when one's sustenance "
        "is unlawful.",
        [
            "Earning and consuming only halal food and income is a precondition for "
            "accepted du'a and accepted worship.",
            "Allah does not judge only the outward form of good deeds; the source of "
            "one's livelihood directly affects spiritual acceptance.",
            "The traveller's supplication is normally answered (Sunan Tirmidhi 3598), "
            "which makes the blocking caused by haram all the more serious.",
        ],
        "This hadith connects economic ethics (halal earnings) directly to spiritual "
        "efficacy, establishing that material purity is inseparable from worship.",
    ),
    11: (
        "When faced with a choice between something that creates doubt or unease in the "
        "heart and something that does not, the Muslim should choose the certain and "
        "clear option. This protects both religion and personal integrity.",
        "Al-Hasan ibn Ali, the grandson of the Prophet ﷺ, narrated that he memorised "
        "this teaching directly from the Prophet ﷺ. It is a concise personal rule of "
        "thumb for navigating doubtful situations in daily life.",
        [
            "The conscience is a moral compass — when it signals unease about an action, "
            "take that signal seriously.",
            "Choosing certainty over doubt is not weakness; it is wara' (scrupulousness), "
            "a praised virtue in Islamic ethics.",
            "This principle applies to food, financial dealings, speech, and all areas "
            "where lawfulness is uncertain.",
        ],
        "This hadith complements Hadith 6 on doubtful matters and is cited by scholars "
        "as evidence for the Islamic precautionary principle (ihtiyat).",
    ),
    12: (
        "An important marker of a person's good Islam is their ability to avoid what "
        "does not concern them — idle gossip, unnecessary interfering, irrelevant "
        "conversation. Focusing on what matters is itself an act of worship.",
        "This brief but profound teaching addresses a key deficiency in religious "
        "character: the tendency to involve oneself in matters that have no benefit "
        "for one's deen or dunya. Imam al-Nawawi placed it early in his collection "
        "for its foundational importance to character.",
        [
            "Guard your tongue and attention — wasting them on useless matters depletes "
            "your spiritual capital.",
            "This principle covers speech, actions, and even thoughts: what does not "
            "concern you should not occupy your mind.",
            "Focusing on self-improvement rather than others' affairs is the practical "
            "implementation of this teaching.",
        ],
        "This hadith is the textual basis for the Islamic principle of purposefulness "
        "in speech and action — a cornerstone of Islamic character development (tahdhib).",
    ),
    13: (
        "Complete Iman (faith) requires loving for one's Muslim brother or sister "
        "everything that one loves for oneself. This mutual care is not optional — it "
        "is a condition of true belief.",
        "Anas ibn Malik, the Prophet's personal servant for ten years, narrated this "
        "as a direct teaching. The conditional structure ('none of you believes until') "
        "makes it a measure of faith rather than a mere recommendation.",
        [
            "Selflessness and concern for other Muslims is a pillar of Iman, not just "
            "a virtue — it directly affects the completeness of one's faith.",
            "This teaching drives Islamic concepts of brotherhood (ukhuwwah): sharing "
            "information, correcting errors kindly, supporting in hardship.",
            "It also prohibits envy (hasad) — wishing others lose what you do not have.",
        ],
        "This hadith is the Islamic version of the Golden Rule and establishes the "
        "fraternal ethic that makes Muslim communities cohesive.",
    ),
    14: (
        "The blood (life) of a Muslim is sacred and may only be taken in three specific "
        "circumstances: when a married person commits adultery, in retaliation for "
        "murder, and when someone apostasises and breaks from the Muslim community. "
        "Outside these, killing a Muslim is one of the gravest sins.",
        "Ibn Masood narrated this as a judicial ruling that defines the limited "
        "circumstances in which capital punishment may apply. It underscores that "
        "the default position in Islam is inviolability of Muslim life.",
        [
            "The life of every Muslim is sanctified — harming or killing without legal "
            "justification is among the greatest sins (Sahih Bukhari 6871).",
            "These three cases require due legal process through an Islamic court; "
            "they are not a licence for vigilante justice.",
            "The hadith teaches the value of human life and the extreme seriousness "
            "with which Islam treats its violation.",
        ],
        "This hadith is foundational to Islamic criminal law (hudud) and the principle "
        "that life is one of the five necessities (daruriyyat) that Islamic law "
        "exists to protect.",
    ),
    15: (
        "Iman in Allah and the Last Day must manifest in actions: good speech or "
        "silence, generosity to the neighbour, and hospitality to the guest. These "
        "three practical duties are markers of authentic belief.",
        "The Prophet ﷺ linked outward social virtues directly to the inner state of "
        "faith. The phrase 'let him who believes in Allah and the Last Day' before each "
        "command signals that neglecting these duties is a deficiency in iman.",
        [
            "Control the tongue: every word either earns reward or invites sin — "
            "silence is safer when one cannot speak good.",
            "The neighbour's right in Islam is extensive; the Prophet ﷺ emphasised "
            "it so often the companions thought it might become an inheritance right.",
            "Hospitality (diyafa) for a guest is a minimum of three days, with the "
            "first day being the formal guest right.",
        ],
        "This hadith establishes that the social dimension of Islam — generosity, "
        "speech, and hospitality — is inseparable from one's personal faith, not a "
        "cultural add-on.",
    ),
    16: (
        "A Muslim must not become angry. The Prophet ﷺ repeated this injunction three "
        "times to emphasise its priority. Controlling anger is presented not as a "
        "personality preference but as the key to avoiding greater spiritual harm.",
        "A companion asked the Prophet ﷺ to summarise his advice, expecting a lengthy "
        "answer. Instead, the Prophet ﷺ gave three identical replies: 'Do not get "
        "angry.' The repetition conveys urgency and finality.",
        [
            "Anger is the gateway to many sins — harsh speech, physical harm, broken "
            "relationships, injustice — so containing it prevents all of them.",
            "Practical tools the Sunnah teaches: seek refuge from Shaitan, sit down, "
            "perform wudu, or remain silent until the anger passes.",
            "True strength is not physical might but mastering one's anger "
            "(Sahih Bukhari 6114).",
        ],
        "This hadith connects to the broader Islamic ethics of anger management, "
        "citing the Quranic praise of those 'who restrain their anger' (Ali Imran 3:134).",
    ),
    17: (
        "Allah has prescribed excellence (ihsan) in all things — including how animals "
        "are treated. When slaughtering, sharpen the blade and do it swiftly to "
        "minimise pain. This principle of ihsan extends to every action in life.",
        "Shaddad ibn Aws narrated this as a direct command of the Prophet ﷺ. The "
        "choice of slaughter as the example is deliberate: if ihsan is required even "
        "in killing an animal, it is certainly required in all dealings with humans.",
        [
            "Excellence (ihsan) is mandatory in every act, not just in worship. "
            "Do each task as well as it can be done.",
            "Islamic animal welfare ethics: sharpen the knife before slaughter, do not "
            "slaughter one animal in front of another, and avoid causing extra pain.",
            "This teaching applies to all areas of life: craftsmanship, service, "
            "scholarship, and human relationships.",
        ],
        "This hadith is the primary source for Islamic animal welfare rulings and "
        "the broader principle that Allah mandates quality and care in every act.",
    ),
    18: (
        "Fear Allah wherever you are, follow a bad deed with a good deed to erase it, "
        "and deal with people with good character. These three principles summarise "
        "the entire ethical framework of a Muslim's life.",
        "Muadh ibn Jabal, one of the most knowledgeable companions in halal and haram "
        "(Sunan Tirmidhi 3790), received this direct personal advice from the Prophet ﷺ. "
        "It is a personalised summary of Islamic ethics.",
        [
            "Taqwa (God-consciousness) must be constant — not just in the mosque but "
            "privately, at home, in business, and in solitude.",
            "Good deeds erase bad ones: the Quran confirms 'Indeed, good deeds wipe "
            "away evil deeds' (Hud 11:114). Repentance followed by righteous action "
            "is the path to forgiveness.",
            "Good character (husn al-khuluq) is one of the heaviest deeds in the "
            "scales on the Day of Judgment (Sunan Tirmidhi 2003).",
        ],
        "This hadith is sometimes called 'a summary of Islamic ethics' because it "
        "covers the vertical (relationship with Allah) and horizontal (relationship "
        "with people) dimensions of religious life in three short commands.",
    ),
    19: (
        "Allah is gracious about mistakes made through genuine forgetfulness or "
        "compulsion. A Muslim is not held accountable for thoughts that pass through "
        "the mind without being acted upon, as long as they do not speak or act on them.",
        "Ibn Abbas narrated this as a mercy from Allah. The hadith specifically "
        "addresses involuntary thoughts (waswasah) and forgetfulness — common "
        "sources of spiritual anxiety for sincere believers.",
        [
            "You are not punished for passing thoughts of sin or unbelief — only for "
            "acting on them or speaking them.",
            "Acts done under genuine duress or coercion are excused, though one should "
            "still seek to avoid harm to others.",
            "Forgetfulness in worship (e.g., missing a portion of prayer) can be "
            "corrected through the prostration of forgetfulness (sujud al-sahw).",
        ],
        "This hadith establishes the Islamic principle of 'lifting the pen' (raf' "
        "al-qalam) for three categories of people and is foundational to Islamic "
        "legal theory on intention and capacity.",
    ),
    20: (
        "Hayaa (modesty and shame before Allah and people) is a branch of faith. "
        "When modesty disappears, a person loses the internal restraint that prevents "
        "sin — therefore 'do whatever you wish' is not permission but a warning of "
        "spiritual destruction.",
        "The Prophet ﷺ passed by a man advising his brother to reduce his modesty. "
        "He corrected this, clarifying that hayaa is part of iman, not an obstacle "
        "to it. The phrase 'if you have no hayaa, do whatever you wish' conveys that "
        "without modesty, nothing prevents sin.",
        [
            "Hayaa encompasses modesty in dress, in speech, in relations with the "
            "opposite sex, and in one's private conduct with Allah.",
            "It is a protective quality — a believer with hayaa naturally avoids many "
            "sins without being told explicitly.",
            "This is not shyness born of low confidence but a conscious awareness of "
            "being seen by Allah and of maintaining dignity.",
        ],
        "This hadith is cited as evidence that Islamic ethics are rooted in internal "
        "character (hayaa) rather than external enforcement alone.",
    ),
    21: (
        "To enter Paradise, one must speak good words (Shahada) and feed others. These "
        "are presented as the path to Paradise, connecting personal faith to social "
        "generosity as inseparable.",
        "Abdullah ibn Amr ibn al-As asked the Prophet ﷺ which action in Islam is best. "
        "The answer — greeting others with salam and feeding people — elevates two "
        "social acts to the highest category of deeds.",
        [
            "Spreading the greeting of salam (peace) widely is a sunnah with great "
            "spiritual reward and community-building power.",
            "Feeding others — whether at a feast or in giving to the poor — is one of "
            "the most beloved acts in Islam.",
            "Paradise is reached through both iman (inner faith) and ihsan (outward "
            "service to others) — neither alone is sufficient.",
        ],
        "This hadith establishes the social dimension of Islamic worship: external "
        "acts of kindness are not mere etiquette but a path to the highest spiritual "
        "reward.",
    ),
    22: (
        "The Prayer is a pillar of the religion. Whoever establishes it has established "
        "the religion; whoever abandons it has demolished it. The other pillars are "
        "compared to ropes around the body — Salah is the central pillar holding them up.",
        "Muadh ibn Jabal narrated this as a comprehensive teaching from the Prophet ﷺ "
        "on the structure of the religion. It uses architectural and physical metaphors "
        "to convey the load-bearing role of Salah.",
        [
            "Salah is not one optional pillar among many — it is the central support "
            "of the entire religious structure.",
            "Establishing prayer consistently (on time, with proper form, and with "
            "concentration) maintains the structure of one's deen.",
            "The Prophet ﷺ said elsewhere: 'The first thing a slave will be held "
            "accountable for on the Day of Judgment is prayer' (Sunan Nasa'i 463).",
        ],
        "This hadith is among the primary evidences for the supreme importance of "
        "Salah and is cited in fiqh discussions about the ruling on abandoning prayer.",
    ),
    23: (
        "Purification (taharah) is half of iman. Glorifying and praising Allah fills "
        "scales with reward. Prayer is a light, charity is a proof, and patience "
        "is illumination. These metaphors convey the spiritual function of each act.",
        "Abu Malik al-Ash'ari narrated this as a comprehensive teaching on the "
        "connection between ritual practice and inner spiritual state. The Quran "
        "itself repeatedly links purity with closeness to Allah.",
        [
            "Wudu (ritual purification) is a spiritual act as well as physical — it "
            "removes minor sins with each drop of water (Sahih Muslim 244).",
            "Sadaqa (charity) as 'proof' means it proves genuine faith — a person "
            "who truly loves wealth but gives it away demonstrates real iman.",
            "Patience (sabr) is the light of the believer in the darkness of trials — "
            "the Quran promises 'Allah is with the patient' (Al-Baqarah 2:153).",
        ],
        "This hadith is foundational in Sufi and mainstream Islamic spirituality for "
        "understanding how outward rituals (taharah, salah, zakat) produce inward "
        "spiritual qualities (light, proof, illumination).",
    ),
    24: (
        "Allah's prohibitions are His sanctuary. Just as a king's protected zone must "
        "not be violated, a Muslim who crosses Allah's limits damages their own "
        "relationship with Him. The heart — not the mind or the body — is the organ "
        "that governs all conduct.",
        "This is the continuation of Hadith 6 (the shepherd parable). It concludes "
        "with the famous declaration about the heart as the governing organ of all "
        "human action, which became one of the most quoted lines in Islamic literature.",
        [
            "The heart must be given attention and care: dhikr, reflection, avoiding "
            "sin, and seeking knowledge all purify it.",
            "A diseased heart leads to corrupt actions even when the person knows "
            "right from wrong — knowledge alone does not guarantee righteous conduct.",
            "The physical body follows what the heart commands — rectifying the heart "
            "is therefore the most important form of Islamic self-development.",
        ],
        "This hadith is the Prophetic foundation for the entire discipline of "
        "tazkiyat al-nafs (purification of the soul) and Islamic spiritual psychology.",
    ),
    25: (
        "Poverty is not a barrier to acts of charity. Every tasbeeh, tahmid, takbeer, "
        "and tahleel said to glorify Allah is a form of sadaqa. Even fulfilling one's "
        "lawful needs with one's spouse is rewarded.",
        "The poor companions came to the Prophet ﷺ saying the wealthy had more "
        "opportunities to earn reward. The Prophet ﷺ taught them that free acts of "
        "dhikr are equivalent to sadaqa — an equalising mercy from Allah.",
        [
            "Dhikr (remembrance of Allah) is available to everyone regardless of "
            "wealth, health, or status — it costs nothing but attention.",
            "Every act — including halal physical enjoyment — can be turned into "
            "worship with the right intention.",
            "The wealthy companions later adopted the same dhikr, but the Prophet ﷺ "
            "said that is Allah's grace, not an injustice.",
        ],
        "This hadith demonstrates that Islamic worship is accessible to all economic "
        "classes and that dhikr is not merely devotional but equivalent in reward to "
        "material charity.",
    ),
    26: (
        "Every joint in the human body owes a sadaqa (act of charity or gratitude) "
        "each day. These obligations are fulfilled through acts of worship, service, "
        "and justice — even the performance of Duha prayer covers them all.",
        "Abu Hurayrah narrated this as a summary of the vast scope of sadaqa in Islam. "
        "The 360 joints mentioned correspond to classical anatomical understanding, "
        "and each represents a daily opportunity for worship.",
        [
            "Sadaqa is far broader than financial giving — it includes good speech, "
            "helping others, removing obstacles from the path, and acts of justice.",
            "The Duha prayer (two to eight rak'ahs performed in the late morning) "
            "is a powerful sunnah that fulfils the daily gratitude obligation.",
            "Every moment of physical ability is a gift from Allah that calls for "
            "gratitude expressed through worship and service.",
        ],
        "This hadith is the primary textual basis for the sunnah of Duha prayer and "
        "establishes that gratitude to Allah must be expressed through action.",
    ),
    27: (
        "Righteousness is what the soul is at peace with and what the heart settles "
        "upon contentedly. Sin is what creates unease in the soul and what one would "
        "dislike others to witness, even if scholars issue a permit.",
        "Al-Nawwas ibn Sam'an narrated this as an internal moral compass for navigating "
        "grey areas. It does not replace fiqh rulings but serves as a supplement for "
        "personal spiritual discernment.",
        [
            "The conscience (fitra) is a reliable guide when fiqh does not provide a "
            "clear ruling — trust the unease you feel.",
            "This principle assumes a spiritually healthy, trained conscience — "
            "someone with a corrupted conscience cannot rely on it alone.",
            "This hadith works alongside Hadith 11 ('leave what makes you doubt') "
            "to provide a personal ethics framework.",
        ],
        "This hadith is cited in Islamic ethics as evidence that internal spiritual "
        "discernment (wara') is a valid tool for personal moral decision-making, "
        "alongside scholarly fiqh.",
    ),
    28: (
        "It is obligatory upon every Muslim to obey lawful commands from their "
        "leaders, whether they like it or not. The exception is any command that "
        "constitutes disobedience to Allah — in that case, there is no obedience "
        "to a creation that entails disobedience to the Creator.",
        "Ibn Umar narrated this in the context of political obedience within an Islamic "
        "framework. The Prophet ﷺ is here teaching the principle of qualified obedience "
        "to authority, with a clear ceiling defined by divine commands.",
        [
            "Muslims must obey lawful authority as a religious duty, not merely a "
            "civic one — this maintains order and prevents chaos (fitna).",
            "Obedience to authority has a clear ceiling: no human command can override "
            "Allah's command.",
            "This teaching prevents both anarchy (refusing all authority) and "
            "blind tyranny (obeying any command without limit).",
        ],
        "This hadith is the foundation of Islamic political ethics: qualified obedience "
        "to legitimate authority, with the shariah as the absolute upper limit.",
    ),
    29: (
        "If a person fears that public knowledge of their sins would harm them or "
        "cause disgrace, they should repent privately. Repentance accepted by Allah is "
        "complete and wipes out the sin entirely, and Allah veils sins when repentance "
        "is sincere.",
        "Muadh ibn Jabal narrated this teaching as part of a longer hadith that covers "
        "the foundations of Islamic ethics. It emphasises that public confession of sins "
        "is not required — private sincere repentance is sufficient.",
        [
            "Private repentance (tawbah) directly to Allah is always available and "
            "always accepted while the soul is still in the body.",
            "Concealing one's sins (sitr) is the Islamic default — there is no "
            "confession to clergy; one repents directly to Allah.",
            "Following sin immediately with a good deed (as in Hadith 18) is itself "
            "a form of practical repentance.",
        ],
        "This hadith establishes that Islamic repentance is direct, private, and "
        "unconditional — there is no intermediary between a servant and Allah for "
        "seeking forgiveness.",
    ),
    30: (
        "Allah has established fixed limits (hudud). Do not transgress them. He has "
        "made certain things obligatory — do not neglect them. He has forbidden certain "
        "things — do not violate them. He has left certain things unspecified as "
        "a mercy — do not seek to define them.",
        "Abu Tha'labah al-Khushani narrated this concise framework for navigating "
        "Islamic law. The category of 'left unspecified as mercy' refers to the vast "
        "area of permissible (mubah) matters that have no ruling.",
        [
            "The Islamic legal framework covers obligatory (fard), forbidden (haram), "
            "recommended (mustahabb), disliked (makruh), and permissible (mubah) acts.",
            "Do not search for rulings on things Allah deliberately left open — "
            "this is a mercy that creates flexibility and ease.",
            "Transgressing the boundaries of the shariah in any direction — by being "
            "more restrictive or more permissive than intended — is itself wrong.",
        ],
        "This hadith is foundational to Islamic legal theory (usul al-fiqh) and the "
        "understanding that the absence of a ruling is itself a form of divine guidance.",
    ),
    31: (
        "Detachment from the world (zuhd) does not require poverty; it means not "
        "letting what you possess distract you from Allah, and not grieving over what "
        "you have lost. It is an internal orientation, not an external condition.",
        "Ibn Abbas narrated this as a direct teaching on zuhd. The Prophet ﷺ "
        "deliberately broadened the definition to include the wealthy who are "
        "internally free — and exclude the poor who remain attached.",
        [
            "Zuhd (asceticism) in Islam is not abandoning the world but using it "
            "without being enslaved to it.",
            "Grief over lost wealth or status is itself a form of attachment that "
            "Islam asks the believer to work against.",
            "The wealthy person who gives charity freely and is not distracted by "
            "wealth has attained zuhd, while the poor person who covets wealth has not.",
        ],
        "This hadith redefines Islamic spirituality away from extreme asceticism "
        "toward a balanced engagement with the world free from internal attachment.",
    ),
    32: (
        "Causing harm is forbidden, and retaliating with harm is also forbidden. "
        "This dual prohibition establishes a foundational principle of Islamic ethics "
        "and law: harm must be prevented and not initiated, even in response to "
        "being wronged.",
        "Ibn Abbas and Ubadah ibn al-Samit both narrated this brief but powerful "
        "teaching. Its brevity and completeness made it one of the most cited hadiths "
        "in Islamic jurisprudence.",
        [
            "Muslims may not initiate harm against others — this covers physical harm, "
            "financial harm, reputational harm, and emotional harm.",
            "Retaliating with disproportionate harm is also forbidden — justice "
            "requires measured response, not excess.",
            "This principle underpins Islamic medical ethics, commercial ethics, "
            "environmental law, and international relations.",
        ],
        "This hadith is universally cited as one of the five universal maxims of "
        "Islamic law: 'Harm shall be neither inflicted nor reciprocated' "
        "(la darar wa la dirar), forming the basis of the entire body of harm prevention in fiqh.",
    ),
    33: (
        "If someone accuses another of injustice, the defendant cannot be the judge "
        "in their own case. Evidence must be produced by the claimant; the oath falls "
        "on the one who denies. This establishes the procedural justice framework of "
        "Islamic law.",
        "Ibn Abbas narrated this as a fundamental rule of Islamic judicial procedure. "
        "Its brevity makes it a memorable legal maxim that shaped Islamic courts "
        "for centuries.",
        [
            "The burden of proof lies on the claimant — a mere accusation does not "
            "establish guilt in Islamic law.",
            "The oath (yamin) is given to the one who denies the claim, providing "
            "a solemn mechanism for resolving disputes when evidence is absent.",
            "This procedural justice prevents oppression through baseless accusations "
            "and protects the presumption of innocence.",
        ],
        "This hadith is the textual source of the Islamic procedural principle "
        "'al-bayyinah 'ala al-mudda'i wal-yamin 'ala man ankara' — foundational "
        "to Islamic civil and criminal procedure.",
    ),
    34: (
        "Wronging others is a form of darkness that accumulates and engulfs the "
        "oppressor on the Day of Judgment. The Prophet ﷺ forbade injustice for himself "
        "and for his nation, warning that it leads to destruction.",
        "Abu Dharr al-Ghifari narrated this as a divine hadith (qudsi) in a longer "
        "form, but Imam Nawawi recorded this summary. The inclusion of 'for Myself' "
        "conveys that Allah's own attribute is absolute freedom from injustice.",
        [
            "Dhulm (injustice/oppression) is one of the gravest sins — it includes "
            "taking what belongs to others, breaking promises, and failing in duties.",
            "The oppressed person's du'a has special power in Islam — Allah does not "
            "veil it (Sahih Bukhari 1496).",
            "Guard against injustice in small matters as well as large: even an "
            "extra word that hurts someone unjustly counts.",
        ],
        "This hadith establishes that Justice (adalah) is one of Allah's own "
        "attributes and a non-negotiable demand of Islamic ethics in all relationships.",
    ),
    35: (
        "Muslims are obligated to remove evil by action if they have the power; if not, "
        "by speaking against it; if not even that is possible, by detesting it in the "
        "heart. The last level is the weakest expression of faith.",
        "Abu Sa'id al-Khudri narrated this as the Islamic framework for responding to "
        "wrongdoing. The three levels create a hierarchy of obligation based on ability "
        "and authority, preventing both paralysis and anarchy.",
        [
            "Changing evil by hand is the duty of those with authority (rulers, parents, "
            "employers) within their jurisdiction — not a licence for vigilantism.",
            "Speaking against evil is the duty of scholars, community leaders, and "
            "anyone with a platform, when it is safe and likely to be effective.",
            "The heart level is the absolute minimum — a believer can never become "
            "comfortable with or indifferent to evil.",
        ],
        "This hadith is the textual foundation for the Islamic obligation of "
        "al-amr bil-ma'ruf wa-l-nahy 'an al-munkar (enjoining good and forbidding "
        "evil), one of Islam's most important communal obligations.",
    ),
    36: (
        "Whoever fulfils the needs of a fellow Muslim, Allah will fulfil their needs. "
        "Whoever relieves a Muslim of distress, Allah will relieve them of a distress "
        "on the Day of Judgment. Whoever conceals a Muslim's fault, Allah will conceal "
        "theirs.",
        "Ibn Umar narrated this as a statement about the direct correspondence "
        "between how a Muslim treats others and how Allah treats them. Each clause "
        "mirrors in the divine realm what one does in the human realm.",
        [
            "Service to fellow Muslims is service to oneself — divine reciprocity "
            "is a certainty, not a probability.",
            "Concealing the sins and faults of others (sitr) is a highly rewarded act "
            "in Islam, provided there is no harm being concealed from potential victims.",
            "The believer is described as the one who makes things easier for others, "
            "not harder — this is the essence of Islamic brotherhood.",
        ],
        "This hadith is the scriptural basis for the Islamic ethic of mutual "
        "support (ta'awun), establishing that caring for the Muslim community is "
        "itself a path to divine mercy.",
    ),
    37: (
        "Allah has recorded both good and bad deeds, but applies them with divine "
        "generosity: a good intention earns a full reward even if not acted upon; "
        "a bad intention not acted upon is not recorded as a sin. This is the mercy "
        "of Allah in the recording of deeds.",
        "Ibn Abbas narrated this as words directly from Jibreel to the Prophet ﷺ, "
        "conveying Allah's framework for how deeds are evaluated. The hadith contains "
        "one of the most merciful provisions in all of Islamic theology.",
        [
            "A sincere intention to do good earns a full reward with Allah even if "
            "circumstances prevent the action — intent is not just a formality.",
            "A bad thought that does not become an intention and is then abandoned "
            "is not recorded against you — this is an extraordinary mercy.",
            "Acting on a bad intention multiplies sin, but abandoning it for the "
            "sake of Allah turns it into a reward (the exception in the hadith).",
        ],
        "This hadith is the foundation for the Islamic understanding that Allah "
        "judges intentions (niyyat) as generously as possible and applies His mercy "
        "in the recording of every human thought and deed.",
    ),
    38: (
        "Allah descends each night to the lowest heaven during the last third of the "
        "night, calling out for anyone who supplicates, asks forgiveness, or seeks. "
        "This special time of night is the most powerful window for du'a.",
        "Abu Hurayrah narrated this as one of the most widely known hadiths on the "
        "virtue of night worship (tahajjud). The description of divine descent (nuzul) "
        "is accepted by Sunni scholars as real, without asking how, as is befitting "
        "Allah's majesty.",
        [
            "The last third of the night — roughly the hour before Fajr — is the "
            "prime time for tahajjud prayer, du'a, and istighfar.",
            "Du'a in this time is almost certainly answered — the Prophet ﷺ "
            "consistently rose for night prayer (Sahih Bukhari 1147).",
            "Waking even briefly to make sincere du'a before Fajr can transform "
            "one's spiritual life; it is a mark of the awliya (close servants of Allah).",
        ],
        "This hadith is the primary textual source for the special virtue of "
        "Qiyam al-Layl (night prayer) and the supreme opportunity of the last third "
        "of the night for supplication.",
    ),
    39: (
        "Allah forgives all sins — no matter how great — for the one who repents "
        "sincerely and turns back to Him with hope. Despair of Allah's mercy is itself "
        "condemned in the Quran. This hadith is among the most hopeful in all of Islam.",
        "Abdullah ibn Umar narrated this as a divine address to those overwhelmed "
        "by their sins. Its unconditional phrasing is designed to prevent despair "
        "and motivate return to Allah at any stage of life.",
        [
            "No sin is too great for Allah to forgive — the condition is sincerity "
            "in turning back to Him and not associating partners with Him.",
            "Despair of Allah's mercy (ya's) is forbidden in Islam; Allah ﷻ says "
            "'do not despair of the mercy of Allah' (Az-Zumar 39:53).",
            "This hadith is often given to those struggling with guilt over past "
            "sins — it is a direct divine invitation, not merely a human reassurance.",
        ],
        "This hadith is the most comprehensive statement of Allah's forgiveness in "
        "the Sunnah and is cited alongside Surah Az-Zumar 39:53 as the ultimate "
        "declaration of divine mercy open to every repentant believer.",
    ),
    40: (
        "Be mindful of Allah and He will protect you. Remember Him in prosperity and "
        "He will remember you in adversity. Know that what missed you could not have "
        "hit you, and what hit you could not have missed you. Help Allah and He will "
        "help you. These constitute a complete philosophy of reliance on Allah.",
        "Ibn Abbas narrated this lengthy piece of advice from the Prophet ﷺ as a "
        "comprehensive guide to a life built on tawakkul (reliance on Allah) and "
        "constant awareness of divine decree.",
        [
            "Maintaining God-consciousness in easy times builds the spiritual reserve "
            "needed to remain firm in hard times.",
            "The certainty that every event in your life was destined brings peace — "
            "no catastrophe is a mistake, no blessing is accidental.",
            "When you seek help, seek it from Allah first; when you trust, trust Allah "
            "first — this is the practical meaning of tawakkul.",
        ],
        "This hadith is among the most comprehensive summaries of the Islamic "
        "worldview: divine protection, decree, and mutual commitment between the "
        "servant and their Lord.",
    ),
    41: (
        "True faith requires loving for all people — not just Muslims — what you love "
        "for yourself. This extends the ethic of brotherhood in Hadith 13 to all of "
        "humanity.",
        "Abdullah ibn Amr narrated this as a broadening of the Nawawi 40 ethic. "
        "Some versions add 'for all people' explicitly, which scholars use to "
        "demonstrate Islam's universal ethical concern for humanity.",
        [
            "The duty of goodwill is not confined to Muslims — a believer should "
            "genuinely wish good for all human beings.",
            "This principle underlies Islamic ethics of trade, diplomacy, "
            "neighbourly relations with non-Muslims, and charity.",
            "It counters any exclusivist reading of Islam that treats non-Muslims "
            "as outside the scope of ethical concern.",
        ],
        "This hadith reinforces Islam's universal moral framework and is cited "
        "alongside Hadith 13 in discussions of the scope of Islamic brotherhood.",
    ),
    42: (
        "Every human being has the capacity for good (righteous deeds) and harm "
        "(sins). The best of those who sin are those who repent readily and return "
        "to Allah. Perfection is not expected; what is expected is sincere return.",
        "Anas ibn Malik narrated this as a final teaching emphasising that consistent "
        "repentance is within everyone's reach. The hadith closes Imam Nawawi's "
        "collection on a note of hope and accessibility.",
        [
            "All humans sin — this is acknowledged and accepted by Allah. The "
            "distinguishing quality of the believer is how quickly and sincerely "
            "they repent.",
            "Regular istighfar (seeking forgiveness) is the sunnah of every Prophet, "
            "including the Prophet ﷺ himself who sought forgiveness over 70 times a "
            "day (Sahih Bukhari 6307).",
            "Do not delay repentance waiting for a 'perfect moment' — the best time "
            "to repent is immediately after every sin.",
        ],
        "This hadith closes the Nawawi 40 by grounding the entire collection in "
        "mercy: the final teaching is not a warning but an invitation to return "
        "to Allah, no matter how many times one has sinned.",
    ),
}

# Pre-written explanations for Hadith Qudsi (divine hadith from Allah)
# Each entry: (teaches, context, lessons_list, related_principle)
_QUDSI_EXPLANATIONS: dict[int, tuple[str, str, list[str], str]] = {
    1: (
        "Allah's mercy is greater than His wrath — this is a divine pledge written by "
        "Allah Himself and kept with Him. It is not a conditional promise but an absolute "
        "statement of divine nature.",
        "This hadith is reported by both Bukhari and Muslim and establishes the "
        "foundational Islamic understanding of Allah's character. It is particularly "
        "important for believers who fear their sins outweigh divine mercy.",
        [
            "Never despair of Allah's mercy — His own written pledge confirms it "
            "surpasses His wrath for the sincere believer.",
            "This is not a licence to sin freely but a comfort for the repentant, "
            "encouraging them to return to Allah without despair.",
            "The concept of Allah's rahma (mercy) is central: it is mentioned 113 "
            "times in the Quran in the Bismillah alone (once per surah).",
        ],
        "This Hadith Qudsi is the divine source for the Islamic axiom: 'Allah's "
        "mercy precedes His wrath,' used by scholars to explain His preference for "
        "forgiveness over punishment.",
    ),
    2: (
        "Denying resurrection and claiming Allah has a son are two grave theological "
        "errors that Allah describes as false and unfounded. This hadith affirms "
        "tawhid (oneness) and the certainty of resurrection in the most direct "
        "divine voice.",
        "This Hadith Qudsi records Allah's own words about two forms of denial "
        "that were common in the pre-Islamic and early Islamic world: denial of "
        "resurrection and the attribution of a son to Allah.",
        [
            "Belief in resurrection is not just a hope — it is a certainty that Allah "
            "declares as straightforward as creating the heavens and earth the first time.",
            "The oneness of Allah (tawhid) is absolute: He has no son, no partner, "
            "no equal. This is the declaration of Surah al-Ikhlas.",
            "Misrepresenting Allah's nature through theological speculation is treated "
            "with great seriousness in the Quran and Sunnah.",
        ],
        "This Hadith Qudsi is cited in aqeedah (creed) discussions as a divine "
        "rebuttal to both materialist denial of the afterlife and Trinitarian theology.",
    ),
    3: (
        "Attributing rain or blessings to stars, planets, or natural forces rather "
        "than to Allah's will is a form of disbelief (kufr). True monotheism means "
        "recognising Allah alone as the ultimate cause of all provisions and natural events.",
        "This hadith was said after a night of rain at al-Hudaybiyah. The Prophet ﷺ "
        "asked the companions what Allah had said, and reported this divine response "
        "distinguishing the believer who attributes rain to Allah's grace from the one "
        "who attributes it to a star's position.",
        [
            "In Islamic theology, natural causes are secondary causes — Allah is "
            "always the primary cause. Seeing only the secondary cause without "
            "acknowledging Allah is a spiritual deficiency.",
            "Pre-Islamic Arabs believed certain stars caused rain; this hadith "
            "directly corrects that superstition with monotheistic clarity.",
            "A believer acknowledges natural phenomena while always referring their "
            "ultimate cause back to Allah: 'We have been given rain by Allah's grace.'",
        ],
        "This Hadith Qudsi is foundational to the Islamic concept of tawhid al-rububiyyah "
        "(oneness in Allah's lordship) — affirming that all universal affairs are "
        "governed exclusively by Allah.",
    ),
    4: (
        "To curse or inveigh against Time (dahr) is a form of indirect insult to Allah, "
        "because Allah controls time and all that happens within it. The Muslim should "
        "not complain about 'fate' or 'time' as an impersonal force.",
        "Pre-Islamic Arabs had a concept of 'dahr' (Time) as a blind, impersonal force "
        "that brought suffering. This Hadith Qudsi corrects that notion: Time is not "
        "autonomous — Allah is its Lord and Controller.",
        [
            "Expressions like 'time has treated me badly' or 'fate is cruel' are "
            "discouraged — they implicitly blame something other than Allah.",
            "Replace complaints about 'time' with acknowledgment of Allah's wisdom "
            "and patience in accepting His decree.",
            "Night and day, seasons and years — all are under Allah's control, not "
            "impersonal forces.",
        ],
        "This Hadith Qudsi is cited in discussions of Islamic determinism (qadar) "
        "and the avoidance of language that implies a deity or force beside Allah.",
    ),
    5: (
        "Allah declares that He does not need human worship and is free from all "
        "need (al-Samad). However, if all creation were maximally righteous, it would "
        "not increase His kingdom; if all were maximally evil, it would not decrease it. "
        "Worship benefits the worshipper, not Allah.",
        "Abu Dharr al-Ghifari narrated this comprehensive Hadith Qudsi which covers "
        "divine self-sufficiency, the distribution of guidance, and the impossibility "
        "of affecting Allah through human deeds.",
        [
            "Worship is for the worshipper's benefit — it elevates the soul, "
            "builds taqwa, and earns divine reward. Allah needs nothing from it.",
            "This eliminates any sense of doing Allah a favour by worshipping — "
            "gratitude and servitude are the proper attitudes.",
            "The unity and interdependence of all creation is affirmed: as one heart "
            "with one Lord, yet each individual fully accountable.",
        ],
        "This Hadith Qudsi is central to Islamic theology of divine self-sufficiency "
        "(istighnah) and the understanding that Islamic worship exists for human "
        "benefit and spiritual elevation.",
    ),
    6: (
        "Allah calls on His servants to ask Him for all their needs, promising to "
        "provide everything they need. Giving to all creation simultaneously would "
        "not diminish His treasure any more than a needle dipped in the ocean. This "
        "communicates the boundlessness of divine provision.",
        "This Hadith Qudsi addresses a human tendency to feel that asking Allah too "
        "much might be burdensome. The ocean-needle analogy dispels that notion "
        "with a vivid image of infinite divine generosity.",
        [
            "Ask Allah for everything — big and small. He welcomes being asked and "
            "is displeased when His servants do not ask (Sunan Tirmidhi 3604).",
            "Material needs, spiritual needs, forgiveness, guidance — all are "
            "within the scope of du'a.",
            "The vastness of divine provision should inspire confidence and "
            "gratitude, not hesitancy in supplication.",
        ],
        "This Hadith Qudsi is a divine invitation to du'a and is used in Islamic "
        "spiritual guidance to overcome the feeling that one's needs are 'too small' "
        "or 'too many' to bring to Allah.",
    ),
    7: (
        "Allah calls all people to guidance and will provide for all who come to Him. "
        "If He were to guide everyone simultaneously, it would not diminish His "
        "dominion. The distribution of guidance is entirely within His power and wisdom.",
        "This continuation of the previous Hadith Qudsi emphasises that divine "
        "guidance is not a finite resource that runs out — Allah's capacity to guide "
        "is as infinite as His provision.",
        [
            "Pray for the guidance of others with confidence — asking Allah to guide "
            "people does not deplete His capacity.",
            "The door to guidance is always open; Allah's call to His servants is "
            "constant and never withdrawn.",
            "Believers should embody hope for others' guidance, not limit their prayers "
            "to those they think 'deserve' it.",
        ],
        "This Hadith Qudsi grounds Islamic da'wah (calling to Islam) in a theology "
        "of abundance — divine guidance is inexhaustible and available to all.",
    ),
    8: (
        "Allah will respond to the one who calls on Him with sincerity. The divine "
        "response described in this hadith — 'I am as My servant thinks of Me' — "
        "establishes that having a good opinion of Allah (husn al-dhann billah) "
        "is itself a form of worship.",
        "Abu Hurayrah narrated this foundational Hadith Qudsi on the intimacy "
        "between Allah and the sincere believer. The phrase 'I am with him when he "
        "remembers Me' is the Quranic theme of Allah's presence with those who "
        "remember Him (Al-Baqarah 2:152).",
        [
            "Always have a good opinion of Allah — He will treat you as you expect "
            "Him to, so expect His mercy, not His wrath.",
            "Dhikr (remembrance) is reciprocal: when you remember Allah, He "
            "remembers you before the best of creation.",
            "Allah's closeness is a spiritual reality — 'closer to him than his "
            "jugular vein' (Qaf 50:16).",
        ],
        "This Hadith Qudsi is the textual basis for the Islamic principle of "
        "husn al-dhann billah (having a good opinion of Allah), which scholars "
        "call one of the conditions of a good death.",
    ),
    9: (
        "On the Day of Judgment, Allah will ask the believer why they did not feed "
        "Him when He was hungry — revealing that feeding the poor IS feeding Allah "
        "in a metaphorical, meritorious sense. Serving the vulnerable is equated "
        "with direct service to the divine.",
        "This Hadith Qudsi presents a profound theological statement about the "
        "relationship between service to the poor and service to Allah. It is among "
        "the most moving hadith on social justice in the entire Sunnah.",
        [
            "Feeding the hungry, caring for the sick, and supporting the destitute "
            "are among the acts most beloved to Allah.",
            "This hadith removes the separation between 'spiritual worship' and "
            "'social service' — serving people IS worship.",
            "The question on the Day of Judgment will include: did you visit Me "
            "when I was sick? Did you feed Me when I was hungry? The answer "
            "comes through service to other humans.",
        ],
        "This Hadith Qudsi is a cornerstone of Islamic social justice theology: "
        "serving the vulnerable is not a supplement to worship but an act of "
        "direct obedience to and nearness to Allah.",
    ),
    10: (
        "Allah forgives sins generously if the servant acknowledges them sincerely. "
        "The cycle of sin, acknowledgment, and forgiveness can repeat — Allah will "
        "keep forgiving as long as the servant keeps returning, without limit.",
        "Abu Hurayrah narrated this as a demonstration of the boundlessness of "
        "divine forgiveness. The repeated cycle in the hadith removes any excuse "
        "for permanent despair over recurring sin.",
        [
            "Repetitive sin followed by sincere repentance is still forgiven — "
            "Allah does not place a ceiling on forgiveness.",
            "The condition is sincerity of acknowledgment and turning back; "
            "insincere 'repentance' made while planning to sin again is not tawbah.",
            "This hadith is a profound mercy for those who struggle with the same "
            "sin repeatedly — return to Allah every single time.",
        ],
        "This Hadith Qudsi is the divine basis for the Islamic doctrine that "
        "tawbah (repentance) is always accepted and that the door of return to "
        "Allah never closes during a person's lifetime.",
    ),
    11: (
        "Allah calls out to the sinful servant who has not associated partners with "
        "Him, promising to fill their repentance with forgiveness matching the size "
        "of the earth — no matter what sins they carry. This is the most expansive "
        "promise of forgiveness in the Sunnah.",
        "Abu Dharr narrated this Hadith Qudsi in which Allah personally addresses "
        "the believer burdened with sins. The earth-filling metaphor of forgiveness "
        "is designed to dissolve any sense that one's sins are too many for mercy.",
        [
            "The only condition for earth-filling forgiveness is not associating "
            "partners with Allah (shirk). Every other sin can be forgiven.",
            "This hadith is directed at the person who comes to Allah with sins "
            "filling the earth but with a sincere heart — Allah meets them with "
            "forgiveness of equal magnitude.",
            "Never let the accumulation of past sins be an excuse to delay repentance "
            "— the greater the sin, the greater the divine capacity to forgive it.",
        ],
        "This Hadith Qudsi is among the most powerful expressions of divine mercy "
        "in Islam and is cited alongside Surah Az-Zumar 39:53 as the ultimate "
        "invitation to repentance for the heavily burdened sinner.",
    ),
}


# ─── Automatic explanation derivation for hadiths without pre-written entries ─

def _derive_explanation(
    english: str,
    collection_display: str,
    hadith_num: int,
) -> tuple[str, str, list[str], str]:
    """Derive a minimal but coherent explanation from the hadith English text.

    Used as fallback when no pre-written entry exists (mainly for Bukhari sample).

    Returns:
        (teaches, context, lessons, related_principle)
    """
    text = english.strip()
    # Extract a key phrase — the core prophetic saying, if discernible
    # Look for the innermost quoted text
    inner_quotes = re.findall(r'["""]([^"""]{30,200})["""]', text)
    core_saying = inner_quotes[-1].strip() if inner_quotes else text[:150].strip()

    # Truncate for readability
    if len(core_saying) > 150:
        core_saying = core_saying[:147] + "..."

    teaches = (
        f"The Prophet ﷺ establishes in this narration: '{core_saying}' — "
        f"a direct guideline that defines both obligation and virtue for the believer."
    )
    context = (
        f"This hadith is recorded in {collection_display} (Hadith {hadith_num}), "
        "one of the most rigorously authenticated collections in the Sunnah. "
        "It was transmitted through multiple reliable companions."
    )
    lessons = [
        "Apply this teaching directly in your daily worship and conduct.",
        "The Prophet's ﷺ instruction here carries the weight of prophetic authority — "
        "following it is following the Sunnah.",
        "Reflect on how this teaching relates to your relationship with Allah and "
        "your duties toward other people.",
    ]
    related_principle = (
        "This hadith is part of the broader Sunnah that defines Islamic practice, "
        "underpinning the fiqh principle that the Prophet's ﷺ commands constitute "
        "obligatory guidance for the Muslim community."
    )
    return teaches, context, lessons, related_principle


# ─── Answer builder ───────────────────────────────────────────────────────────

def _build_explanation_answer(
    collection_key: str,
    hadith_num: int,
    arabic: str,
    english: str,
    grade: str,
    narrator: str,
    pre_written: dict[int, tuple[str, str, list[str], str]],
) -> str:
    """Build the structured hadith explanation answer.

    Args:
        collection_key: Internal key ('nawawi_40', 'hadith_qudsi', 'bukhari').
        hadith_num: Hadith number.
        arabic: Raw Arabic text (may be empty or include isnad).
        english: Full English text.
        grade: Hadith grade string.
        narrator: Extracted narrator name (may be empty).
        pre_written: Dict mapping hadith_num to pre-written explanation tuples.

    Returns:
        Multi-line formatted answer string.
    """
    display = _DISPLAY.get(collection_key, collection_key.replace("_", " ").title())
    clean_arabic = _clean_arabic(arabic)
    grade_str = grade.strip() if grade.strip() else "See source"

    # Narrator line
    if narrator:
        narrator_line = narrator
    else:
        # Try to extract from text
        narrator_line = _extract_narrator(english) or "Reported in the Sunnah"

    # Collection citation line
    citation = f"({display}, Hadith {hadith_num}) — Grade: {grade_str}"

    # Explanation content
    if hadith_num in pre_written:
        teaches, context, lessons, related = pre_written[hadith_num]
    else:
        teaches, context, lessons, related = _derive_explanation(
            english, display, hadith_num
        )

    # Build answer
    parts: list[str] = ["**Hadith Explanation**\n"]

    if clean_arabic:
        parts.append(clean_arabic + "\n")

    parts.append(f'The Prophet ﷺ said: "{english.strip()}"')
    parts.append(f"Narrated by: {narrator_line}")
    parts.append(citation + "\n")

    parts.append("**What This Hadith Teaches:**")
    parts.append(teaches + "\n")

    parts.append("**Context:**")
    parts.append(context + "\n")

    parts.append("**Key Lessons:**")
    for lesson in lessons:
        parts.append(f"• {lesson}")
    parts.append("")

    parts.append("**Related Principle:**")
    parts.append(related)

    return "\n".join(parts)


# ─── Question template generators ────────────────────────────────────────────

def _make_questions(
    collection_key: str,
    hadith_num: int,
    english: str,
    narrator: str,
    rng: random.Random,
    count: int,
) -> list[str]:
    """Generate `count` distinct question strings for a hadith.

    Args:
        collection_key: Internal key.
        hadith_num: Hadith number.
        english: Full English text of the hadith.
        narrator: Extracted narrator name.
        rng: Seeded random instance.
        count: Number of questions to generate.

    Returns:
        List of question strings (length == count).
    """
    display = _DISPLAY.get(collection_key, collection_key.replace("_", " ").title())
    snippet = _hadith_snippet(english, max_chars=40)
    narrator_str = narrator if narrator else "a companion of the Prophet ﷺ"

    # Build pool based on collection
    pool: list[str] = [
        f"Explain the hadith: '{snippet}'",
        f"What does this hadith mean: '{snippet}'",
        f"Explain Hadith {hadith_num} from {display}.",
        f"What is the teaching of Hadith {hadith_num} in {display}?",
        f"Break down the meaning of this hadith: '{narrator_str} narrated — {snippet}'",
    ]

    if collection_key == "nawawi_40":
        pool += [
            f"What lessons can we take from Hadith {hadith_num} of the Nawawi 40?",
            f"Explain Hadith {hadith_num} of the 40 Nawawi hadiths.",
            f"What principle does Nawawi Hadith {hadith_num} establish in Islamic ethics?",
            f"Summarise the meaning and importance of Nawawi Hadith {hadith_num}.",
        ]
    elif collection_key == "hadith_qudsi":
        pool += [
            f"This is a Hadith Qudsi — explain its meaning: '{snippet}'",
            f"What does Allah say in Hadith Qudsi {hadith_num}?",
            f"Explain the divine message in Hadith Qudsi number {hadith_num}.",
            f"What is the spiritual teaching of Hadith Qudsi {hadith_num}?",
        ]
    elif collection_key == "bukhari":
        pool += [
            f"What guidance does Sahih al-Bukhari Hadith {hadith_num} provide?",
            f"Explain the significance of Bukhari Hadith {hadith_num}.",
        ]

    # Shuffle and pick `count` unique items (cap at pool size)
    rng.shuffle(pool)
    unique: list[str] = []
    seen: set[str] = set()
    for q in pool:
        if q not in seen:
            unique.append(q)
            seen.add(q)
        if len(unique) == count:
            break

    # Pad if pool was too small (unlikely but safe)
    while len(unique) < count:
        unique.append(f"Explain Hadith {hadith_num} from {display}.")

    return unique[:count]


# ─── Collection loader ────────────────────────────────────────────────────────

def _load_hadiths(path: Path) -> list[dict[str, Any]]:
    """Load and return the hadiths list from a JSON file."""
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("hadiths", [])


# ─── Main entry point ─────────────────────────────────────────────────────────

def generate_hadith_explanation_pairs(seed: int = 42) -> list[dict[str, Any]]:
    """Generate Q&A training pairs for hadith-explanation type questions.

    Sources:
    - Nawawi 40 Hadith (all 42 entries, 4-5 templates each)
    - 40 Hadith Qudsi (all 40 entries, 4-5 templates each)
    - Sahih al-Bukhari first 50 by hadith_number (2-3 templates each)

    Target: 300-500 pairs total.

    Args:
        seed: Random seed for reproducible shuffling of templates.

    Returns:
        List of dicts with keys: instruction, input, output, metadata.
    """
    rng = random.Random(seed)
    pairs: list[dict[str, Any]] = []

    # ── Nawawi 40 ─────────────────────────────────────────────────────────────
    nawawi_hadiths = _load_hadiths(_NAWAWI_PATH)
    for h in nawawi_hadiths:
        num = h["hadith_number"]
        english = h.get("english_text", "").strip()
        if not english:
            continue

        arabic = h.get("arabic_text", "")
        grade = h.get("grade", "")
        narrator = _extract_narrator(english)

        answer = _build_explanation_answer(
            collection_key="nawawi_40",
            hadith_num=num,
            arabic=arabic,
            english=english,
            grade=grade,
            narrator=narrator,
            pre_written=_NAWAWI_EXPLANATIONS,
        )

        questions = _make_questions(
            collection_key="nawawi_40",
            hadith_num=num,
            english=english,
            narrator=narrator,
            rng=rng,
            count=4,  # 4-5 per hadith (use 4 to stay in 300-500 range)
        )

        for question in questions:
            pairs.append(
                {
                    "instruction": question,
                    "input": "",
                    "output": answer,
                    "metadata": {
                        "category": "hadith_explanation",
                        "collection": "nawawi_40",
                        "hadith_number": num,
                    },
                }
            )

    # ── Hadith Qudsi ──────────────────────────────────────────────────────────
    qudsi_hadiths = _load_hadiths(_QUDSI_PATH)
    for h in qudsi_hadiths:
        num = h["hadith_number"]
        english = h.get("english_text", "").strip()
        if not english:
            continue

        arabic = h.get("arabic_text", "")
        grade = h.get("grade", "")
        narrator = _extract_narrator(english)

        answer = _build_explanation_answer(
            collection_key="hadith_qudsi",
            hadith_num=num,
            arabic=arabic,
            english=english,
            grade=grade,
            narrator=narrator,
            pre_written=_QUDSI_EXPLANATIONS,
        )

        questions = _make_questions(
            collection_key="hadith_qudsi",
            hadith_num=num,
            english=english,
            narrator=narrator,
            rng=rng,
            count=4,  # 4-5 per hadith (use 4 to stay in 300-500 range)
        )

        for question in questions:
            pairs.append(
                {
                    "instruction": question,
                    "input": "",
                    "output": answer,
                    "metadata": {
                        "category": "hadith_explanation",
                        "collection": "hadith_qudsi",
                        "hadith_number": num,
                    },
                }
            )

    # ── Bukhari (first 50 by hadith_number) ───────────────────────────────────
    bukhari_hadiths = _load_hadiths(_BUKHARI_PATH)
    # Sort by hadith_number and take first 50 with valid English text
    bukhari_hadiths_sorted = sorted(
        bukhari_hadiths, key=lambda x: x.get("hadith_number", 0)
    )
    bukhari_sample: list[dict[str, Any]] = []
    for h in bukhari_hadiths_sorted:
        if len(bukhari_sample) >= 50:
            break
        if h.get("english_text", "").strip():
            bukhari_sample.append(h)

    for h in bukhari_sample:
        num = h["hadith_number"]
        english = h.get("english_text", "").strip()
        arabic = h.get("arabic_text", "")
        grade = h.get("grade", "")
        narrator = _extract_narrator(english)

        answer = _build_explanation_answer(
            collection_key="bukhari",
            hadith_num=num,
            arabic=arabic,
            english=english,
            grade=grade,
            narrator=narrator,
            pre_written={},  # No pre-written for Bukhari — use auto-derivation
        )

        questions = _make_questions(
            collection_key="bukhari",
            hadith_num=num,
            english=english,
            narrator=narrator,
            rng=rng,
            count=3,  # 2-3 per hadith
        )

        for question in questions:
            pairs.append(
                {
                    "instruction": question,
                    "input": "",
                    "output": answer,
                    "metadata": {
                        "category": "hadith_explanation",
                        "collection": "bukhari",
                        "hadith_number": num,
                    },
                }
            )

    rng.shuffle(pairs)
    return pairs


# ─── CLI smoke test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = generate_hadith_explanation_pairs()
    print(f"Generated {len(results)} hadith explanation pairs.")

    from collections import Counter
    coll_counts = Counter(p["metadata"]["collection"] for p in results)
    print("By collection:", dict(coll_counts))

    # Print a sample from each collection
    for target_coll in ("nawawi_40", "hadith_qudsi", "bukhari"):
        sample = next(
            (p for p in results if p["metadata"]["collection"] == target_coll), None
        )
        if sample:
            print(f"\n{'='*60}")
            print(f"SAMPLE [{target_coll}] Hadith {sample['metadata']['hadith_number']}")
            print(f"Q: {sample['instruction']}")
            print(f"A:\n{sample['output'][:600]}...")
