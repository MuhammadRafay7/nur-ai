# Integration Guide

How to integrate the Islamic AI model into the main Flutter app after Phase 6 passes.

**Read the Phase 7 README for the actual step-by-step instructions.**
This document explains the higher-level decisions.

---

## Pre-integration Checklist

Before touching the main app:

- [ ] Phase 6 batch test: reference accuracy >= 90%
- [ ] Phase 6 batch test: refusal accuracy >= 95%
- [ ] Phase 6 CLI chat: qualitative review passes
- [ ] GGUF file uploaded to HuggingFace (private repo)
- [ ] Model download URL tested and working
- [ ] File size verified: <= 2 GB

---

## What NOT to do

- Do not run the Python training scripts in the Flutter project
- Do not commit `.gguf` files to git (they are gitignored)
- Do not hardcode the HuggingFace download URL in the app — put it in a config file
- Do not load the model in the Flutter UI thread — use an isolate

---

## Key Integration Points

### Model Loading
The model takes 2–5 seconds to load into memory on a modern phone.
Show a loading indicator. Load it once at app startup and keep it in memory.

### Streaming Responses
The model generates one token at a time. Use Flutter's `StreamBuilder` to show
text appearing incrementally — this feels much more responsive than waiting for
the full response.

### Memory Management
The model uses ~2 GB of RAM while loaded. On low-end devices (< 3 GB RAM total),
the OS may kill the app. Add a memory check before loading.

### First Launch
On first launch, the user must download the model (~1.7 GB).
Show a clear progress indicator and an explanation of why the download is needed.
Store the model in the app's documents directory (survives app updates).
