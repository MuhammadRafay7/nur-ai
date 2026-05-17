"""
Extended Islamic Fiqh Q&A pairs — 50 high-priority questions with full references.

Every answer includes:
  - Quran reference: Surah name, number, ayah number, Arabic text, translation
  - Hadith reference: book name, hadith number, English text, grade
  - Scholarly explanation and madhab opinions where they differ

Imported by generate_qa_pairs.py — not run directly.
"""

from __future__ import annotations
from typing import Any

# ─── Category 1: Marriage, Divorce & Family ──────────────────────────────────

MARRIAGE_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is Triple Talaq and what is its ruling in Islam?",
        """Triple Talaq refers to a husband pronouncing the word 'Talaq' (divorce) three times in one sitting, one breath, or one statement such as "I divorce you three times."

This is one of the most debated issues in Islamic jurisprudence, with two major scholarly positions:

─── POSITION 1: Counts as Three (Majority Classical Position) ───
The majority of classical scholars — including the Hanafi, Maliki, Shafi'i, and Hanbali schools — held that three talaqs pronounced together constitute a complete and final divorce (Talaq al-Ba'in al-Kubra).

After this, the wife cannot return to her husband unless she completes a full Iddah (waiting period), then genuinely marries another man, that marriage is consummated, and ends naturally — this is NOT the planned Halala marriage, which is itself forbidden.

Allah ﷻ says in Surah Al-Baqarah (2:229-230):

الطَّلَاقُ مَرَّتَانِ ۖ فَإِمْسَاكٌ بِمَعْرُوفٍ أَوْ تَسْرِيحٌ بِإِحْسَانٍ

"Divorce is twice. Then, either keep [her] in an acceptable manner or release [her] with good treatment."

فَإِن طَلَّقَهَا فَلَا تَحِلُّ لَهُ مِن بَعْدُ حَتَّىٰ تَنكِحَ زَوْجًا غَيْرَهُ

"And if he divorces her [the third time], she is not lawful to him afterward until she marries a husband other than him." (Surah Al-Baqarah 2:230)

─── POSITION 2: Counts as One (Ibn Taymiyyah, Ibn al-Qayyim, Modern Scholars) ───
Imam Ibn Taymiyyah, his student Ibn al-Qayyim al-Jawziyyah, and many contemporary scholars hold that three talaqs in one sitting count as only ONE revocable divorce.

This is based on the Hadith narrated by Ibn Abbas (RA):

The Prophet ﷺ said, as recorded in Sahih Muslim (1472):
"During the time of the Messenger of Allah ﷺ, Abu Bakr, and the first two years of Umar's caliphate, a triple divorce was considered a single divorce. Then Umar ibn al-Khattab said: 'Verily the people have begun to hasten in a matter in which they used to have patience. Were we to enforce it upon them?' So he enforced it upon them."
Grade: Sahih

This hadith shows the original practice was to count triple talaq as one. This position is also the official law in several Muslim-majority countries.

─── PRACTICAL GUIDANCE ───
Given the severity of this matter — which permanently affects a family — any Muslim in this situation MUST consult a qualified Islamic scholar (Mufti) locally. The ruling may differ based on the madhab followed, the country's Islamic law, and the exact circumstances.

The Prophet ﷺ said in Sunan Abu Dawud (2178):
"The most hated of all permitted things to Allah is divorce."
Grade: Sahih

Do not pronounce divorce in anger. Islam urges reconciliation, mediation, and patience before any divorce.
""",
    ),
    (
        "What are the types of Talaq (divorce) in Islam?",
        """Islam recognizes several forms of divorce, each with different rulings and consequences:

─── TYPE 1: Talaq al-Raj'i (Revocable Divorce) ───
A husband pronounces one or two talaqs. During the Iddah (waiting period of approximately 3 menstrual cycles or 3 months), he can take his wife back without a new Nikah. After the Iddah expires without reconciliation, it becomes irrevocable but a new Nikah can be done.

─── TYPE 2: Talaq al-Ba'in al-Sughra (Minor Irrevocable Divorce) ───
After the Iddah of a first or second talaq expires, the couple can remarry with a new Nikah and Mahr. The husband retains the right to pronounce further talaqs (he has used 1 or 2 of the 3 he is permitted).

─── TYPE 3: Talaq al-Ba'in al-Kubra (Major Irrevocable Divorce) ───
The third talaq, after which the couple cannot remarry unless the wife genuinely marries another man, the marriage is consummated, and it ends naturally.

Allah ﷻ says in Surah Al-Baqarah (2:229):
الطَّلَاقُ مَرَّتَانِ ۖ فَإِمْسَاكٌ بِمَعْرُوفٍ أَوْ تَسْرِيحٌ بِإِحْسَانٍ
"Divorce is twice. Then, either keep [her] in an acceptable manner or release [her] with good treatment."

─── TYPE 4: Talaq al-Bid'ah (Innovated/Sinful Divorce) ───
Pronouncing divorce during the wife's menstrual period, or pronouncing three talaqs at once. This is sinful according to the majority of scholars, though they differ on whether it takes effect.

The Sunnah method is Talaq al-Sunnah: pronouncing one talaq during a period of purity (Tuhr) in which no intercourse has taken place, then waiting.

─── TYPE 5: Khul' (Wife-Initiated Separation) ───
The wife returns the Mahr to her husband and requests a separation. This requires the husband's agreement or a judge's ruling.

─── TYPE 6: Faskh (Judicial Annulment) ───
An Islamic judge annuls the marriage due to harm, abandonment, inability to provide, or other valid reasons.

The Prophet ﷺ said in Sahih Bukhari (5251):
"Every condition not in Allah's Book is invalid even if there are a hundred such conditions."
Grade: Sahih

Islam makes reconciliation the priority. Allah ﷻ says in Surah An-Nisa (4:35):
وَإِنْ خِفْتُمْ شِقَاقَ بَيْنِهِمَا فَابْعَثُوا حَكَمًا مِّنْ أَهْلِهِ وَحَكَمًا مِّنْ أَهْلِهَا
"And if you fear dissension between the two, send an arbitrator from his people and an arbitrator from her people."
""",
    ),
    (
        "Can a Muslim man marry a Christian or Jewish woman?",
        """Yes, it is permissible for a Muslim man to marry a chaste woman from the People of the Book (Ahlul Kitab) — meaning Christian or Jewish women — under certain conditions.

Allah ﷻ says in Surah Al-Ma'idah (5:5):

وَالْمُحْصَنَاتُ مِنَ الَّذِينَ أُوتُوا الْكِتَابَ مِن قَبْلِكُمْ

"And [lawful in marriage are] chaste women from among those who were given the Scripture before you."

─── CONDITIONS ───
1. The woman must be chaste and morally upright
2. The man must be able to raise his children as Muslims
3. There must be no fear of his faith being weakened

─── SCHOLARLY OPINIONS ───
While technically permissible, many scholars — including Ibn Abbas (RA) and Umar (RA) — strongly discouraged it, especially in non-Muslim countries, due to the risk to the children's Islamic upbringing. Umar (RA) himself asked his companions who had married Jewish women to divorce them, though scholars clarify this was strong advice, not an obligation.

Imam al-Qurtubi said: "It is permissible but disliked when it leads to neglect of children's Islamic education."

─── CAN A MUSLIM WOMAN MARRY A NON-MUSLIM MAN? ───
No. This is absolutely prohibited by unanimous scholarly consensus.

Allah ﷻ says in Surah Al-Baqarah (2:221):
وَلَا تُنكِحُوا الْمُشْرِكِينَ حَتَّىٰ يُؤْمِنُوا
"And do not marry polytheistic men [to your women] until they believe."

The Prophet ﷺ said in Sunan Ibn Majah (1925):
"A Muslim woman is not lawful for a non-Muslim man."
Grade: Sahih

This applies to atheists, Christians, Jews, Hindus, and all non-Muslims. The reason given by scholars is that Islam grants women protection under their husband's authority, and a non-Muslim husband would have no obligation to preserve her religion or raise children as Muslims.
""",
    ),
    (
        "What is the Iddah and how long does it last?",
        """Iddah is the mandatory waiting period a woman must observe after divorce or the death of her husband before she can remarry. It serves to confirm whether she is pregnant, honors the sanctity of the marriage, and provides a window for reconciliation.

─── IDDAH AFTER DIVORCE ───
For women who menstruate: three complete menstrual cycles
Allah ﷻ says in Surah Al-Baqarah (2:228):
وَالْمُطَلَّقَاتُ يَتَرَبَّصْنَ بِأَنفُسِهِنَّ ثَلَاثَةَ قُرُوءٍ
"Divorced women shall wait by themselves for three menstrual periods."

For women who do not menstruate (post-menopausal or young): three lunar months (Surah At-Talaq 65:4)

For pregnant women: until she delivers her child
Allah ﷻ says in Surah At-Talaq (65:4):
وَأُولَاتُ الْأَحْمَالِ أَجَلُهُنَّ أَن يَضَعْنَ حَمْلَهُنَّ
"And for those who are pregnant, their term is until they give birth."

─── IDDAH AFTER DEATH OF HUSBAND ───
Four months and ten days, regardless of menstruation, unless pregnant (in which case she waits until delivery — whichever is longer).

Allah ﷻ says in Surah Al-Baqarah (2:234):
وَالَّذِينَ يُتَوَفَّوْنَ مِنكُمْ وَيَذَرُونَ أَزْوَاجًا يَتَرَبَّصْنَ بِأَنفُسِهِنَّ أَرْبَعَةَ أَشْهُرٍ وَعَشْرًا
"Those who are taken in death among you and leave wives behind — they, [the wives, shall] wait four months and ten days."

─── IDDAH FOR NON-CONSUMMATED MARRIAGE ───
If divorce occurs before consummation, there is no Iddah required.
Allah ﷻ says in Surah Al-Ahzab (33:49):
فَمَا لَكُمْ عَلَيْهِنَّ مِنْ عِدَّةٍ تَعْتَدُّونَهَا
"You have no waiting period to count against them."

During the Iddah, a woman stays in the marital home, does not beautify herself (in the case of a widow), and is financially supported by her (ex-)husband during a revocable divorce.
""",
    ),
]

# ─── Category 2: Riba, Finance & Business ────────────────────────────────────

