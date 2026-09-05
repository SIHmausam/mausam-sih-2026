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

  const CardDisplayData({
    required this.icon,
    required this.title,
    required this.value,
    required this.status,
    required this.insight,
    required this.indicatorColor,
  });
}

class CardMapper {
  static CardDisplayData? map(PersonalizedCard card, WeatherData weather) {
    switch (card.cardId) {
      case 'aqi':
        return CardDisplayData(
          icon: Icons.air,
          title: 'Air Quality',
          value: weather.usAqi.toStringAsFixed(0),
          status: _aqiStatus(weather.usAqi),
          insight: card.insight,
          indicatorColor: _aqiColor(weather.usAqi),
        );

      case 'uv':
        return CardDisplayData(
          icon: Icons.wb_sunny_outlined,
          title: 'UV Index',
          value: weather.uvIndex.toStringAsFixed(0),
          status: _uvStatus(weather.uvIndex),
          insight: card.insight,
          indicatorColor: _uvColor(weather.uvIndex),
        );

      case 'temperature':
        return CardDisplayData(
          icon: Icons.thermostat_outlined,
          title: 'Temperature',
          value: '${weather.temperature.toStringAsFixed(0)}°C',
          status:
              'Feels like ${weather.apparentTemperature.toStringAsFixed(0)}°C',
          insight: card.insight,
          indicatorColor: _temperatureColor(weather.temperature),
        );

      case 'humidity':
        return CardDisplayData(
          icon: Icons.water_drop_outlined,
          title: 'Humidity',
          value: '${weather.humidity.toStringAsFixed(0)}%',
          status: _humidityStatus(weather.humidity),
          insight: card.insight,
          indicatorColor: _humidityColor(weather.humidity),
        );

      case 'rain':
        return CardDisplayData(
          icon: Icons.water_drop_outlined,
          title: 'Rainfall',
          value: '${weather.rain.toStringAsFixed(1)} mm',
          status: weather.rain > 0 ? 'Rain detected' : 'No rain',
          insight: card.insight,
          indicatorColor: _rainColor(weather.rain),
        );

      case 'wind':
        return CardDisplayData(
          icon: Icons.air,
          title: 'Wind',
          value: '${weather.windSpeed.toStringAsFixed(0)} km/h',
          status: _windStatus(weather.windSpeed),
          insight: card.insight,
          indicatorColor: _windColor(weather.windSpeed),
        );

      case 'soil_moisture':
        if (weather.soilMoisture == null) {
          return null;
        }

        return CardDisplayData(
          icon: Icons.grass,
          title: 'Soil Moisture',
          value: '${weather.soilMoisture!.toStringAsFixed(0)}%',
          status: _soilStatus(weather.soilMoisture!),
          insight: card.insight,
          indicatorColor: _soilColor(weather.soilMoisture!),
        );

      case 'weather_condition':
        return CardDisplayData(
          icon: Icons.cloud_outlined,
          title: 'Condition',
          value: weatherCodeToCondition(weather.weatherCode),
          status: weather.isDaylight ? 'Daylight' : 'Night',
          insight: card.insight,
          indicatorColor: _weatherConditionColor(weather.weatherCode),
        );

      default:
        return null;
    }
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
    if (temperature >= 18 && temperature <= 30) {
      return Colors.greenAccent;
    }
    if (temperature >= 12 && temperature <= 36) {
      return Colors.amberAccent;
    }
    return Colors.redAccent;
  }

  static Color _rainColor(double rain) {
    if (rain <= 0.2) return Colors.greenAccent;
    if (rain <= 5) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _windColor(double wind) {
    if (wind < 10) return Colors.greenAccent;
    if (wind < 25) return Colors.amberAccent;
    return Colors.redAccent;
  }

  static Color _soilColor(double moisture) {
    if (moisture >= 35 && moisture <= 65) {
      return Colors.greenAccent;
    }
    if (moisture >= 20 && moisture <= 80) {
      return Colors.amberAccent;
    }
    return Colors.redAccent;
  }

  static Color _weatherConditionColor(int code) {
    if (code >= 95) return Colors.redAccent;
    if (code >= 51) return Colors.amberAccent;
    return Colors.greenAccent;
  }
}
