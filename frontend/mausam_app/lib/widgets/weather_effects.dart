import 'dart:math';

import 'package:flutter/material.dart';

class WeatherEffects extends StatefulWidget {
  final int weatherCode;
  final bool isDaylight;

  const WeatherEffects({
    super.key,
    required this.weatherCode,
    this.isDaylight = true,
  });

  @override
  State<WeatherEffects> createState() => _WeatherEffectsState();
}

class _WeatherEffectsState extends State<WeatherEffects>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final List<_RainDrop> _drops;
  late final List<_AtmosphereParticle> _particles;
  late final List<_Snowflake> _snowflakes;

  final Random _random = Random();

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();

    _drops = List.generate(
      widget.weatherCode >= 95 ? 28 : 20,
      (_) => _RainDrop.random(_random),
    );

    _particles = List.generate(
      22,
      (_) => _AtmosphereParticle.random(_random),
    );

    _snowflakes = List.generate(
      32,
      (_) => _Snowflake.random(_random),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  bool get _isRain =>
      (widget.weatherCode >= 51 && widget.weatherCode <= 67) ||
      (widget.weatherCode >= 80 && widget.weatherCode <= 82) ||
      widget.weatherCode >= 95;

  bool get _isStorm => widget.weatherCode >= 95;

  bool get _isSnow =>
      (widget.weatherCode >= 71 && widget.weatherCode <= 77) ||
      (widget.weatherCode >= 85 && widget.weatherCode <= 86);

  bool get _isFog =>
      widget.weatherCode == 45 || widget.weatherCode == 48;

  bool get _isCloudy =>
      widget.weatherCode == 2 || widget.weatherCode == 3;

  bool get _isMostlyClear =>
      widget.weatherCode == 0 || widget.weatherCode == 1;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          if (_isStorm || _isRain) {
            return CustomPaint(
              painter: _RainPainter(
                drops: _drops,
                progress: _controller.value,
                storm: _isStorm,
                random: _random,
              ),
              size: Size.infinite,
            );
          }

          if (_isSnow) {
            return CustomPaint(
              painter: _SnowPainter(
                snowflakes: _snowflakes,
                progress: _controller.value,
              ),
              size: Size.infinite,
            );
          }

          return CustomPaint(
            painter: _AtmospherePainter(
              particles: _particles,
              progress: _controller.value,
              fog: _isFog,
              cloudy: _isCloudy,
              mostlyClear: _isMostlyClear,
              daylight: widget.isDaylight,
            ),
            size: Size.infinite,
          );
        },
      ),
    );
  }
}

class _RainDrop {
  final double x;
  final double startY;
  final double length;
  final double speed;
  final double opacity;

  const _RainDrop({
    required this.x,
    required this.startY,
    required this.length,
    required this.speed,
    required this.opacity,
  });

  factory _RainDrop.random(Random random) {
    return _RainDrop(
      x: random.nextDouble(),
      startY: random.nextDouble(),
      length: 12 + random.nextDouble() * 20,
      speed: 0.7 + random.nextDouble() * 0.8,
      opacity: 0.18 + random.nextDouble() * 0.28,
    );
  }
}

class _AtmosphereParticle {
  final double x;
  final double y;
  final double radius;
  final double speed;
  final double opacity;
  final double phase;

  const _AtmosphereParticle({
    required this.x,
    required this.y,
    required this.radius,
    required this.speed,
    required this.opacity,
    required this.phase,
  });

  factory _AtmosphereParticle.random(Random random) {
    return _AtmosphereParticle(
      x: random.nextDouble(),
      y: random.nextDouble(),
      radius: 1.5 + random.nextDouble() * 3,
      speed: 0.3 + random.nextDouble() * 0.7,
      opacity: 0.025 + random.nextDouble() * 0.06,
      phase: random.nextDouble() * pi * 2,
    );
  }
}

