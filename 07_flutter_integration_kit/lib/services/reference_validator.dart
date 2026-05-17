import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/islamic_reference.dart';

// Matches: "Quran 2:255", "Surah Al-Baqarah 2:255", "(2:255)", "Quran (2:255)"
final _quranPattern = RegExp(
  r'(?:Quran|Surah\s+[\w\s\-]+)?\s*[\(（]?(\d{1,3})\s*:\s*(\d{1,3})[\)）]?',
  caseSensitive: false,
);

// Matches: "Sahih Bukhari 1234", "Muslim #7285", "Abu Dawud 1234", "Tirmidhi 1234"
final _hadithPattern = RegExp(
  r'\b(Sahih\s+(?:al-)?(?:Bukhari|Muslim)|(?:Sunan\s+)?(?:Abu\s+Dawud|Tirmidhi|Nasai|Ibn\s+Majah)|Musnad\s+Ahmad|Riyad\s+(?:us|as)-Salih[ie]?n|Muwatta)\s*[#,]?\s*(\d+)\b',
  caseSensitive: false,
);

/// Parses AI response text and validates citations against loaded indexes.
class ReferenceValidator {
  static ReferenceValidator? _instance;
  static ReferenceValidator get instance => _instance ??= ReferenceValidator._();
  ReferenceValidator._();

  Map<String, dynamic>? _quranIndex;
  Map<String, dynamic>? _hadithIndex;

  Future<void> loadIndexes() async {
    if (_quranIndex != null) return;
    final qRaw = await rootBundle.loadString('assets/quran_index.json');
    final hRaw = await rootBundle.loadString('assets/hadith_index.json');
    _quranIndex = json.decode(qRaw) as Map<String, dynamic>;
    _hadithIndex = json.decode(hRaw) as Map<String, dynamic>;
  }

  /// Extracts and validates all Islamic references from [responseText].
  Future<List<IslamicReference>> validate(String responseText) async {
    await loadIndexes();
    final refs = <IslamicReference>[];

    // Quran citations
    for (final match in _quranPattern.allMatches(responseText)) {
      final surah = int.tryParse(match.group(1) ?? '');
      final ayah = int.tryParse(match.group(2) ?? '');
      if (surah == null || surah < 1 || surah > 114) continue;

      final surahData = _quranIndex!['surahs']
          ?.firstWhere((s) => s['number'] == surah, orElse: () => null);
      final maxAyah = surahData?['ayahs'] as int?;
      final verified = maxAyah != null && ayah != null && ayah >= 1 && ayah <= maxAyah;

      refs.add(IslamicReference(
        type: ReferenceType.quran,
        rawText: match.group(0)!,
        surahNumber: surah,
        surahName: surahData?['name_transliteration'] as String?,
        ayahNumber: ayah,
        isVerified: verified,
      ));
    }

    // Hadith citations
    for (final match in _hadithPattern.allMatches(responseText)) {
      final collectionRaw = match.group(1)!.trim();
      final number = int.tryParse(match.group(2) ?? '');
      final collection = _normalizeCollection(collectionRaw);

      final collectionData = _hadithIndex!['collections']
          ?.firstWhere((c) => c['key'] == collection, orElse: () => null);
      final maxNum = collectionData?['total'] as int?;
      final verified = maxNum != null && number != null && number >= 1 && number <= maxNum;

      refs.add(IslamicReference(
        type: ReferenceType.hadith,
        rawText: match.group(0)!,
        collection: collection,
        hadithNumber: number,
        grade: collectionData?['default_grade'] as String?,
        isVerified: verified,
      ));
    }

    return refs;
  }

  String _normalizeCollection(String raw) {
    final lower = raw.toLowerCase().replaceAll(RegExp(r'\s+'), ' ').trim();
    if (lower.contains('bukhari')) return 'Sahih al-Bukhari';
    if (lower.contains('muslim')) return 'Sahih Muslim';
    if (lower.contains('abu dawud') || lower.contains('abu dawood')) return 'Sunan Abu Dawud';
    if (lower.contains('tirmidhi')) return 'Jami at-Tirmidhi';
    if (lower.contains('nasai') || lower.contains("nasa'i")) return "Sunan an-Nasa'i";
    if (lower.contains('ibn majah')) return 'Sunan Ibn Majah';
    if (lower.contains('ahmad')) return 'Musnad Ahmad';
    if (lower.contains('riyad')) return 'Riyad as-Salihin';
    if (lower.contains('muwatta')) return 'Muwatta Malik';
    return raw;
  }
}
