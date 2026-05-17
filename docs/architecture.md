# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   TRAINING PIPELINE                      │
│                                                          │
│  Phase 1          Phase 2          Phase 3               │
│  Raw Data    →    Dataset      →   Fine-tune             │
│  (JSON)           (JSONL)          (Colab T4)            │
│                                        ↓                 │
│  Phase 6          Phase 5          Phase 4               │
│  Local Test  ←    GGUF         ←   Evaluate              │
│  Harness          Export            Model                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   FLUTTER APP                            │
│                                                          │
│  Phase 7: Integration Kit                                │
│                                                          │
│  User Input                                              │
│      ↓                                                   │
│  LlamaService (llama.cpp on-device)                      │
│      ↓                                                   │
│  ReferenceValidator (checks citations)                   │
│      ↓                                                   │
│  MessageBubble + ReferenceCard (UI)                      │
└─────────────────────────────────────────────────────────┘
```

## Model Architecture

- **Base**: Meta Llama 3.2 3B Instruct (decoder-only transformer)
- **Parameters**: ~3.2 billion
- **Context window**: 2048 tokens (training), 4096 supported at inference
- **Fine-tuning method**: QLoRA (Quantized Low-Rank Adaptation)
  - Rank (r): 16
  - Alpha: 32
  - Target modules: attention + feed-forward projections
- **Quantization**: 4-bit (NF4) during training, Q4_K_M for inference

## Data Architecture

```
quran_full.json
└── surahs[]
    └── ayahs[]
        ├── arabic_text
        ├── english_translation
        ├── tafsir_ibn_kathir
        └── verse_key  (e.g. "2:153")

{collection}.json
└── hadiths[]
    ├── hadith_number
    ├── arabic_text
    ├── english_text
    └── grade
```

## Training Data Format (ChatML)

```
<|im_start|>system
You are an Islamic knowledge assistant...
<|im_end|>
<|im_start|>user
{instruction}
<|im_end|>
<|im_start|>assistant
{output}
<|im_end|>
```

## Inference Architecture (On-Device)

- Runtime: llama.cpp (C++ with GGUF format)
- Flutter binding: `flutter_llama_cpp` package
- Model loaded into RAM once at startup
- Streaming token generation via callback
- No internet required after model download
