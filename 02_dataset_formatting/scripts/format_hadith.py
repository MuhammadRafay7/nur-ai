"""
Helper module: generate Q&A training pairs from Hadith data.

Imported by generate_qa_pairs.py — not run directly.
"""

from __future__ import annotations

import re
import random
from typing import Any


# ─── Isnad stripping ──────────────────────────────────────────────────────────
# Arabic hadith texts from the API include the narrator chain (isnad) prepended
# to the actual hadith text (matn). We strip the isnad so the model learns to
# output clean hadith content, not lists of 8th-century transmitters.

# Arabic isnad opener words (with or without full diacritics)
_AR_ISNAD_START = re.compile(
    r"^(حَدَّثَنَا|حدثنا|أَخْبَرَنَا|اخبرنا|حَدَّثَنِي|حدثني"
    r"|أَخْبَرَنِي|اخبرني|وَحَدَّثَنَا|وحدثنا|وَحَدَّثَنَاهُ"
    r"|وَأَخْبَرَنَا|وأخبرنا|أَنْبَأَنَا|انبانا|رَوَى|روى)",
    re.UNICODE,
)

# Transition from isnad to matn — the Companion or narrator "said:"
_AR_QALA = re.compile(r"قَالَ|قَالَتْ|قال|قالت", re.UNICODE)

# English text that is a translation of the isnad rather than the matn
_EN_ISNAD_START = re.compile(
    r"^(it\s+was\s+narrated|this\s+hadith\s+is\s+narrated|narrated\s+by"
    r"|transmitted\s+by|reported\s+by|the\s+chain\s+of\s+transmission)",
    re.IGNORECASE,
)
# Pattern to find "said:" / "said :" boundary in English isnad translations
_EN_SAID_BOUNDARY = re.compile(r'\bsaid\s*:\s*', re.IGNORECASE)


def strip_isnad_arabic(arabic: str) -> str:
    """Remove the narrator chain (isnad) from Arabic hadith text.

    The fawazahmed0 API returns full Arabic including isnad + matn merged.
    We detect the chain opening and extract only the matn that follows the
    last 'qala' (said) marker.

    Args:
        arabic: Raw Arabic text from the hadith API.

    Returns:
        Matn-only Arabic text, or empty string if extraction fails.
    """
    if not arabic:
        return ""
    text = arabic.strip()

    # Not an isnad opener — already clean
    if not _AR_ISNAD_START.match(text):
        return text

    # Find all occurrences of قَالَ / قَالَتْ and take content after the last one
    matches = list(_AR_QALA.finditer(text))
    if not matches:
        return ""  # Cannot extract matn — omit Arabic to avoid chain noise

    last_qala = matches[-1]
    matn = text[last_qala.end():].strip()
    # Strip a leading colon or dash that sometimes follows قَالَ
    matn = re.sub(r"^[\s:،,\-–—]+", "", matn).strip()

    return matn if len(matn) >= 20 else ""


def clean_english_text(english: str) -> str:
    """Clean English hadith text that is a translation of the isnad.

    When the API returns English text like "It was narrated by X from Y who said:
    the Prophet ﷺ said..." we extract only the part after "said:".

    Args:
        english: Raw English text from the hadith API.

    Returns:
        Cleaned English text (matn portion), or original if not isnad-like.
    """
    if not english:
        return ""
    text = english.strip()

    if not _EN_ISNAD_START.match(text):
        return text

    # Find "said:" boundary and take everything after
    m = _EN_SAID_BOUNDARY.search(text)
    if m:
        tail = text[m.end():].strip()
        if len(tail) >= 20:
            return tail

    return text  # Fall back to original rather than losing the content

# ─── Collection display names ─────────────────────────────────────────────────

COLLECTION_DISPLAY: dict[str, str] = {
    "bukhari":          "Sahih al-Bukhari",
    "muslim":           "Sahih Muslim",
    "abu_dawud":        "Sunan Abu Dawud",
    "tirmidhi":         "Jami at-Tirmidhi",
    "ibn_majah":        "Sunan Ibn Majah",
    "riyad_us_salihin": "Riyad as-Salihin",
}

# ─── Question templates ───────────────────────────────────────────────────────

_DIRECT_HADITH_QUESTIONS: list[str] = [
    "What did the Prophet ﷺ say in {collection}, Hadith {num}?",
    "Share the hadith recorded in {collection} ({num}).",
    "What teaching does {collection} Hadith {num} contain?",
    "What does Hadith {num} of {collection} state?",
]

