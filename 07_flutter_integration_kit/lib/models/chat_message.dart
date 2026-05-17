import 'islamic_reference.dart';

enum MessageRole { user, assistant }

enum MessageState { done, streaming, error }

class ChatMessage {
  final String id;
  final MessageRole role;
  final String text;
  final MessageState state;
  final List<IslamicReference> references;
  final DateTime timestamp;

  const ChatMessage({
    required this.id,
    required this.role,
    required this.text,
    this.state = MessageState.done,
    this.references = const [],
    required this.timestamp,
  });

  factory ChatMessage.user(String text) => ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch.toString(),
        role: MessageRole.user,
        text: text,
        timestamp: DateTime.now(),
      );

  factory ChatMessage.assistantStreaming() => ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch.toString(),
        role: MessageRole.assistant,
        text: '',
        state: MessageState.streaming,
        timestamp: DateTime.now(),
      );

  ChatMessage copyWith({
    String? text,
    MessageState? state,
    List<IslamicReference>? references,
  }) =>
      ChatMessage(
        id: id,
        role: role,
        text: text ?? this.text,
        state: state ?? this.state,
        references: references ?? this.references,
        timestamp: timestamp,
      );

  Map<String, dynamic> toJson() => {
        'role': role.name,
        'content': text,
      };
}
