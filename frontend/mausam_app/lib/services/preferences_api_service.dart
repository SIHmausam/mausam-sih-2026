import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/user_preferences.dart';
import 'token_storage_service.dart';

class PreferencesApiService {
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

  Future<UserPreferences> getPreferences() async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/users/preferences');

    final response = await http
        .get(uri, headers: await _headers())
        .timeout(const Duration(seconds: 15));

    if (response.statusCode != 200) {
      throw Exception(_errorMessage(response, 'Failed to load preferences'));
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return UserPreferences.fromJson(body);
  }

  Future<UserPreferences> completeOnboarding({
    required String preferredLanguage,
    required String temperatureUnit,
    required String persona,
    required List<String> interests,
    int? preferredStartHour,
    int? preferredEndHour,
    required List<String> activityContexts,
    required Map<String, bool> notifications,
    required Map<String, bool> personalization,
  }) async {
    final payload = <String, dynamic>{
      'preferred_language': preferredLanguage,
      'temperature_unit': temperatureUnit,
      'persona': persona,
      'interests': interests,
      'preferred_start_hour': preferredStartHour,
      'preferred_end_hour': preferredEndHour,
      'activity_contexts': activityContexts,
      'notifications': notifications,
      'personalization': personalization,
    };

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/users/onboarding');

    final response = await http
        .post(uri, headers: await _headers(), body: jsonEncode(payload))
        .timeout(const Duration(seconds: 15));

    if (response.statusCode != 201) {
      throw Exception(_errorMessage(response, 'Failed to complete onboarding'));
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return UserPreferences.fromJson(body);
  }

  Future<UserPreferences> updatePreferences({
    String? preferredLanguage,
    String? temperatureUnit,
    String? persona,
    int? preferredStartHour,
    int? preferredEndHour,
    List<String>? interests,
    List<String>? activityContexts,
    Map<String, bool>? notifications,
    Map<String, bool>? personalization,
  }) async {
    final payload = <String, dynamic>{};

    if (preferredLanguage != null) {
      payload['preferred_language'] = preferredLanguage;
    }

    if (temperatureUnit != null) {
      payload['temperature_unit'] = temperatureUnit;
    }

    if (persona != null) {
      payload['persona'] = persona;
    }

    if (preferredStartHour != null) {
      payload['preferred_start_hour'] = preferredStartHour;
    }

    if (preferredEndHour != null) {
      payload['preferred_end_hour'] = preferredEndHour;
    }

    if (interests != null) {
      payload['interests'] = interests;
    }

    if (activityContexts != null) {
      payload['activity_contexts'] = activityContexts;
    }

    if (notifications != null) {
      payload['notifications'] = notifications;
    }

    if (personalization != null) {
      payload['personalization'] = personalization;
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/api/v1/users/preferences');

    final response = await http
        .patch(uri, headers: await _headers(), body: jsonEncode(payload))
        .timeout(const Duration(seconds: 15));

    if (response.statusCode != 200) {
      throw Exception(_errorMessage(response, 'Failed to update preferences'));
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    return UserPreferences.fromJson(body);
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
