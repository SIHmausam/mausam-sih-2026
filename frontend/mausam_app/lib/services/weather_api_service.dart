import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/weather_data.dart';

class WeatherApiService {
  static Future<WeatherData> getWeather({
    required double latitude,
    required double longitude,
    String city = 'Ghaziabad, UP',
    bool includeMarine = false,
  }) async {
    final queryParameters = <String, String>{
      'latitude': latitude.toString(),
      'longitude': longitude.toString(),
    };

    if (includeMarine) {
      queryParameters['include_marine'] = 'true';
    }

    final uri = Uri.parse(
      '${AppConfig.apiBaseUrl}/api/v1/weather/context',
    ).replace(
      queryParameters: queryParameters,
    );

    final response = await http
        .get(uri)
        .timeout(const Duration(seconds: 20));

    if (response.statusCode != 200) {
      String message = 'Weather request failed (${response.statusCode})';

      try {
        final body = jsonDecode(response.body);

        if (body is Map<String, dynamic> && body['detail'] != null) {
          message = body['detail'].toString();
        }
      } catch (_) {}

      throw Exception(message);
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;

    final current = body['current'] as Map<String, dynamic>;
    final agriculture =
        body['agriculture'] as Map<String, dynamic>?;
    final airQuality =
        body['air_quality'] as Map<String, dynamic>?;

    final marine =
      body['marine'] as Map<String, dynamic>?;

    final hourly = _parseHourly(body['hourly']);
    final daily = _parseDaily(body['daily']);

    return WeatherData(
      city: city,
      timestamp: DateTime.parse(
        current['observed_at'].toString(),
      ),
      temperature: _toDouble(current['temperature']),
      humidity: _toDouble(current['humidity']),
      apparentTemperature:
          _toDouble(current['apparent_temperature']),
      precipitation: _toDouble(current['precipitation']),
      rain: _toDouble(current['rain']),
      weatherCode: _toInt(current['weather_code']),
      windSpeed: _toDouble(current['wind_speed']),
      dewPoint: _toDoubleOrZero(current['dew_point']),
      showers: _toDoubleOrZero(current['showers']),
      rainProbability: _toDoubleOrZero(current['rain_probability']),
      cloudCover: _toDoubleOrZero(current['cloud_cover']),
      windDirection: _toDoubleOrZero(current['wind_direction']),
      windGusts: _toDoubleOrZero(current['wind_gusts']),
      visibility: _toDoubleOrZero(current['visibility']),

      soilMoisture: agriculture == null
          ? null
          : _toDoubleOrNull(
              agriculture['surface_soil_moisture'],
            ),
      soilMoisture7To28cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_moisture_7_to_28cm']),
      soilMoisture28To100cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_moisture_28_to_100cm']),
      soilMoisture100To255cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_moisture_100_to_255cm']),
      soilTemperature0To7cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_temperature_0_to_7cm']),
      soilTemperature7To28cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_temperature_7_to_28cm']),
      soilTemperature28To100cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_temperature_28_to_100cm']),
      soilTemperature100To255cm: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['soil_temperature_100_to_255cm']),
      evapotranspiration: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['evapotranspiration']),
      vapourPressureDeficit: agriculture == null
          ? null
          : _toDoubleOrNull(agriculture['vapour_pressure_deficit']),

      usAqi: airQuality == null
          ? 0
          : _toDouble(airQuality['us_aqi']),
      europeanAqi: airQuality == null
          ? 0
          : _toDouble(airQuality['european_aqi']),
      aqiStandard: airQuality?['aqi_standard']?.toString(),
      uvIndex: airQuality == null
          ? 0
          : _toDouble(airQuality['uv_index']),
      uvIndexClearSky: airQuality == null
          ? 0
          : _toDouble(airQuality['uv_index_clear_sky']),
      pm25: airQuality == null
          ? 0
          : _toDouble(airQuality['pm2_5']),
      pm10: airQuality == null
          ? 0
          : _toDouble(airQuality['pm10']),

      nitrogenDioxide: airQuality == null
          ? null
          : _toDoubleOrNull(
              airQuality['nitrogen_dioxide'],
            ),
      sulphurDioxide: airQuality == null
          ? null
          : _toDoubleOrNull(
              airQuality['sulphur_dioxide'],
            ),
      carbonMonoxide: airQuality == null
          ? null
          : _toDoubleOrNull(
              airQuality['carbon_monoxide'],
            ),
      ozone: airQuality == null
          ? null
          : _toDoubleOrNull(
              airQuality['ozone'],
            ),

      isDaylight: current['is_daylight'] == true,

      waveHeight: _toDoubleOrNull(
        marine?['wave_height'],
      ),
      waveDirection: _toDoubleOrNull(
        marine?['wave_direction'],
      ),
      wavePeriod: _toDoubleOrNull(
        marine?['wave_period'],
      ),
      swellWaveHeight: _toDoubleOrNull(
        marine?['swell_wave_height'],
      ),
      swellWaveDirection: _toDoubleOrNull(
        marine?['swell_wave_direction'],
      ),
      swellWavePeriod: _toDoubleOrNull(
        marine?['swell_wave_period'],
      ),
      seaLevelHeightMsl: _toDoubleOrNull(
        marine?['sea_level_height_msl'],
      ),
      seaSurfaceTemperature: _toDoubleOrNull(
        marine?['sea_surface_temperature'],
      ),

      hourly: hourly,
      daily: daily,
    );
  }

  static List<HourlyWeather> _parseHourly(dynamic value) {
    if (value is! List) {
      return const [];
    }

    return value
        .whereType<Map<String, dynamic>>()
        .map(
          (item) => HourlyWeather(
            time: DateTime.parse(item['time'].toString()),
            temperature: _toDoubleOrZero(item['temperature']),
            apparentTemperature:
                _toDoubleOrZero(item['apparent_temperature']),
            humidity: _toDoubleOrZero(item['humidity']),
            precipitation:
                _toDoubleOrZero(item['precipitation']),
            rain: _toDoubleOrZero(item['rain']),
            rainProbability:
                _toDoubleOrZero(item['rain_probability']),
            weatherCode: _toIntOrZero(item['weather_code']),
            windSpeed: _toDoubleOrZero(item['wind_speed']),
            visibility: _toDoubleOrZero(item['visibility']),
            dewPoint: _toDoubleOrZero(item['dew_point']),
            showers: _toDoubleOrZero(item['showers']),
            cloudCover: _toDoubleOrZero(item['cloud_cover']),
            windDirection: _toDoubleOrZero(item['wind_direction']),
            windGusts: _toDoubleOrZero(item['wind_gusts']),
          ),
        )
        .toList();
  }

  static List<DailyWeather> _parseDaily(dynamic value) {
    if (value is! List) {
      return const [];
    }

    return value
        .whereType<Map<String, dynamic>>()
        .map(
          (item) => DailyWeather(
            date: item['date'].toString(),
            weatherCode: _toIntOrZero(item['weather_code']),
            temperatureMax:
                _toDoubleOrZero(item['temperature_max']),
            temperatureMin:
                _toDoubleOrZero(item['temperature_min']),
            apparentTemperatureMax:
                _toDoubleOrZero(
              item['apparent_temperature_max'],
            ),
            apparentTemperatureMin:
                _toDoubleOrZero(
              item['apparent_temperature_min'],
            ),
            sunrise: _toDateTimeOrNull(item['sunrise']),
            sunset: _toDateTimeOrNull(item['sunset']),
            moonrise: _toDateTimeOrNull(item['moonrise']),
            moonset: _toDateTimeOrNull(item['moonset']),
            moonPhase: _toDoubleOrNull(item['moon_phase']),
            precipitationSum:
                _toDoubleOrZero(item['precipitation_sum']),
            rainSum: _toDoubleOrZero(item['rain_sum']),
            rainProbabilityMax:
                _toDoubleOrZero(
              item['rain_probability_max'],
            ),
            windSpeedMax:
                _toDoubleOrZero(item['wind_speed_max']),
            precipitationHours:
                _toDoubleOrZero(item['precipitation_hours']),
          ),
        )
        .toList();
  }

  static double _toDouble(dynamic value) {
    if (value is num) return value.toDouble();
    return double.parse(value.toString());
  }

  static double _toDoubleOrZero(dynamic value) {
    if (value == null) return 0;
    if (value is num) return value.toDouble();

    return double.tryParse(value.toString()) ?? 0;
  }

  static double? _toDoubleOrNull(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();

    return double.tryParse(value.toString());
  }

  static int _toInt(dynamic value) {
    if (value is num) return value.toInt();
    return int.parse(value.toString());
  }

  static int _toIntOrZero(dynamic value) {
    if (value == null) return 0;
    if (value is num) return value.toInt();

    return int.tryParse(value.toString()) ?? 0;
  }

  static DateTime? _toDateTimeOrNull(dynamic value) {
    if (value == null) return null;

    return DateTime.tryParse(value.toString());
  }
}