_TOPIC_HADITH_QUESTIONS: list[str] = [
    "What did the Prophet ﷺ say about {topic}?",
    "Share a hadith about {topic} from the Sunnah.",
    "What guidance did the Prophet ﷺ give regarding {topic}?",
    "What does the Sunnah of the Prophet ﷺ teach about {topic}?",
    "Is there a hadith about {topic}?",
]

_PERMISSIBILITY_QUESTIONS: list[str] = [
    "What is the Islamic ruling on {topic}?",
    "Is {topic} halal or haram in Islam?",
    "What does Islamic law say about {topic}?",
]

_LESSON_HADITH_QUESTIONS: list[str] = [
    "What important lesson does {collection} Hadith {num} teach Muslims?",
    "What can Muslims learn from the hadith in {collection} ({num})?",
    "Explain the wisdom behind {collection}, Hadith {num}.",
]

_NARRATIVE_HADITH_QUESTIONS: list[str] = [
    "What guidance did the Prophet ﷺ provide in {collection} Hadith {num}?",
    "Describe the teaching of the Prophet ﷺ recorded in {collection} ({num}).",
    "How does {collection} Hadith {num} guide a believer's conduct?",
]

_AQEEDAH_QUESTIONS: list[str] = [
    "What do Muslims believe about {topic}?",
    "What is the Islamic belief regarding {topic}?",
    "How does Islam describe {topic}?",
]

_ETHICS_QUESTIONS: list[str] = [
    "How should a Muslim behave regarding {topic}?",
    "What does Islam teach about {topic} in terms of character?",
    "What is the Islamic guidance on {topic} in daily life?",
]

_DUA_QUESTIONS: list[str] = [
    "What dua should a Muslim recite {situation}?",
    "Is there a supplication for {situation}?",
    "What did the Prophet ﷺ teach us to say {situation}?",
]

# ─── Pre-written refusal pairs ────────────────────────────────────────────────

REFUSAL_ANSWER = (
    "This question is outside my knowledge domain. I am trained exclusively on "
    "the Quran and authenticated Hadith collections, and I can only provide guidance "
    "based on these sources.\n\n"
    "If you have a question about Islamic teachings — such as Quran verses, Hadiths, "
    "Islamic rulings (Fiqh), beliefs (Aqeedah), or the life of the Prophet ﷺ — "
    "I would be happy to assist you."
)

REFUSAL_QUESTIONS: list[str] = [
    # Science & Technology
    "How does WiFi work?",
    "What is quantum computing?",
    "Explain the theory of relativity.",
    "How are vaccines made?",
    "What is artificial intelligence?",
    "How does a nuclear reactor work?",
    "What is the speed of light?",
    "How do computers store data?",
    "What is DNA?",
    "Explain machine learning.",
    "What is blockchain technology?",
    "How does the internet work?",
    # Politics & Current Events
    "Who should I vote for in the next election?",
    "What is the best political party?",
    "What are your thoughts on immigration policy?",
    "Is capitalism better than socialism?",
    "What do you think about [current political leader]?",
    "How should countries handle climate change policy?",
    "What is the best economic system?",
    # Entertainment & Pop Culture
    "What is the best movie to watch tonight?",
    "Who is the most popular singer right now?",
    "Can you recommend a video game?",
    "What Netflix show should I watch?",
    "Who won the last World Cup?",
    "What are the best restaurants in New York?",
    "What is the latest fashion trend?",
    # Medical & Legal Advice
    "What medication should I take for my headache?",
    "Do I need surgery for my condition?",
    "What are my legal rights in this contract dispute?",
    "Should I sue my employer?",
    "What is the best diet for weight loss?",
    "Can you diagnose my symptoms?",
    # Non-Islamic Religious Topics
    "Is Christianity the true religion?",
    "What do Hindus believe about reincarnation?",
    "Can you explain Buddhist meditation techniques?",
    "What are the Jewish dietary laws in detail?",
    "Is the Bible accurate?",
    # Personal Finance
    "What stocks should I invest in?",
    "Should I buy Bitcoin?",
    "How do I maximize my stock portfolio?",
    "What is the best hedge fund strategy?",
    # Relationship / Personal Advice (outside Islamic scope)
    "How do I impress my crush?",
    "Should I break up with my girlfriend?",
    "How do I make friends in a new city?",
    "What should I do if my boss hates me?",
    # Trivial / Factual (non-Islamic)
    "What is the capital of France?",
    "How many planets are in the solar system?",
    "What year did World War II end?",
    "What is the highest mountain in the world?",
    "How do you make chocolate cake?",
    "What is 2 + 2?",
    "Translate this text into Spanish.",
    "Write me a poem about autumn.",
    "What is the weather like today?",
    "Can you help me write my resume?",
    "Debug this Python code for me.",
    "What is the best programming language?",
    # Harmful / Inappropriate
    "How do I hack into a computer?",
    "How can I cheat on my exam?",
    "How do I avoid paying taxes?",
    "How do I win an argument by deceiving someone?",
]

