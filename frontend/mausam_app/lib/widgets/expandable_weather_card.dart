import 'dart:ui';

import 'package:flutter/material.dart';

import '../services/card_mapper.dart';

class ExpandableWeatherCard extends StatelessWidget {
  final CardDisplayData card;
  final bool featured;
  final VoidCallback? onTap;

  const ExpandableWeatherCard({
    super.key,
    required this.card,
    this.featured = false,
    this.onTap,
  });

  Widget _miniDetails() {
    if (card.details.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(
        children: [
          for (int i = 0; i < card.details.length; i++) ...[
            if (i > 0) const SizedBox(height: 5),
            Row(
              children: [
                Expanded(
                  child: Text(
                    card.details[i].split(':').first.trim(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.58),
                      fontSize: 10.5,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Flexible(
                  child: Text(
                    card.details[i].contains(':')
                        ? card.details[i].substring(
                            card.details[i].indexOf(':') + 1,
                          ).trim()
                        : '—',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.right,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final radius = featured ? 22.0 : 18.0;

    return GestureDetector(
      onTap: onTap,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
          child: Container(
            width: double.infinity,
            padding: EdgeInsets.all(featured ? 17 : 14),
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: featured ? 0.17 : 0.14),
              borderRadius: BorderRadius.circular(radius),
              border: Border.all(
                color: Colors.white.withValues(alpha: featured ? 0.28 : 0.22),
              ),
            ),
            child: Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: featured ? 46 : 42,
                      height: featured ? 46 : 42,
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.14),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        card.icon,
                        color: Colors.white,
                        size: featured ? 23 : 21,
                      ),
                    ),
                    SizedBox(width: featured ? 14 : 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            card.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.78),
                              fontSize: featured ? 13 : 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  card.value,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: featured ? 23 : 18,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Flexible(
                                child: Text(
                                  card.status,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.82),
                                    fontSize: featured ? 12.5 : 11.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    Column(
                      children: [
                        Container(
                          width: 9,
                          height: 9,
                          decoration: BoxDecoration(
                            color: card.indicatorColor,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: card.indicatorColor.withValues(
                                  alpha: 0.5,
                                ),
                                blurRadius: 7,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 12),
                        Icon(
                          Icons.chevron_right_rounded,
                          color: Colors.white.withValues(alpha: 0.55),
                          size: 21,
                        ),
                      ],
                    ),
                  ],
                ),
                if (featured) ...[
                  _miniDetails(),
                  const SizedBox(height: 10),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 11,
                      vertical: 9,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(13),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.13),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.auto_awesome_rounded,
                          color: Colors.white.withValues(alpha: 0.72),
                          size: 14,
                        ),
                        const SizedBox(width: 7),
                        Expanded(
                          child: Text(
                            card.insight,
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.72),
                              fontSize: 11.5,
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
