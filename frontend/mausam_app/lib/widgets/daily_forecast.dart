import 'package:flutter/material.dart';

import '../models/weather_data.dart';

class DailyForecast extends StatelessWidget {
  final List<DailyWeather> daily;

  const DailyForecast({
    super.key,
    required this.daily,
  });

  @override
  Widget build(BuildContext context) {
    final forecast = daily.take(7).toList();

    if (forecast.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 4),
          child: Text(
            '7-DAY FORECAST',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
              color: Colors.white70,
            ),
          ),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.10),
            ),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Column(
              children: [
                for (int i = 0; i < forecast.length; i++) ...[
                  _DailyForecastRow(
                    weather: forecast[i],
                    isToday: i == 0,
                  ),
                  if (i < forecast.length - 1)
                    Container(
                      height: 1,
                      margin: const EdgeInsets.symmetric(horizontal: 14),
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _DailyForecastRow extends StatelessWidget {
  final DailyWeather weather;
  final bool isToday;

  const _DailyForecastRow({
    required this.weather,
    required this.isToday,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 62,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Row(
          children: [
            SizedBox(
              width: 64,
              child: Text(
                isToday ? 'Today' : _formatDay(weather.date),
                style: TextStyle(
                  fontSize: 13,
                  fontWeight:
                      isToday ? FontWeight.w700 : FontWeight.w500,
                  color:
                      isToday ? Colors.white : Colors.white70,
                ),
              ),
            ),

            const SizedBox(width: 18),

            SizedBox(
              width: 38,
              child: Text(
                _weatherIcon(weather.weatherCode),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 23),
              ),
            ),

            const Spacer(),

            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.water_drop_outlined,
                  size: 11,
                  color: Colors.white60,
                ),
                const SizedBox(width: 4),
                Text(
                  '${weather.rainProbabilityMax.round()}%',
                  style: const TextStyle(
                    fontSize: 10,
                    color: Colors.white60,
                  ),
                ),
              ],
            ),

            const SizedBox(width: 18),

            SizedBox(
              width: 64,
              child: Text(
                '${weather.temperatureMax.round()}° / '
                '${weather.temperatureMin.round()}°',
                textAlign: TextAlign.right,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDay(String date) {
    final parsed = DateTime.tryParse(date);

    if (parsed == null) {
      return date;
    }

    const days = [
      'Mon',
      'Tue',
      'Wed',
      'Thu',
      'Fri',
      'Sat',
      'Sun',
    ];

    return days[parsed.weekday - 1];
  }

  String _weatherIcon(int code) {
    if (code == 0) return '☀️';
    if (code == 1) return '🌤️';
    if (code == 2) return '⛅';
    if (code == 3) return '☁️';

    if (code >= 45 && code <= 48) return '🌫️';
    if (code >= 51 && code <= 57) return '🌦️';
    if (code >= 61 && code <= 67) return '🌧️';
    if (code >= 71 && code <= 77) return '❄️';
    if (code >= 80 && code <= 82) return '🌦️';
    if (code >= 85 && code <= 86) return '🌨️';
    if (code >= 95) return '⛈️';

    return '🌤️';
  }
}
