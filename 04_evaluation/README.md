# Phase 4 — Evaluation

Test the fine-tuned model for accuracy, hallucination, and refusal behaviour.

**Status: LOCKED — complete Phase 3 training first.**

---

## Test Question Sets

| File | Category | Questions |
|------|---------|-----------|
| `aqeedah.json` | Islamic beliefs (Tawhid, Angels, etc.) | 50+ |
| `fiqh.json` | Rulings (prayer, fasting, zakah, etc.) | 50+ |
| `quran_tafsir.json` | Quran verses and their meanings | 50+ |
| `hadith.json` | Hadith knowledge and attribution | 50+ |
| `seerah.json` | Prophet's biography | 30+ |
| `ethics.json` | Islamic character and conduct | 30+ |
| `dua.json` | Supplications for daily situations | 30+ |

---

## Evaluation Scripts

| Script | What it checks |
|--------|---------------|
| `run_evaluation.py` | Run all test questions through the model |
| `hallucination_check.py` | Verify every Quran/Hadith reference is real |
| `reference_validator.py` | Load index files, validate specific citations |
| `generate_report.py` | Produce a full HTML/JSON evaluation report |

---

## Pass Criteria

| Metric | Target |
|--------|--------|
| Reference accuracy | >= 90% (cited verses/hadiths must exist) |
| Refusal accuracy | >= 95% (out-of-scope questions refused) |
| Arabic text present | >= 95% of Quran-citing answers |
| Hadith grade cited | >= 90% of Hadith-citing answers |
| Zero fabricated Surahs | 100% — any fabricated reference = FAIL |

---

## How to Run

```bash
cd 04_evaluation/scripts

# Run all test questions through the local GGUF
python run_evaluation.py --model-path ../../05_model_output/gguf/islamic_llm_q4_k_m.gguf

# Check for hallucinated references
python hallucination_check.py --report-dir ../reports

# Generate final report
python generate_report.py
```
