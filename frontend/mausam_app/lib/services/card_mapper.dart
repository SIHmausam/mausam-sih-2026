import 'package:flutter/material.dart';

import '../models/personalized_card.dart';
import '../models/weather_data.dart';

import 'weather_code_mapper.dart';

class CardDisplayData {
  final IconData icon;
  final String title;
  final String value;
  final String status;
  final String insight;
  final Color indicatorColor;
  final List<String> details;

  const CardDisplayData({
    required this.icon,
    required this.title,
    required this.value,
    required this.status,
    required this.insight,
    required this.indicatorColor,
    this.details = const [],
  });
}

class CardMapper {
  static CardDisplayData? map(PersonalizedCard card, WeatherData weather) {
    switch (card.cardId) {
      case 'temperature':
        return CardDisplayData(
          icon: Icons.thermostat_outlined,
          title: 'Temperature',
          value: '${weather.temperature.toStringAsFixed(0)}°C',
          status:
              'Feels like ${weather.apparentTemperature.toStringAsFixed(0)}°C',
          insight: card.insight,
          indicatorColor: _temperatureColor(weather.temperature),
          details: [
            'Feels like: ${weather.apparentTemperature.toStringAsFixed(1)}°C',
            'Dew point: ${weather.dewPoint.toStringAsFixed(1)}°C',
            'Cloud cover: ${weather.cloudCover.toStringAsFixed(0)}%',
          ],
        );

      case 'weather_conditions':
      case 'weather_condition':
        return CardDisplayData(
          icon: Icons.cloud_outlined,
          title: 'Weather Conditions',
          value: weatherCodeToCondition(weather.weatherCode),
          status: weather.isDaylight ? 'Daylight' : 'Night',
          insight: card.insight,
          indicatorColor: _weatherConditionColor(weather.weatherCode),
          details: [
            'Cloud cover: ${weather.cloudCover.toStringAsFixed(0)}%',
            'Visibility: ${_visibilityKm(weather.visibility)} km',
            'Precipitation: ${weather.precipitation.toStringAsFixed(1)} mm',
            'Showers: ${weather.showers.toStringAsFixed(1)} mm',
          ],
        );

      case 'humidity':
        return CardDisplayData(
          icon: Icons.water_drop_outlined,
          title: 'Humidity',
          value: '${weather.humidity.toStringAsFixed(0)}%',
          status: _humidityStatus(weather.humidity),
          insight: card.insight,
          indicatorColor: _humidityColor(weather.humidity),
          details: [
            'Dew point: ${weather.dewPoint.toStringAsFixed(1)}°C',
            'Feels like: ${weather.apparentTemperature.toStringAsFixed(1)}°C',
            'Vapour pressure deficit: ${_optional(weather.vapourPressureDeficit, 'kPa')}',
          ],
        );

      case 'rain_forecast':
      case 'rain':
      case 'rainfall':
        return CardDisplayData(
          icon: Icons.water_drop_outlined,
          title: 'Rain Forecast',
          value: '${weather.rainProbability.toStringAsFixed(0)}%',
          status: weather.rain > 0
              ? '${weather.rain.toStringAsFixed(1)} mm rain'
              : 'No rain currently',
          insight: card.insight,
          indicatorColor: _rainColor(weather.rainProbability),
          details: [
            'Current rain: ${weather.rain.toStringAsFixed(1)} mm',
            'Precipitation: ${weather.precipitation.toStringAsFixed(1)} mm',
            'Showers: ${weather.showers.toStringAsFixed(1)} mm',
            if (weather.daily.isNotEmpty)
              'Today max probability: ${weather.daily.first.rainProbabilityMax.toStringAsFixed(0)}%',
          ],
        );

      case 'wind':
        return CardDisplayData(
          icon: Icons.air,
          title: 'Wind',
          value: '${weather.windSpeed.toStringAsFixed(1)} km/h',
          status: _windStatus(weather.windSpeed),
          insight: card.insight,
          indicatorColor: _windColor(weather.windSpeed),
          details: [
            'Direction: ${weather.windDirection.toStringAsFixed(0)}°',
            'Gusts: ${weather.windGusts.toStringAsFixed(1)} km/h',
            'Visibility: ${_visibilityKm(weather.visibility)} km',
          ],
        );

      case 'air_quality':
      case 'aqi':
        return CardDisplayData(
          icon: Icons.air,
          title: 'Air Quality',
          value: weather.usAqi.toStringAsFixed(0),
          status: _aqiStatus(weather.usAqi),
          insight: card.insight,
          indicatorColor: _aqiColor(weather.usAqi),
          details: [
            'PM2.5: ${weather.pm25.toStringAsFixed(1)} µg/m³',
            'PM10: ${weather.pm10.toStringAsFixed(1)} µg/m³',
            'European AQI: ${weather.europeanAqi.toStringAsFixed(0)}',
            if (weather.ozone != null)
              'Ozone: ${weather.ozone!.toStringAsFixed(1)} µg/m³',
            if (weather.nitrogenDioxide != null)
              'NO₂: ${weather.nitrogenDioxide!.toStringAsFixed(1)} µg/m³',
          ],
        );

      case 'uv_allergy':
      case 'uv':
        return CardDisplayData(
          icon: Icons.wb_sunny_outlined,
          title: 'UV & Allergy',
          value: weather.uvIndex.toStringAsFixed(0),
          status: _uvStatus(weather.uvIndex),
          insight: card.insight,
          indicatorColor: _uvColor(weather.uvIndex),
          details: [
            'UV index: ${weather.uvIndex.toStringAsFixed(1)}',
            'Clear-sky UV: ${weather.uvIndexClearSky.toStringAsFixed(1)}',
            'Daylight: ${weather.isDaylight ? 'Yes' : 'No'}',
          ],
        );

      case 'running_conditions':
        final score = _runningScore(weather);
        return CardDisplayData(
          icon: Icons.directions_run,
          title: 'Running Conditions',
          value: score,
          status: _runningStatus(weather),
          insight: card.insight,
          indicatorColor: _runningColor(weather),
          details: [
            'Temperature: ${weather.temperature.toStringAsFixed(1)}°C',
            'Feels like: ${weather.apparentTemperature.toStringAsFixed(1)}°C',
            'Humidity: ${weather.humidity.toStringAsFixed(0)}%',
            'Wind: ${weather.windSpeed.toStringAsFixed(1)} km/h',
            'UV: ${weather.uvIndex.toStringAsFixed(1)}',
          ],
        );

      case 'surf_conditions':
        return CardDisplayData(
          icon: Icons.surfing,
          title: 'Surf Conditions',
          value: weather.waveHeight == null
              ? 'N/A'
              : '${weather.waveHeight!.toStringAsFixed(1)} m',
          status: weather.waveHeight == null
              ? 'Marine data unavailable'
              : 'Wave height',
          insight: card.insight,
          indicatorColor: Colors.blueAccent,
          details: [
            if (weather.waveDirection != null)
              'Wave direction: ${weather.waveDirection!.toStringAsFixed(0)}°',
            if (weather.wavePeriod != null)
              'Wave period: ${weather.wavePeriod!.toStringAsFixed(1)} s',
            if (weather.swellWaveHeight != null)
              'Swell height: ${weather.swellWaveHeight!.toStringAsFixed(1)} m',
            if (weather.seaSurfaceTemperature != null)
              'Sea temperature: ${weather.seaSurfaceTemperature!.toStringAsFixed(1)}°C',
          ],
        );

      case 'tide_water':
        return CardDisplayData(
          icon: Icons.waves,
          title: 'Tide & Water',
          value: weather.seaLevelHeightMsl == null
              ? 'N/A'
              : '${weather.seaLevelHeightMsl!.toStringAsFixed(2)} m',
          status: weather.seaLevelHeightMsl == null
              ? 'Marine data unavailable'
              : 'Sea level',
          insight: card.insight,
          indicatorColor: Colors.cyanAccent,
          details: [
            if (weather.seaLevelHeightMsl != null)
              'Sea level: ${weather.seaLevelHeightMsl!.toStringAsFixed(2)} m',
            if (weather.seaSurfaceTemperature != null)
              'Water temperature: ${weather.seaSurfaceTemperature!.toStringAsFixed(1)}°C',
            if (weather.waveHeight != null)
              'Wave height: ${weather.waveHeight!.toStringAsFixed(1)} m',
          ],
        );

      case 'farm_garden':
      case 'soil_moisture':
        if (weather.soilMoisture == null) return null;
        return CardDisplayData(
          icon: Icons.grass,
          title: 'Farm & Garden',
          value: '${weather.soilMoisture!.toStringAsFixed(0)}%',
          status: _soilStatus(weather.soilMoisture!),
          insight: card.insight,
          indicatorColor: _soilColor(weather.soilMoisture!),
          details: [
            'Surface moisture: ${weather.soilMoisture!.toStringAsFixed(1)}%',
            if (weather.soilMoisture7To28cm != null)
              '7–28 cm moisture: ${weather.soilMoisture7To28cm!.toStringAsFixed(1)}%',
            if (weather.soilMoisture28To100cm != null)
              '28–100 cm moisture: ${weather.soilMoisture28To100cm!.toStringAsFixed(1)}%',
            if (weather.soilTemperature0To7cm != null)
              'Surface soil temperature: ${weather.soilTemperature0To7cm!.toStringAsFixed(1)}°C',
            if (weather.evapotranspiration != null)
              'Evapotranspiration: ${weather.evapotranspiration!.toStringAsFixed(1)} mm',
          ],
        );

      case 'commute_conditions':
        return CardDisplayData(
          icon: Icons.directions_car_outlined,
          title: 'Commute Conditions',
          value: weather.visibility >= 5000 ? 'Clear' : 'Reduced',
          status:
              '${weather.visibility >= 1000 ? _visibilityKm(weather.visibility) : '<1'} km visibility',
          insight: card.insight,
          indicatorColor: weather.visibility >= 5000
              ? Colors.greenAccent
              : Colors.amberAccent,
          details: [
            'Visibility: ${_visibilityKm(weather.visibility)} km',
            'Rain probability: ${weather.rainProbability.toStringAsFixed(0)}%',
            'Wind: ${weather.windSpeed.toStringAsFixed(1)} km/h',
            'Condition: ${weatherCodeToCondition(weather.weatherCode)}',
          ],
        );

      case 'travel_conditions':
        return CardDisplayData(
          icon: Icons.travel_explore,
          title: 'Travel Conditions',
          value: weatherCodeToCondition(weather.weatherCode),
          status:
              '${weather.temperature.toStringAsFixed(0)}°C • ${weather.humidity.toStringAsFixed(0)}% humidity',
          insight: card.insight,
          indicatorColor: _weatherConditionColor(weather.weatherCode),
          details: [
            'Feels like: ${weather.apparentTemperature.toStringAsFixed(1)}°C',
            'Visibility: ${_visibilityKm(weather.visibility)} km',
            'Rain probability: ${weather.rainProbability.toStringAsFixed(0)}%',
            'Wind: ${weather.windSpeed.toStringAsFixed(1)} km/h',
            'UV: ${weather.uvIndex.toStringAsFixed(1)}',
          ],
        );

      case 'family_school':
        return CardDisplayData(
          icon: Icons.school_outlined,
          title: 'Family & School',
          value: weatherCodeToCondition(weather.weatherCode),
          status:
              '${weather.temperature.toStringAsFixed(0)}°C • ${_humidityStatus(weather.humidity)} humidity',
          insight: card.insight,
          indicatorColor: _weatherConditionColor(weather.weatherCode),
          details: [
            'Temperature: ${weather.temperature.toStringAsFixed(1)}°C',
            'Rain probability: ${weather.rainProbability.toStringAsFixed(0)}%',
            'Visibility: ${_visibilityKm(weather.visibility)} km',
            'Wind: ${weather.windSpeed.toStringAsFixed(1)} km/h',
            'UV: ${weather.uvIndex.toStringAsFixed(1)}',
          ],
        );

      case 'event_conditions':
        return CardDisplayData(
          icon: Icons.event_outlined,
          title: 'Event Conditions',
          value: weatherCodeToCondition(weather.weatherCode),
          status:
              '${weather.temperature.toStringAsFixed(0)}°C • ${weather.rainProbability.toStringAsFixed(0)}% rain',
          insight: card.insight,
          indicatorColor: _weatherConditionColor(weather.weatherCode),
          details: [
            'Temperature: ${weather.temperature.toStringAsFixed(1)}°C',
            'Feels like: ${weather.apparentTemperature.toStringAsFixed(1)}°C',
            'Rain probability: ${weather.rainProbability.toStringAsFixed(0)}%',
            'Wind: ${weather.windSpeed.toStringAsFixed(1)} km/h',
            'Visibility: ${_visibilityKm(weather.visibility)} km',
          ],
        );

      default:
        return null;
    }
  }

