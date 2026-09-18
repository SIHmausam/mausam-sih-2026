import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/weather_data.dart';

class SunMoonPath extends StatelessWidget {
  final DailyWeather daily;

  const SunMoonPath({super.key, required this.daily});

  @override
  Widget build(BuildContext context) {
    final hasSun = daily.sunrise != null && daily.sunset != null;

    final moonrise = daily.moonrise;
    final moonset = daily.moonset;
    final moonPhase = daily.moonPhase;

    final hasMoon = moonrise != null && moonset != null;

    if (!hasSun && !hasMoon) {
      return const SizedBox.shrink();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 4),
          child: Text(
            'SUN & MOON',
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
            border: Border.all(color: Colors.white.withValues(alpha: 0.10)),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 18, 16, 17),
              child: Column(
                children: [
                  SizedBox(
                    height: 170,
                    width: double.infinity,
                    child: CustomPaint(
                      painter: _SunMoonPathPainter(
                        sunrise: daily.sunrise,
                        sunset: daily.sunset,
                        moonrise: moonrise,
                        moonset: moonset,
                      ),
                    ),
                  ),

                  if (hasSun) ...[
                    Row(
                      children: [
                        Expanded(
                          child: _TimeInfo(
                            icon: Icons.wb_sunny_outlined,
                            label: 'SUNRISE',
                            time: _formatTime(daily.sunrise),
                          ),
                        ),
                        Expanded(
                          child: _TimeInfo(
                            icon: Icons.wb_sunny,
                            label: 'SUNSET',
                            time: _formatTime(daily.sunset),
                            alignEnd: true,
                          ),
                        ),
                      ],
                    ),
                  ],

                  if (hasSun && hasMoon)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      child: Container(
                        height: 1,
                        color: Colors.white.withValues(alpha: 0.07),
                      ),
                    ),

                  if (hasMoon)
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(child: _MoonPhase(phase: moonPhase)),
                        const SizedBox(width: 12),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            _CompactTime(
                              label: 'Moonrise',
                              time: _formatTime(moonrise),
                            ),
                            const SizedBox(height: 7),
                            _CompactTime(
                              label: 'Moonset',
                              time: _formatTime(moonset),
                            ),
                          ],
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  static String _formatTime(DateTime? time) {
    if (time == null) return '--';

    final hour = time.hour;
    final minute = time.minute;
    final suffix = hour >= 12 ? 'PM' : 'AM';
    final displayHour = hour % 12 == 0 ? 12 : hour % 12;

    return '$displayHour:${minute.toString().padLeft(2, '0')} $suffix';
  }
}

class _TimeInfo extends StatelessWidget {
  final IconData icon;
  final String label;
  final String time;
  final bool alignEnd;

  const _TimeInfo({
    required this.icon,
    required this.label,
    required this.time,
    this.alignEnd = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: alignEnd
          ? CrossAxisAlignment.end
          : CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: Colors.white.withValues(alpha: 0.68)),
        const SizedBox(height: 5),
        Text(
          label,
          style: TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8,
            color: Colors.white.withValues(alpha: 0.42),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          time,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
      ],
    );
  }
}

class _CompactTime extends StatelessWidget {
  final String label;
  final String time;

  const _CompactTime({required this.label, required this.time});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          '$label  ',
          style: TextStyle(
            fontSize: 10,
            color: Colors.white.withValues(alpha: 0.43),
          ),
        ),
        Text(
          time,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: Colors.white70,
          ),
        ),
      ],
    );
  }
}

class _MoonPhase extends StatelessWidget {
  final double? phase;

  const _MoonPhase({required this.phase});