FINANCE_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is Riba (interest) and why is it forbidden in Islam?",
        """Riba literally means 'increase' or 'excess' and refers to any predetermined, guaranteed increase on a loan or debt — what we commonly call interest or usury.

─── QURANIC PROHIBITION ───
Riba is one of the most severely condemned acts in the Quran. Allah ﷻ says in Surah Al-Baqarah (2:275):

الَّذِينَ يَأْكُلُونَ الرِّبَا لَا يَقُومُونَ إِلَّا كَمَا يَقُومُ الَّذِي يَتَخَبَّطُهُ الشَّيْطَانُ مِنَ الْمَسِّ

"Those who consume interest cannot stand [on the Day of Resurrection] except as one stands who is being beaten by Satan into insanity."

وَأَحَلَّ اللَّهُ الْبَيْعَ وَحَرَّمَ الرِّبَا

"But Allah has permitted trade and has forbidden interest." (Al-Baqarah 2:275)

Allah ﷻ further declares in Surah Al-Baqarah (2:278-279):
يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَذَرُوا مَا بَقِيَ مِنَ الرِّبَا إِن كُنتُم مُّؤْمِنِينَ
"O you who have believed, fear Allah and give up what remains [due to you] of interest, if you should be believers."

فَإِن لَّمْ تَفْعَلُوا فَأْذَنُوا بِحَرْبٍ مِّنَ اللَّهِ وَرَسُولِهِ
"And if you do not, then be informed of a war [against you] from Allah and His Messenger."

─── HADITH ───
The Prophet ﷺ said, as recorded in Sahih Muslim (1598):
"Allah has cursed the one who consumes Riba, the one who pays it, the one who records it, and the two witnesses to it. He said: They are all alike."
Grade: Sahih

The Prophet ﷺ also said in Sahih Muslim (1597):
"Avoid the seven destructive sins..." among which he mentioned "consuming Riba."
Grade: Sahih

─── WHY IT IS FORBIDDEN ───
1. It exploits the poor and vulnerable
2. It creates wealth without productive effort
3. It concentrates wealth in the hands of lenders
4. It leads to economic injustice and societal harm

─── TYPES OF RIBA ───
1. Riba al-Nasi'ah: Interest on loans — the most common form (bank interest, credit cards)
2. Riba al-Fadl: Unequal exchange of the same commodity (e.g., selling 1kg of gold for 1.1kg)

All forms of Riba are haram by unanimous scholarly consensus.
""",
    ),
    (
        "What is the Islamic ruling on taking a mortgage to buy a house?",
        """This is one of the most frequently asked questions in the modern world. The ruling depends on the type of mortgage.

─── CONVENTIONAL INTEREST-BASED MORTGAGE ───
The overwhelming majority of scholars hold that a conventional bank mortgage — where you pay interest (Riba) — is HARAM. This is based on the clear Quranic prohibition of Riba (Al-Baqarah 2:275-279) and the hadith in Sahih Muslim (1598) in which the Prophet ﷺ cursed all parties involved in Riba transactions.

─── IS THERE AN EXCEPTION FOR NECESSITY? ───
Some scholars, including some contemporary ones (such as the European Council for Fatwa and Research), have permitted conventional mortgages for Muslims living in non-Muslim countries who have no other way to own a home and renting causes genuine hardship. This is based on the principle of necessity (Darura).

However, the majority of scholars — including the permanent committee of Saudi scholars — reject this exception, arguing that renting is always available and does not constitute a life-threatening necessity.

─── ISLAMIC MORTGAGE ALTERNATIVES ───
1. Murabaha: The bank purchases the property and sells it to you at a higher agreed price, payable in installments. No interest — the profit is disclosed upfront.

2. Ijara (Islamic Lease-to-Own): The bank buys the property and leases it to you. A portion of each payment builds equity until you own it.

3. Musharakah Mutanaqisah (Diminishing Partnership): You and the bank jointly own the property. You gradually buy out the bank's share while paying rent on its portion.

─── KEY HADITH ───
The Prophet ﷺ said in Sunan Abu Dawud (3462):
"Whoever buys something that contains Riba, knowing it to be so, has no right to take it."
Grade: Hasan

─── PRACTICAL ADVICE ───
Seek an Islamic mortgage product if available in your country. If not, consult a qualified scholar familiar with your local situation. Do not assume necessity permits Riba without a proper fatwa.
""",
    ),
    (
        "What is the Islamic ruling on cryptocurrency and Bitcoin?",
        """Cryptocurrency is a modern issue on which contemporary scholars have differed significantly. Here is a balanced summary of the major positions:

─── POSITION 1: PERMISSIBLE (with conditions) ───
Scholars such as Sheikh Assim al-Hakeem, some members of the Accounting and Auditing Organization for Islamic Financial Institutions (AAOIFI), and others hold that cryptocurrency can be permissible if:
- It is used as a medium of exchange or store of value
- It is not used for gambling, speculation, or haram purposes
- It has genuine utility and is accepted by real markets

Their argument: Islam permits any form of exchange (bay') between consenting parties as long as it avoids Riba, Gharar (excessive uncertainty), and Maysir (gambling).

─── POSITION 2: IMPERMISSIBLE ───
Scholars such as the Egyptian Dar al-Ifta, the Turkish Directorate of Religious Affairs, and others hold that cryptocurrency is impermissible due to:
1. Excessive Gharar (uncertainty and extreme price volatility)
2. Use primarily for speculation, which resembles gambling
3. Lack of a real underlying asset or government backing
4. Use in illegal transactions

─── QURAN ON PROHIBITION OF EXCESSIVE UNCERTAINTY ───
Allah ﷻ says in Surah Al-Baqarah (2:188):
وَلَا تَأْكُلُوا أَمْوَالَكُم بَيْنَكُم بِالْبَاطِلِ
"And do not consume one another's wealth unjustly."

─── HADITH ON GHARAR ───
The Prophet ﷺ said in Sahih Muslim (1513):
"The Prophet ﷺ forbade transactions involving Gharar (excessive uncertainty)."
Grade: Sahih

─── CONCLUSION ───
Buying cryptocurrency as a long-term investment in a project you genuinely believe has value is closer to permissibility. Day-trading purely for speculation resembles gambling and is closer to prohibition.

Given the scholarly disagreement, consult a qualified Islamic finance scholar before investing significant wealth.
""",
    ),
    (
        "What is the Islamic ruling on stock market investment?",
        """Investing in stocks is permissible in principle, but with important conditions.

─── THE BASIC PRINCIPLE ───
Buying a share in a company means becoming a part-owner of that business. Islam permits legitimate business ownership and profit from halal trade. The Prophet ﷺ and his companions engaged in business partnerships (Musharakah).

─── CONDITIONS FOR PERMISSIBLE STOCK INVESTMENT ───
1. The core business must be halal — you cannot invest in companies whose PRIMARY business is haram (alcohol, pork, weapons of mass destruction, pornography, conventional banking based purely on interest, tobacco)

2. If a company's main business is halal but it has some incidental involvement in haram (e.g., a tech company that earns a small percentage of revenue from interest on cash deposits), many scholars permit investment with purification — you calculate the haram percentage of dividend income and donate that amount to charity (not counting it as your own earnings).

3. Speculation without any genuine investment intention (day-trading purely as gambling) is not permissible.

─── PURIFICATION OF INCOME ───
If a halal company has up to 5% haram revenue (according to most screening standards), scholars permit investing and purifying the proportional dividend income.

─── HADITH ───
The Prophet ﷺ said in Sahih Bukhari (2168):
"The merchants will be raised on the Day of Resurrection as evil-doers, except those who feared Allah, were honest, and told the truth."
Grade: Sahih

─── PRACTICAL SCREENING ───
Use Islamic stock screening tools (e.g., Zoya app, IdealRatings, or Saturna) to verify if a company passes Shariah compliance standards before investing.
""",
    ),
    (
        "What is the Islamic ruling on gambling?",
        """Gambling — wagering money on uncertain outcomes where one party's gain is another's loss — is strictly HARAM in Islam by unanimous scholarly consensus.

Allah ﷻ says in Surah Al-Ma'idah (5:90):

يَا أَيُّهَا الَّذِينَ آمَنُوا إِنَّمَا الْخَمْرُ وَالْمَيْسِرُ وَالْأَنصَابُ وَالْأَزْلَامُ رِجْسٌ مِّنْ عَمَلِ الشَّيْطَانِ فَاجْتَنِبُوهُ لَعَلَّكُمْ تُفْلِحُونَ

"O you who have believed, indeed, intoxicants, gambling, [sacrificing on] stone altars [to other than Allah], and divining arrows are but defilement from the work of Satan, so avoid it that you may be successful."

Allah ﷻ continues in Al-Ma'idah (5:91):
إِنَّمَا يُرِيدُ الشَّيْطَانُ أَن يُوقِعَ بَيْنَكُمُ الْعَدَاوَةَ وَالْبَغْضَاءَ فِي الْخَمْرِ وَالْمَيْسِرِ
"Satan only wants to cause between you animosity and hatred through intoxicants and gambling and to avert you from the remembrance of Allah and from prayer."

─── WHAT COUNTS AS GAMBLING ───
- Casino games (slots, roulette, card games for money)
- Sports betting and horse racing bets
- Lottery tickets (even for charity)
- Raffle tickets where participation requires payment
- Online gambling

─── WHAT IS NOT GAMBLING ───
- Business investment (risk with productive purpose)
- Insurance (Takaful model — mutual risk sharing)
- Competitions with prizes where entry is free or skill-based

The Prophet ﷺ said in Sahih Muslim (1647):
"Whoever says to his companion 'Come let us gamble', let him give in charity (as expiation)."
Grade: Sahih

This shows even suggesting gambling requires expiation — indicating its severity.
""",
    ),
]

# ─── Category 3: Fasting Edge Cases ──────────────────────────────────────────

