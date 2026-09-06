import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/saved_location.dart';
import 'token_storage_service.dart';

class LocationApiService {
  final TokenStorageService _tokenStorage = TokenStorageService();

  Future<Map<String, String>> _headers() async {
    final accessToken = await _tokenStorage.getAccessToken();

    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('You are not signed in.');
    }

    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    };
  }

  Future<List<SavedLocation>> getLocations() async {
    final response = await http
        .get(
          Uri.parse('${AppConfig.apiBaseUrl}/api/v1/locations'),
          headers: await _headers(),
        )
        .timeout(const Duration(seconds: 20));

    if (response.statusCode != 200) {
      throw Exception(_errorMessage(response));
    }

    final body = jsonDecode(response.body);

    if (body is! List) {
      throw Exception('Invalid locations response.');
    }

    return body
        .whereType<Map<String, dynamic>>()
        .map(SavedLocation.fromJson)
        .toList();
  }

  Future<SavedLocation> createLocation({
    required String label,
    required String city,
    required double latitude,
    required double longitude,
    required String locationType,
    bool isPrimary = false,
  }) async {
    final response = await http
        .post(
          Uri.parse('${AppConfig.apiBaseUrl}/api/v1/locations'),
          headers: await _headers(),
          body: jsonEncode({
            'label': label,
            'city': city,
            'latitude': latitude,
            'longitude': longitude,
            'location_type': locationType,
            'is_primary': isPrimary,
          }),
        )
        .timeout(const Duration(seconds: 20));

    if (response.statusCode != 201) {
      throw Exception(_errorMessage(response));
    }

    final body = jsonDecode(response.body);

    if (body is! Map<String, dynamic>) {
      throw Exception('Invalid location response.');
    }

    return SavedLocation.fromJson(body);
  }

  String _errorMessage(http.Response response) {
    try {
      final body = jsonDecode(response.body);

      if (body is Map<String, dynamic> && body['detail'] != null) {
        return body['detail'].toString();
      }
    } catch (_) {
      // Fall through to the generic message.
    }

    return 'Location request failed (${response.statusCode}).';
  }
}