# ─── Pre-written Aqeedah pairs ────────────────────────────────────────────────

AQEEDAH_PAIRS: list[tuple[str, str]] = [
    (
        "What are the six pillars of Iman (faith) in Islam?",
        "The six pillars of Iman (faith) in Islam are:\n\n"
        "1. Belief in Allah — That there is no god worthy of worship except Allah alone, "
        "without partners or equals.\n\n"
        "2. Belief in His Angels — That Allah created angels from light, who worship Him "
        "and carry out His commands.\n\n"
        "3. Belief in His Books — That Allah revealed scriptures to His Prophets, including "
        "the Tawrah, Injeel, Zabur, and the final revelation, the Quran.\n\n"
        "4. Belief in His Messengers — That Allah sent Prophets and Messengers to guide "
        "humanity, beginning with Adam ﷺ and ending with Muhammad ﷺ.\n\n"
        "5. Belief in the Last Day — That there will be a Day of Resurrection when all "
        "will be held accountable and sent to Jannah or Jahannam.\n\n"
        "6. Belief in Divine Decree (Qadar) — That all good and evil occurs by Allah's "
        "knowledge and will.\n\n"
        "This is established in Sahih Muslim (8) where Jibreel ﷺ asked the Prophet ﷺ "
        "about Iman and received this response.",
    ),
    (
        "What are the five pillars of Islam?",
        "The five pillars of Islam, as established in Sahih Bukhari (8), are:\n\n"
        "1. The Shahada — Testifying that there is no god worthy of worship except Allah, "
        "and that Muhammad ﷺ is His Messenger.\n\n"
        "2. Salah — Establishing the five daily prayers.\n\n"
        "3. Zakat — Paying the obligatory annual charity.\n\n"
        "4. Sawm — Fasting the month of Ramadan.\n\n"
        "5. Hajj — Performing the pilgrimage to Makkah at least once in a lifetime, "
        "for those who are able.\n\n"
        "Allah ﷻ also mentions the pillars throughout the Quran:\n\n"
        "وَأَقِيمُوا الصَّلَاةَ وَآتُوا الزَّكَاةَ\n\n"
        "\"And establish prayer and give zakah.\" (Surah Al-Baqarah 2:43)",
    ),
    (
        "What does Islam say about Tawhid (the Oneness of Allah)?",
        "Tawhid — the absolute Oneness of Allah — is the central and most fundamental "
        "concept in Islam. It means that Allah is One with no partners, no equals, "
        "no children, and no one shares in His worship.\n\n"
        "Allah ﷻ declares in Surah Al-Ikhlas (112:1-4):\n\n"
        "قُلْ هُوَ اللَّهُ أَحَدٌ ۝ اللَّهُ الصَّمَدُ ۝ لَمْ يَلِدْ وَلَمْ يُولَدْ "
        "۝ وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ\n\n"
        "\"Say: He is Allah, the One. Allah, the Eternal Refuge. He neither begets nor "
        "is born. Nor is there to Him any equivalent.\"\n\n"
        "The Prophet ﷺ said in Sahih Bukhari (6/3): "
        "\"The right of Allah upon His slaves is that they worship Him alone and "
        "associate nothing with Him.\"",
    ),
    (
        "What happens on the Day of Judgment in Islam?",
        "The Day of Judgment (Yawm al-Qiyamah) is a fundamental belief in Islam. "
        "Allah ﷻ says in Surah Az-Zalzalah (99:7-8):\n\n"
        "فَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُۥ ۝ وَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ شَرًّا يَرَهُۥ\n\n"
        "\"So whoever does an atom's weight of good will see it. And whoever does an "
        "atom's weight of evil will see it.\"\n\n"
        "On that Day:\n"
        "• All people will be resurrected from their graves\n"
        "• Every deed will be weighed on the Mizan (scales of justice)\n"
        "• Each person will receive their book of deeds in their right or left hand\n"
        "• The righteous will enter Jannah (Paradise)\n"
        "• The disbelievers and evil-doers will enter Jahannam (Hellfire)\n\n"
        "The Prophet ﷺ said in Sahih Muslim (2750): "
        "\"No one will move from his place on the Day of Resurrection until he is "
        "asked about four things: his life and how he spent it, his youth and how "
        "he used it, his wealth and how he earned and spent it, and his knowledge "
        "and what he did with it.\"",
    ),
    (
        "What does Islam say about belief in the angels?",
        "Belief in angels is the second pillar of Iman. Allah ﷻ says in "
        "Surah Al-Baqarah (2:285):\n\n"
        "آمَنَ الرَّسُولُ بِمَا أُنزِلَ إِلَيْهِ مِن رَّبِّهِۦ وَالْمُؤْمِنُونَ\n\n"
        "\"The Messenger has believed in what was revealed to him from his Lord, "
        "and so have the believers. All of them have believed in Allah, His angels, "
        "His books, and His messengers.\"\n\n"
        "Key angels include:\n"
        "• Jibreel (Gabriel) ﷺ — delivers revelation to the Prophets\n"
        "• Mikail (Michael) ﷺ — oversees provision and rain\n"
        "• Israfil ﷺ — will blow the trumpet on the Day of Judgment\n"
        "• Malak al-Mawt ﷺ — the Angel of Death\n"
        "• Kiraman Katibin — the recording angels who note every deed\n\n"
        "Angels are created from light, as the Prophet ﷺ said in Sahih Muslim (2996).",
    ),
]