  @override
  Widget build(BuildContext context) {
    final info = _getMoonPhase(phase);

    return Row(
      children: [
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white.withValues(alpha: 0.055),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          alignment: Alignment.center,
          child: Text(info.symbol, style: const TextStyle(fontSize: 26)),
        ),
        const SizedBox(width: 11),
        Flexible(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'MOON PHASE',
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.7,
                  color: Colors.white.withValues(alpha: 0.40),
                ),
              ),
              const SizedBox(height: 3),
              Text(
                info.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '${(info.fraction * 100).round()}% of lunar cycle',
                style: TextStyle(
                  fontSize: 9,
                  color: Colors.white.withValues(alpha: 0.40),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  static _MoonPhaseData _getMoonPhase(double? value) {
    if (value == null || value.isNaN) {
      return const _MoonPhaseData('🌙', 'Unavailable', 0);
    }

    final phase = value.clamp(0.0, 1.0);

    if (phase < 0.0625 || phase >= 0.9375) {
      return _MoonPhaseData('🌑', 'New Moon', phase);
    }
    if (phase < 0.1875) {
      return _MoonPhaseData('🌒', 'Waxing Crescent', phase);
    }
    if (phase < 0.3125) {
      return _MoonPhaseData('🌓', 'First Quarter', phase);
    }
    if (phase < 0.4375) {
      return _MoonPhaseData('🌔', 'Waxing Gibbous', phase);
    }
    if (phase < 0.5625) {
      return _MoonPhaseData('🌕', 'Full Moon', phase);
    }
    if (phase < 0.6875) {
      return _MoonPhaseData('🌖', 'Waning Gibbous', phase);
    }
    if (phase < 0.8125) {
      return _MoonPhaseData('🌗', 'Last Quarter', phase);
    }

    return _MoonPhaseData('🌘', 'Waning Crescent', phase);
  }
}

class _MoonPhaseData {
  final String symbol;
  final String name;
  final double fraction;

  const _MoonPhaseData(this.symbol, this.name, this.fraction);
}

class _SunMoonPathPainter extends CustomPainter {
  final DateTime? sunrise;
  final DateTime? sunset;
  final DateTime? moonrise;
  final DateTime? moonset;

  const _SunMoonPathPainter({
    required this.sunrise,
    required this.sunset,
    required this.moonrise,
    required this.moonset,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final centerX = size.width / 2;

    // The two tracks deliberately use different heights and radii so
    // they read as two separate celestial paths rather than one doubled arc.
    final sunRadius = size.width * 0.43;
    final moonRadius = size.width * 0.34;

    final sunCenter = Offset(centerX, size.height + 20);

    final moonCenter = Offset(centerX, size.height + 32);

    final sunRect = Rect.fromCircle(center: sunCenter, radius: sunRadius);

    final moonRect = Rect.fromCircle(center: moonCenter, radius: moonRadius);

    final sunStartAngle = math.pi * 1.16;
    final sunSweepAngle = math.pi * 0.68;

    final moonStartAngle = math.pi * 1.20;
    final moonSweepAngle = math.pi * 0.60;

    final sunPathPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2
      ..strokeCap = StrokeCap.round
      ..color = Colors.white.withValues(alpha: 0.20);

    final moonPathPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round
      ..color = Colors.white.withValues(alpha: 0.11);

    canvas.drawArc(sunRect, sunStartAngle, sunSweepAngle, false, sunPathPaint);

    canvas.drawArc(
      moonRect,
      moonStartAngle,
      moonSweepAngle,
      false,
      moonPathPaint,
    );

    if (sunrise != null && sunset != null) {
      _drawEndpoint(
        canvas,
        sunRect,
        sunStartAngle,
        Colors.white.withValues(alpha: 0.42),
      );
      _drawEndpoint(
        canvas,
        sunRect,
        sunStartAngle + sunSweepAngle,
        Colors.white.withValues(alpha: 0.42),
      );

      final progress = _progress(DateTime.now(), sunrise!, sunset!);

      if (progress != null) {
        final angle = sunStartAngle + sunSweepAngle * progress;
        final position = _pointOnCircle(sunCenter, sunRadius, angle);

        _drawSun(canvas, position);
      }
    }

    if (moonrise != null && moonset != null) {
      _drawEndpoint(
        canvas,
        moonRect,
        moonStartAngle,
        Colors.white.withValues(alpha: 0.25),
      );
      _drawEndpoint(
        canvas,
        moonRect,
        moonStartAngle + moonSweepAngle,
        Colors.white.withValues(alpha: 0.25),
      );

      final progress = _progress(DateTime.now(), moonrise!, moonset!);

      if (progress != null) {
        final angle = moonStartAngle + moonSweepAngle * progress;
        final position = _pointOnCircle(moonCenter, moonRadius, angle);

        _drawMoon(canvas, position);
      }
    }
  }

  double? _progress(DateTime now, DateTime start, DateTime end) {
    var startTime = start;
    var endTime = end;

    if (endTime.isBefore(startTime)) {
      endTime = endTime.add(const Duration(days: 1));

      if (now.isBefore(startTime)) {
        now = now.add(const Duration(days: 1));
      }
    }

    final total = endTime.difference(startTime).inSeconds;

    if (total <= 0) return null;

    final elapsed = now.difference(startTime).inSeconds;

    if (elapsed < 0 || elapsed > total) {
      return null;
    }

    return (elapsed / total).clamp(0.0, 1.0);
  }

  Offset _pointOnCircle(Offset center, double radius, double angle) {
    return Offset(
      center.dx + radius * math.cos(angle),
      center.dy + radius * math.sin(angle),
    );
  }

  void _drawEndpoint(Canvas canvas, Rect rect, double angle, Color color) {
    final point = Offset(
      rect.center.dx + rect.width / 2 * math.cos(angle),
      rect.center.dy + rect.height / 2 * math.sin(angle),
    );

    final dotPaint = Paint()..color = color;

    canvas.drawCircle(point, 2.2, dotPaint);
  }

  void _drawSun(Canvas canvas, Offset position) {
    // Soft atmospheric halo.
    final outerGlow = Paint()
      ..color = Colors.white.withValues(alpha: 0.10)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 14);

    canvas.drawCircle(position, 12, outerGlow);

    // Fine rays give the sun a more celestial, less icon-like silhouette.
    final rayPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.46)
      ..strokeWidth = 1.1
      ..strokeCap = StrokeCap.round;

    for (int i = 0; i < 12; i++) {
      final angle = i * math.pi / 6;
      final innerRadius = i.isEven ? 8.2 : 8.8;
      final outerRadius = i.isEven ? 11.5 : 10.8;

      final start = Offset(
        position.dx + math.cos(angle) * innerRadius,
        position.dy + math.sin(angle) * innerRadius,
      );

      final end = Offset(
        position.dx + math.cos(angle) * outerRadius,
        position.dy + math.sin(angle) * outerRadius,
      );

      canvas.drawLine(start, end, rayPaint);
    }

    // Outer rim.
    final rimPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0
      ..color = Colors.white.withValues(alpha: 0.68);

    canvas.drawCircle(position, 6.1, rimPaint);

    // Bright inner solar core.
    final corePaint = Paint()
      ..shader = RadialGradient(
        colors: [
          Colors.white.withValues(alpha: 1.0),
          Colors.white.withValues(alpha: 0.72),
          Colors.white.withValues(alpha: 0.35),
        ],
      ).createShader(Rect.fromCircle(center: position, radius: 5.2));

    canvas.drawCircle(position, 5.2, corePaint);

    // Tiny highlight adds depth without making it cartoonish.
    final highlightPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.85);

    canvas.drawCircle(
      Offset(position.dx - 1.5, position.dy - 1.7),
      1.1,
      highlightPaint,
    );
  }

  void _drawMoon(Canvas canvas, Offset position) {
    // Subtle lunar halo.
    final glow = Paint()
      ..color = Colors.white.withValues(alpha: 0.075)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12);

    canvas.drawCircle(position, 11.5, glow);

    // Crescent silhouette. Drawing the cutout against the transparent
    // canvas keeps it independent of the card background.
    final moonPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.88)
      ..style = PaintingStyle.fill;

    // Difference mode creates the actual crescent from the two circles.
    moonPaint.blendMode = BlendMode.srcOver;

    final crescentPath = Path()
      ..addOval(Rect.fromCircle(center: position, radius: 6.2));

    final cutoutPath = Path()
      ..addOval(
        Rect.fromCircle(
          center: Offset(position.dx + 3.0, position.dy - 2.0),
          radius: 5.7,
        ),
      );

    final combined = Path.combine(
      PathOperation.difference,
      crescentPath,
      cutoutPath,
    );

    canvas.drawPath(combined, moonPaint);

    // Fine illuminated edge.
    final edgePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8
      ..color = Colors.white.withValues(alpha: 0.48);

    canvas.drawPath(combined, edgePaint);

    // Tiny lunar highlight.
    final highlightPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.22);

    canvas.drawCircle(
      Offset(position.dx - 2.4, position.dy - 2.0),
      1.0,
      highlightPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _SunMoonPathPainter oldDelegate) {
    return oldDelegate.sunrise != sunrise ||
        oldDelegate.sunset != sunset ||
        oldDelegate.moonrise != moonrise ||
        oldDelegate.moonset != moonset;
  }
}