class _Snowflake {
  final double x;
  final double startY;
  final double radius;
  final double speed;
  final double drift;
  final double opacity;
  final double phase;

  const _Snowflake({
    required this.x,
    required this.startY,
    required this.radius,
    required this.speed,
    required this.drift,
    required this.opacity,
    required this.phase,
  });

  factory _Snowflake.random(Random random) {
    return _Snowflake(
      x: random.nextDouble(),
      startY: random.nextDouble(),
      radius: 1.5 + random.nextDouble() * 3.0,
      speed: 0.18 + random.nextDouble() * 0.35,
      drift: 12 + random.nextDouble() * 24,
      opacity: 0.28 + random.nextDouble() * 0.38,
      phase: random.nextDouble() * pi * 2,
    );
  }
}

class _AtmospherePainter extends CustomPainter {
  final List<_AtmosphereParticle> particles;
  final double progress;
  final bool fog;
  final bool cloudy;
  final bool mostlyClear;
  final bool daylight;

  _AtmospherePainter({
    required this.particles,
    required this.progress,
    required this.fog,
    required this.cloudy,
    required this.mostlyClear,
    required this.daylight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (!daylight) {
      _paintNightAtmosphere(canvas, size);
      return;
    }

    if (fog) {
      _paintFog(canvas, size);
      return;
    }

    if (cloudy) {
      _paintCloudAtmosphere(canvas, size);
      return;
    }

    _paintClearAtmosphere(canvas, size);
  }

  void _paintClearAtmosphere(Canvas canvas, Size size) {
    // Soft sun glow in the upper-right portion of the sky.
    final sunCenter = Offset(
      size.width * 0.78,
      size.height * 0.14,
    );

    for (int i = 5; i >= 1; i--) {
      final radius = size.width * (0.10 + i * 0.045);

      final paint = Paint()
        ..color = Colors.white.withValues(
          alpha: 0.012 + (6 - i) * 0.004,
        )
        ..maskFilter = MaskFilter.blur(
          BlurStyle.normal,
          radius * 0.55,
        );

      canvas.drawCircle(sunCenter, radius, paint);
    }

    // Very subtle sun core.
    final corePaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.055)
      ..maskFilter = const MaskFilter.blur(
        BlurStyle.normal,
        18,
      );

    canvas.drawCircle(
      sunCenter,
      size.width * 0.045,
      corePaint,
    );

    // Barely visible atmospheric particles.
    for (final particle in particles) {
      final drift =
          sin(progress * pi * 2 * particle.speed + particle.phase) * 18;

      final x = particle.x * size.width + drift;
      final y = particle.y * size.height;

      final paint = Paint()
        ..color = Colors.white.withValues(
          alpha: particle.opacity * 0.45,
        );

      canvas.drawCircle(
        Offset(x, y),
        particle.radius * 0.5,
        paint,
      );
    }
  }

  void _paintCloudAtmosphere(Canvas canvas, Size size) {
    // Soft moving cloud masses.
    for (int i = 0; i < 6; i++) {
      final width = size.width * (0.40 + i * 0.035);
      final height = size.height * (0.12 + i * 0.012);

      final baseX = (i * size.width * 0.23) - width * 0.30;
      final drift = sin(progress * pi * 2 * 0.28 + i) * 30;

      final rect = Rect.fromLTWH(
        baseX + drift,
        size.height * (0.04 + i * 0.14),
        width,
        height,
      );

      final paint = Paint()
        ..color = Colors.white.withValues(alpha: 0.026)
        ..maskFilter = const MaskFilter.blur(
          BlurStyle.normal,
          32,
        );

      canvas.drawOval(rect, paint);
    }

    // Small amount of atmospheric motion.
    for (final particle in particles.take(10)) {
      final drift =
          sin(progress * pi * 2 * particle.speed + particle.phase) * 12;

      final paint = Paint()
        ..color = Colors.white.withValues(
          alpha: particle.opacity * 0.25,
        );

      canvas.drawCircle(
        Offset(
          particle.x * size.width + drift,
          particle.y * size.height,
        ),
        particle.radius * 0.4,
        paint,
      );
    }
  }

