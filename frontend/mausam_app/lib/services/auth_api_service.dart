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

class AuthApiException implements Exception {
  final String message;
  final int statusCode;

  const AuthApiException({required this.message, required this.statusCode});

  @override
  String toString() => message;
}

class AuthApiService {
  Future<AuthTokens> login({
    required String email,
    required String password,
  }) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/auth/login');

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email, 'password': password}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Login failed';

      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;

        final detail = body['detail'];

        if (detail is String && detail.isNotEmpty) {
          message = detail;
        }
      } catch (_) {
        // Keep the generic message.
      }

      throw AuthApiException(message: message, statusCode: response.statusCode);
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return AuthTokens.fromJson(body);
  }

  Future<void> register({
    required String name,
    required String email,
    required String password,
  }) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/auth/register');

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'name': name,
            'email': email,
            'password': password,
          }),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Registration failed';

      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;

        final detail = body['detail'];

        if (detail is String && detail.isNotEmpty) {
          message = detail;
        }
      } catch (_) {
        // Keep generic message.
      }

      throw Exception('$message (${response.statusCode})');
    }
  }

  Future<void> verifyEmail({
    required String email,
    required String code,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}'
      '/api/v1/auth/email-verification/verify',
    );

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email, 'code': code}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Email verification failed';

      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;

        final detail = body['detail'];

        if (detail is String && detail.isNotEmpty) {
          message = detail;
        }
      } catch (_) {
        // Keep generic message.
      }

      throw Exception('$message (${response.statusCode})');
    }
  }

  Future<void> resendVerificationCode({required String email}) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}'
      '/api/v1/auth/email-verification/resend',
    );

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'email': email}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Could not resend verification code';

      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;

        final detail = body['detail'];

        if (detail is String && detail.isNotEmpty) {
          message = detail;
        }
      } catch (_) {
        // Keep generic message.
      }

      throw Exception('$message (${response.statusCode})');
    }
  }

  Future<AuthTokens> loginWithGoogle({required String idToken}) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/auth/google');

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'id_token': idToken}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Google login failed';

      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;

        final detail = body['detail'];

        if (detail is String && detail.isNotEmpty) {
          message = detail;
        }
      } catch (_) {
        // Keep the generic message.
      }

      throw Exception('$message (${response.statusCode})');
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return AuthTokens.fromJson(body);
  }

  Future<AuthTokens> refreshSession({required String refreshToken}) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/auth/refresh');

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh_token': refreshToken}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Session refresh failed (${response.statusCode})');
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return AuthTokens.fromJson(body);
  }

  Future<void> logout({required String refreshToken}) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/auth/logout');

    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh_token': refreshToken}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('Logout failed (${response.statusCode})');
    }
  }
}
