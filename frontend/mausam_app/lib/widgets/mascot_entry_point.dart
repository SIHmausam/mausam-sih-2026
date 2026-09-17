import 'dart:async';
import 'dart:ui';

import 'package:flutter/material.dart';

class MascotEntryPoint extends StatefulWidget {
  final FutureOr<void> Function() onTap;
  final bool showHint;

  const MascotEntryPoint({
    super.key,
    required this.onTap,
    this.showHint = true,
  });

  @override
  State<MascotEntryPoint> createState() => _MascotEntryPointState();
}

class _MascotEntryPointState extends State<MascotEntryPoint>
    with TickerProviderStateMixin {
  late final AnimationController _idleController;
  late final AnimationController _tapController;
  bool _showHint = false;

  @override
  void initState() {
    super.initState();

    _idleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2600),
    )..repeat(reverse: true);

    _tapController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 260),
    );

    _startHintCycle();
  }

  Future<void> _startHintCycle() async {
    while (mounted) {
      if (!mounted) return;

      setState(() => _showHint = true);

      await Future.delayed(const Duration(seconds: 4));

      if (!mounted) return;

      setState(() => _showHint = false);

      await Future.delayed(const Duration(seconds: 26));
    }
  }

  @override
  void dispose() {
    _idleController.dispose();
    _tapController.dispose();
    super.dispose();
  }

  Future<void> _handleTap() async {
    await _tapController.forward(from: 0);

    if (!mounted) return;

    await widget.onTap();

    if (!mounted) return;

    await _tapController.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_idleController, _tapController]),
      builder: (context, child) {
        final idleOffset = lerpDouble(-2.0, 2.0, _idleController.value) ?? 0.0;

        final tapProgress = Curves.easeOutCubic.transform(_tapController.value);

        final tapOffset = lerpDouble(0.0, -11.0, tapProgress) ?? 0.0;
        final tapScale = lerpDouble(1.0, 1.055, tapProgress) ?? 1.0;
        final tapTilt = lerpDouble(0.0, 0.12, tapProgress) ?? 0.0;

        return Transform.translate(
          offset: Offset(0, idleOffset + tapOffset),
          child: Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.0015)
              ..rotateY(tapTilt),
            child: Transform.scale(scale: tapScale, child: child),
          ),
        );
      },
      child: GestureDetector(
        onTap: _handleTap,
        behavior: HitTestBehavior.opaque,
        child: SizedBox(
          width: 92,
          height: 104,
          child: Stack(
            clipBehavior: Clip.none,
            alignment: Alignment.bottomCenter,
            children: [
              if (widget.showHint && _showHint)
                Positioned(top: 0, right: -28, child: _HintBubble()),

              // Soft grounding shadow makes the mascot feel attached
              // to the navigation surface.
              Positioned(
                bottom: 4,
                child: Container(
                  width: 58,
                  height: 14,
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.22),
                    borderRadius: BorderRadius.circular(50),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.16),
                        blurRadius: 14,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                ),
              ),

              // Temporary vector mascot.
              // This keeps the entry point functional until the final
              // Mausam mascot artwork is supplied.
              Positioned(bottom: 10, child: MausamCloudMascot()),
            ],
          ),
        ),
      ),
    );
  }
}

class _HintBubble extends StatelessWidget {
  const _HintBubble();

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(14),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.42),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
          ),
          child: Text(
            'Need help?',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.92),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }
}

class MausamCloudMascot extends StatefulWidget {
  const MausamCloudMascot({super.key});

  @override
  State<MausamCloudMascot> createState() => _MausamCloudMascotState();
}

class _MausamCloudMascotState extends State<MausamCloudMascot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _eyeController;

  @override
  void initState() {
    super.initState();

    _eyeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );

    _startEyeCycle();
  }

  Future<void> _startEyeCycle() async {
    while (mounted) {
      await Future.delayed(const Duration(seconds: 15));

      if (!mounted) return;

      await _eyeController.animateTo(
        0.2,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
      );

      await Future.delayed(const Duration(seconds: 2));

      if (!mounted) return;

      await _eyeController.animateTo(
        0.7,
        duration: const Duration(milliseconds: 500),
        curve: Curves.easeInOut,
      );

      await Future.delayed(const Duration(seconds: 2));

      if (!mounted) return;

      await _eyeController.animateTo(
        1.0,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
      );
    }
  }

  @override
  void dispose() {
    _eyeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 70,
      height: 66,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 61,
            height: 36,
            margin: const EdgeInsets.only(top: 18),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.96),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.20),
                  blurRadius: 12,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
          ),
          Positioned(
            left: 14,
            top: 16,
            child: Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
            ),
          ),
          Positioned(
            right: 13,
            top: 21,
            child: Container(
              width: 26,
              height: 26,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
            ),
          ),
          AnimatedBuilder(
            animation: _eyeController,
            builder: (context, child) {
              final progress = _eyeController.value;

              final eyeX = progress < 0.2
                  ? lerpDouble(0.0, -7.0, progress / 0.2) ?? 0.0
                  : progress < 0.7
                  ? lerpDouble(-7.0, 7.0, (progress - 0.2) / 0.5) ?? 0.0
                  : lerpDouble(7.0, 0.0, (progress - 0.7) / 0.3) ?? 0.0;

              final eyeY = progress < 0.2
                  ? lerpDouble(0.0, -5.0, progress / 0.2) ?? 0.0
                  : progress < 0.7
                  ? lerpDouble(-5.0, -5.0, (progress - 0.2) / 0.5) ?? -5.0
                  : lerpDouble(-5.0, 0.0, (progress - 0.7) / 0.3) ?? 0.0;

              return Positioned(
                left: 27 + eyeX,
                top: 37 + eyeY,
                child: Row(
                  children: [
                    const _MascotEye(),
                    const SizedBox(width: 10),
                    const _MascotEye(),
                  ],
                ),
              );
            },
          ),
          Positioned(
            left: 31,
            top: 47,
            child: Container(
              width: 9,
              height: 4,
              decoration: BoxDecoration(
                color: const Color(0xFF263B52),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MascotEye extends StatelessWidget {
  const _MascotEye();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 4,
      height: 6,
      decoration: BoxDecoration(
        color: const Color(0xFF263B52),
        borderRadius: BorderRadius.circular(8),
      ),
    );
  }
}
