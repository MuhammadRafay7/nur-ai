import 'package:flutter/material.dart';
import '../models/islamic_reference.dart';

class ReferenceCard extends StatelessWidget {
  final IslamicReference reference;

  const ReferenceCard({super.key, required this.reference});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final isQuran = reference.type == ReferenceType.quran;

    return Container(
      margin: const EdgeInsets.only(top: 4),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: isQuran
            ? colors.secondaryContainer.withOpacity(0.6)
            : colors.tertiaryContainer.withOpacity(0.6),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: reference.isVerified
              ? (isQuran ? colors.secondary : colors.tertiary)
              : colors.outline.withOpacity(0.4),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isQuran ? Icons.menu_book_rounded : Icons.auto_stories_rounded,
            size: 14,
            color: isQuran ? colors.secondary : colors.tertiary,
          ),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              reference.displayTitle,
              style: TextStyle(
                fontSize: 12,
                color: isQuran ? colors.onSecondaryContainer : colors.onTertiaryContainer,
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (reference.isVerified) ...[
            const SizedBox(width: 6),
            Icon(
              Icons.verified_rounded,
              size: 12,
              color: isQuran ? colors.secondary : colors.tertiary,
            ),
          ],
        ],
      ),
    );
  }
}