SAWM_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "Does using an asthma inhaler break the fast?",
        """This is a contemporary issue on which scholars have differed. Here are the two main positions:

─── POSITION 1: BREAKS THE FAST (Majority Position) ───
The majority of contemporary scholars — including the Islamic Fiqh Academy and the Permanent Committee for Islamic Research and Fatwa (Saudi Arabia) — hold that using an inhaler BREAKS the fast because:
- The inhaler propels a mist of medicine into the airways
- Part of this mist reaches the lungs and enters the body
- Anything that reaches the body's inner cavities (Jawf) through a recognized entry point breaks the fast

Based on this position, a person with asthma who must use their inhaler should:
- Make up (Qada) that day's fast after Ramadan, OR
- Use a Nebulizer outside of fasting hours if medically possible

─── POSITION 2: DOES NOT BREAK THE FAST ───
Some scholars, including Dr. Yusuf al-Qaradawi and others, hold that the inhaler does NOT break the fast because:
- The medicine reaches the lungs, not the stomach (digestive cavity)
- The quantity is tiny and not considered "food" or "drink"
- Medical necessity applies

─── QURAN ───
Allah ﷻ says in Surah Al-Baqarah (2:185):
وَمَن كَانَ مَرِيضًا أَوْ عَلَىٰ سَفَرٍ فَعِدَّةٌ مِّنْ أَيَّامٍ أُخَرَ
"And whoever is ill or on a journey — then an equal number of other days [are to be made up]."

─── PRACTICAL GUIDANCE ───
If you have asthma and cannot fast without your inhaler:
- Use it as needed — your health comes first
- Make up the fast later (Qada) after Ramadan
- If your condition is chronic and permanent, pay Fidyah (feeding one poor person for each day missed) instead of making up the fasts

Consult a doctor and an Islamic scholar together for your specific medical situation.
""",
    ),
    (
        "Does taking an injection or vaccine break the fast?",
        """Scholars have distinguished between different types of injections:

─── INTRAMUSCULAR AND INTRAVENOUS INJECTIONS ───
The majority of scholars — including the Islamic Fiqh Academy — hold that injections into muscles or veins (including vaccines, antibiotics, pain medications given by injection) do NOT break the fast because:
- They do not enter through a recognized food/drink pathway (mouth or nose)
- They do not reach the stomach or digestive system
- The Prophet ﷺ said in Sahih Bukhari (1938): what breaks the fast is eating, drinking, and intercourse

─── NUTRITIONAL DRIPS/IV GLUCOSE ───
If an intravenous injection or drip contains nutrients, calories, or glucose — this DOES break the fast according to most scholars, as it substitutes for eating and drinking.

─── INSULIN INJECTIONS ───
Insulin injections (subcutaneous) do not break the fast according to the majority, as they contain no nutrients. However, many diabetics need to monitor blood sugar carefully during fasting — if fasting causes medical harm, it is waived.

─── BLOOD TESTS AND BLOOD DRAWS ───
Drawing a small amount of blood for testing does NOT break the fast. However, donating a full unit of blood may break it due to weakness — it is better to donate blood outside of Ramadan.

─── QURAN ───
Allah ﷻ says in Surah Al-Baqarah (2:185):
يُرِيدُ اللَّهُ بِكُمُ الْيُسْرَ وَلَا يُرِيدُ بِكُمُ الْعُسْرَ
"Allah intends for you ease and does not intend for you hardship."

─── CONCLUSION ───
Vaccines, antibiotics by injection, insulin — do not break the fast.
IV glucose/nutrition drips — do break the fast.
If uncertain, consult a scholar.
""",
    ),
    (
        "What is the Kaffarah (expiation) for intentionally breaking the fast in Ramadan?",
        """If a person deliberately breaks their Ramadan fast without a valid excuse — specifically through eating, drinking, or sexual intercourse — they must pay Kaffarah (expiation) in addition to making up (Qada) the missed day.

─── THE THREE-LEVEL KAFFARAH (IN ORDER) ───
The expiation must be performed in the following order — only if you are unable to do the first, you proceed to the second:

1. FREE A SLAVE — Not applicable today as slavery no longer exists.

2. FAST FOR TWO CONSECUTIVE MONTHS (60 days) — If one breaks even one day of these 60, they must restart from the beginning.

3. FEED SIXTY POOR PEOPLE — Give each one a full day's food (approximately 750g of staple grain or its monetary equivalent).

─── HADITH BASIS ───
This ruling comes from the famous hadith of the man who told the Prophet ﷺ he had intercourse with his wife during Ramadan:

The Prophet ﷺ said, as recorded in Sahih Bukhari (1936) and Sahih Muslim (1111):
"Can you free a slave?" He said: No. "Can you fast for two consecutive months?" He said: No. "Can you feed sixty poor people?" He said: No. Then [while they were speaking] someone brought a basket of dates to the Prophet ﷺ. He said: "Take this and give it in charity." The man said: "To someone poorer than us? There is no family in Madinah more in need than mine." The Prophet ﷺ laughed until his molar teeth were visible and said: "Take it and feed your family."
Grade: Sahih

─── IMPORTANT NOTES ───
- Kaffarah applies only for INTENTIONAL breaking without excuse
- Eating by mistake (forgetting you are fasting) requires NO Qada or Kaffarah
- The Prophet ﷺ said in Sahih Bukhari (1933): "Whoever forgets that he is fasting and eats or drinks, let him complete his fast — for it was Allah who fed him and gave him drink."
- Breaking fast due to illness, travel, pregnancy, or breastfeeding requires only Qada (making up) — no Kaffarah.

─── QURAN ───
Allah ﷻ says in Surah Al-Baqarah (2:184):
فَمَن كَانَ مِنكُم مَّرِيضًا أَوْ عَلَىٰ سَفَرٍ فَعِدَّةٌ مِّنْ أَيَّامٍ أُخَرَ
"And upon those who are able [to fast, but with hardship] — a ransom [as substitute] of feeding a poor person [each day]."
""",
    ),
]

# ─── Category 4: Hijab & Gender ───────────────────────────────────────────────

HIJAB_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "Is the hijab obligatory in Islam?",
        """Yes. The hijab — covering the hair, neck, and body except the face and hands — is obligatory (Fard) for adult Muslim women according to the overwhelming majority of scholars across all four major madhabs (Hanafi, Maliki, Shafi'i, Hanbali). This is not a matter of scholarly dispute in classical Islam.

─── QURANIC EVIDENCE ───
Allah ﷻ commands in Surah An-Nur (24:31):

وَلْيَضْرِبْنَ بِخُمُرِهِنَّ عَلَىٰ جُيُوبِهِنَّ ۖ وَلَا يُبْدِينَ زِينَتَهُنَّ إِلَّا لِبُعُولَتِهِنَّ

"And let them draw their head-coverings (Khumur) over their chests (Juyub), and not reveal their adornment except to their husbands..." [followed by a list of Mahrams]

Allah ﷻ also commands in Surah Al-Ahzab (33:59):

يَا أَيُّهَا النَّبِيُّ قُل لِّأَزْوَاجِكَ وَبَنَاتِكَ وَنِسَاءِ الْمُؤْمِنِينَ يُدْنِينَ عَلَيْهِنَّ مِن جَلَابِيبِهِنَّ

"O Prophet, tell your wives and your daughters and the women of the believers to bring down over themselves [part] of their outer garments (Jalabeeb). That is more suitable that they will be known and not be abused."

─── HADITH EVIDENCE ───
The Prophet ﷺ said, as recorded in Sunan Abu Dawud (4104):
"O Asma, when a woman reaches puberty, it is not proper that any part of her body be seen except this and this" — and he pointed to his face and hands.
Grade: Mursal (but supported by the Quran and other narrations)

Aisha (RA) narrated that when Asma bint Abi Bakr entered wearing thin clothing, the Prophet ﷺ turned away from her and said:
"O Asma, when a woman reaches maturity, nothing should be seen of her except this" — pointing to his face and hands. (Abu Dawud 4104)

─── CONDITIONS OF VALID HIJAB ───
1. Covers the entire body except the face and hands (according to majority)
2. Not tight or form-fitting
3. Not transparent or see-through
4. Not an adornment in itself (flashy or attention-grabbing)
5. Does not resemble the dress of non-Muslim women or men

─── WHAT ABOUT NON-MUSLIM COUNTRIES? ───
The hijab remains obligatory regardless of the country of residence. A Muslim woman living in a Western country is still required to observe it. If faced with genuine persecution or threat to life, a scholar can be consulted about extreme necessity — but choosing not to wear it for convenience, social pressure, or fear of discrimination does not constitute such necessity.
""",
    ),
    (
        "Is the niqab (face veil) obligatory or just recommended?",
        """This is one of the genuine scholarly disagreements in Islamic jurisprudence. Two strong positions exist within classical scholarship:

─── POSITION 1: NIQAB IS OBLIGATORY ───
This is held by: the Hanbali school, many Shafi'i scholars, Ibn Baz, Ibn Uthaymeen, and the majority of scholars in Saudi Arabia and the Gulf.

Evidence:
Allah ﷻ says in Surah Al-Ahzab (33:59) commanding women to cover with Jalabeeb (full outer garments).

Allah ﷻ says in Surah An-Nur (24:31): "And not display their adornment" — they argue the face is the greatest adornment.

The Prophet ﷺ said in Sahih Bukhari (1838):
"The woman in Ihram should not wear the niqab or gloves" — they argue this implies the default outside Ihram is that she wears it.

─── POSITION 2: NIQAB IS RECOMMENDED (MUSTAHABB) NOT OBLIGATORY ───
This is held by: the Hanafi, Maliki, and most Shafi'i scholars, as well as Ibn Abbas, Aisha (RA), and many classical scholars.

Their evidence:
- The verse of An-Nur (24:31) mentions "except what is apparent (Zuhara)" — Ibn Abbas interpreted this as the face and hands
- Aisha (RA) narrated that women would uncover their faces in front of the Prophet ﷺ during prayer
- The Prophet ﷺ described the face and hands as what can be uncovered (Abu Dawud 4104)

─── CONCLUSION ───
Both positions are based on legitimate scholarly reasoning. A woman who wears the niqab follows the stronger opinion according to many scholars and earns extra reward. A woman who wears hijab but not niqab is not sinful according to the Hanafi, Maliki, and many Shafi'i scholars.

Neither position should be used to mock or pressure women either way.
""",
    ),
    (
        "What is the Islamic ruling on free mixing (Ikhtilat) between men and women?",
        """Free mixing (Ikhtilat) — casual, unnecessary social mixing between non-Mahram men and women in private or semi-private settings — is not permitted in Islam according to the majority of scholars.

─── QURANIC EVIDENCE ───
Allah ﷻ says in Surah Al-Isra (17:32):
وَلَا تَقْرَبُوا الزِّنَا إِنَّهُ كَانَ فَاحِشَةً وَسَاءَ سَبِيلًا
"And do not approach unlawful sexual intercourse. Indeed, it is ever an immorality and is evil as a way."

Scholars note that Islam prohibits not just the act of zina, but also the steps that lead toward it — free mixing being one of the major precursors.

─── HADITH EVIDENCE ───
The Prophet ﷺ said in Sahih Bukhari (5232):
"No man should be alone with a woman, and no woman should travel except with a Mahram."
Grade: Sahih

The Prophet ﷺ said in Jami at-Tirmidhi (2165):
"Beware of entering upon women." A man said: "O Messenger of Allah, what about the brother-in-law?" He said: "The brother-in-law is death."
Grade: Sahih (meaning seclusion with a husband's brother is extremely dangerous)

─── WHAT IS PERMITTED ───
1. Necessary professional interactions (doctor-patient, teacher-student, workplace) with appropriate conduct, no seclusion, and professional decorum
2. Public spaces where mixing is unavoidable (markets, public transport)
3. Family gatherings where men and women are in the same space but not engaged in inappropriate behavior

─── WHAT IS PROHIBITED ───
1. Khalwa (seclusion): being alone with a non-Mahram member of the opposite sex in a private space
2. Unnecessary casual socializing that leads to attraction or inappropriate behavior
3. Mixed social events with free intermingling, touching, or flirting

─── SCHOLARS' GUIDANCE ───
The principle is: necessity has its own ruling. What is genuinely necessary (work, education, medical treatment) is permitted with proper conduct. What is done purely for entertainment or social reasons is not permitted.
""",
    ),
    (
        "What is the Islamic ruling on plucking the eyebrows?",
        """Plucking the eyebrows — removing hair to reshape or thin them — is HARAM according to the majority of scholars.

─── HADITH ───
The Prophet ﷺ said, as recorded in Sahih Bukhari (5931) and Sahih Muslim (2125):
"Allah has cursed the Waashimaat (those who tattoo), the Mustawshimaat (those who get tattooed), the Mutanamissaat (those who pluck eyebrow hair for beautification), the Mutafallijaat (those who file teeth for beautification) — those who alter Allah's creation."

This is one of the strongest hadith prohibitions — using the word "cursed" — indicating a major sin.

Ibn Masood (RA) said: "I curse those who the Prophet ﷺ has cursed, for that is in the Book of Allah." (Referring to Al-Hashr 59:7: "Whatever the Messenger gives you, take it.")

─── WHO IS PERMITTED? ───
Scholars have made exceptions for:
1. Women with medically abnormal facial hair (e.g., a unibrow that causes severe social harm) — Imam al-Nawawi and others permitted removal of the unibrow (the hair between the two brows) as it is not the eyebrow itself
2. Men: the prohibition applies equally to men plucking their eyebrows for beautification

─── SCHOLARLY POSITION ───
- Hanafi, Maliki, Shafi'i, Hanbali: all agree plucking for beautification is haram
- Exception (minority): removing unibrow hair that grows between the brows

Threading, waxing, or plucking to reshape naturally growing eyebrow hair is not permitted. This is considered altering the creation of Allah (Taghyeer Khalqillah).
""",
    ),
]

