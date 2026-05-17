import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../models/chat_message.dart';
import 'reference_card.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  bool get _isUser => message.role == MessageRole.user;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colors = theme.colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: _isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!_isUser) _Avatar(isUser: false),
          if (!_isUser) const SizedBox(width: 8),
          Flexible(
            child: Column(
              crossAxisAlignment: _isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                _Bubble(
                  message: message,
                  isUser: _isUser,
                  bgColor: _isUser
                      ? colors.primary
                      : colors.surfaceContainerHigh,
                  textColor: _isUser ? colors.onPrimary : colors.onSurface,
                ),
                if (message.references.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  ...message.references.map((r) => ReferenceCard(reference: r)),
                ],
              ],
            ),
          ),
          if (_isUser) const SizedBox(width: 8),
          if (_isUser) _Avatar(isUser: true),
        ],
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  final ChatMessage message;
  final bool isUser;
  final Color bgColor;
  final Color textColor;

  const _Bubble({
    required this.message,
    required this.isUser,
    required this.bgColor,
    required this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    final isStreaming = message.state == MessageState.streaming;
    final isEmpty = message.text.isEmpty && isStreaming;

    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.sizeOf(context).width * 0.78,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(18),
          topRight: const Radius.circular(18),
          bottomLeft: Radius.circular(isUser ? 18 : 4),
          bottomRight: Radius.circular(isUser ? 4 : 18),
        ),
      ),
      child: isEmpty
          ? _TypingIndicator(color: textColor)
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                MarkdownBody(
                  data: message.text,
                  styleSheet: MarkdownStyleSheet(
                    p: TextStyle(color: textColor, fontSize: 15, height: 1.5),
                    strong: TextStyle(color: textColor, fontWeight: FontWeight.w700),
                    em: TextStyle(color: textColor, fontStyle: FontStyle.italic),
                    code: TextStyle(
                      color: textColor,
                      backgroundColor: Colors.black12,
                      fontSize: 13,
                    ),
                  ),
                ),
                if (isStreaming) ...[
                  const SizedBox(height: 6),
                  _TypingIndicator(color: textColor.withOpacity(0.5)),
                ],
              ],
            ),
    );
  }
}

class _TypingIndicator extends StatefulWidget {
  final Color color;
  const _TypingIndicator({required this.color});

  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            final opacity = (((_ctrl.value * 3) - i).clamp(0.0, 1.0) *
                    (1 - ((_ctrl.value * 3) - i - 1).clamp(0.0, 1.0)))
                .abs();
            return Container(
              margin: const EdgeInsets.only(right: 4),
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: widget.color.withOpacity(0.3 + opacity * 0.7),
              ),
            );
          }),
        );
      },
    );
  }
}

class _Avatar extends StatelessWidget {
  final bool isUser;
  const _Avatar({required this.isUser});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return CircleAvatar(
      radius: 16,
      backgroundColor: isUser ? colors.primaryContainer : colors.tertiaryContainer,
      child: Text(
        isUser ? '👤' : 'نور',
        style: const TextStyle(fontSize: 11),
      ),
    );
  }
}
