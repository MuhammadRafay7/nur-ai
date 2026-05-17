# Phase 5 — Model Output

Storage for all model artifacts: checkpoints, merged model, and final GGUF files.

**Note: All files in this folder are gitignored (too large for git).**
Store on Google Drive or HuggingFace (free private repo).

---

## Folder Structure

```
05_model_output/
├── checkpoints/          ← LoRA adapter checkpoints saved during training
│   ├── checkpoint-100/
│   ├── checkpoint-200/
│   └── final_adapter/    ← final trained LoRA weights
│
├── merged/               ← base model + LoRA merged into one full model
│   └── (safetensors files, ~6GB)
│
└── gguf/
    ├── islamic_llm_q4_k_m.gguf    ← PRIMARY — use this in Flutter (~1.7 GB)
    └── islamic_llm_q8_0.gguf      ← BACKUP — higher quality, larger (~3.2 GB)
```

---

## GGUF Format Reference

| Format | Size | Quality | Use Case |
|--------|------|---------|----------|
| Q2_K | ~1.1 GB | Fair | Minimum viable mobile |
| Q3_K_M | ~1.3 GB | Good | Low-end devices |
| Q4_K_M | ~1.7 GB | Very Good | **Recommended for mobile** |
| Q8_0 | ~3.2 GB | Best | Desktop / testing only |

---

## How Files Are Created

- `checkpoints/` — auto-saved during Colab Notebook 03
- `merged/` — created by Colab Notebook 05 (merge LoRA + base)
- `gguf/` — created by Colab Notebook 05 (convert + quantize)

---

## Uploading to HuggingFace (free)

```python
# In Colab Notebook 05:
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj="islamic_llm_q4_k_m.gguf",
    path_in_repo="islamic_llm_q4_k_m.gguf",
    repo_id="your-username/islamic-llm",
    repo_type="model",
    token="hf_your_token"
)
```

Set the repo to **private** so only your app can download it.