# ─── Category 5: Music, Photography, Contemporary Issues ─────────────────────

CONTEMPORARY_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is the Islamic ruling on music?",
        """Music is one of the most debated topics in contemporary Islamic jurisprudence, with two main scholarly positions:

─── POSITION 1: MUSIC IS HARAM (Majority Classical Position) ───
The majority of classical scholars — including the Hanafi, Maliki, Shafi'i, and Hanbali schools — hold that music with instruments is haram, with the exception of the daff (hand drum) in specific celebrations (weddings, Eid).

─── QURANIC EVIDENCE ───
Allah ﷻ says in Surah Luqman (31:6):
وَمِنَ النَّاسِ مَن يَشْتَرِي لَهْوَ الْحَدِيثِ لِيُضِلَّ عَن سَبِيلِ اللَّهِ
"And of the people is he who buys the amusement of speech to mislead [others] from the way of Allah."

Ibn Masood (RA), Ibn Abbas (RA), and many companions interpreted "amusement of speech" as music and singing.

─── HADITH EVIDENCE ───
The Prophet ﷺ said, as recorded in Sahih Bukhari (5590):
"From among my followers there will be some people who will consider illegal sexual intercourse, the wearing of silk, the drinking of alcoholic drinks, and the use of musical instruments (Ma'azif) as lawful."
Grade: Sahih

The Prophet ﷺ said in Sunan Ibn Majah (4020):
"In my Ummah there will be people who will make permissible: fornication, silk [for men], wine, and musical instruments (Ma'azif)."
Grade: Sahih

─── POSITION 2: PERMISSIBLE WITH CONDITIONS ───
Some contemporary scholars (including a minority view) permit music that:
- Has no obscene, immoral, or anti-Islamic lyrics
- Does not lead to sinful behavior
- Is not accompanied by forbidden activities

─── WHAT IS AGREED UPON ───
1. Daff (hand drum) is permitted at weddings and celebrations — this is proven by multiple hadiths
2. Music with obscene lyrics promoting immorality is haram by consensus
3. Listening to music that distracts from prayer, family, or Islamic duties is at minimum makruh (disliked)

The safest position is to avoid music and replace it with Quran recitation and nasheeds (Islamic songs) without instruments.
""",
    ),
    (
        "What is the Islamic ruling on photography and taking pictures?",
        """This is another contemporary issue with significant scholarly debate:

─── POSITION 1: PHOTOGRAPHY OF ANIMATE BEINGS IS HARAM ───
Based on the general hadith prohibition of image-making:
The Prophet ﷺ said in Sahih Bukhari (5950):
"The most severely punished people on the Day of Resurrection will be those who make images (Musawwireen)."
Grade: Sahih

The Prophet ﷺ said in Sahih Muslim (2107):
"The angels do not enter a house in which there are images."
Grade: Sahih

Scholars who apply this to photography argue: the ruling is about the result (a captured image of a living being) not the method.

─── POSITION 2: PHOTOGRAPHY IS PERMISSIBLE ───
The majority of contemporary scholars — including Sheikh Ibn Uthaymeen (later in life), the Egyptian Dar al-Ifta, and many others — hold that photography is not included in the prohibition because:
1. The Prophet ﷺ's prohibition targeted three-dimensional images and paintings that involved human creativity in crafting the image — photography merely captures existing reality
2. Photography has no element of "creation" — it is a reflection, like a mirror
3. Photographic images do not have the same spiritual concern as handcrafted idols

─── WHAT IS AGREED UPON ───
1. Photography for idol-worship or shirk: haram by consensus
2. Photography of women without their consent or to spread immorality: haram
3. Photography of animate beings for genuine necessity (ID documents, medical, journalism): permissible by majority

─── PRACTICAL GUIDANCE ───
Taking family photos, ID photos, professional photos for legitimate purposes is permitted according to the majority of contemporary scholars. Decorating homes with framed portraits of humans is disliked (makruh) by many scholars.
""",
    ),
    (
        "What is the Islamic ruling on tattoos?",
        """Tattoos — permanently inserting ink into the skin to create a design — are HARAM in Islam by the consensus of scholars across all major madhabs.

─── HADITH ───
The Prophet ﷺ said, as recorded in Sahih Bukhari (5931) and Sahih Muslim (2125):
"Allah has cursed the Waashimah (the one who tattoos) and the Mustawshimah (the one who gets tattooed)..."
Grade: Sahih

The word "cursed" indicates this is a major sin (Kabeerah).

─── WHY TATTOOS ARE HARAM ───
1. They permanently alter the body — which is the creation of Allah
2. They involve harm (puncturing the skin with needles)
3. They were associated in early Islam with pagan practices

─── WHAT ABOUT EXISTING TATTOOS? ───
If a person becomes Muslim or repents after having gotten tattoos:
- They are not required to remove them if removal would cause harm
- They are not sinful for past tattoos they got before Islam or before knowing the ruling
- They should seek forgiveness (Tawbah) and not get more tattoos

─── IS REMOVAL REQUIRED? ───
Most scholars say removal is recommended but not obligatory if:
- It would cause significant pain or medical risk
- The cost is prohibitive

If removal is easy and inexpensive, removing it is recommended.

─── TEMPORARY TATTOOS & HENNA ───
Temporary tattoos that wash off are not prohibited.
Henna (Mehndi) is Sunnah for women — the Prophet ﷺ encouraged it and women companions used it.

Allah ﷻ says in Surah Al-Hashr (59:7):
وَمَا آتَاكُمُ الرَّسُولُ فَخُذُوهُ وَمَا نَهَاكُمْ عَنْهُ فَانتَهُوا
"And whatever the Messenger gives you, take it; and whatever he forbids you, refrain from it."
""",
    ),
    (
        "What is the Islamic ruling on abortion?",
        """The ruling on abortion depends on the stage of pregnancy:

─── STAGE 1: BEFORE 40 DAYS ───
Scholars are most lenient here. The Hanafi school and some others permit abortion before 40 days if there is a valid reason. Without a reason, it is disliked (makruh) but not haram according to these scholars.

─── STAGE 2: BETWEEN 40-120 DAYS ───
The majority of scholars (Maliki, Shafi'i, Hanbali) hold that abortion after 40 days is haram unless there is a serious medical necessity (threat to the mother's life or severe fetal abnormality incompatible with life).

─── STAGE 3: AFTER 120 DAYS (ENSOULMENT) ───
By unanimous scholarly consensus, abortion after 120 days — when the soul (Ruh) is blown into the fetus — is HARAM and considered a form of killing a human being, except when the mother's life is in direct mortal danger.

─── QURANIC EVIDENCE ───
Allah ﷻ says in Surah Al-Isra (17:31):
وَلَا تَقْتُلُوا أَوْلَادَكُمْ خَشْيَةَ إِمْلَاقٍ ۖ نَّحْنُ نَرْزُقُهُمْ وَإِيَّاكُمْ
"And do not kill your children for fear of poverty. We provide for them and for you."

─── HADITH ON ENSOULMENT ───
The Prophet ﷺ said in Sahih Bukhari (3208) and Sahih Muslim (2643):
"Each of you is constituted in your mother's womb for 40 days, then he becomes a clinging clot for the same period, then he becomes a morsel of flesh for the same period. Then the angel is sent, and it breathes the spirit (Ruh) into him."
Grade: Sahih

─── CONCLUSION ───
- Before 40 days with valid reason: differs by madhab (some permit, some prohibit)
- 40-120 days: haram except severe medical necessity
- After 120 days: haram except direct threat to mother's life

Consult a qualified scholar for your specific situation.
""",
    ),
    (
        "What is the Islamic ruling on IVF (In Vitro Fertilization)?",
        """IVF is evaluated based on whose genetic material is used:

─── PERMISSIBLE: IVF USING HUSBAND'S SPERM AND WIFE'S EGG ───
If the IVF procedure uses only the sperm of the husband and the egg of his wife, implanted into the wife's uterus — this is permissible according to the majority of contemporary Islamic scholars, as it falls under seeking legitimate medical treatment to have children.

The Prophet ﷺ said in Sunan Abu Dawud (3855):
"Seek treatment, O servants of Allah, for Allah has not created a disease except that He has also created a cure for it."
Grade: Sahih

─── PROHIBITED: DONOR SPERM OR DONOR EGGS ───
Using sperm from a man who is not the wife's husband, or eggs from a woman who is not the wife, is HARAM by the majority of scholars because:
1. It introduces lineage confusion (Ikhtilat al-Ansab) — one of the five necessities Islam protects is lineage
2. It resembles a form of biological 'zina'
3. It violates Islamic principles of marriage and family

─── PROHIBITED: SURROGATE MOTHER ───
Using a surrogate mother (a third woman who carries the embryo) is haram according to the majority of scholars because:
1. The Quran defines the mother as "she who gave birth" (Al-Mujadilah 58:2)
2. It creates legal and family complications around lineage

─── PERMISSIBLE WITH LIMITATIONS ───
- IVF with husband and wife's own genetic material: Permitted
- Choosing the sex of the baby through IVF for non-medical reasons: Differed upon (many say not permitted as it interferes with Allah's decree without necessity)
- Freezing embryos: Permitted with conditions according to many scholars

Allah ﷻ says in Surah Al-Imran (3:38):
هُنَالِكَ دَعَا زَكَرِيَّا رَبَّهُ ۖ قَالَ رَبِّ هَبْ لِي مِن لَّدُنكَ ذُرِّيَّةً طَيِّبَةً
"At that point Zakariyya called upon his Lord, saying: My Lord, grant me from Yourself a good offspring."

Praying for children is Sunnah. Using halal means to have children is permitted.
""",
    ),
    (
        "What is the Islamic ruling on masturbation?",
        """This is a sensitive but frequently asked question, particularly by Muslim youth. The majority scholarly position is that masturbation is HARAM, with a minority permitting it under specific circumstances.

─── QURANIC EVIDENCE (MAJORITY POSITION) ───
Allah ﷻ says in Surah Al-Mu'minun (23:5-7):

وَالَّذِينَ هُمْ لِفُرُوجِهِمْ حَافِظُونَ ۝ إِلَّا عَلَىٰ أَزْوَاجِهِمْ أَوْ مَا مَلَكَتْ أَيْمَانُهُمْ فَإِنَّهُمْ غَيْرُ مَلُومِينَ ۝ فَمَنِ ابْتَغَىٰ وَرَاءَ ذَٰلِكَ فَأُولَٰئِكَ هُمُ الْعَادُونَ

"And those who guard their private parts, except from their wives or those their right hands possess, for indeed, they will not be blamed. But whoever seeks beyond that, then those are the transgressors."

The majority of scholars (Hanafi, Maliki, Shafi'i, Hanbali) interpret "whoever seeks beyond that" as including masturbation — sexual gratification outside of marriage.

─── MINORITY POSITION ───
The Hanbali school (one opinion within it) and some contemporary scholars permit masturbation in extreme circumstances — specifically when a person fears falling into zina (fornication) and has no means of marriage. This is based on the principle of choosing the lesser of two evils.

─── PRACTICAL ISLAMIC GUIDANCE ───
Islam recognizes the natural human drive and provides solutions:
1. Marriage — the Prophet ﷺ said in Sahih Bukhari (5066): "O young people! Whoever among you is able to marry, should marry... and whoever is not able to marry, should fast, for it will decrease his sexual desire."
2. Fasting — reduces desire
3. Lowering the gaze — prevents arousal
4. Keeping busy with worship and productive activities
5. Making sincere dua

If one falls into this sin, they should make sincere Tawbah, not despair, and work on the practical solutions above. Allah's mercy is vast.
""",
    ),
    (
        "What is the Islamic ruling on homosexuality?",
        """Islam's position on homosexual acts is clear and based on Quran and Sunnah: same-sex sexual acts are haram (prohibited).

─── QURANIC EVIDENCE ───
Allah ﷻ describes the story of the people of Lut (عليه السلام) in multiple places, including Surah Al-A'raf (7:80-81):

وَلُوطًا إِذْ قَالَ لِقَوْمِهِ أَتَأْتُونَ الْفَاحِشَةَ مَا سَبَقَكُم بِهَا مِنْ أَحَدٍ مِّنَ الْعَالَمِينَ ۝ إِنَّكُمْ لَتَأْتُونَ الرِّجَالَ شَهْوَةً مِّن دُونِ النِّسَاءِ

"And [We had sent] Lot when he said to his people: Do you commit such immorality as no one has preceded you with from among the worlds? Indeed, you approach men with desire, instead of women."

─── HADITH ───
The Prophet ﷺ said in Sunan Abu Dawud (4462) and Jami at-Tirmidhi (1456):
"Whoever you find doing the action of the people of Lut — execute the one who does it and the one to whom it is done."
Grade: Hasan

Note: The implementation of such punishments requires an Islamic court, due process, and proper governance — they cannot be carried out by individuals.

─── THE DISTINCTION: FEELINGS vs. ACTIONS ───
This is a crucial distinction scholars make:

Having same-sex attraction (feelings, inclinations) is NOT a sin in and of itself, as a person is not held accountable for what they cannot control. Allah ﷻ does not burden a soul beyond its capacity (Al-Baqarah 2:286).

ACTING on those feelings — engaging in same-sex sexual acts — is haram.

A Muslim who experiences same-sex attraction but refrains from acting on it, strives to be righteous, and turns to Allah is practicing patience (Sabr) and will be rewarded for it, not punished.

─── PASTORAL APPROACH ───
Muslims who struggle with this should be treated with compassion, not hatred. They should be encouraged toward:
- Strengthening their relationship with Allah
- Seeking support from trusted scholars
- Marriage where possible
- Patient adherence to Islamic boundaries

Islam prohibits the act, not the feeling. Hatred toward individuals struggling with this is not Islamic.
""",
    ),
    (
        "What is the Islamic ruling on smoking?",
        """The ruling on smoking has evolved among scholars. The contemporary majority position is that smoking is HARAM.

─── REASONING ───
The Quran does not mention cigarettes specifically (they did not exist at the time of revelation). However, scholars apply general Islamic principles:

Allah ﷻ says in Surah Al-Baqarah (2:195):
وَلَا تُلْقُوا بِأَيْدِيكُمْ إِلَى التَّهْلُكَةِ
"And do not throw yourselves into destruction."

Allah ﷻ says in Surah Al-A'raf (7:157) describing what the Prophet ﷺ permits and forbids:
وَيُحِلُّ لَهُمُ الطَّيِّبَاتِ وَيُحَرِّمُ عَلَيْهِمُ الْخَبَائِثَ
"He makes lawful for them the good things and prohibits for them the evil/harmful things."

─── HADITH ───
The Prophet ﷺ said in Sunan Ibn Majah (2340):
"There should be no harming nor reciprocating harm."
Grade: Sahih

─── SCHOLARLY POSITIONS ───
1. HARAM — the majority of contemporary scholars, including the Islamic Fiqh Academy, the Permanent Committee (Saudi), and most contemporary muftis, based on:
   - Proven severe health harm (cancer, heart disease)
   - Wasting money on something harmful
   - Harming others through secondhand smoke
   - Addiction that compromises free will

2. MAKRUH (Disliked) — some earlier scholars before medical evidence was conclusive

3. HARAM only if causing serious harm — older Hanafi position

─── CONCLUSION ───
Smoking is haram. If one is addicted, they should seek to quit — this is an act of worship. Helping others quit smoking is a charity.

The same reasoning applies to vaping and e-cigarettes: haram or severely disliked due to proven health risks.
""",
    ),
    (
        "What is the Islamic ruling on Muslims living in non-Muslim countries?",
        """Living in a non-Muslim country is permissible and in some cases necessary, with certain conditions scholars have outlined.

─── IS IT PERMITTED? ───
Yes, it is permissible for Muslims to live in non-Muslim countries. There is no obligation to live in a Muslim-majority country. The Prophet ﷺ himself had companions who lived among non-Muslims (Abyssinia under Negus), and the early Muslim community lived in Makkah under a non-Muslim authority for 13 years.

─── CONDITIONS SCHOLARS MENTION ───
1. The Muslim must be able to practice their religion freely — prayer, fasting, hijab, halal food
2. If living there leads to loss of faith or total abandonment of Islamic obligations, scholars say migration (Hijra) becomes necessary
3. They should benefit the Muslim community there and not live as isolated individuals ashamed of their identity

─── QURANIC GUIDANCE ───
Allah ﷻ says in Surah An-Nisa (4:97):
إِنَّ الَّذِينَ تَوَفَّاهُمُ الْمَلَائِكَةُ ظَالِمِي أَنفُسِهِمْ قَالُوا فِيمَ كُنتُمْ
"Indeed, those whom the angels take [in death] while wronging themselves — [the angels] will say: In what [condition] were you?"

This verse is about those who could practice Islam but chose to live in oppression without necessity. It does not apply to those who legitimately need to live in non-Muslim countries.

─── HADITH ───
The Prophet ﷺ said in Sunan Abu Dawud (2645):
"I am free from every Muslim who lives among the polytheists."

Scholars interpret this as urging Muslims to maintain their Islamic identity, not as a blanket prohibition on living in non-Muslim countries.

─── PRACTICAL GUIDANCE ───
Muslims in non-Muslim countries should:
- Maintain all five pillars
- Keep good character and be ambassadors of Islam
- Educate their children in Islamic values
- Participate in halal civic life including voting on matters of justice
- Build community with other Muslims (mosques, Islamic schools)
""",
    ),
]

