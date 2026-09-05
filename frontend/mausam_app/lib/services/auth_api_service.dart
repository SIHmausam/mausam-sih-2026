import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';

class AuthTokens {
  final String accessToken;
  final String refreshToken;
  final String tokenType;

  const AuthTokens({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) {
    return AuthTokens(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
    );
  }
}

class AuthApiService {
  Future<AuthTokens> loginWithGoogle({
    required String idToken,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/auth/google',
    );

    final response = await http
        .post(
          uri,
          headers: {
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            'id_token': idToken,
          }),
        )
        .timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      String message = 'Google login failed';

      try {
        final body =
            jsonDecode(response.body)
                as Map<String, dynamic>;

        final detail = body['detail'];

        if (detail is String &&
            detail.isNotEmpty) {
          message = detail;
        }
      } catch (_) {
        // Keep the generic message.
      }

      throw Exception(
        '$message (${response.statusCode})',
      );
    }

    final body =
        jsonDecode(response.body)
            as Map<String, dynamic>;

    return AuthTokens.fromJson(body);
  }

  Future<AuthTokens> refreshSession({
    required String refreshToken,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/auth/refresh',
    );

    final response = await http
        .post(
          uri,
          headers: {
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            'refresh_token': refreshToken,
          }),
        )
        .timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode < 200 ||
        response.statusCode >= 300) {
      throw Exception(
        'Session refresh failed (${response.statusCode})',
      );
    }

    final body =
        jsonDecode(response.body)
            as Map<String, dynamic>;

    return AuthTokens.fromJson(body);
  }
}