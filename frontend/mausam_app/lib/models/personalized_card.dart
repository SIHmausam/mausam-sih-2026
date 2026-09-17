class PersonalizedCard {
  final String cardId;
  final int rank;
  final double score;
  final String insight;

  const PersonalizedCard({
    required this.cardId,
    required this.rank,
    required this.score,
    required this.insight,
  });

  PersonalizedCard copyWith({
    String? cardId,
    int? rank,
    double? score,
    String? insight,
  }) {
    return PersonalizedCard(
      cardId: cardId ?? this.cardId,
      rank: rank ?? this.rank,
      score: score ?? this.score,
      insight: insight ?? this.insight,
    );
  }
}