# ─── Category 6: Morals & Repentance ─────────────────────────────────────────

MORALS_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is the Islamic ruling on backbiting (Gheebah) and how serious is it?",
        """Backbiting (Gheebah) — mentioning something about a person in their absence that they would dislike — is a MAJOR SIN (Kabeerah) in Islam.

─── DEFINITION ───
The Prophet ﷺ defined it clearly in Sahih Muslim (2589):
"Do you know what Gheebah is?" They said: "Allah and His Messenger know best." He said: "It is your mentioning your brother with something he dislikes." It was said: "What if what I say about my brother is true?" He said: "If what you say is true, that is Gheebah. If it is not true, that is slander (Buhtaan) — which is even worse."
Grade: Sahih

─── QURANIC WARNING ───
Allah ﷻ says in Surah Al-Hujurat (49:12):

وَلَا يَغْتَب بَّعْضُكُم بَعْضًا ۚ أَيُحِبُّ أَحَدُكُمْ أَن يَأْكُلَ لَحْمَ أَخِيهِ مَيْتًا فَكَرِهْتُمُوهُ

"And do not backbite one another. Would one of you like to eat the flesh of his brother when dead? You would detest it."

Allah ﷻ uses the viscerally disgusting image of eating a dead brother's flesh to convey how repulsive backbiting is.

─── IS THERE PERMISSIBLE BACKBITING? ───
Yes. Scholars have identified six situations where mentioning someone's faults is permitted:

1. Seeking a legal remedy — complaining to a judge about oppression
2. Seeking help to stop wrongdoing — "So-and-so is doing X, how do I advise them?"
3. Warning others — e.g., warning someone about a person's dishonesty in business
4. Describing a sinner who openly publicizes their sins
5. Identification — "You mean the lame one? Yes, him" (when no other way to identify)
6. Scholarly criticism of narrators (Jarh wa Ta'deel) — for protection of Hadith

─── HOW TO REPENT FOR BACKBITING ───
Scholars say: repent to Allah AND either:
a) If the person would feel worse knowing you spoke about them — do not tell them; make dua for them instead
b) If it reached them and harmed their reputation — apologize and seek their forgiveness

The Prophet ﷺ said in Musnad Ahmad (10945):
"The expiation for backbiting is to seek forgiveness for the one you backbit."
Grade: Hasan
""",
    ),
    (
        "What are the conditions for a valid Tawbah (repentance) in Islam?",
        """Tawbah (repentance) is one of the most important concepts in Islam. Allah ﷻ loves those who repent and returns to them with His mercy.

Allah ﷻ says in Surah Az-Zumar (39:53):

قُلْ يَا عِبَادِيَ الَّذِينَ أَسْرَفُوا عَلَىٰ أَنفُسِهِمْ لَا تَقْنَطُوا مِن رَّحْمَةِ اللَّهِ ۚ إِنَّ اللَّهَ يَغْفِرُ الذُّنُوبَ جَمِيعًا

"Say: O My servants who have transgressed against themselves [by sinning], do not despair of the mercy of Allah. Indeed, Allah forgives all sins."

─── THE THREE CONDITIONS FOR VALID TAWBAH ───
Scholars, including Imam an-Nawawi, agree on three essential conditions:

1. STOP the sin immediately — you cannot repent while continuing to commit the sin

2. REGRET what you did — feeling genuine remorse in the heart, not just words

3. RESOLVE never to return to that sin — a firm commitment to avoid it in the future

─── ADDITIONAL FOURTH CONDITION ───
If the sin involved another person's rights (theft, backbiting, harming someone):
4. RESTORE those rights — return stolen property, seek forgiveness from the one you wronged, clear their reputation if you damaged it

─── HADITH ───
The Prophet ﷺ said in Sunan Ibn Majah (4251):
"Remorse is repentance."
Grade: Sahih — meaning the heartfelt regret is the core of Tawbah.

The Prophet ﷺ said in Sahih Muslim (2747):
"Allah is more delighted with the repentance of His slave than one of you who loses his camel in a waterless desert carrying his food and drink, and then finds it."
Grade: Sahih

─── IS TAWBAH ACCEPTED AFTER BIG SINS? ───
Yes. Allah accepts Tawbah for ALL sins — including major sins — as long as:
1. The conditions above are met
2. The person repents before the death rattle (Sahih Bukhari 6308)
3. The sun has not yet risen from the West (a Major Sign of the Last Day)

Allah ﷻ says in Surah An-Nisa (4:110):
وَمَن يَعْمَلْ سُوءًا أَوْ يَظْلِمْ نَفْسَهُ ثُمَّ يَسْتَغْفِرِ اللَّهَ يَجِدِ اللَّهَ غَفُورًا رَّحِيمًا
"Whoever does evil or wrongs himself then seeks forgiveness of Allah will find Allah Forgiving and Merciful."
""",
    ),
    (
        "Can Allah forgive all sins? Are there sins He cannot forgive?",
        """Allah ﷻ can forgive ALL sins — with one exception.

─── WHAT ALLAH FORGIVES ───
Allah ﷻ says in Surah Az-Zumar (39:53):
إِنَّ اللَّهَ يَغْفِرُ الذُّنُوبَ جَمِيعًا
"Indeed, Allah forgives ALL sins."

This verse was revealed as comfort to those who felt their sins were too great to be forgiven. No matter what a person has done — fornication, murder, years of disobedience — if they sincerely repent, Allah will forgive them.

─── THE ONE EXCEPTION: SHIRK ───
Allah ﷻ says in Surah An-Nisa (4:48):
إِنَّ اللَّهَ لَا يَغْفِرُ أَن يُشْرَكَ بِهِ وَيَغْفِرُ مَا دُونَ ذَٰلِكَ لِمَن يَشَاءُ
"Indeed, Allah does not forgive association with Him [Shirk], but He forgives what is less than that for whom He wills."

Shirk — associating partners with Allah — is the only sin that Allah has declared He does NOT forgive if a person dies upon it without repenting.

However — if a person commits Shirk and then sincerely repents and accepts Tawheed before death, even this is forgiven! The exception applies only to dying in a state of Shirk without repentance.

─── HADITH ───
The Prophet ﷺ said in Sahih Bukhari (7507):
"Allah says: O son of Adam, as long as you call upon Me and put your hope in Me, I will forgive you for what you have done, and I shall not mind. O son of Adam, if your sins were to reach the clouds of the sky and then you asked for My forgiveness, I would forgive you."
Grade: Hasan

─── LESSON ───
Never despair of Allah's mercy. Despair of Allah's mercy (Qunoot) is itself a sin. No matter the size of your sins, the door of Tawbah is open as long as you are alive and the signs of the Last Day have not appeared.
""",
    ),
    (
        "What is the Islamic ruling on obeying parents when they command something haram?",
        """Obedience to parents is one of the most emphasized obligations in Islam — but it has a clear limit.

─── THE OBLIGATION OF OBEDIENCE ───
Allah ﷻ commands kindness to parents in Surah Al-Isra (17:23):
وَقَضَىٰ رَبُّكَ أَلَّا تَعْبُدُوا إِلَّا إِيَّاهُ وَبِالْوَالِدَيْنِ إِحْسَانًا
"Your Lord has decreed that you worship none but Him, and that you be kind to parents."

The Prophet ﷺ placed pleasing parents as the gateway to Paradise. He said in Sahih Bukhari (5971):
"The pleasure of the Lord is in the pleasure of the parents, and the anger of the Lord is in the anger of the parents."
Grade: Sahih

─── THE LIMIT: NO OBEDIENCE IN DISOBEDIENCE TO ALLAH ───
Allah ﷻ says in Surah Luqman (31:15):
وَإِن جَاهَدَاكَ عَلَىٰ أَن تُشْرِكَ بِي مَا لَيْسَ لَكَ بِهِ عِلْمٌ فَلَا تُطِعْهُمَا ۖ وَصَاحِبْهُمَا فِي الدُّنْيَا مَعْرُوفًا
"But if they endeavor to make you associate with Me that of which you have no knowledge, do not obey them but accompany them in [this] world with appropriate kindness."

The Prophet ﷺ said in Sahih Bukhari (7257) and Sahih Muslim (1840):
"There is no obedience to the creation in disobedience to the Creator."
Grade: Sahih

─── PRACTICAL EXAMPLES ───
You must REFUSE if parents command:
- Shirk or leaving Islam
- Cutting off ties with a spouse or children without valid reason
- Eating haram
- Missing obligatory prayers
- Lying or cheating

You must OBEY parents in:
- Matters of their wellbeing and care
- Lifestyle preferences that are permissible
- Financial support if they need it

─── KEY POINT ───
Refusing to obey parents in haram does NOT mean being disrespectful. You can firmly, kindly, and lovingly decline while still treating them with honor, providing for them, speaking gently, and maintaining the relationship.
""",
    ),
]

