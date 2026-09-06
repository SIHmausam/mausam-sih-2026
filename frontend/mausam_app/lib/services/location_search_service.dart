import 'dart:convert';

import 'package:http/http.dart' as http;

class LocationSearchResult {
  final String name;
  final String? admin1;
  final String country;
  final String countryCode;
  final double latitude;
  final double longitude;

  const LocationSearchResult({
    required this.name,
    required this.admin1,
    required this.country,
    required this.countryCode,
    required this.latitude,
    required this.longitude,
  });

  String get displayName {
    final parts = <String>[
      name,
      if (admin1 != null && admin1!.isNotEmpty) admin1!,
      country,
    ];

    return parts.join(', ');
  }

  String get subtitle {
    final parts = <String>[
      if (admin1 != null && admin1!.isNotEmpty) admin1!,
      country,
    ];

    return parts.join(', ');
  }
}

class LocationSearchService {
  static const String _baseUrl =
      'https://geocoding-api.open-meteo.com/v1/search';

  static Future<List<LocationSearchResult>> search(
    String query,
  ) async {
    final trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      return const [];
    }

    final uri = Uri.parse(_baseUrl).replace(
      queryParameters: {
        'name': trimmedQuery,
        'count': '8',
        'language': 'en',
        'format': 'json',
      },
    );

    final response = await http
        .get(uri)
        .timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) {
      throw Exception(
        'Location search failed (${response.statusCode})',
      );
    }

    final body = jsonDecode(response.body);

    if (body is! Map<String, dynamic>) {
      return const [];
    }

    final results = body['results'];

    if (results is! List) {
      return const [];
    }

    return results
        .whereType<Map<String, dynamic>>()
        .map(_fromJson)
        .whereType<LocationSearchResult>()
        .toList();
  }

  static LocationSearchResult? _fromJson(
    Map<String, dynamic> json,
  ) {
    final name = json['name']?.toString();
    final country = json['country']?.toString();
    final countryCode = json['country_code']?.toString();
    final latitude = _toDouble(json['latitude']);
    final longitude = _toDouble(json['longitude']);

    if (name == null ||
        country == null ||
        countryCode == null ||
        latitude == null ||
        longitude == null) {
      return null;
    }

    return LocationSearchResult(
      name: name,
      admin1: json['admin1']?.toString(),
      country: country,
      countryCode: countryCode,
      latitude: latitude,
      longitude: longitude,
    );
  }

  static double? _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '');
  }
}
