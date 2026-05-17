# Phase 2 — Dataset Formatting

Convert raw Quran and Hadith JSON into 15,000+ instruction-following training pairs.

**Status: LOCKED — complete Phase 1 validation first.**

---

## What This Phase Does

Takes the raw JSON from Phase 1 and produces clean JSONL training files:

```
raw/quran/quran_full.json   ─┐
raw/hadith/*.json            ─┤──► 15,000+ Q&A pairs ──► train.jsonl
raw/supplementary/*.json     ─┘                          eval.jsonl
                                                         test.jsonl
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `format_quran.py` | Generate Q&A pairs from Quran verses |
| `format_hadith.py` | Generate Q&A pairs from Hadith collections |
| `generate_qa_pairs.py` | Master script — runs both + combined pairs |
| `deduplicate.py` | Remove near-duplicate questions (85%+ similarity) |
| `validate_dataset.py` | Validate final JSONL before training |

---

## Output Format (JSONL)

Each line in the output file is one JSON training example:

```json
{
  "instruction": "What does the Quran say about patience in hardship?",
  "input": "",
  "output": "Allah ﷻ says in Surah Al-Baqarah (2:153):\n\nٱسْتَعِينُوا۟ بِٱلصَّبْرِ وَٱلصَّلَوٰةِ\n\nTranslation: 'O you who have believed, seek help through patience and prayer. Indeed, Allah is with the patient.'\n\nIbn Kathir explains: This ayah was revealed to encourage the believers to rely on two pillars during hardship...\n\nThe Prophet ﷺ also said in Sahih Muslim (2999):\n\n'How wonderful is the affair of the believer, for his affairs are all good...'\n\nGrade: Sahih",
  "metadata": {
    "category": "quran+hadith",
    "sources": ["quran:2:153", "muslim:2999"],
    "generated_at": "2026-05-16T00:00:00Z"
  }
}
```

---

## Question Categories (10 types)

| # | Category | Example |
|---|---------|---------|
| 1 | Direct Quran | "What does Allah say about X?" |
| 2 | Direct Hadith | "What did the Prophet ﷺ say about X?" |
| 3 | Fiqh ruling | "What is the ruling on X in Islam?" |
| 4 | Combined | Quran + Hadith answer on same topic |
| 5 | Surah meaning | "What is the meaning of Surah X?" |
| 6 | Dua | "What dua to read before/after X?" |
| 7 | Aqeedah | "What do Muslims believe about X?" |
| 8 | Ethics | "How should a Muslim behave regarding X?" |
| 9 | Permissibility | "Is X halal or haram in Islam?" |
| 10 | Refusal | Out-of-scope questions → model refuses |

---

## Targets

- Minimum: **15,000 total Q&A pairs**
- Per category: **>= 2,000 pairs**
- Refusal pairs: **>= 500**
- Split: **80% train / 10% eval / 10% test**

---

## How to Run (after Phase 1 passes)

```bash
cd 02_dataset_formatting/scripts

# Step 1: Link raw data
ln -sf ../../01_data_collection/raw ../raw_input

# Step 2: Generate all Q&A pairs
python generate_qa_pairs.py

# Step 3: Remove near-duplicates
python deduplicate.py

# Step 4: Validate final dataset
python validate_dataset.py
```