  static String _visibilityKm(double metres) {
    return (metres / 1000).toStringAsFixed(1);
  }

  static String _optional(double? value, String unit) {
    if (value == null) return 'N/A';
    return '${value.toStringAsFixed(2)} $unit';
  }

  static String _aqiStatus(double aqi) {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Satisfactory';
    if (aqi <= 200) return 'Moderate';
    if (aqi <= 300) return 'Poor';
    if (aqi <= 400) return 'Very Poor';
    return 'Severe';
  }

  static String _uvStatus(double uv) {
    if (uv <= 2) return 'Low';
    if (uv <= 5) return 'Moderate';
    if (uv <= 7) return 'High';
    if (uv <= 10) return 'Very High';
    return 'Extreme';
  }

  static String _humidityStatus(double humidity) {
    if (humidity < 30) return 'Low';
    if (humidity <= 60) return 'Comfortable';
    if (humidity <= 80) return 'High';
    return 'Very High';
  }

  static String _soilStatus(double moisture) {
    if (moisture < 20) return 'Very Dry';
    if (moisture < 35) return 'Dry';
    if (moisture <= 65) return 'Good';
    if (moisture <= 80) return 'High';
    return 'Very High';
  }

  static String _windStatus(double wind) {
    if (wind < 10) return 'Light';
    if (wind < 25) return 'Moderate';
    if (wind < 40) return 'Strong';
    return 'Very Strong';
  }

