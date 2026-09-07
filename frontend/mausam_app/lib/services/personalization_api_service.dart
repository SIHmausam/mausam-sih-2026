import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/personalized_card.dart';
import 'token_storage_service.dart';

class PersonalizationApiService {
  static final TokenStorageService _tokenStorage = TokenStorageService();

  static Future<List<PersonalizedCard>> getPersonalizedCards({
    required double latitude,
    required double longitude,
    required String city,
  }) async {
    final accessToken = await _tokenStorage.getAccessToken();

    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('Authentication required');
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/personalization')
        .replace(
          queryParameters: {
            'latitude': latitude.toString(),
            'longitude': longitude.toString(),
            'city': city,
          },
        );

    final response = await http
        .get(uri, headers: {'Authorization': 'Bearer $accessToken'})
        .timeout(const Duration(seconds: 20));

    if (response.statusCode != 200) {
      String message =
          'Personalization request failed (${response.statusCode})';

      try {
        final body = jsonDecode(response.body);

        if (body is Map<String, dynamic> && body['detail'] != null) {
          message = body['detail'].toString();
        }
      } catch (_) {}

      throw Exception(message);
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final cards = body['cards'];

    if (cards is! List) {
      throw Exception('Invalid personalization response');
    }

    return cards
        .whereType<Map<String, dynamic>>()
        .map(
          (item) => PersonalizedCard(
            cardId: item['card'].toString(),
            rank: (item['rank'] as num).toInt(),
            score: item['score'] == null
                ? 0
                : (item['score'] as num).toDouble(),
            insight: item['insight']?.toString() ?? '',
          ),
        )
        .toList();
  }
}
