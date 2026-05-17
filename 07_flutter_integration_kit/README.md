# Phase 7 — Flutter Integration Kit

Drop-in files for integrating the Islamic AI model into the main Flutter app.

**Status: LOCKED — complete Phase 6 local testing first.**
**DO NOT copy these files into the main app until Phase 6 passes all checks.**

---

## What to Copy Into the Main App

```
07_flutter_integration_kit/
├── lib/                        ← copy entire lib/ into your main app's lib/
│   ├── services/
│   │   ├── llama_service.dart         → lib/services/llama_service.dart
│   │   ├── model_downloader.dart      → lib/services/model_downloader.dart
│   │   └── reference_validator.dart   → lib/services/reference_validator.dart
│   ├── models/
│   │   ├── chat_message.dart          → lib/models/chat_message.dart
│   │   └── islamic_reference.dart     → lib/models/islamic_reference.dart
│   └── widgets/
│       ├── message_bubble.dart        → lib/widgets/message_bubble.dart
│       └── reference_card.dart        → lib/widgets/reference_card.dart
│
├── assets/                     ← copy into your main app's assets/
│   ├── quran_index.json               → assets/quran_index.json
│   └── hadith_index.json              → assets/hadith_index.json
│
└── pubspec_additions.yaml      ← add these dependencies to your pubspec.yaml
```

---

## Step-by-Step Integration Guide

### Step 1 — Add Dependencies

Open `pubspec_additions.yaml` and add the listed packages to your main app's `pubspec.yaml`:

```yaml
dependencies:
  flutter_llama_cpp: ^0.1.0
  dio: ^5.4.3
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  flutter_markdown: ^0.6.22
  path_provider: ^2.1.3
  percent_indicator: ^4.2.3
```

Then run:
```bash
flutter pub get
```

### Step 2 — Add Assets

In your main app's `pubspec.yaml`:
```yaml
flutter:
  assets:
    - assets/quran_index.json
    - assets/hadith_index.json
```

Copy the JSON files:
```bash
cp 07_flutter_integration_kit/assets/quran_index.json  your_app/assets/
cp 07_flutter_integration_kit/assets/hadith_index.json your_app/assets/
```

### Step 3 — Copy Dart Files

```bash
cp -r 07_flutter_integration_kit/lib/services/  your_app/lib/services/
cp -r 07_flutter_integration_kit/lib/models/    your_app/lib/models/
cp -r 07_flutter_integration_kit/lib/widgets/   your_app/lib/widgets/
```

### Step 4 — Add Model Download Screen

On first app launch, show a download screen using `ModelDownloader`:

```dart
import 'services/model_downloader.dart';

final downloader = ModelDownloader();
if (!await downloader.checkModelExists()) {
  // Show download UI — see widgets/model_download_screen.dart
  await downloader.downloadModel(
    url: 'https://huggingface.co/your-username/islamic-llm/resolve/main/islamic_llm_q4_k_m.gguf',
    savePath: await downloader.getDefaultModelPath(),
    onProgress: (double progress) { setState(() => _progress = progress); },
  );
}
```

### Step 5 — Initialize and Use the Chat

```dart
import 'services/llama_service.dart';

final llama = LlamaService();
await llama.loadModel(modelPath);

// Stream tokens as they generate
Stream<String> response = llama.generateResponse(
  userMessage: "What does Islam say about patience?",
  history: chatHistory,
);
```

---

## Architecture in the Main App

```
User types message
       ↓
LlamaService.generateResponse()
       ↓
Model generates tokens (streaming)
       ↓
ReferenceValidator.validateResponse()   ← checks citations are real
       ↓
Display in MessageBubble + ReferenceCard widgets
```

---

## Model Download Info

| Item | Detail |
|------|--------|
| Model file | `islamic_llm_q4_k_m.gguf` |
| Size | ~1.7 GB |
| Download | Once on first launch |
| Storage | App's documents directory |
| Offline | Fully offline after download |

---

## Platform Requirements

| Platform | Min Version |
|----------|------------|
| Android | API 26 (Android 8.0) |
| iOS | iOS 14.0 |
| RAM required | 4 GB recommended |
| Storage | ~2 GB free |
