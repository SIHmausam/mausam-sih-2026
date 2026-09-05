class WeatherData {
  final String city;
  final DateTime timestamp;

  final double temperature;
  final double humidity;
  final double apparentTemperature;

  final double precipitation;
  final double rain;
  final int weatherCode;
  final double windSpeed;

  final double? soilMoisture;

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
    this.soilMoisture,
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
  });
}