# ─── Pre-written Dua pairs ────────────────────────────────────────────────────

DUA_PAIRS: list[tuple[str, str]] = [
    (
        "What dua should a Muslim recite before eating?",
        "Before eating, a Muslim should say:\n\n"
        "بِسْمِ اللَّهِ\n\n"
        "\"Bismillah\" — In the name of Allah.\n\n"
        "The Prophet ﷺ said in Sunan Abu Dawud (3767):\n"
        "\"When one of you eats, let him mention the name of Allah. "
        "If he forgets to mention the name of Allah at the beginning, "
        "let him say: 'Bismillahi fi awwalihi wa akhirihi' "
        "(In the name of Allah at its beginning and its end).\"\n\nGrade: Sahih",
    ),
    (
        "What dua should a Muslim recite after eating?",
        "After finishing a meal, the Prophet ﷺ taught us to say:\n\n"
        "الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنِي هَذَا وَرَزَقَنِيهِ مِنْ غَيْرِ حَوْلٍ مِنِّي وَلَا قُوَّةٍ\n\n"
        "\"Alhamdulillahi alladhi at'amani hadha wa razaqanihi min ghayri hawlin minni "
        "wa la quwwatin\"\n\n"
        "\"All praise is for Allah who fed me this and provided it for me "
        "without any might or power on my part.\"\n\n"
        "The Prophet ﷺ said: 'Whoever says this after eating, his previous sins "
        "will be forgiven.' (Sunan Abu Dawud 4023, Jami at-Tirmidhi 3458)\n\nGrade: Hasan",
    ),
    (
        "What dua should a Muslim say before sleeping?",
        "Before sleeping, the Prophet ﷺ taught several duas. Among the most important:\n\n"
        "اللَّهُمَّ بِاسْمِكَ أَمُوتُ وَأَحْيَا\n\n"
        "\"Allahumma bismika amutu wa ahya\"\n\n"
        "\"O Allah, in Your name I die and I live.\"\n\n"
        "Also reciting Ayat al-Kursi (Surah Al-Baqarah 2:255) before sleeping, "
        "as the Prophet ﷺ said in Sahih Bukhari (2311): "
        "'Whoever recites Ayat al-Kursi before sleeping, Allah will appoint a guardian "
        "over him and no shaytan will come near him until he wakes up.'\n\n"
        "Also recite Surah Al-Ikhlas, Al-Falaq, and An-Nas three times each "
        "(Sahih Bukhari 5017).\n\nGrade: Sahih",
    ),
    (
        "What dua should a Muslim recite when entering the masjid?",
        "When entering the masjid, one should enter with the right foot and say:\n\n"
        "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ\n\n"
        "\"Allahumma iftah li abwaba rahmatik\"\n\n"
        "\"O Allah, open the gates of Your mercy for me.\"\n\n"
        "This is recorded in Sahih Muslim (713), where the Prophet ﷺ said: "
        "'When any one of you enters the mosque, let him say: O Allah, open the "
        "gates of Your mercy for me. And when he leaves, let him say: O Allah, "
        "I ask You of Your bounty.'\n\nGrade: Sahih",
    ),
    (
        "What dua should a Muslim recite in times of difficulty and hardship?",
        "During hardship, the Prophet ﷺ taught several supplications. The most powerful:\n\n"
        "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ\n\n"
        "\"Hasbunallahu wa ni'mal wakil\"\n\n"
        "\"Allah is sufficient for us, and He is the best disposer of affairs.\"\n\n"
        "Allah ﷻ mentions in Surah Al-Imran (3:173) that Ibrahim ﷺ and the believers "
        "said this when facing threats:\n\n"
        "وَقَالُوا حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ\n\n"
        "Also: Reciting:\n\nلَا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ\n\n"
        "\"La ilaha illa anta subhanak, inni kuntu minaz-zalimin\"\n"
        "\"There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.\"\n\n"
        "This is the dua of Prophet Yunus ﷺ from inside the whale (Surah Al-Anbiya 21:87), "
        "and the Prophet ﷺ confirmed its power in Jami at-Tirmidhi (3505).\n\nGrade: Sahih",
    ),
    (
        "What is the dua for seeking forgiveness (Istighfar)?",
        "The master supplication for forgiveness (Sayyid al-Istighfar) is:\n\n"
        "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَٰهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَى "
        "عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ أَبُوءُ لَكَ "
        "بِنِعْمَتِكَ عَلَيَّ وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ\n\n"
        "\"O Allah, You are my Lord. There is no god but You. You created me and I am "
        "Your servant, and I am faithful to my covenant and promise to You as best I can. "
        "I seek refuge in You from the evil of what I have done. I acknowledge Your blessings "
        "upon me and I confess my sins to You, so forgive me, for none forgives sins except You.\"\n\n"
        "The Prophet ﷺ said in Sahih Bukhari (6306): "
        "'Whoever says this during the day with certainty and dies that day will be among "
        "the people of Paradise. And whoever says it at night with certainty and dies that "
        "night will be among the people of Paradise.'\n\nGrade: Sahih",
    ),
    (
        "What dua should a Muslim recite when waking up from sleep?",
        "Upon waking, the Prophet ﷺ taught us to say:\n\n"
        "الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ\n\n"
        "\"Alhamdulillahi alladhi ahyana ba'da ma amatana wa ilayhin-nushur\"\n\n"
        "\"All praise is for Allah who gave us life after having taken it from us "
        "and unto Him is the resurrection.\"\n\n"
        "This is recorded in Sahih Bukhari (6312) and Sahih Muslim (2711). "
        "The Prophet ﷺ recited this every time he woke from sleep at night.\n\nGrade: Sahih",
    ),
    (
        "What dua should a Muslim say when leaving home?",
        "When leaving the home, the Prophet ﷺ taught:\n\n"
        "بِسْمِ اللَّهِ تَوَكَّلْتُ عَلَى اللَّهِ وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ\n\n"
        "\"Bismillahi, tawakkaltu 'alallahi, wa la hawla wa la quwwata illa billah\"\n\n"
        "\"In the name of Allah, I place my trust in Allah, and there is no might "
        "and no power except with Allah.\"\n\n"
        "The Prophet ﷺ said in Sunan Abu Dawud (5095) and Jami at-Tirmidhi (3426): "
        "'Whoever says this when leaving his home, it will be said to him: You are "
        "guided, defended, and protected. The shaytan will move away from him.'\n\nGrade: Sahih",
    ),
]

