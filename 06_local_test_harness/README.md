# Phase 6 — Local Test Harness

Test the GGUF model in a terminal chatbot and batch tester before touching Flutter.

**Status: LOCKED — complete Phase 5 (GGUF export) first.**

---

## Scripts

| Script | Purpose |
|--------|---------|
| `cli_chat.py` | Interactive terminal chatbot using the GGUF |
| `api_server.py` | FastAPI server (test from Postman or browser) |
| `batch_test.py` | Run all evaluation questions, save results |

---

## Reference Index Files

These JSON files are used to validate that the model's citations are real:

```
reference_index/
├── quran_index.json     ← all valid "surah:ayah" keys (6236 entries)
└── hadith_index.json    ← all valid "collection:number" keys (30,000+ entries)
```

These are generated automatically from Phase 1 raw data.

---

## How to Run

### Terminal Chatbot

```bash
cd 06_local_test_harness

python cli_chat.py --model-path ../05_model_output/gguf/islamic_llm_q4_k_m.gguf
```

Commands inside the chat:
- `/quit` — exit
- `/reset` — clear conversation history
- `/save` — save conversation to a JSON file

---

### API Server (optional)

```bash
python api_server.py --model-path ../05_model_output/gguf/islamic_llm_q4_k_m.gguf

# Then test from another terminal:
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What does Islam say about patience?"}'
```

---

### Batch Test

```bash
python batch_test.py \
  --model-path ../05_model_output/gguf/islamic_llm_q4_k_m.gguf \
  --questions-dir ../04_evaluation/test_questions \
  --output-dir ../04_evaluation/reports
```

---

## Pass Criteria Before Flutter Integration

All of the following must be true before moving to Phase 7:

- [ ] CLI chat produces accurate, referenced answers
- [ ] No fabricated Surah or Hadith references in batch test
- [ ] Out-of-scope questions are politely refused
- [ ] Arabic text appears in all Quran-citing responses
- [ ] Response time < 30 seconds on a modern laptop (CPU)
- [ ] Model loads without crashing (memory check)