  static String _runningScore(WeatherData weather) {
    var score = 100;
    if (weather.temperature > 30) score -= 15;
    if (weather.temperature < 10) score -= 10;
    if (weather.humidity > 80) score -= 15;
    if (weather.windSpeed > 25) score -= 10;
    if (weather.uvIndex > 7) score -= 10;
    if (weather.usAqi > 100) score -= 20;
    if (weather.rainProbability > 50) score -= 15;
    if (score < 0) score = 0;
    return '$score/100';
  }

  static String _runningStatus(WeatherData weather) {
    final score = int.parse(_runningScore(weather).split('/').first);
    if (score >= 75) return 'Good for running';
    if (score >= 50) return 'Use caution';
    return 'Poor conditions';
  }

  static Color _runningColor(WeatherData weather) {
    final score = int.parse(_runningScore(weather).split('/').first);
    if (score >= 75) return Colors.greenAccent;
    if (score >= 50) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _aqiColor(double aqi) {
    if (aqi <= 100) return Colors.greenAccent;
    if (aqi <= 200) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _uvColor(double uv) {
    if (uv <= 2) return Colors.greenAccent;
    if (uv <= 5) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _humidityColor(double humidity) {
    if (humidity <= 60) return Colors.greenAccent;
    if (humidity <= 80) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _temperatureColor(double temperature) {
    if (temperature >= 18 && temperature <= 30) return Colors.greenAccent;
    if (temperature >= 12 && temperature <= 36) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _rainColor(double probability) {
    if (probability <= 20) return Colors.greenAccent;
    if (probability <= 50) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _windColor(double wind) {
    if (wind < 10) return Colors.greenAccent;
    if (wind < 25) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _soilColor(double moisture) {
    if (moisture >= 35 && moisture <= 65) return Colors.greenAccent;
    if (moisture >= 20 && moisture <= 80) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _weatherConditionColor(int code) {
    if (code >= 95) return Colors.redAccent;
    if (code >= 51) return Colors.amberAccent;
    return Colors.greenAccent;
  }
}