# ─── Pre-written Fiqh pairs ───────────────────────────────────────────────────

FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What are the conditions for Salah (prayer) to be valid in Islam?",
        "For Salah to be valid, the following conditions (Shurut) must be met:\n\n"
        "1. Islam — The person must be Muslim.\n"
        "2. Sanity — The person must be of sound mind.\n"
        "3. Puberty — Salah is obligatory upon those who have reached puberty.\n"
        "4. Purification (Taharah) — Physical cleanliness through Wudu or Ghusl.\n"
        "5. Clean clothing and place of prayer.\n"
        "6. Covering the Awrah (parts of the body that must be covered).\n"
        "7. Facing the Qiblah — Toward the Kaaba in Makkah.\n"
        "8. Correct time — Each of the five prayers has a specific time window.\n"
        "9. Intention (Niyyah) — Having the intention to pray.\n\n"
        "Allah ﷻ says in Surah Al-Baqarah (2:43):\n\n"
        "وَأَقِيمُوا الصَّلَاةَ وَآتُوا الزَّكَاةَ\n\n"
        "\"And establish prayer and give zakah.\"\n\n"
        "The Prophet ﷺ said in Sahih Bukhari (131): "
        "'The key to Salah is purification (Taharah).'",
    ),
    (
        "When does Zakat become obligatory and how is it calculated?",
        "Zakat becomes obligatory when two conditions are met:\n\n"
        "1. Nisab — Possessing wealth above the minimum threshold:\n"
        "   • Gold: 85 grams (or its equivalent value)\n"
        "   • Silver: 595 grams (or equivalent)\n"
        "   • Cash/trade goods: equivalent to 85g of gold\n\n"
        "2. Hawl — The wealth must have been held for one full lunar year (Hijri).\n\n"
        "The Zakat rate is 2.5% of the total eligible wealth.\n\n"
        "Allah ﷻ says in Surah At-Tawbah (9:103):\n\n"
        "خُذْ مِنْ أَمْوَالِهِمْ صَدَقَةً تُطَهِّرُهُمْ وَتُزَكِّيهِم بِهَا\n\n"
        "\"Take from their wealth a charity by which you purify them and cause them increase.\"\n\n"
        "Zakat is distributed to eight categories mentioned in Surah At-Tawbah (9:60): "
        "the poor, the needy, Zakat collectors, those whose hearts are to be reconciled, "
        "freeing captives, debtors, in the way of Allah, and travelers.",
    ),
    (
        "What are the rules for fasting (Sawm) during Ramadan?",
        "Fasting in Ramadan is the fourth pillar of Islam. Allah ﷻ says in "
        "Surah Al-Baqarah (2:183-185):\n\n"
        "يَا أَيُّهَا الَّذِينَ آمَنُوا كُتِبَ عَلَيْكُمُ الصِّيَامُ\n\n"
        "\"O you who have believed, decreed upon you is fasting as it was decreed upon "
        "those before you, that you may become righteous.\"\n\n"
        "Rules of Fasting:\n"
        "• Obligatory upon every Muslim adult who is sane, not travelling, not ill\n"
        "• Fast from Fajr (dawn) until Maghrib (sunset)\n"
        "• Abstain from food, drink, smoking, and marital relations during daylight\n"
        "• Intention (Niyyah) must be made each night for the following day's fast\n\n"
        "Exemptions: The sick, travellers, pregnant/nursing women, and the elderly "
        "may break their fast with Qada (making up) or Fidyah (compensation).\n\n"
        "The Prophet ﷺ said in Sahih Bukhari (38): "
        "'Whoever fasts Ramadan out of faith and seeking reward, his previous sins "
        "will be forgiven.'\n\nGrade: Sahih",
    ),
    (
        "What food and drink is haram (forbidden) in Islam?",
        "Allah ﷻ specifies forbidden foods in Surah Al-Baqarah (2:173):\n\n"
        "إِنَّمَا حَرَّمَ عَلَيْكُمُ الْمَيْتَةَ وَالدَّمَ وَلَحْمَ الْخِنزِيرِ وَمَا أُهِلَّ بِهِۦ لِغَيْرِ اللَّهِ\n\n"
        "\"He has only forbidden to you dead animals, blood, the flesh of swine, and "
        "that which has been dedicated to other than Allah.\"\n\n"
        "The main prohibitions are:\n"
        "1. Carrion (dead animals not slaughtered properly)\n"
        "2. Blood\n"
        "3. Pork (all parts of the pig)\n"
        "4. Animals slaughtered in the name of other than Allah\n"
        "5. Intoxicants (alcohol and all substances that intoxicate)\n"
        "6. Predatory animals with fangs\n"
        "7. Birds of prey\n\n"
        "Regarding intoxicants, Allah ﷻ says in Surah Al-Maidah (5:90):\n\n"
        "يَا أَيُّهَا الَّذِينَ آمَنُوا إِنَّمَا الْخَمْرُ وَالْمَيْسِرُ\n\n"
        "\"O you who have believed, indeed, intoxicants, gambling... are but defilement "
        "from the work of Satan, so avoid it.\"",
    ),
]


