import 'package:flutter/material.dart';

import '../models/weather_data.dart';

class HourlyForecast extends StatefulWidget {
  final List<HourlyWeather> hourly;

  const HourlyForecast({super.key, required this.hourly});

  @override
  State<HourlyForecast> createState() => _HourlyForecastState();
}

class _HourlyForecastState extends State<HourlyForecast> {
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    _scrollController = ScrollController();
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _scrollController
      ..removeListener(_onScroll)
      ..dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final forecast = widget.hourly.take(24).toList();

    if (forecast.isEmpty) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 4),
          child: Text(
            '24-HOUR FORECAST',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
              color: Colors.white70,
            ),
          ),
        ),
        const SizedBox(height: 12),

        // One continuous glass container.
        Container(
          height: 154,
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white.withValues(alpha: 0.10)),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Stack(
              children: [
                ListView.separated(
                  controller: _scrollController,
                  scrollDirection: Axis.horizontal,
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
                  itemCount: forecast.length,
                  separatorBuilder: (_, _) => Container(
                    width: 1,
                    margin: const EdgeInsets.symmetric(vertical: 20),
                    color: Colors.white.withValues(alpha: 0.08),
                  ),
                  itemBuilder: (context, index) {
                    final item = forecast[index];

                    return _HourlyForecastItem(
                      weather: item,
                      isFirst: index == 0,
                    );
                  },
                ),
                _HourlyScrollIndicator(controller: _scrollController),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _HourlyScrollIndicator extends StatelessWidget {
  final ScrollController controller;

  const _HourlyScrollIndicator({required this.controller});

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: 28,
      right: 28,
      bottom: 7,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final maxScroll = controller.hasClients
              ? controller.position.maxScrollExtent
              : 0.0;

          final currentScroll = controller.hasClients
              ? controller.offset.clamp(0.0, maxScroll)
              : 0.0;

          final progress = maxScroll <= 0 ? 0.0 : currentScroll / maxScroll;

          final thumbWidth = constraints.maxWidth * 0.22;
          final travel = constraints.maxWidth - thumbWidth;

          return Container(
            height: 3,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(99),
            ),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Transform.translate(
                offset: Offset(travel * progress, 0),
                child: Container(
                  width: thumbWidth,
                  height: 3,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(99),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _HourlyForecastItem extends StatelessWidget {
  final HourlyWeather weather;
  final bool isFirst;

  const _HourlyForecastItem({required this.weather, required this.isFirst});

  @override
  Widget build(BuildContext context) {
    final timeLabel = isFirst ? 'NOW' : _formatHour(weather.time);

    return SizedBox(
      width: 82,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              timeLabel,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
                color: isFirst ? Colors.white : Colors.white70,
              ),
            ),

            Text(
              _weatherIcon(weather.weatherCode),
              style: const TextStyle(fontSize: 27),
            ),

            Text(
              '${weather.temperature.round()}°',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),

            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.water_drop_outlined,
                  size: 11,
                  color: Colors.white60,
                ),
                const SizedBox(width: 3),
                Text(
                  '${weather.rainProbability.round()}%',
                  style: const TextStyle(fontSize: 10, color: Colors.white70),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatHour(DateTime time) {
    final hour = time.hour;
    final suffix = hour >= 12 ? 'PM' : 'AM';
    final displayHour = hour % 12 == 0 ? 12 : hour % 12;

    return '$displayHour $suffix';
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
