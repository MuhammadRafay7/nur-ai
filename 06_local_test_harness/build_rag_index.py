#!/usr/bin/env python3
"""
build_rag_index.py — One-time script that builds BM25 search indices from
raw Phase 1 JSON data for Quran, Hadith, and Fiqh/Knowledge-Base.

Run this ONCE before using the RAG pipeline:
    python build_rag_index.py

Output (written to rag_index/):
    quran_docs.json     — flat list of Quran passage documents
    hadith_docs.json    — flat list of Hadith documents
    fiqh_docs.json      — flat list of Fiqh/KB documents
    quran_bm25.pkl      — serialised BM25Okapi index for Quran
    hadith_bm25.pkl     — serialised BM25Okapi index for Hadith
    fiqh_bm25.pkl       — serialised BM25Okapi index for Fiqh
    index_meta.json     — counts and build timestamp
"""

from __future__ import annotations

import json
import pickle
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    print("rank_bm25 not installed.  Run:  pip install rank-bm25")
    sys.exit(1)

from tqdm import tqdm

RAW_DIR   = Path(__file__).parent.parent / "01_data_collection" / "raw"
INDEX_DIR = Path(__file__).parent / "rag_index"
INDEX_DIR.mkdir(exist_ok=True)

QURAN_PATH   = RAW_DIR / "quran" / "quran_full.json"
HADITH_PATHS = sorted((RAW_DIR / "hadith").glob("*.json"))
KB_PATHS     = sorted((RAW_DIR / "knowledge_bases").glob("*.json"))
TAFSIR_PATHS = sorted((RAW_DIR / "tafsir").glob("*.json"))
CLASSICAL_PATHS = sorted((RAW_DIR / "classical").glob("*.json"))
FATWA_PATHS  = sorted((RAW_DIR / "fatwa").glob("*.json"))


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s؀-ۿ]", " ", text)
    return [t for t in text.split() if len(t) > 1]


# ─── Quran ────────────────────────────────────────────────────────────────────

def build_quran_docs() -> list[dict]:
    print("Building Quran documents...")
    if not QURAN_PATH.exists():
        print(f"  [SKIP] {QURAN_PATH} not found")
        return []

    data = json.loads(QURAN_PATH.read_text(encoding="utf-8"))
    docs = []
    for surah in tqdm(data["surahs"], desc="  Quran surahs"):
        snum  = surah["surah_number"]
        sname = surah["name_english"]
        sname_ar = surah["name_arabic"]
        revelation = surah.get("revelation_type", "")

        for ayah in surah["ayahs"]:
            anum   = ayah["ayah_number"]
            vkey   = ayah["verse_key"]
            arabic = ayah.get("arabic_text", "")
            trans  = ayah.get("english_translation", "")
            tafsir = ayah.get("tafsir_ibn_kathir", "")
            translit = ayah.get("transliteration", "")

            search_text = f"{sname} {trans} {tafsir[:300]}"
            docs.append({
                "id":           f"quran:{vkey}",
                "source":       "quran",
                "ref":          vkey,
                "surah_num":    snum,
                "surah_name":   sname,
                "surah_arabic": sname_ar,
                "surah_revelation": revelation,
                "ayah_num":     anum,
                "arabic":       arabic,
                "translation":  trans,
                "transliteration": translit,
                "tafsir":       tafsir,
                "search_text":  search_text,
            })
    print(f"  {len(docs):,} Quran ayah documents")
    return docs


# ─── Hadith ───────────────────────────────────────────────────────────────────

