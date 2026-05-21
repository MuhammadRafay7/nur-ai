#!/usr/bin/env python3
"""
reference_validator.py — Validate that Quran and Hadith references cited in
a model answer actually exist in the ground-truth index files.

Usage:
    from reference_validator import ReferenceValidator
    v = ReferenceValidator()
    result = v.validate_answer("See Quran 2:255 and Bukhari 1...")
    print(result)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

INDEX_DIR = Path(__file__).parent.parent.parent / "06_local_test_harness" / "reference_index"
QURAN_INDEX_PATH  = INDEX_DIR / "quran_index.json"
HADITH_INDEX_PATH = INDEX_DIR / "hadith_index.json"

QURAN_PATTERN  = re.compile(r"\b(\d{1,3})\s*:\s*(\d{1,3})\b")
HADITH_PATTERN = re.compile(
    r"\b(?:(?:Sahih\s+)?(?:Bukhari|Muslim|Tirmidhi|Abu\s+Dawud|Ibn\s+Majah|Nasa['’i]+|Nasai|Muwatta|Malik|"
    r"Riyadh\s+al-Salihin|Nawawi|Mishkat|Bulugh|Hisn|Adab|Qudsi|Shamail|Darimi|Ahmad))\s*[#:,\s]*(\d+)\b",
    re.IGNORECASE,
)
COLLECTION_NORMALISE = {
    "bukhari": "bukhari", "sahih bukhari": "bukhari",
    "muslim": "muslim", "sahih muslim": "muslim",
    "tirmidhi": "tirmidhi",
    "abu dawud": "abu_dawud", "abudawud": "abu_dawud",
    "ibn majah": "ibn_majah", "ibnmajah": "ibn_majah",
    "nasai": "nasai", "nasa'i": "nasai",
    "muwatta": "muwatta_malik", "malik": "muwatta_malik",
    "riyadh al-salihin": "riyadh_al_salihin",
    "nawawi": "nawawi_40",
    "mishkat": "mishkat_al_masabih",
    "bulugh": "bulugh_al_maram",
    "hisn": "hisn_al_muslim",
    "adab": "al_adab_al_mufrad",
    "qudsi": "hadith_qudsi",
    "shamail": "shamail_muhammadiyya",
    "ahmad": "musnad_ahmad",
}


@dataclass
class ValidationResult:
    quran_cited:     list[str] = field(default_factory=list)
    quran_valid:     list[str] = field(default_factory=list)
    quran_invalid:   list[str] = field(default_factory=list)
    hadith_cited:    list[str] = field(default_factory=list)
    hadith_valid:    list[str] = field(default_factory=list)
    hadith_invalid:  list[str] = field(default_factory=list)

    @property
    def has_fabrication(self) -> bool:
        return bool(self.quran_invalid or self.hadith_invalid)

    @property
    def quran_accuracy(self) -> float:
        total = len(self.quran_cited)
        return len(self.quran_valid) / total if total else 1.0

    @property
    def hadith_accuracy(self) -> float:
        total = len(self.hadith_cited)
        return len(self.hadith_valid) / total if total else 1.0

    def summary(self) -> str:
        lines = []
        lines.append(f"Quran  refs: {len(self.quran_cited):3d}  valid={len(self.quran_valid)}  invalid={len(self.quran_invalid)}")
        lines.append(f"Hadith refs: {len(self.hadith_cited):3d}  valid={len(self.hadith_valid)}  invalid={len(self.hadith_invalid)}")
        if self.quran_invalid:
            lines.append(f"  FABRICATED QURAN : {self.quran_invalid}")
        if self.hadith_invalid:
            lines.append(f"  FABRICATED HADITH: {self.hadith_invalid}")
        return "\n".join(lines)


class ReferenceValidator:
    def __init__(self) -> None:
        self._quran_map:  dict[str, int] = {}   # "surah:ayah" → max_ayah
        self._hadith_map: dict[str, int] = {}   # "collection" → total_count
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._load_quran_index()
        self._load_hadith_index()
        self._loaded = True

    def _load_quran_index(self) -> None:
        if not QURAN_INDEX_PATH.exists():
            print(f"[WARN] Quran index not found: {QURAN_INDEX_PATH}")
            return
        data = json.loads(QURAN_INDEX_PATH.read_text(encoding="utf-8"))
        for surah in data.get("surahs", []):
            snum = surah["number"]
            self._quran_map[str(snum)] = surah["ayahs"]

    def _load_hadith_index(self) -> None:
        if not HADITH_INDEX_PATH.exists():
            print(f"[WARN] Hadith index not found: {HADITH_INDEX_PATH}")
            return
        data = json.loads(HADITH_INDEX_PATH.read_text(encoding="utf-8"))
        for col in data.get("collections", []):
            key = col.get("sunnah_com_key") or col["key"].lower().replace(" ", "_")
            self._hadith_map[key] = col["total"]

    def _quran_ref_valid(self, surah: str, ayah: str) -> bool:
        max_ayah = self._quran_map.get(surah)
        if max_ayah is None:
            return False
        return 1 <= int(ayah) <= max_ayah

    def _hadith_ref_valid(self, collection_raw: str, number: str) -> bool:
        key = COLLECTION_NORMALISE.get(collection_raw.lower().strip())
        if key is None:
            return True  # unknown collection — don't flag as fabrication
        total = self._hadith_map.get(key)
        if total is None:
            return True  # not in index — skip
        return 1 <= int(number) <= total

    def validate_answer(self, answer: str) -> ValidationResult:
        self._load()
        result = ValidationResult()

        for m in QURAN_PATTERN.finditer(answer):
            surah, ayah = m.group(1), m.group(2)
            ref = f"{surah}:{ayah}"
            if ref not in result.quran_cited:
                result.quran_cited.append(ref)
                if self._quran_ref_valid(surah, ayah):
                    result.quran_valid.append(ref)
                else:
                    result.quran_invalid.append(ref)

        for m in HADITH_PATTERN.finditer(answer):
            collection = m.group(0).rsplit(m.group(1), 1)[0].strip(" #:,")
            number = m.group(1)
            ref = f"{collection} #{number}"
            if ref not in result.hadith_cited:
                result.hadith_cited.append(ref)
                if self._hadith_ref_valid(collection, number):
                    result.hadith_valid.append(ref)
                else:
                    result.hadith_invalid.append(ref)

        return result


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "See Quran 2:255 (Ayat al-Kursi) and Bukhari #1 about intentions. "
        "Also Quran 999:99 is mentioned (fake). And Bukhari #99999 (out of range)."
    )
    v = ReferenceValidator()
    res = v.validate_answer(text)
    print(res.summary())
    print("Has fabrication:", res.has_fabrication)
