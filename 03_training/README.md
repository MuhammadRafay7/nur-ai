# Phase 3 — Model Training (Google Colab)

Fine-tune Llama 3.2 3B Instruct on the Islamic Q&A dataset using QLoRA on a free T4 GPU.

**Status: LOCKED — complete Phase 2 validation first.**

---

## What This Phase Does

Takes the `train.jsonl` + `eval.jsonl` from Phase 2 and produces a fine-tuned LoRA adapter:

```
train.jsonl + eval.jsonl
         ↓
   Llama 3.2 3B (base)
   + QLoRA fine-tuning
   + Unsloth acceleration
         ↓
   LoRA adapter weights → 05_model_output/checkpoints/
```

---

## Notebooks (run in order on Google Colab)

| Notebook | Purpose | Est. Time |
|----------|---------|-----------|
| `01_setup_environment.ipynb` | Install packages, verify GPU | 5 min |
| `02_load_base_model.ipynb` | Load Llama 3.2 3B, verify no OOM | 3 min |
| `03_train_qlora.ipynb` | Full training run (3 epochs) | 3–4 hours |
| `04_evaluate_model.ipynb` | Run test questions, check references | 30 min |
| `05_export_gguf.ipynb` | Merge adapter + export to GGUF | 20 min |

---

## Training Config

```yaml
model: unsloth/Llama-3.2-3B-Instruct
load_in_4bit: true
max_seq_length: 2048
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
per_device_train_batch_size: 2
gradient_accumulation_steps: 4       # effective batch = 8
warmup_steps: 50
num_train_epochs: 3
learning_rate: 2e-4
fp16: true
optim: adamw_8bit
lr_scheduler_type: cosine
seed: 42
```

---

## System Prompt (injected during training)

```
You are an Islamic knowledge assistant trained exclusively on the Quran
and authenticated Hadith collections. You always cite exact references
(Surah:Ayah or Collection:Number). You do not answer questions outside
Islamic knowledge. You present Arabic text alongside translations.
You note the grade of every Hadith you cite (Sahih, Hasan, etc).
```

---

## How to Run

1. Upload `train.jsonl` and `eval.jsonl` to your Google Drive
2. Open each notebook in Colab (in order)
3. Set `Runtime → Change runtime type → T4 GPU`
4. Run all cells in each notebook
5. Adapter weights will be saved to your Drive automatically

---

## What Gets Saved

```
05_model_output/
├── checkpoints/
│   ├── checkpoint-100/     ← saved every 100 steps
│   ├── checkpoint-200/
│   └── ...
└── (merged + GGUF from Notebook 05)
```
