class HourlyWeather {
  final DateTime time;
  final double temperature;
  final double apparentTemperature;
  final double humidity;
  final double precipitation;
  final double rain;
  final double rainProbability;
  final int weatherCode;
  final double windSpeed;
  final double visibility;

  const HourlyWeather({
    required this.time,
    required this.temperature,
    required this.apparentTemperature,
    required this.humidity,
    required this.precipitation,
    required this.rain,
    required this.rainProbability,
    required this.weatherCode,
    required this.windSpeed,
    required this.visibility,
  });
}

class DailyWeather {
  final String date;
  final int weatherCode;
  final double temperatureMax;
  final double temperatureMin;
  final double apparentTemperatureMax;
  final double apparentTemperatureMin;
  final DateTime? sunrise;
  final DateTime? sunset;
  final double precipitationSum;
  final double rainSum;
  final double rainProbabilityMax;
  final double windSpeedMax;

  const DailyWeather({
    required this.date,
    required this.weatherCode,
    required this.temperatureMax,
    required this.temperatureMin,
    required this.apparentTemperatureMax,
    required this.apparentTemperatureMin,
    required this.sunrise,
    required this.sunset,
    required this.precipitationSum,
    required this.rainSum,
    required this.rainProbabilityMax,
    required this.windSpeedMax,
  });
}

class WeatherData {
  final String city;
  final DateTime timestamp;

  // Current weather
  final double temperature;
  final double humidity;
  final double apparentTemperature;
  final double precipitation;
  final double rain;
  final int weatherCode;
  final double windSpeed;

  // Agriculture
  final double? soilMoisture;

  // Air quality
  final double usAqi;
  final double europeanAqi;
  final double uvIndex;
  final double pm25;
  final double pm10;
  final double? nitrogenDioxide;
  final double? sulphurDioxide;
  final double? carbonMonoxide;
  final double? ozone;

  final bool isDaylight;

  // Forecast
  final List<HourlyWeather> hourly;
  final List<DailyWeather> daily;

  const WeatherData({
    required this.city,
    required this.timestamp,
    required this.temperature,
    required this.humidity,
    required this.apparentTemperature,
    required this.precipitation,
    required this.rain,
    required this.weatherCode,
    required this.windSpeed,
    required this.soilMoisture,
    required this.usAqi,
    required this.europeanAqi,
    required this.uvIndex,
    required this.pm25,
    required this.pm10,
    this.nitrogenDioxide,
    this.sulphurDioxide,
    this.carbonMonoxide,
    this.ozone,
    required this.isDaylight,
    this.hourly = const [],
    this.daily = const [],
  });
}
