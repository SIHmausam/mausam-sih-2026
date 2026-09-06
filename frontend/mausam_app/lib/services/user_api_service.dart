import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/user_profile.dart';
import 'token_storage_service.dart';

class UserApiService {
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

  Future<UserProfile> getCurrentUser() async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/users/me');

    final response = await http
        .get(uri, headers: await _headers())
        .timeout(const Duration(seconds: 15));

    if (response.statusCode != 200) {
      throw Exception(_errorMessage(response, 'Failed to load profile'));
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return UserProfile.fromJson(body);
  }

  String _errorMessage(http.Response response, String fallback) {
    try {
      final body = jsonDecode(response.body);

      if (body is Map<String, dynamic>) {
        final detail = body['detail'];

        if (detail is String && detail.isNotEmpty) {
          return '$detail (${response.statusCode})';
        }
      }
    } catch (_) {
      // Ignore malformed error responses.
    }

    return '$fallback (${response.statusCode})';
  }
}
