import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/weather_map_config.dart';
import 'token_storage_service.dart';


class WeatherMapApiService {
  final TokenStorageService _tokenStorage =
      TokenStorageService();

  Future<String> _accessToken() async {
    final accessToken =
        await _tokenStorage.getAccessToken();

    if (accessToken == null ||
        accessToken.isEmpty) {
      throw Exception(
        'You are not authenticated.',
      );
    }

    return accessToken;
  }


  Future<Map<String, String>>
      getTileHeaders() async {
    final accessToken =
        await _accessToken();

    return {
      'Authorization':
          'Bearer $accessToken',
    };
  }


  Future<WeatherMapConfig>
      getConfig() async {
    final accessToken =
        await _accessToken();

    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}'
      '/api/v1/weather/maps/config',
    );

    final response = await http
        .get(
          uri,
          headers: {
            'Accept': 'application/json',
            'Authorization':
                'Bearer $accessToken',
          },
        )
        .timeout(
          const Duration(
            seconds: 15,
          ),
        );

    if (response.statusCode != 200) {
      throw Exception(
        _errorMessage(
          response,
          'Failed to load weather map configuration',
        ),
      );
    }

    final body =
        jsonDecode(response.body);

    if (body
        is! Map<String, dynamic>) {
      throw Exception(
        'Invalid weather map configuration response.',
      );
    }

    return WeatherMapConfig.fromJson(
      body,
    );
  }


  String resolveTileUrlTemplate({
    required String template,
    required String layer,
  }) {
    final resolvedTemplate =
        template.replaceAll(
      '{layer}',
      layer,
    );

    if (resolvedTemplate
            .startsWith('http://') ||
        resolvedTemplate
            .startsWith('https://')) {
      return resolvedTemplate;
    }

    final baseUrl =
        AppConfig.apiBaseUrl.endsWith('/')
            ? AppConfig.apiBaseUrl
                .substring(
                  0,
                  AppConfig
                          .apiBaseUrl.length -
                      1,
                )
            : AppConfig.apiBaseUrl;

    final path =
        resolvedTemplate.startsWith('/')
            ? resolvedTemplate
            : '/$resolvedTemplate';

    return '$baseUrl$path';
  }


  String _errorMessage(
    http.Response response,
    String fallback,
  ) {
    try {
      final body =
          jsonDecode(response.body);

      if (body
          is Map<String, dynamic>) {
        final detail =
            body['detail'];

        if (detail is String &&
            detail.isNotEmpty) {
          return '$detail '
              '(${response.statusCode})';
        }
      }
    } catch (_) {
      // Keep generic message.
    }

    return '$fallback '
        '(${response.statusCode})';
  }
}