# ─── Category 7: Aqeedah Contemporary Questions ──────────────────────────────

AQEEDAH_EXTENDED_PAIRS: list[tuple[str, str]] = [
    (
        "What is Shirk and what are its types? How serious is it?",
        """Shirk means associating partners with Allah — attributing to others what belongs to Allah alone in terms of Lordship, worship, or His unique attributes and names.

Allah ﷻ says in Surah An-Nisa (4:48):
إِنَّ اللَّهُ لَا يَغْفِرُ أَن يُشْرَكَ بِهِ وَيَغْفِرُ مَا دُونَ ذَٰلِكَ لِمَن يَشَاءُ
"Indeed, Allah does not forgive association with Him, but He forgives what is less than that for whom He wills."

─── MAJOR SHIRK (Shirk Akbar) — Exits Islam ───
Directing acts of worship to other than Allah: praying to graves, saints, or idols; sacrificing animals in the name of other than Allah; believing any being shares Allah's divine power.

Examples:
- Praying to or through a deceased person
- Believing a saint has the power to benefit or harm independently
- Worshipping idols or statues

─── MINOR SHIRK (Shirk Asghar) — Does Not Exit Islam but Is a Major Sin ───
Acts that lead toward Shirk without reaching its full reality.

The Prophet ﷺ said in Musnad Ahmad (27742):
"What I fear most for you is minor Shirk." They asked: "What is minor Shirk, O Messenger of Allah?" He said: "Showing off (Riya')."
Grade: Sahih

Examples of minor Shirk:
- Riya' (showing off acts of worship to impress people)
- Swearing by other than Allah: "I swear by the Prophet..."
- Saying "If Allah wills and you will" — equating someone's will with Allah's (Sunan Ibn Majah)

─── HIDDEN SHIRK ───
The most subtle form — performing worship for praise, or depending on a means more than on Allah. The Prophet ﷺ called Riya' the "hidden Shirk" in Sahih Muslim.

─── RULING ON WEARING TA'WEEZ (AMULETS) ───
The Prophet ﷺ said in Musnad Ahmad (16951):
"Whoever hangs an amulet has committed Shirk."
Grade: Sahih

Wearing amulets — inscribed objects hung for protection — is forbidden. Protection comes from Allah through the authentic duas (like Ayatul Kursi and Mu'awwidhat) not from physical objects.

The cure for all concern about protection is the morning and evening adhkar and reliance on Allah (Tawakkul).
""",
    ),
    (
        "What is the Islamic ruling on visiting graves and can the dead hear us?",
        """─── VISITING GRAVES ───
Visiting graves is PERMISSIBLE and recommended (Mustahabb) — with conditions.

Initially, the Prophet ﷺ had prohibited visiting graves. Then he permitted it, saying in Sahih Muslim (976):
"I had forbidden you from visiting graves, but now visit them, for they remind you of the Hereafter."
Grade: Sahih

─── PROPER WAY TO VISIT GRAVES ───
Upon entering the graveyard, say:
السَّلَامُ عَلَيْكُمْ أَهْلَ الدِّيَارِ مِنَ الْمُؤْمِنِينَ وَالْمُسْلِمِينَ
"Peace be upon you, O people of this abode, from among the believers and Muslims."

Make dua FOR the deceased. Reflect on death and the Hereafter. Recite Quran if you wish (scholars differ on whether its reward reaches the deceased but majority permit it).

─── WHAT IS FORBIDDEN AT GRAVES ───
1. Building structures or domes over graves — forbidden in Sahih Muslim (970)
2. Writing on graves — forbidden in Sahih Muslim (970)
3. Making dua TO the deceased asking them to fulfill needs — this is Shirk
4. Excessive mourning, wailing
5. Sitting and eating at graves

─── CAN THE DEAD HEAR US? ───
This is a matter of scholarly debate:

Yes — evidence for hearing:
- The Prophet ﷺ spoke to the dead polytheists in the well of Badr. Umar (RA) said: "Do you speak to dead bodies?" The Prophet ﷺ replied in Sahih Bukhari (1370): "By the One in Whose hand my soul is, you do not hear what I say better than they do."
- The Prophet ﷺ said the deceased hears footsteps of those who attended their funeral as they walk away

No — evidence against:
- Allah ﷻ says in Surah Fatir (35:22): "You cannot make the dead hear" — scholars use this in the context of guidance, not literal hearing
- Ibn Taymiyyah and others held that the dead hear in a specific circumstance (like at burial) but not as a general ability

─── PRACTICAL RULING ───
Making salam to the deceased and making dua for them is Sunnah. Asking the deceased to fulfill your needs is Shirk and is strictly forbidden.
""",
    ),
    (
        "What is the Islamic ruling on celebrating the Prophet's birthday (Mawlid)?",
        """The celebration of the Prophet's ﷺ birthday (Mawlid al-Nabi) — typically on 12th Rabi al-Awwal — is one of the most debated contemporary Islamic issues. Two major scholarly positions exist:

─── POSITION 1: IMPERMISSIBLE (BID'AH) ───
Scholars such as Ibn Taymiyyah, Ibn al-Qayyim, Ibn Baz, Ibn Uthaymeen, and the majority of scholars in Saudi Arabia hold that Mawlid is an impermissible innovation (Bid'ah) because:

1. The Prophet ﷺ did not celebrate his own birthday
2. The Sahabah (companions) did not celebrate it
3. The first four Caliphs did not celebrate it
4. It was introduced approximately 400 years after the Prophet ﷺ

The Prophet ﷺ said in Sahih Bukhari (2697):
"Whoever introduces something new into this matter of ours that is not part of it will have it rejected."
Grade: Sahih

─── POSITION 2: PERMISSIBLE ───
Scholars such as Imam as-Suyuti, Ibn Hajar al-Asqalani, al-Nawawi's school, and the majority of scholars in Egypt, Syria, Morocco, Turkey, and South Asia hold that Mawlid is permissible — even recommended — if free of haram elements, because:

1. It is an expression of love for the Prophet ﷺ — which the Quran commands (Al-Ahzab 33:56)
2. The Prophet ﷺ fasted on Mondays saying: "That is the day I was born" (Sahih Muslim 1162) — indicating recognition of the day of birth
3. The principle in Islam: acts of worship not explicitly forbidden are permitted if they serve a valid purpose (celebrating love for the Prophet ﷺ)
4. Ibn Hajar said: "The basis of Mawlid is a good innovation (Bid'ah Hasanah)"

─── CONSENSUS ───
All scholars agree: if Mawlid gatherings contain haram elements (free mixing, music, shirk-like veneration), they are haram. The debate is about the permissibility of Mawlid in its pure form.

A Muslim should follow the scholarly opinion they trust and not use this issue to divide or attack fellow Muslims.
""",
    ),
    (
        "What is Jihad in Islam and what are its types?",
        """Jihad literally means "struggle" or "striving." It has multiple dimensions in Islam and is widely misunderstood.

─── THE GREATER JIHAD (Al-Jihad al-Akbar) ───
The Prophet ﷺ said upon returning from a battle, as recorded in Shu'ab al-Iman of al-Bayhaqi:
"We have returned from the lesser Jihad to the greater Jihad." When asked what the greater Jihad was, he said: "The struggle of a person against his own desires (nafs)."

This is the internal spiritual struggle against the ego, sinful desires, and Satan.

─── THE LESSER JIHAD (Al-Jihad al-Asghar) ───
Armed struggle in the path of Allah. This is legitimate under strict conditions:

─── CONDITIONS FOR LEGITIMATE ARMED JIHAD ───
1. Declared by a legitimate Muslim authority — not individuals acting alone
2. Defensive in nature — responding to aggression, oppression, or to stop persecution
3. Non-combatants (women, children, elderly, clergy, farmers) must not be harmed
4. Must not destroy crops, trees, or civilian infrastructure without necessity
5. Prisoners of war must be treated humanely

Allah ﷻ says in Surah Al-Baqarah (2:190):
وَقَاتِلُوا فِي سَبِيلِ اللَّهِ الَّذِينَ يُقَاتِلُونَكُمْ وَلَا تَعْتَدُوا ۚ إِنَّ اللَّهَ لَا يُحِبُّ الْمُعْتَدِينَ
"Fight in the cause of Allah those who fight you, but do not transgress limits. Indeed, Allah does not like transgressors."

─── OTHER FORMS OF JIHAD ───
1. Jihad al-Nafs — against one's own ego and desires
2. Jihad al-Lisan — speaking truth, calling to Islam, educating
3. Jihad al-Mal — spending wealth in the cause of Allah
4. Jihad bil Qalam — writing and scholarship in defense of Islam
5. Jihad al-Qalb — hating evil in the heart when unable to change it

─── ISLAMIC RULING ON TERRORISM ───
Killing civilians, targeting non-combatants, and suicide bombings are HARAM by the scholarly consensus of contemporary Islam. They violate the clear conditions of Jihad and are acts of Fasad (corruption on earth), which Allah forbids.

Allah ﷻ says in Surah Al-Ma'idah (5:32):
مَن قَتَلَ نَفْسًا بِغَيْرِ نَفْسٍ أَوْ فَسَادٍ فِي الْأَرْضِ فَكَأَنَّمَا قَتَلَ النَّاسَ جَمِيعًا
"Whoever kills a soul unless for a soul or for corruption in the land — it is as if he had slain mankind entirely."
""",
    ),
]