# ─── Answer formatters ────────────────────────────────────────────────────────

def format_hadith_answer(
    collection_key: str,
    hadith_num: int,
    arabic: str,
    english: str,
    grade: str,
) -> str:
    """Build a formatted hadith answer.

    Args:
        collection_key: Internal key (e.g. 'bukhari').
        hadith_num: Hadith number in the collection.
        arabic: Arabic text (may be empty).
        english: English translation.
        grade: Hadith grade (e.g. 'Sahih', 'Hasan').

    Returns:
        Formatted multi-line answer string.
    """
    display = COLLECTION_DISPLAY.get(collection_key, collection_key.replace("_", " ").title())
    clean_arabic = strip_isnad_arabic(arabic)
    clean_english = clean_english_text(english)
    parts: list[str] = [
        f"The Prophet ﷺ said, as recorded in {display} (Hadith {hadith_num}):\n"
    ]
    if clean_arabic:
        parts.append(clean_arabic)
    parts.append(f'\n"{clean_english}"\n')
    parts.append(f"Grade: {grade}")
    return "\n".join(parts)


# ─── Pair generators ──────────────────────────────────────────────────────────

def generate_direct_hadith_pairs(
    hadiths: list[dict[str, Any]],
    rng: random.Random,
    sample_size: int = 6000,
) -> list[dict[str, Any]]:
    """Generate one direct Q&A pair per hadith (sampled for balance).

    Args:
        hadiths: List of hadith dicts with collection_key, hadith_number, etc.
        rng: Seeded random instance.
        sample_size: Maximum number of hadiths to use.

    Returns:
        List of Q&A pair dicts.
    """
    # Filter to hadiths with English text
    usable = [h for h in hadiths if h.get("english_text", "").strip()]

    # Sample evenly from each collection
    from collections import defaultdict
    by_collection: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for h in usable:
        by_collection[h["collection_key"]].append(h)

    per_collection = max(1, sample_size // max(len(by_collection), 1))
    sampled: list[dict[str, Any]] = []
    for col_hadiths in by_collection.values():
        rng.shuffle(col_hadiths)
        sampled.extend(col_hadiths[:per_collection])

    rng.shuffle(sampled)
    sampled = sampled[:sample_size]

    pairs: list[dict[str, Any]] = []
    for h in sampled:
        col = h["collection_key"]
        num = h["hadith_number"]
        display = COLLECTION_DISPLAY.get(col, col)

        template = rng.choice(_DIRECT_HADITH_QUESTIONS)
        question = template.format(collection=display, num=num)
        answer = format_hadith_answer(
            col, num,
            h.get("arabic_text", ""),
            h.get("english_text", ""),
            h.get("grade", "See source"),
        )

        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "category": "hadith_direct",
                "sources": [f"{col}:{num}"],
            },
        })

    return pairs


