enum ReferenceType { quran, hadith }

class IslamicReference {
  final ReferenceType type;

  // Quran fields
  final int? surahNumber;
  final String? surahName;
  final int? ayahNumber;

  // Hadith fields
  final String? collection;
  final int? hadithNumber;
  final String? grade; // "Sahih", "Hasan", etc.

  // Raw citation text as it appeared in the response
  final String rawText;

  final bool isVerified;

  const IslamicReference({
    required this.type,
    required this.rawText,
    this.surahNumber,
    this.surahName,
    this.ayahNumber,
    this.collection,
    this.hadithNumber,
    this.grade,
    this.isVerified = false,
  });

  String get displayTitle {
    if (type == ReferenceType.quran) {
      final name = surahName ?? 'Surah $surahNumber';
      final ayah = ayahNumber != null ? ':$ayahNumber' : '';
      return 'Quran $surahNumber$ayah — $name';
    } else {
      final num = hadithNumber != null ? ' #$hadithNumber' : '';
      final gr = grade != null ? ' ($grade)' : '';
      return '${collection ?? "Hadith"}$num$gr';
    }
  }

  @override
  String toString() => displayTitle;
}
