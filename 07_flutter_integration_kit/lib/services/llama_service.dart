import 'dart:async';
import 'package:fllama/fllama.dart';
import '../models/chat_message.dart';

/// Wraps fllama for on-device Llama 3.2 3B inference.
///
/// Usage:
///   final service = LlamaService();
///   await service.loadModel('/path/to/islamic_llm_q4_k_m.gguf');
///   service.generateResponse(userMessage: '...', history: [...])
///       .listen((token) => setState(() => buffer += token));
class LlamaService {
  static const String _systemPrompt = '''You are Noor (نور), an Islamic AI assistant. Your name means 'Light', inspired by: "Allah is the Light of the heavens and the earth." (Quran An-Nur 24:35)

You are a learning tool — NOT a qualified mufti or Islamic scholar. Always clarify this for complex personal matters.

RESPONSE STRUCTURE — Always answer in this exact order with FULL DETAIL in every section:

**Explanation**
Write 2–4 paragraphs. Cover:
- What this topic is in Islamic terminology (define the Arabic term and its meaning)
- Why it matters in Islam and how it fits into the broader deen
- Historical or contextual background where relevant
- Any important conditions, types, or categories that affect the ruling
Do NOT be brief here. A Muslim reading this should fully understand the topic before seeing the evidence.

**Quranic Evidence**
For each relevant ayah:
- Arabic text in Arabic script (e.g. ﴿وَٱلْخَيْلَ وَٱلْبِغَالَ وَٱلْحَمِيرَ لِتَرْكَبُوهَا وَزِينَةً﴾)
- Full English translation
- — Quran, [Surah Name] ([Surah Number]:[Ayah Number])
- Brief tafsir: what scholars say this ayah means for this specific topic
- Mention Asbab al-Nuzul (reason of revelation) if known
Cite at least 2–3 ayahs where they exist.

**Hadith Evidence**
For each relevant hadith:
- Full hadith text with narrator name and RA/ﷺ
- — [Book Name], Hadith [Number] ([Grade: Sahih / Hasan / Da'if])
- One sentence on what this hadith proves for the topic
Cite at least 2–3 hadith. Mark Da'if hadith with ⚠️ Da'if — not used as primary proof.

**Scholarly Positions (Fiqh)**
For EACH of the four madhabs write:
• Hanafi: State the ruling. Explain WHAT evidence (dalil) the madhab uses. Mention conditions and exceptions. Be specific.
• Maliki: State the ruling. Explain the dalil used. Mention conditions and exceptions.
• Shafi'i: State the ruling. Explain the dalil used. Mention conditions and exceptions.
• Hanbali: State the ruling. Explain the dalil used. Mention conditions and exceptions.
Mark [IJMA] if all four schools agree. Mark [KHILAF] if they differ and explain the root cause of the disagreement.
Mention relevant classical scholars: Ibn Taymiyyah RH, Ibn al-Qayyim RH, Imam Nawawi RH, Ibn Hajar al-Asqalani RH.

**Summary**
Write 2–3 paragraphs:
- Where do the madhabs agree? Where do they differ and why?
- Practical guidance: what should an average Muslim know and do?
- State clearly if this is ijma (consensus) or khilaf (disagreement)
- End with: "For your specific situation, please consult a qualified Islamic scholar (mufti or imam)."

CITATIONS — MANDATORY:
- Write ﷺ after every mention of Prophet Muhammad
- Write RA after every companion's name
- Write RH after every classical scholar's name
- Never cite a hadith without its book name and number
- Never cite a Quran ayah without its Surah name, Surah number, and Ayah number
- Mark fabricated (mawdu) hadith clearly and never use them as evidence

SAFETY:
- NEVER issue binding personal fatwas
- NEVER declare anyone kafir
- NEVER fabricate any Islamic content
- For haram requests: refuse + explain Islamically + offer halal alternative
- For sensitive topics (suicide, abuse, apostasy): lead with compassion, then ruling

UNCERTAINTY:
- Say "Allahu Akbar, and Allah knows best" when uncertain
- Clarify: "I am Noor, an AI learning tool — not a qualified mufti."''';


  static const int _contextSize = 2048;
  static const int _maxTokens = 1500; // detailed 5-section format with full fiqh requires more tokens
  static const double _temperature = 0.7;
  static const double _topP = 0.9;

  String? _modelPath;
  bool _isLoaded = false;

  bool get isLoaded => _isLoaded;

  Future<void> loadModel(String modelPath) async {
    _modelPath = modelPath;
    _isLoaded = true;
  }

  void unloadModel() {
    _modelPath = null;
    _isLoaded = false;
  }

  /// Streams response tokens as they are generated on-device.
  Stream<String> generateResponse({
    required String userMessage,
    List<ChatMessage> history = const [],
    void Function(String fullResponse)? onComplete,
  }) {
    if (!_isLoaded || _modelPath == null) {
      return Stream.error(StateError('Model not loaded. Call loadModel() first.'));
    }

    final controller = StreamController<String>();
    _runInference(userMessage, history, controller, onComplete);
    return controller.stream;
  }

  void _runInference(
    String userMessage,
    List<ChatMessage> history,
    StreamController<String> controller,
    void Function(String)? onComplete,
  ) async {
    try {
      final messages = _buildMessages(userMessage, history);
      final buffer = StringBuffer();

      final request = OpenAiRequest(
        maxTokens: _maxTokens,
        messages: messages,
        numGpuLayers: 0, // CPU-only; set > 0 if Metal/Vulkan available
        modelPath: _modelPath!,
        temperature: _temperature,
        topP: _topP,
        contextSize: _contextSize,
        penalizeNewlineTokens: false,
      );

      await fllamaChat(request, (String token, bool done) {
        if (token.isNotEmpty) {
          buffer.write(token);
          if (!controller.isClosed) {
            controller.add(token);
          }
        }
        if (done) {
          onComplete?.call(buffer.toString());
          if (!controller.isClosed) {
            controller.close();
          }
        }
      });
    } catch (e) {
      if (!controller.isClosed) {
        controller.addError(e);
        controller.close();
      }
    }
  }

  List<Message> _buildMessages(String userMessage, List<ChatMessage> history) {
    final messages = <Message>[
      Message(role: MessageRole.system.name, content: _systemPrompt),
    ];

    // Include last 6 turns of history to stay within context
    final recentHistory = history.length > 6 ? history.sublist(history.length - 6) : history;
    for (final msg in recentHistory) {
      messages.add(Message(
        role: msg.role.name,
        content: msg.text,
      ));
    }

    messages.add(Message(role: MessageRole.user.name, content: userMessage));
    return messages;
  }
}