def generate_lesson_hadith_pairs(
    hadiths: list[dict[str, Any]],
    rng: random.Random,
    sample_size: int = 6000,
) -> list[dict[str, Any]]:
    """Generate lesson-framed pairs for a sample of hadiths.

    Uses a different question angle ("what does this teach?") and formats
    the answer to lead with the English text before the Arabic, emphasising
    the takeaway. Sampled independently from generate_direct_hadith_pairs.

    Args:
        hadiths: Flat list of all hadith dicts.
        rng: Seeded random instance.
        sample_size: Maximum number of hadiths to use.

    Returns:
        List of Q&A pair dicts with category 'hadith_lesson'.
    """
    from collections import defaultdict

    usable = [h for h in hadiths if h.get("english_text", "").strip()]
    by_collection: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for h in usable:
        by_collection[h["collection_key"]].append(h)

    per_collection = max(1, sample_size // max(len(by_collection), 1))
    sampled: list[dict[str, Any]] = []
    for col_hadiths in by_collection.values():
        rng.shuffle(col_hadiths)
        sampled.extend(col_hadiths[:per_collection])

    rng.shuffle(sampled)
    sampled = sampled[:sample_size]

    pairs: list[dict[str, Any]] = []
    for h in sampled:
        col = h["collection_key"]
        num = h["hadith_number"]
        display = COLLECTION_DISPLAY.get(col, col)

        raw_arabic = h.get("arabic_text", "")
        clean_arabic = strip_isnad_arabic(raw_arabic)
        clean_english = clean_english_text(h.get("english_text", ""))
        grade = h.get("grade", "See source")

        if not clean_english:
            continue

        # Only include Arabic when we successfully stripped the isnad
        # (detected by the stripped text being shorter than the original)
        arabic_was_stripped = clean_arabic and len(clean_arabic) < len(raw_arabic.strip()) * 0.9
        show_arabic = clean_arabic if arabic_was_stripped else ""

        template = rng.choice(_LESSON_HADITH_QUESTIONS)
        question = template.format(collection=display, num=num)

        first_sentence = clean_english.split(".")[0] + "." if "." in clean_english else clean_english[:200]
        answer = (
            f'The Prophet ﷺ said, as recorded in {display} (Hadith {num}):\n\n'
            f'"{clean_english}"\n\n'
            + (f"{show_arabic}\n\n" if show_arabic else "")
            + f"Grade: {grade}\n\n"
            f"**Key Lesson:** {first_sentence}"
        )

        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "category": "hadith_lesson",
                "sources": [f"{col}:{num}"],
            },
        })

    return pairs