def build_hadith_docs() -> list[dict]:
    print("Building Hadith documents...")
    docs = []
    for path in tqdm(HADITH_PATHS, desc="  Hadith collections"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [SKIP] {path.name}: {e}")
            continue

        meta     = data.get("metadata", {})
        col_name = meta.get("name", path.stem)
        hadiths  = data.get("hadiths", [])
        if not isinstance(hadiths, list):
            continue

        for h in hadiths:
            num    = str(h.get("hadith_number", ""))
            arabic = h.get("arabic_text", "")
            english = h.get("english_text", "")
            grade  = h.get("grade", "")

            search_text = f"{col_name} {english[:400]}"
            docs.append({
                "id":         f"hadith:{path.stem}:{num}",
                "source":     "hadith",
                "collection": col_name,
                "collection_key": path.stem,
                "number":     num,
                "arabic":     arabic,
                "english":    english,
                "grade":      grade,
                "search_text": search_text,
            })
    print(f"  {len(docs):,} Hadith documents")
    return docs


# ─── Fiqh / Knowledge Base ────────────────────────────────────────────────────

def _flatten_value(key: str, value, source_file: str, prefix: str = "") -> list[dict]:
    """Recursively flatten nested dict/list KB entries into searchable documents."""
    docs = []
    full_key = f"{prefix}.{key}" if prefix else key

    if isinstance(value, str) and len(value) > 20:
        docs.append({
            "id":          f"fiqh:{source_file}:{full_key}",
            "source":      "fiqh",
            "file":        source_file,
            "topic":       full_key.replace("_", " ").replace(".", " → "),
            "content":     value,
            "search_text": f"{full_key.replace('_', ' ')} {value[:500]}",
        })
    elif isinstance(value, dict):
        for k, v in value.items():
            docs.extend(_flatten_value(k, v, source_file, full_key))
    elif isinstance(value, list):
        combined = " ".join(
            str(item) for item in value
            if isinstance(item, (str, int, float))
        )
        if combined.strip():
            docs.append({
                "id":          f"fiqh:{source_file}:{full_key}",
                "source":      "fiqh",
                "file":        source_file,
                "topic":       full_key.replace("_", " ").replace(".", " → "),
                "content":     combined[:1000],
                "search_text": f"{full_key.replace('_', ' ')} {combined[:500]}",
            })
        for i, item in enumerate(value):
            if isinstance(item, dict):
                docs.extend(_flatten_value(str(i), item, source_file, full_key))
    return docs


def build_fiqh_docs() -> list[dict]:
    print("Building Fiqh / KB documents...")
    docs = []
    all_paths = KB_PATHS + TAFSIR_PATHS + CLASSICAL_PATHS + FATWA_PATHS

    for path in tqdm(all_paths, desc="  KB files"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [SKIP] {path.name}: {e}")
            continue

        stem = path.stem
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "metadata":
                    continue
                docs.extend(_flatten_value(key, value, stem))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                docs.extend(_flatten_value(str(i), item, stem))

    print(f"  {len(docs):,} Fiqh/KB documents")
    return docs


# ─── Index builder ────────────────────────────────────────────────────────────

def build_and_save(docs: list[dict], name: str) -> None:
    if not docs:
        print(f"[SKIP] No documents for {name}")
        return

    tokenized = [tokenize(d["search_text"]) for d in docs]
    bm25 = BM25Okapi(tokenized)

    docs_path = INDEX_DIR / f"{name}_docs.json"
    bm25_path = INDEX_DIR / f"{name}_bm25.pkl"

    docs_path.write_text(json.dumps(docs, ensure_ascii=False), encoding="utf-8")
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25, f)

    print(f"  Saved {len(docs):,} docs → {docs_path.name}")
    print(f"  Saved BM25 index     → {bm25_path.name}")


def main() -> None:
    print("=" * 60)
    print("  Building RAG indices from raw Phase 1 data")
    print("=" * 60)
    print()

    quran_docs  = build_quran_docs()
    hadith_docs = build_hadith_docs()
    fiqh_docs   = build_fiqh_docs()

    print()
    print("Serialising indices...")
    build_and_save(quran_docs,  "quran")
    build_and_save(hadith_docs, "hadith")
    build_and_save(fiqh_docs,   "fiqh")

    meta = {
        "built_at":     datetime.now(timezone.utc).isoformat(),
        "quran_docs":   len(quran_docs),
        "hadith_docs":  len(hadith_docs),
        "fiqh_docs":    len(fiqh_docs),
        "total_docs":   len(quran_docs) + len(hadith_docs) + len(fiqh_docs),
    }
    (INDEX_DIR / "index_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print()
    print("=" * 60)
    print(f"  Done!  Total docs: {meta['total_docs']:,}")
    print(f"    Quran  : {meta['quran_docs']:,}")
    print(f"    Hadith : {meta['hadith_docs']:,}")
    print(f"    Fiqh   : {meta['fiqh_docs']:,}")
    print(f"  Index saved to: {INDEX_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
