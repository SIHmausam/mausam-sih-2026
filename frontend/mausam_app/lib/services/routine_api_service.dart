import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/routine.dart';
import 'token_storage_service.dart';

class RoutineApiService {
  final TokenStorageService _tokenStorage =
      TokenStorageService();

  Future<Map<String, String>> _headers() async {
    final accessToken =
        await _tokenStorage.getAccessToken();

    if (accessToken == null || accessToken.isEmpty) {
      throw Exception('You are not authenticated.');
    }

    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $accessToken',
    };
  }

  Future<List<Routine>> getRoutines() async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/routines',
    );

    final response = await http
        .get(
          uri,
          headers: await _headers(),
        )
        .timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode != 200) {
      throw Exception(
        _errorMessage(
          response,
          'Failed to load routines',
        ),
      );
    }

    final body =
        jsonDecode(response.body) as List<dynamic>;

    return body
        .whereType<Map<String, dynamic>>()
        .map(Routine.fromJson)
        .toList();
  }

  Future<Routine> createRoutine({
    required String name,
    required String activityContext,
    String? savedLocationId,
    required List<String> daysOfWeek,
    required String startTime,
    required int durationMinutes,
    bool isEnabled = true,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/routines',
    );

    final response = await http
        .post(
          uri,
          headers: await _headers(),
          body: jsonEncode({
            'name': name,
            'activity_context': activityContext,
            'saved_location_id': savedLocationId,
            'days_of_week': daysOfWeek,
            'start_time': startTime,
            'duration_minutes': durationMinutes,
            'is_enabled': isEnabled,
          }),
        )
        .timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode != 201) {
      throw Exception(
        _errorMessage(
          response,
          'Failed to create routine',
        ),
      );
    }

    final body =
        jsonDecode(response.body)
            as Map<String, dynamic>;

    return Routine.fromJson(body);
  }

  Future<Routine> updateRoutine({
    required String routineId,
    String? name,
    String? activityContext,
    String? savedLocationId,
    bool clearSavedLocation = false,
    List<String>? daysOfWeek,
    String? startTime,
    int? durationMinutes,
    bool? isEnabled,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/routines/$routineId',
    );

    final payload = <String, dynamic>{};

    if (name != null) {
      payload['name'] = name;
    }

    if (activityContext != null) {
      payload['activity_context'] = activityContext;
    }

    if (clearSavedLocation) {
      payload['saved_location_id'] = null;
    } else if (savedLocationId != null) {
      payload['saved_location_id'] = savedLocationId;
    }

    if (daysOfWeek != null) {
      payload['days_of_week'] = daysOfWeek;
    }

    if (startTime != null) {
      payload['start_time'] = startTime;
    }

    if (durationMinutes != null) {
      payload['duration_minutes'] = durationMinutes;
    }

    if (isEnabled != null) {
      payload['is_enabled'] = isEnabled;
    }

    final response = await http
        .patch(
          uri,
          headers: await _headers(),
          body: jsonEncode(payload),
        )
        .timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode != 200) {
      throw Exception(
        _errorMessage(
          response,
          'Failed to update routine',
        ),
      );
    }

    final body =
        jsonDecode(response.body)
            as Map<String, dynamic>;

    return Routine.fromJson(body);
  }

  Future<void> deleteRoutine({
    required String routineId,
  }) async {
    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/routines/$routineId',
    );

    final response = await http
        .delete(
          uri,
          headers: await _headers(),
        )
        .timeout(
          const Duration(seconds: 15),
        );

    if (response.statusCode != 204) {
      throw Exception(
        _errorMessage(
          response,
          'Failed to delete routine',
        ),
      );
    }
  }

  String _errorMessage(
    http.Response response,
    String fallback,
  ) {
    try {
      final body =
          jsonDecode(response.body);

      if (body is Map<String, dynamic>) {
        final detail = body['detail'];

        if (detail is String &&
            detail.isNotEmpty) {
          return '$detail (${response.statusCode})';
        }
      }
    } catch (_) {}

    return '$fallback (${response.statusCode})';
  }
}