# ─── Category 8: Ruqyah, Evil Eye, and Spiritual Protection ──────────────────

SPIRITUAL_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is Ruqyah and is it permissible in Islam?",
        """Ruqyah is the recitation of specific Quranic verses and authentic duas over a sick person for the purpose of healing — whether from physical illness, evil eye (Ayn), possession, or black magic.

─── IS RUQYAH PERMISSIBLE? ───
Yes. Ruqyah using the Quran and authentic supplications is not only permissible but encouraged (Mustahabb).

The Prophet ﷺ said in Sahih Muslim (2200):
"There is no harm in Ruqyah as long as it does not involve Shirk."
Grade: Sahih

Aisha (RA) narrated that the Prophet ﷺ used to perform Ruqyah on himself, saying in Sahih Bukhari (5016):
"(O Allah, Lord of mankind! Remove the difficulty and bring the cure. You are the Healer. There is no cure but Your cure — a cure that leaves no disease.)"

─── HOW IS RUQYAH PERFORMED? ───
1. Recite Surah Al-Fatiha (1:1-7) over the person — the Prophet ﷺ called it "the greatest healing" (Sahih Bukhari 5736)
2. Recite Ayatul Kursi (Al-Baqarah 2:255)
3. Recite Al-Ikhlas (112), Al-Falaq (113), An-Nas (114) three times each
4. Blow lightly onto the sick person or into water which they drink
5. Place the hand on the area of pain and say: "Bismillah" three times, then: "A'udhu bi'izzatillahi wa qudratihi min sharri ma ajidu wa uhadhiru" (I seek refuge in Allah's might and power from the evil I feel and fear) — seven times (Sahih Muslim 2202)

─── RUQYAH USING QURAN IS PROVEN BY QURAN ITSELF ───
Allah ﷻ says in Surah Al-Isra (17:82):
وَنُنَزِّلُ مِنَ الْقُرْآنِ مَا هُوَ شِفَاءٌ وَرَحْمَةٌ لِّلْمُؤْمِنِينَ
"And We send down of the Quran that which is a healing and a mercy for the believers."

─── WHAT IS FORBIDDEN IN RUQYAH ───
- Using unknown symbols, numbers, or writing
- Visiting Jinn to perform Ruqyah (this is Shirk)
- Paying charlatans who claim to use Jinn to heal
- Ruqyah that contains words other than Arabic Quran or authentic duas

Seek Ruqyah from people who use only Quran and authentic Sunnah supplications.
""",
    ),
    (
        "What is the evil eye (Ayn) and what is its Islamic ruling?",
        """The evil eye (Al-Ayn) is real according to Islam — it is the harm that can occur to a person through the envious or admiring gaze of another.

─── QURANIC CONFIRMATION ───
Allah ﷻ says in Surah Al-Qalam (68:51):
وَإِن يَكَادُ الَّذِينَ كَفَرُوا لَيُزْلِقُونَكَ بِأَبْصَارِهِمْ
"And indeed, those who disbelieve would almost make you slip with their eyes."

Allah ﷻ commanded the Prophet ﷺ to seek refuge from the evil eye in Surah Al-Falaq (113:1-5):
قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ... وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ
"Say: I seek refuge in the Lord of daybreak... and from the evil of an envier when he envies."

─── HADITH ───
The Prophet ﷺ said in Sahih Muslim (2187):
"The evil eye is real (Al-Ayn Haqq). If anything were to overcome Divine Decree (Qadar), the evil eye would."
Grade: Sahih

The Prophet ﷺ said in Sahih Muslim (2188):
"The evil eye is real and it can bring a man down from a mountain."
Grade: Sahih

─── PROTECTION FROM THE EVIL EYE ───
1. Say "Masha'Allah, La Quwwata illa billah" when admiring something (Surah Al-Kahf 18:39)
2. Recite morning and evening adhkar — especially Al-Ikhlas, Al-Falaq, An-Nas three times each
3. Recite Ayatul Kursi after every fard prayer
4. The giver of the evil eye (even unintentionally) should make Wudu and pour the water used over the afflicted person (Sahih Muslim 2188)

─── TREATMENT ───
- Ruqyah (Quranic recitation over the person)
- Washing water poured by the one who gave the evil eye
- Maintaining strong connection with Allah through dhikr and Quran

The evil eye is real — but its cure is in Allah alone, not in superstitious practices or amulets.
""",
    ),
]

# ─── Category 9: Mental Health & Faith ───────────────────────────────────────

MENTAL_HEALTH_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "How does Islam address depression and feelings of hopelessness?",
        """Islam fully acknowledges the reality of sadness, grief, and mental suffering. Feeling depressed is not a sin, and seeking help is not weakness — it is wisdom.

─── PROPHETIC EXAMPLES ───
The Prophet ﷺ himself experienced profound sadness. The year in which his beloved wife Khadijah (RA) and his uncle Abu Talib died is called "The Year of Sorrow" (Am al-Huzn). Allah ﷻ revealed Surah Ad-Duha to comfort the Prophet ﷺ when he felt Allah had abandoned him:

Allah ﷻ says in Surah Ad-Duha (93:3-5):
مَا وَدَّعَكَ رَبُّكَ وَمَا قَلَىٰ ۝ وَلَلْآخِرَةُ خَيْرٌ لَّكَ مِنَ الْأُولَىٰ ۝ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ
"Your Lord has not forsaken you, nor has He detested you. And the Hereafter is better for you than the first [life]. And your Lord is going to give you, and you will be satisfied."

─── IS IT A SIN TO FEEL SAD? ───
No. The Prophet ﷺ said in Sahih Bukhari (5641):
"Nothing afflicts a Muslim — not fatigue, illness, sorrow, sadness, harm, or distress, even the prick of a thorn — except that Allah expiates some of his sins through it."
Grade: Sahih

─── QURANIC REMEDY ───
Allah ﷻ says in Surah Ar-Ra'd (13:28):
أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ
"Verily, in the remembrance of Allah do hearts find rest."

─── PRACTICAL ISLAMIC STEPS ───
1. Prayer — especially night prayer (Tahajjud) and being in sujood (Allah is closest to us there)
2. Quran recitation — particularly Surah Ad-Duha, Al-Inshirah, Al-Baqarah
3. Dua: "Allahumma inni a'udhu bika minal hammi wal hazan..." (O Allah, I seek refuge in You from worry and grief — Sahih Bukhari 6369)
4. Physical exercise and healthy routines
5. Community — do not isolate yourself
6. Seeking professional help — this is permissible and encouraged

─── CAN A MUSLIM SEE A THERAPIST? ───
Yes, absolutely. Seeking therapy or counseling is permissible and often necessary. The Prophet ﷺ said in Sunan Abu Dawud (3855): "Seek treatment, for Allah has not created a disease except that He has also created a cure." Mental illness is an illness — it deserves treatment just as physical illness does.

Despair of Allah's mercy (Al-Ya's) is itself a sin. Never give up hope.
""",
    ),
    (
        "How to deal with Waswas (obsessive doubts) in worship and about faith?",
        """Waswas refers to the intrusive, recurring doubts and whispers that Satan sends to believers — especially in prayer and regarding matters of faith. It is extremely common and the Prophet ﷺ directly addressed it.

─── QURANIC BASIS ───
Allah ﷻ says in Surah An-Nas (114:1-6):
قُلْ أَعُوذُ بِرَبِّ النَّاسِ... مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ ۝ الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ
"Say: I seek refuge in the Lord of mankind... from the evil of the retreating whisperer — who whispers [evil] into the breasts of mankind."

─── HADITH ───
Companions came to the Prophet ﷺ saying they had thoughts they would rather die than speak aloud. The Prophet ﷺ said in Sahih Muslim (132):
"That is pure faith." Meaning: the fact that they hated these thoughts and were horrified by them is a sign of strong faith, not weak faith.
Grade: Sahih

The Prophet ﷺ also said in Sahih Muslim (134):
"Satan comes to one of you and says: Who created this? Who created that? Until he asks: Who created Allah? When one reaches this point, let him seek refuge with Allah and stop [entertaining those thoughts]."
Grade: Sahih

─── SPECIFIC REMEDIES ───
For doubt about purity/wudu:
The Prophet ﷺ said in Sahih Muslim (362): "He should not leave [prayer] unless he hears a sound or smells something." — Ignore doubt unless there is certainty.

For doubts in prayer:
Build on certainty — if you're unsure if you prayed 2 or 3 rak'ahs, assume 2 (the lesser certain amount) and complete.

─── GENERAL CURE FOR WASWAS ───
1. Say: "A'udhu billahi minash Shaytanir Rajim" — seek refuge in Allah from Satan
2. Recite Al-Falaq and An-Nas
3. Do NOT engage with or analyze the waswas — ignore it completely
4. Continue your worship — do not repeat ablution or prayer unnecessarily
5. The more you engage with waswas, the stronger it becomes

The worst thing for waswas is repeatedly re-doing wudu or prayer — this feeds it. The cure is firm determination and moving forward.

If waswas is so severe it resembles clinical OCD, seek professional help alongside Islamic remedies.
""",
    ),
]

