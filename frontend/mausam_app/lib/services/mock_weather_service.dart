import '../models/weather_data.dart';
import '../models/personalized_card.dart';

class MockWeatherService {
  static WeatherData getWeather() {
    return WeatherData(
      city: 'Ghaziabad, UP',
      timestamp: DateTime.now(),
      temperature: 28,
      humidity: 91,
      apparentTemperature: 31,
      precipitation: 0,
      rain: 0,
      weatherCode: 95,
      windSpeed: 14,
      soilMoisture: 42,
      usAqi: 163,
      europeanAqi: 82,
      uvIndex: 9,
      pm25: 72,
      pm10: 118,
      isDaylight: true,
    );
  }

  static List<PersonalizedCard> getPersonalizedCards(String persona) {
    switch (persona) {
      case 'Farmer':
        return const [
          PersonalizedCard(
            cardId: 'soil_moisture',
            rank: 1,
            score: 0.91,
            insight: 'Soil moisture is moderate; monitor levels before irrigation.',
          ),
          PersonalizedCard(
            cardId: 'rain',
            rank: 2,
            score: 0.84,
            insight: 'No rain is currently recorded; irrigation may be needed.',
          ),
          PersonalizedCard(
            cardId: 'humidity',
            rank: 3,
            score: 0.78,
            insight: 'Very high humidity may increase crop disease risk.',
          ),
          PersonalizedCard(
            cardId: 'temperature',
            rank: 4,
            score: 0.68,
            insight: 'Warm conditions may increase moisture loss from the soil.',
          ),
          PersonalizedCard(
            cardId: 'weather_condition',
            rank: 5,
            score: 0.55,
            insight: 'Monitor changing weather conditions before outdoor farm work.',
          ),
          PersonalizedCard(
            cardId: 'wind',
            rank: 6,
            score: 0.43,
            insight: 'Moderate winds are currently blowing across the area.',
          ),
          PersonalizedCard(
            cardId: 'aqi',
            rank: 7,
            score: 0.31,
            insight: 'Air quality is currently unhealthy.',
          ),
          PersonalizedCard(
            cardId: 'uv',
            rank: 8,
            score: 0.22,
            insight: 'UV exposure is currently very high.',
          ),
        ];

      case 'Traveler':
        return const [
          PersonalizedCard(
            cardId: 'weather_condition',
            rank: 1,
            score: 0.91,
            insight: 'Thunderstorm conditions are present; plan outdoor travel carefully.',
          ),
          PersonalizedCard(
            cardId: 'rain',
            rank: 2,
            score: 0.84,
            insight: 'No rainfall is currently recorded at this location.',
          ),
          PersonalizedCard(
            cardId: 'temperature',
            rank: 3,
            score: 0.76,
            insight: 'Current temperatures are warm with a slightly higher feels-like value.',
          ),
          PersonalizedCard(
            cardId: 'aqi',
            rank: 4,
            score: 0.71,
            insight: 'Air quality is unhealthy; sensitive travelers should take care.',
          ),
          PersonalizedCard(
            cardId: 'wind',
            rank: 5,
            score: 0.52,
            insight: 'Moderate winds are currently affecting outdoor conditions.',
          ),
          PersonalizedCard(
            cardId: 'uv',
            rank: 6,
            score: 0.46,
            insight: 'UV exposure is very high during daylight hours.',
          ),
          PersonalizedCard(
            cardId: 'humidity',
            rank: 7,
            score: 0.38,
            insight: 'Humidity is currently very high.',
          ),
          PersonalizedCard(
            cardId: 'soil_moisture',
            rank: 8,
            score: 0.18,
            insight: 'Soil moisture is at a moderate level.',
          ),
        ];

      case 'Fitness Enthusiast':
      default:
        return const [
          PersonalizedCard(
            cardId: 'aqi',
            rank: 1,
            score: 0.91,
            insight: 'Air quality is unhealthy; consider limiting prolonged outdoor exercise.',
          ),
          PersonalizedCard(
            cardId: 'uv',
            rank: 2,
            score: 0.86,
            insight: 'UV exposure is very high; protect yourself during outdoor activity.',
          ),
          PersonalizedCard(
            cardId: 'temperature',
            rank: 3,
            score: 0.76,
            insight: 'Warm conditions may make intense outdoor exercise feel harder.',
          ),
          PersonalizedCard(
            cardId: 'humidity',
            rank: 4,
            score: 0.71,
            insight: 'Very high humidity can make exercise feel more strenuous.',
          ),
          PersonalizedCard(
            cardId: 'weather_condition',
            rank: 5,
            score: 0.52,
            insight: 'Thunderstorm conditions are present; outdoor activity needs caution.',
          ),
          PersonalizedCard(
            cardId: 'rain',
            rank: 6,
            score: 0.42,
            insight: 'No rainfall is currently recorded at this location.',
          ),
          PersonalizedCard(
            cardId: 'wind',
            rank: 7,
            score: 0.34,
            insight: 'Moderate winds are currently blowing.',
          ),
          PersonalizedCard(
            cardId: 'soil_moisture',
            rank: 8,
            score: 0.18,
            insight: 'Soil moisture is at a moderate level.',
          ),
        ];
    }
  }
}