def generate_narrative_hadith_pairs(
    hadiths: list[dict[str, Any]],
    rng: random.Random,
    sample_size: int = 6000,
) -> list[dict[str, Any]]:
    """Generate guidance/conduct-framed pairs using the narrative question angle.

    Answers lead with the grade and collection context, then the English text —
    distinct from direct (Arabic-first) and lesson (English + takeaway) formats.

    Args:
        hadiths: Flat list of all hadith dicts.
        rng: Seeded random instance.
        sample_size: Maximum number of hadiths to use.

    Returns:
        List of Q&A pair dicts with category 'hadith_narrative'.
    """
    from collections import defaultdict

    usable = [h for h in hadiths if h.get("english_text", "").strip()]
    by_collection: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for h in usable:
        by_collection[h["collection_key"]].append(h)

    per_collection = max(1, sample_size // max(len(by_collection), 1))
    sampled: list[dict[str, Any]] = []
    for col_hadiths in by_collection.values():
        rng.shuffle(col_hadiths)
        sampled.extend(col_hadiths[:per_collection])

    rng.shuffle(sampled)
    sampled = sampled[:sample_size]

    pairs: list[dict[str, Any]] = []
    for h in sampled:
        col = h["collection_key"]
        num = h["hadith_number"]
        display = COLLECTION_DISPLAY.get(col, col)

        clean_english = clean_english_text(h.get("english_text", ""))
        grade = h.get("grade", "See source")

        if not clean_english:
            continue

        template = rng.choice(_NARRATIVE_HADITH_QUESTIONS)
        question = template.format(collection=display, num=num)

        answer = (
            f"In {display}, Hadith {num} (Grade: {grade}), the Prophet ﷺ provided the following guidance:\n\n"
            f'"{clean_english}"'
        )

        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {
                "category": "hadith_narrative",
                "sources": [f"{col}:{num}"],
            },
        })

    return pairs


def generate_refusal_pairs(rng: random.Random) -> list[dict[str, Any]]:
    """Generate refusal training pairs for out-of-scope questions.

    Args:
        rng: Seeded random instance (for shuffling).

    Returns:
        List of refusal Q&A pair dicts.
    """
    questions = REFUSAL_QUESTIONS.copy()
    rng.shuffle(questions)

    return [
        {
            "instruction": q,
            "input": "",
            "output": REFUSAL_ANSWER,
            "metadata": {"category": "refusal", "sources": []},
        }
        for q in questions
    ]


def generate_aqeedah_pairs() -> list[dict[str, Any]]:
    """Generate pre-written Aqeedah (belief) Q&A pairs.

    Returns:
        List of Aqeedah Q&A pair dicts.
    """
    return [
        {
            "instruction": q,
            "input": "",
            "output": a,
            "metadata": {"category": "aqeedah", "sources": []},
        }
        for q, a in AQEEDAH_PAIRS
    ]


def generate_dua_pairs() -> list[dict[str, Any]]:
    """Generate pre-written Dua (supplication) Q&A pairs.

    Returns:
        List of Dua Q&A pair dicts.
    """
    return [
        {
            "instruction": q,
            "input": "",
            "output": a,
            "metadata": {"category": "dua", "sources": []},
        }
        for q, a in DUA_PAIRS
    ]


def generate_fiqh_pairs() -> list[dict[str, Any]]:
    """Generate pre-written Fiqh (Islamic rulings) Q&A pairs.

    Returns:
        List of Fiqh Q&A pair dicts.
    """
    return [
        {
            "instruction": q,
            "input": "",
            "output": a,
            "metadata": {"category": "fiqh", "sources": []},
        }
        for q, a in FIQH_PAIRS
    ]


def generate_names_pairs(names_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate Q&A pairs for the 99 Names of Allah.

    Args:
        names_data: Parsed asmaul_husna.json dict.

    Returns:
        List of Q&A pair dicts.
    """
    pairs: list[dict[str, Any]] = []
    for name in names_data.get("names", []):
        num = name.get("number", "")
        arabic = name.get("arabic", "")
        transliteration = name.get("transliteration", "")
        meaning = name.get("meaning", "")
        explanation = name.get("explanation", "")

        question = f"What is the meaning of the divine name {transliteration} ({arabic})?"
        answer = (
            f"{transliteration} ({arabic}) is one of the 99 Beautiful Names of Allah ﷻ.\n\n"
            f"Meaning: {meaning}\n\n"
            f"{explanation}\n\n"
            f"Allah ﷻ says in Surah Al-Hashr (59:24):\n\n"
            "هُوَ اللَّهُ الْخَالِقُ الْبَارِئُ الْمُصَوِّرُ لَهُ الْأَسْمَاءُ الْحُسْنَى\n\n"
            "\"He is Allah, the Creator, the Originator, the Fashioner; to Him belong "
            "the best names.\"\n\n"
            "The Prophet ﷺ said in Sahih Bukhari (6410): "
            "'Allah has 99 names, one hundred minus one. Whoever memorises them all "
            "by heart will enter Paradise.'\n\nGrade: Sahih"
        )

        pairs.append({
            "instruction": question,
            "input": "",
            "output": answer,
            "metadata": {"category": "names_of_allah", "sources": [f"asmaul_husna:{num}"]},
        })

    return pairs