  void _paintFog(Canvas canvas, Size size) {
    for (int i = 0; i < 5; i++) {
      final drift = sin(progress * pi * 2 * 0.20 + i * 1.4) * 35;

      final rect = Rect.fromLTWH(
        -size.width * 0.1 + drift,
        size.height * (0.16 + i * 0.18),
        size.width * 1.2,
        size.height * 0.16,
      );

      final paint = Paint()
        ..color = Colors.white.withValues(alpha: 0.045)
        ..maskFilter = const MaskFilter.blur(
          BlurStyle.normal,
          45,
        );

      canvas.drawOval(rect, paint);
    }
  }

  void _paintNightAtmosphere(Canvas canvas, Size size) {
    // More visible but still elegant stars.
    for (final particle in particles) {
      final drift =
          sin(progress * pi * 2 * particle.speed + particle.phase) * 8;

      final x = particle.x * size.width + drift;
      final y = particle.y * size.height;

      // Smooth twinkling cycle.
      final twinkle =
          0.35 + (sin(progress * pi * 2 * 1.2 + particle.phase) + 1) * 0.32;

      final opacity = min(
        0.48,
        particle.opacity * 5.0 * twinkle,
      );

      final paint = Paint()
        ..color = Colors.white.withValues(alpha: opacity);

      canvas.drawCircle(
        Offset(x, y),
        particle.radius * 0.65,
        paint,
      );

      // A tiny glow around brighter stars.
      if (twinkle > 0.75) {
        final glowPaint = Paint()
          ..color = Colors.white.withValues(alpha: opacity * 0.16)
          ..maskFilter = const MaskFilter.blur(
            BlurStyle.normal,
            5,
          );

        canvas.drawCircle(
          Offset(x, y),
          particle.radius * 1.8,
          glowPaint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant _AtmospherePainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

class _SnowPainter extends CustomPainter {
  final List<_Snowflake> snowflakes;
  final double progress;

  _SnowPainter({
    required this.snowflakes,
    required this.progress,
  });

  @override
  void paint(Canvas canvas, Size size) {
    for (final snowflake in snowflakes) {
      final yProgress =
          (snowflake.startY + progress * snowflake.speed) % 1.12;

      final y = yProgress * (size.height + 60) - 30;

      final x = snowflake.x * size.width +
          sin(progress * pi * 2 + snowflake.phase) * snowflake.drift;

      final paint = Paint()
        ..color = Colors.white.withValues(alpha: snowflake.opacity)
        ..style = PaintingStyle.fill;

      canvas.drawCircle(
        Offset(x, y),
        snowflake.radius,
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _SnowPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

class _RainPainter extends CustomPainter {
  final List<_RainDrop> drops;
  final double progress;
  final bool storm;
  final Random random;

  _RainPainter({
    required this.drops,
    required this.progress,
    required this.storm,
    required this.random,
  });

  @override
  void paint(Canvas canvas, Size size) {
    for (final drop in drops) {
      final yProgress = (drop.startY + progress * drop.speed) % 1.15;
      final y = yProgress * (size.height + 80) - 40;
      final x = drop.x * size.width;

      final paint = Paint()
        ..color = Colors.white.withValues(alpha: drop.opacity)
        ..strokeWidth = 1.2
        ..strokeCap = StrokeCap.round;

      canvas.drawLine(
        Offset(x, y),
        Offset(x - 5, y + drop.length),
        paint,
      );
    }

    if (storm) {
      final lightningChance = random.nextDouble();

      if (lightningChance < 0.015) {
        final flashPaint = Paint()
          ..color = Colors.white.withValues(alpha: 0.16);

        canvas.drawRect(Offset.zero & size, flashPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _RainPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}
