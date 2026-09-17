import 'dart:convert';
import 'dart:math';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import 'token_storage_service.dart';

class ChatbotApiService {
  final TokenStorageService _tokenStorage = TokenStorageService();

  Future<Map<String, String>> _headers() async {
    final accessToken = await _tokenStorage.getAccessToken();

    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('You are not authenticated.');
    }

    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    };
  }

  Future<String> ask({
    required String sessionId,
    required String question,
    double? latitude,
    double? longitude,
  }) async {
    if ((latitude == null) != (longitude == null)) {
      throw ArgumentError(
        'Latitude and longitude must be provided together.',
      );
    }

    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/chatbot/ask',
    );

    final payload = <String, dynamic>{
      'session_id': sessionId,
      'question': question,
      'latitude': latitude,
      'longitude': longitude,
    };

    final response = await http
        .post(
          uri,
          headers: await _headers(),
          body: jsonEncode(payload),
        )
        .timeout(const Duration(seconds: 35));

    final body = jsonDecode(response.body);

    if (response.statusCode == 200) {
      final answer = body['answer'];

      if (answer is String && answer.trim().isNotEmpty) {
        return answer;
      }

      throw Exception('Mausam returned an empty response.');
    }

    if (response.statusCode == 400 ||
        response.statusCode == 422 ||
        response.statusCode == 503) {
      final detail = body['detail'];

      if (detail is String && detail.trim().isNotEmpty) {
        throw Exception(detail);
      }

      throw Exception('Mausam could not process your request.');
    }

    throw Exception(
      'Mausam request failed (${response.statusCode}).',
    );
  }

  String createSessionId() {
    final timestamp = DateTime.now().microsecondsSinceEpoch;
    final random = Random().nextInt(1 << 32);
    return 'flutter-$timestamp-$random';
  }
}
