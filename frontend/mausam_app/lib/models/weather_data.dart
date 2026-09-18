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
  final double dewPoint;
  final double showers;
  final double cloudCover;
  final double windDirection;
  final double windGusts;

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
    this.dewPoint = 0,
    this.showers = 0,
    this.cloudCover = 0,
    this.windDirection = 0,
    this.windGusts = 0,
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
  final DateTime? moonrise;
  final DateTime? moonset;
  final double? moonPhase;
  final double precipitationSum;
  final double rainSum;
  final double rainProbabilityMax;
  final double windSpeedMax;
  final double precipitationHours;

  const DailyWeather({
    required this.date,
    required this.weatherCode,
    required this.temperatureMax,
    required this.temperatureMin,
    required this.apparentTemperatureMax,
    required this.apparentTemperatureMin,
    required this.sunrise,
    required this.sunset,
    this.moonrise,
    this.moonset,
    this.moonPhase,
    required this.precipitationSum,
    required this.rainSum,
    required this.rainProbabilityMax,
    required this.windSpeedMax,
    this.precipitationHours = 0,
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
  final double dewPoint;
  final double showers;
  final double rainProbability;
  final double cloudCover;
  final double windDirection;
  final double windGusts;
  final double visibility;

  // Agriculture
  final double? soilMoisture;
  final double? soilMoisture7To28cm;
  final double? soilMoisture28To100cm;
  final double? soilMoisture100To255cm;
  final double? soilTemperature0To7cm;
  final double? soilTemperature7To28cm;
  final double? soilTemperature28To100cm;
  final double? soilTemperature100To255cm;
  final double? evapotranspiration;
  final double? vapourPressureDeficit;

  // Air quality
  final double usAqi;
  final double europeanAqi;
  final String? aqiStandard;
  final double uvIndex;
  final double uvIndexClearSky;
  final double pm25;
  final double pm10;
  final double? nitrogenDioxide;
  final double? sulphurDioxide;
  final double? carbonMonoxide;
  final double? ozone;

  final bool isDaylight;

  // Marine
  final double? waveHeight;
  final double? waveDirection;
  final double? wavePeriod;
  final double? swellWaveHeight;
  final double? swellWaveDirection;
  final double? swellWavePeriod;
  final double? seaLevelHeightMsl;
  final double? seaSurfaceTemperature;

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
    this.dewPoint = 0,
    this.showers = 0,
    this.rainProbability = 0,
    this.cloudCover = 0,
    this.windDirection = 0,
    this.windGusts = 0,
    this.visibility = 0,
    this.soilMoisture7To28cm,
    this.soilMoisture28To100cm,
    this.soilMoisture100To255cm,
    this.soilTemperature0To7cm,
    this.soilTemperature7To28cm,
    this.soilTemperature28To100cm,
    this.soilTemperature100To255cm,
    this.evapotranspiration,
    this.vapourPressureDeficit,
    this.aqiStandard,
    this.uvIndexClearSky = 0,
    this.waveHeight,
    this.waveDirection,
    this.wavePeriod,
    this.swellWaveHeight,
    this.swellWaveDirection,
    this.swellWavePeriod,
    this.seaLevelHeightMsl,
    this.seaSurfaceTemperature,
    this.hourly = const [],
    this.daily = const [],
  });
}