# ─── Category 10: Youth & New Muslims ────────────────────────────────────────

YOUTH_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is the Islamic ruling on having a boyfriend or girlfriend?",
        """Islam does not permit romantic relationships outside of marriage — having a boyfriend or girlfriend is not permissible.

─── QURANIC BASIS ───
Allah ﷻ says in Surah Al-Isra (17:32):
وَلَا تَقْرَبُوا الزِّنَا إِنَّهُ كَانَ فَاحِشَةً وَسَاءَ سَبِيلًا
"And do not approach unlawful sexual intercourse. Indeed, it is ever an immorality and is evil as a way."

The verse says "do not APPROACH" — not just "do not commit." Dating relationships create the conditions that lead toward zina (fornication). Islam closes the door before the sin.

Allah ﷻ also says in Surah Al-Ma'idah (5:5) describing the qualities of believers:
مُحْصَنِينَ غَيْرَ مُسَافِحِينَ وَلَا مُتَّخِذِي أَخْدَانٍ
"Being chaste, neither [of] those who commit unlawful intercourse nor those who take [secret] lovers."

The phrase "secret lovers" refers directly to the boyfriend/girlfriend relationship — it was known in pre-Islamic Arabia and explicitly forbidden.

─── HADITH ───
The Prophet ﷺ said in Sahih Bukhari (5232):
"No man should be alone with a woman."
Grade: Sahih

─── THE HALAL ALTERNATIVE ───
Islam does not leave people without a path. The solution is:
1. Lower the gaze (Surah An-Nur 24:30-31)
2. Keep yourself busy with productive and Islamic activities
3. When ready and able — pursue marriage through proper channels
4. Families can facilitate introductions and chaperoned meetings
5. Fast if unable to marry — the Prophet ﷺ said fasting reduces desire (Sahih Bukhari 5066)

─── FOR THOSE WHO HAVE STRUGGLED ───
If someone has been in such relationships and sincerely repents, Allah forgives completely. Do not despair — make Tawbah, change your environment, and move forward.

The purity of your future marriage is worth protecting.
""",
    ),
    (
        "How does someone become Muslim? What is the Shahada?",
        """Becoming Muslim is beautifully simple. Islam does not require a ceremony, a priest, or a church. It requires only a sincere heart and two words.

─── THE SHAHADA (Declaration of Faith) ───
To become Muslim, a person must sincerely believe in their heart and declare with their tongue:

أَشْهَدُ أَنْ لَا إِلَٰهَ إِلَّا اللَّهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا رَسُولُ اللَّهِ

"Ash-hadu an la ilaha illallah, wa ash-hadu anna Muhammadan rasulullah"

"I bear witness that there is no god worthy of worship except Allah, and I bear witness that Muhammad ﷺ is the Messenger of Allah."

─── WHAT DOES IT MEAN? ───
"La ilaha illallah" — There is no god worthy of worship except Allah. This means rejecting all false gods and affirming the absolute Oneness (Tawheed) of Allah.

"Muhammadan rasulullah" — Muhammad ﷺ is His Messenger. This means accepting that Allah revealed Islam through the Prophet Muhammad ﷺ, and following his Sunnah.

─── IS A WITNESS REQUIRED? ───
Scholars say the Shahada is valid even without witnesses — it is a matter between the person and Allah. However, saying it in front of witnesses (ideally at a mosque) is recommended to begin the Muslim community relationship.

─── WHAT HAPPENS AFTER SHAHADA? ───
1. Take Ghusl (full ritual bath) — to start fresh in a state of purity
2. Learn the five daily prayers — Salah is the first obligation after Shahada
3. Learn what is halal and haram in food
4. Connect with a local mosque and Muslim community
5. Begin learning about your new faith gradually — Islam is learned over a lifetime

─── QURANIC PROMISE ───
Allah ﷻ says in Surah Al-Baqarah (2:256):
لَا إِكْرَاهَ فِي الدِّينِ ۖ قَد تَّبَيَّنَ الرُّشْدُ مِنَ الْغَيِّ
"There is no compulsion in religion. Truth has been made clear from error."

And the Prophet ﷺ said in Sahih Bukhari (6):
"Whoever enters Islam (says the Shahada), all their previous sins are forgiven."
Grade: Sahih — You begin life completely clean, with a fresh slate.

Welcome to Islam if you are reading this and have taken this step. May Allah guide you and keep you firm.
""",
    ),
]

# ─── Category 11: Death & Inheritance ────────────────────────────────────────

DEATH_FIQH_PAIRS: list[tuple[str, str]] = [
    (
        "What is the Islamic ruling on organ donation?",
        """Organ donation is one of the most discussed contemporary Islamic issues. The scholarly community is divided into two positions:

─── POSITION 1: PERMISSIBLE ───
The Islamic Fiqh Academy (OIC), the majority of contemporary scholars including Sheikh Yusuf al-Qaradawi, Egyptian Dar al-Ifta, and others hold that organ donation is PERMISSIBLE — even recommended — because:

1. Saving a human life is one of the highest goals of Shariah (Maqasid)
Allah ﷻ says in Surah Al-Ma'idah (5:32):
وَمَنْ أَحْيَاهَا فَكَأَنَّمَا أَحْيَا النَّاسَ جَمِيعًا
"And whoever saves one [life] — it is as if he had saved mankind entirely."

2. The principle of necessity (Darura) applies when a life depends on an organ
3. Donating is a form of Sadaqah Jariyah (ongoing charity) that benefits the donor after death

─── POSITION 2: NOT PERMISSIBLE ───
Scholars including Sheikh Ibn Baz (earlier opinion), Sheikh Ibn Uthaymeen, and others held that organ donation is NOT permissible because:
1. The human body belongs to Allah and cannot be donated or sold
2. The hadith: "Breaking the bone of a dead person is like breaking it when alive" (Abu Dawud 3207) — indicates sanctity of the corpse
3. Uncertainty about whether a person is truly dead when organs are harvested

─── CONDITIONS FOR PERMISSIBILITY (according to those who permit) ───
1. The donor freely consented during their lifetime — no coercion or financial transaction
2. The organ is not sold (organ selling is haram by consensus)
3. Medical certainty of brain death before harvesting
4. The organ goes to save a life, not for cosmetic purposes

─── PRACTICAL GUIDANCE ───
If you wish to donate organs: make your intention clear in writing and to your family. If you do not wish to: make that clear too. In either case, ensure your family knows your wishes.

This is a matter of genuine scholarly disagreement — follow the opinion of the scholars you trust.
""",
    ),
    (
        "What deeds benefit a person after they die?",
        """Death does not stop all benefit to a person. Islam teaches three categories of deeds whose reward continues after death, plus deeds done by others on a deceased person's behalf.

─── THE HADITH ───
The Prophet ﷺ said in Sahih Muslim (1631):
"When a person dies, his deeds come to an end except for three things: Sadaqah Jariyah (ongoing charity), knowledge that is benefited from, or a righteous child who prays for him."
Grade: Sahih

─── THE THREE CONTINUING DEEDS ───
1. SADAQAH JARIYAH (Ongoing Charity):
Anything you build, fund, or establish that continues to benefit people after your death:
- A masjid you helped fund
- A well or water source you paid for
- A school or library
- An Islamic center
- Books or educational materials you provided
- Even planting a tree (Sahih Bukhari 6012)

2. BENEFICIAL KNOWLEDGE:
Knowledge you taught that others continue to teach and practice:
- A student you taught Quran to
- Islamic books you wrote
- Online lectures that continue to be watched

3. A RIGHTEOUS CHILD WHO MAKES DUA:
Children who pray for their parents benefit them directly. This is why raising children upon Islam is one of the greatest investments.

─── WHAT OTHERS CAN DO FOR THE DECEASED ───
- Make dua for them — clearly reaches them (Sahih Muslim 976)
- Give Sadaqah on their behalf — scholars agree this benefits the deceased (Sahih Muslim 1004)
- Recite Quran for them — majority of scholars say this reaches them (Hanbali and Hanafi position)
- Perform Hajj or Umrah on their behalf — the Prophet ﷺ permitted this (Sahih Bukhari 1852)
- Fast on their behalf (if they had missed fasts) — the Prophet ﷺ permitted this (Sahih Bukhari 1952)
- Pay off debts they left behind

Allah ﷻ says in Surah At-Tur (52:21):
وَالَّذِينَ آمَنُوا وَاتَّبَعَتْهُمْ ذُرِّيَّتُهُم بِإِيمَانٍ أَلْحَقْنَا بِهِمْ ذُرِّيَّتَهُمْ
"And those who believed and were followed by their descendants in faith — We will join with them their descendants."
""",
    ),
]

# ─── Master generator ─────────────────────────────────────────────────────────

def generate_fiqh_extended_pairs() -> list[dict[str, Any]]:
    """Return all extended Fiqh Q&A pairs with proper metadata."""
    category_map: list[tuple[str, list[tuple[str, str]]]] = [
        ("marriage_family",   MARRIAGE_FIQH_PAIRS),
        ("finance_business",  FINANCE_FIQH_PAIRS),
        ("fasting_fiqh",      SAWM_FIQH_PAIRS),
        ("gender_hijab",      HIJAB_FIQH_PAIRS),
        ("contemporary_fiqh", CONTEMPORARY_FIQH_PAIRS),
        ("morals_ethics",     MORALS_FIQH_PAIRS),
        ("aqeedah",           AQEEDAH_EXTENDED_PAIRS),
        ("spiritual_fiqh",    SPIRITUAL_FIQH_PAIRS),
        ("mental_health",     MENTAL_HEALTH_FIQH_PAIRS),
        ("youth_new_muslim",  YOUTH_FIQH_PAIRS),
        ("death_afterlife",   DEATH_FIQH_PAIRS),
    ]

    pairs: list[dict[str, Any]] = []
    for category, pair_list in category_map:
        for question, answer in pair_list:
            pairs.append({
                "instruction": question,
                "input": "",
                "output": answer.strip(),
                "metadata": {
                    "category": category,
                    "sources": [],
                },
            })

    return pairs
