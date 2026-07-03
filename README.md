# Islamic AI Engine

A fully custom Islamic AI chatbot — trained from scratch on authentic Quran and Hadith
data, exported as an on-device GGUF model, and integrated into a Flutter app.

**Total cost: $0**

---

## Project Goal

Build a ChatGPT-like assistant that:
- Answers questions **only** from the Quran and authenticated Hadith
- Always cites **exact references** (Surah:Ayah, Hadith collection + number)
- Includes **Arabic text** alongside translations
- Notes the **grade** of every Hadith (Sahih, Hasan, etc.)
- Runs **100% on-device** — no internet required after setup
- Refuses to answer anything outside its Islamic knowledge domain

---

## Architecture

```
01_data_collection/     ← Download Quran + Hadith JSON data
        ↓
02_dataset_formatting/  ← Convert raw data into 15,000+ Q&A training pairs
        ↓
03_training/            ← Fine-tune Llama 3.2 3B on Google Colab (free GPU)
        ↓
04_evaluation/          ← Test the model for accuracy + hallucination
        ↓
05_model_output/        ← Export to GGUF (Q4_K_M, ~1.7GB)
        ↓
06_local_test_harness/  ← Test GGUF in terminal before touching Flutter
        ↓
07_flutter_integration/ ← Drop-in kit: copy files into main Flutter app
```

---

## Phases

| Phase | Folder | Status |
|-------|--------|--------|
| 1 | `01_data_collection/` | **Start here** |
| 2 | `02_dataset_formatting/` | After Phase 1 passes validation |
| 3 | `03_training/` | After Phase 2 produces clean dataset |
| 4 | `04_evaluation/` | After training completes |
| 5 | `05_model_output/` | After evaluation passes |
| 6 | `06_local_test_harness/` | After GGUF is exported |
| 7 | `07_flutter_integration_kit/` | After local testing passes |

---

## Setup

```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in this root directory:

```env
# Required for Phase 3 and 5 (uploading model to HuggingFace)
HF_TOKEN=hf_your_token_here

# Optional: override default output paths
QURAN_OUTPUT_DIR=01_data_collection/raw/quran
HADITH_OUTPUT_DIR=01_data_collection/raw/hadith
```

Get a free HuggingFace token at: https://huggingface.co/settings/tokens

---

## Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Base model | Llama 3.2 3B Instruct | Best quality/size ratio for mobile |
| Fine-tuning method | QLoRA (4-bit) | Fits in free Colab T4 GPU |
| Training library | Unsloth | 2x faster, 60% less VRAM |
| Export format | GGUF Q4_K_M | ~1.7GB, best quality-to-size for mobile |
| On-device runtime | llama.cpp | Mature, battle-tested, Flutter bindings exist |
| Training data | 15,000+ Q&A pairs | Quran + 6 Hadith collections |

---

## Data Sources

| Source | URL | License |
|--------|-----|---------|
| Quran text + translation | api.quran.com/api/v4 | Free, no key |
| Hadith collections | cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1 | MIT |
| Base model | huggingface.co/unsloth/Llama-3.2-3B-Instruct | Llama 3.2 Community |

---

## Important Notes

- This project is **completely separate** from the main Flutter app
- Do **not** copy any files into the main app until Phase 6 local testing passes
- Model files (`*.gguf`) are gitignored — store on Google Drive or HuggingFace
- Raw data is gitignored — re-download using Phase 1 scripts if needed
- See `docs/training_log.md` to track each training run

---

## Docs

- [Architecture](docs/architecture.md)
- [Training Log](docs/training_log.md)
- [Evaluation Results](docs/evaluation_results.md)
- [Integration Guide](docs/integration_guide.md)
