import 'dart:ui';

import 'package:flutter/material.dart';

import 'models/weather_data.dart';
import 'services/mock_weather_service.dart';
import 'services/card_mapper.dart';
import 'services/weather_code_mapper.dart';

import 'widgets/priority_card.dart';
import 'widgets/weather_effects.dart';

import 'config/app_config.dart';
import 'services/google_auth_service.dart';
import 'services/auth_api_service.dart';
import 'services/token_storage_service.dart';
import 'services/auth_session_service.dart';

void main() {
  runApp(const MausamApp());
}

class MausamApp extends StatelessWidget {
  const MausamApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Mausam',
      theme: ThemeData(useMaterial3: true, fontFamily: 'sans'),
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _fade;
  late final Animation<double> _scale;
  late final Animation<double> _cloudOne;
  late final Animation<double> _cloudTwo;
  late final Animation<double> _cloudThree;
  final AuthSessionService _authSessionService =
    AuthSessionService();

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 6000),
    )..forward();

    _fade = CurvedAnimation(
      parent: _controller,
      curve: const Interval(0.0, 0.45, curve: Curves.easeOut),
    );

    _scale = Tween<double>(
      begin: 1.035,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic));

    _cloudOne = Tween<double>(
      begin: -0.15,
      end: 1.15,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

    _cloudTwo = Tween<double>(
      begin: 1.15,
      end: -0.20,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

    _cloudThree = Tween<double>(
      begin: -0.25,
      end: 1.10,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

    _restoreSessionAndContinue();
  }

  Future<void> _restoreSessionAndContinue() async {
    // Keep the splash visible for a short minimum duration
    // while session restoration happens.
    final results = await Future.wait([
      _authSessionService.restoreSession(),
      Future<void>.delayed(
        const Duration(milliseconds: 2500),
      ),
    ]);

    if (!mounted) {
      return;
    }

    final isAuthenticated = results.first as bool;

    final Widget nextScreen;

    if (isAuthenticated) {
      // Temporary destination.
      // Later we will load the user's saved persona/profile
      // from the backend and go directly to MainShell.
      nextScreen = const PersonaSelectionScreen();
    } else {
      nextScreen = const OnboardingScreen();
    }

    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, _, _) => nextScreen,
        transitionDuration:
            const Duration(milliseconds: 700),
        transitionsBuilder:
            (_, animation, _, child) {
          return FadeTransition(
            opacity: CurvedAnimation(
              parent: animation,
              curve: Curves.easeInOut,
            ),
            child: child,
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _cloud({
    required double progress,
    required double top,
    required double width,
    required double height,
    required double opacity,
  }) {
    final screenWidth = MediaQuery.sizeOf(context).width;
    final left = (screenWidth + width) * progress - width;

    return Positioned(
      left: left,
      top: top,
      child: Opacity(
        opacity: opacity,
        child: ImageFiltered(
          imageFilter: ImageFilter.blur(sigmaX: 1.5, sigmaY: 1.5),
          child: SizedBox(
            width: width,
            height: height,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Positioned(
                  left: width * 0.08,
                  bottom: height * 0.05,
                  child: Container(
                    width: width * 0.72,
                    height: height * 0.38,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(height),
                    ),
                  ),
                ),
                Positioned(
                  left: width * 0.25,
                  bottom: height * 0.20,
                  child: Container(
                    width: width * 0.34,
                    height: height * 0.46,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
                Positioned(
                  left: width * 0.48,
                  bottom: height * 0.14,
                  child: Container(
                    width: width * 0.30,
                    height: height * 0.40,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedBuilder(
        animation: _controller,
        builder: (context, child) {
          return Stack(
            fit: StackFit.expand,
            children: [
              Transform.scale(
                scale: _scale.value,
                child: Image.asset(
                  'assets/mausam_splash.png',
                  fit: BoxFit.cover,
                ),
              ),

              // Soft atmospheric veil.
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.black.withValues(alpha: 0.04),
                      Colors.transparent,
                      Colors.black.withValues(alpha: 0.10),
                    ],
                  ),
                ),
              ),

              // Slowly drifting atmospheric clouds.
              _cloud(
                progress: _cloudOne.value,
                top: MediaQuery.sizeOf(context).height * 0.20,
                width: 145,
                height: 65,
                opacity: 0.075,
              ),

              _cloud(
                progress: _cloudTwo.value,
                top: MediaQuery.sizeOf(context).height * 0.43,
                width: 190,
                height: 80,
                opacity: 0.055,
              ),

              _cloud(
                progress: _cloudThree.value,
                top: MediaQuery.sizeOf(context).height * 0.68,
                width: 125,
                height: 55,
                opacity: 0.065,
              ),

              // Gentle entrance fade.
              FadeTransition(opacity: _fade, child: const SizedBox.expand()),

              // Minimal loading indicator.
              Positioned(
                left: 0,
                right: 0,
                bottom: MediaQuery.sizeOf(context).height * 0.055,
                child: Center(
                  child: SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 1.8,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        Colors.white.withValues(alpha: 0.82),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<_OnboardingData> _pages = const [
    _OnboardingData(
      icon: Icons.cloud_outlined,
      title: 'Welcome to Mausam',
      description:
          'Personalized weather, designed around you and the way you live.',
    ),
    _OnboardingData(
      icon: Icons.auto_awesome_outlined,
      title: 'Weather that adapts to you',
      description: 'See the weather information that matters most to your lifestyle and interests.',
    ),
    _OnboardingData(
      icon: Icons.notifications_none_rounded,
      title: 'Stay ahead of the weather',
      description: 'Get useful insights and timely alerts so you can plan your day with confidence.',
    ),
  ];

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _nextPage() {
    if (_currentPage < _pages.length - 1) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 450),
        curve: Curves.easeInOutCubic,
      );
    } else {
      _openGetStarted();
    }
  }

  void _skip() {
    _openGetStarted();
  }

  void _openGetStarted() {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => const GetStartedScreen(),
        transitionDuration: const Duration(milliseconds: 550),
        transitionsBuilder: (_, animation, __, child) {
          return FadeTransition(
            opacity: CurvedAnimation(
              parent: animation,
              curve: Curves.easeInOut,
            ),
            child: child,
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(22, 14, 22, 0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        onPressed: _skip,
                        child: Text(
                          'Skip',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.72),
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                Expanded(
                  child: PageView.builder(
                    controller: _pageController,
                    itemCount: _pages.length,
                    onPageChanged: (index) {
                      setState(() => _currentPage = index);
                    },
                    itemBuilder: (context, index) {
                      final page = _pages[index];

                      return Padding(
                        padding: const EdgeInsets.fromLTRB(28, 18, 28, 20),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Spacer(),

                            AnimatedContainer(
                              duration: const Duration(milliseconds: 400),
                              width: 108,
                              height: 108,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.10),
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.18),
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withValues(alpha: 0.16),
                                    blurRadius: 28,
                                    spreadRadius: 2,
                                  ),
                                ],
                              ),
                              child: Icon(
                                page.icon,
                                color: Colors.white.withValues(alpha: 0.92),
                                size: 48,
                              ),
                            ),

                            const SizedBox(height: 42),

                            Text(
                              page.title,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 30,
                                height: 1.15,
                                fontWeight: FontWeight.w700,
                                letterSpacing: -0.6,
                              ),
                            ),

                            const SizedBox(height: 18),

                            Text(
                              page.description,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.72),
                                fontSize: 16,
                                height: 1.55,
                                fontWeight: FontWeight.w400,
                              ),
                            ),

                            const Spacer(),
                          ],
                        ),
                      );
                    },
                  ),
                ),

                Padding(
                  padding: const EdgeInsets.fromLTRB(28, 0, 28, 24),
                  child: Row(
                    children: [
                      Expanded(
                        child: Row(
                          children: List.generate(_pages.length, (index) {
                            final selected = index == _currentPage;

                            return AnimatedContainer(
                              duration: const Duration(milliseconds: 300),
                              margin: const EdgeInsets.only(right: 7),
                              width: selected ? 24 : 7,
                              height: 7,
                              decoration: BoxDecoration(
                                color: selected
                                    ? Colors.white.withValues(alpha: 0.92)
                                    : Colors.white.withValues(alpha: 0.25),
                                borderRadius: BorderRadius.circular(10),
                              ),
                            );
                          }),
                        ),
                      ),

                      _OnboardingNextButton(
                        label: _currentPage == _pages.length - 1
                            ? 'Get Started'
                            : 'Next',
                        onPressed: _nextPage,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OnboardingData {
  final IconData icon;
  final String title;
  final String description;

  const _OnboardingData({
    required this.icon,
    required this.title,
    required this.description,
  });
}

class _OnboardingBackground extends StatelessWidget {
  const _OnboardingBackground();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF101C2C), Color(0xFF263B52), Color(0xFF526678)],
        ),
      ),
      child: Stack(
        fit: StackFit.expand,
        children: [
          Positioned(
            top: -90,
            right: -80,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withValues(alpha: 0.035),
              ),
            ),
          ),
          Positioned(
            bottom: -110,
            left: -90,
            child: Container(
              width: 280,
              height: 280,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withValues(alpha: 0.025),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _OnboardingNextButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const _OnboardingNextButton({required this.label, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(18),
        child: Ink(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.13),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 9),
              const Icon(
                Icons.arrow_forward_rounded,
                color: Colors.white,
                size: 18,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class GetStartedScreen extends StatelessWidget {
  const GetStartedScreen({super.key});

  void _continue(BuildContext context) {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => const LoginScreen(),
        transitionDuration: const Duration(milliseconds: 500),
        transitionsBuilder: (_, animation, __, child) {
          return FadeTransition(
            opacity: CurvedAnimation(
              parent: animation,
              curve: Curves.easeInOut,
            ),
            child: child,
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(28, 30, 28, 28),
              child: Column(
                children: [
                  const Spacer(),

                  Container(
                    width: 92,
                    height: 92,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.white.withValues(alpha: 0.10),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.17),
                      ),
                    ),
                    child: const Icon(
                      Icons.wb_cloudy_outlined,
                      color: Colors.white,
                      size: 43,
                    ),
                  ),

                  const SizedBox(height: 30),

                  const Text(
                    'Your Mausam.\nYour way.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 34,
                      height: 1.12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.8,
                    ),
                  ),

                  const SizedBox(height: 18),

                  Text(
                    'Let’s personalize your weather experience.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.70),
                      fontSize: 16,
                      height: 1.5,
                    ),
                  ),

                  const Spacer(),

                  SizedBox(
                    width: double.infinity,
                    child: _OnboardingNextButton(
                      label: 'Continue',
                      onPressed: () => _continue(context),
                    ),
                  ),

                  const SizedBox(height: 12),

                  Text(
                    'You can change your preferences anytime.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.42),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class PersonaSelectionScreen extends StatefulWidget {
  const PersonaSelectionScreen({super.key});

  @override
  State<PersonaSelectionScreen> createState() => _PersonaSelectionScreenState();
}

class _PersonaSelectionScreenState extends State<PersonaSelectionScreen> {
  int _selectedPersona = 0;

  final List<Map<String, dynamic>> _personas = [
    {
      'title': 'Fitness Enthusiast',
      'subtitle': 'Weather insights for workouts and outdoor activity.',
      'icon': Icons.directions_run_rounded,
    },
    {
      'title': 'Farmer',
      'subtitle': 'Weather conditions that help you plan farm activities.',
      'icon': Icons.agriculture_rounded,
    },
    {
      'title': 'Traveler',
      'subtitle': 'Stay prepared for weather while you travel.',
      'icon': Icons.flight_takeoff_rounded,
    },
  ];

  void _continue() {
    Navigator.of(context).push(
      _darkRoute(
        page: LocationSetupScreen(
          persona: _personas[_selectedPersona]['title'] as String,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 18, 24, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),

                  const SizedBox(height: 42),

                  const Text(
                    'Make Mausam yours',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 30,
                      fontWeight: FontWeight.w700,
                      height: 1.15,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Text(
                    'Choose what best describes you. We’ll prioritize '
                    'weather information that matters to you.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.62),
                      fontSize: 15,
                      height: 1.45,
                    ),
                  ),

                  const SizedBox(height: 34),

                  ...List.generate(
                    _personas.length,
                    (index) => Padding(
                      padding: const EdgeInsets.only(bottom: 14),
                      child: _PersonaCard(
                        title: _personas[index]['title'] as String,
                        subtitle: _personas[index]['subtitle'] as String,
                        icon: _personas[index]['icon'] as IconData,
                        selected: _selectedPersona == index,
                        onTap: () {
                          setState(() {
                            _selectedPersona = index;
                          });
                        },
                      ),
                    ),
                  ),

                  const SizedBox(height: 22),

                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: _continue,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF182535),
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                        ),
                      ),
                      child: const Text(
                        'Continue',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  Center(
                    child: Text(
                      'You can change this later in your profile.',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.42),
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PersonaCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  const _PersonaCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: selected
              ? Colors.white.withValues(alpha: 0.15)
              : Colors.white.withValues(alpha: 0.07),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: selected
                ? Colors.white.withValues(alpha: 0.55)
                : Colors.white.withValues(alpha: 0.12),
            width: selected ? 1.4 : 1,
          ),
        ),
        child: Row(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              width: 54,
              height: 54,
              decoration: BoxDecoration(
                color: selected
                    ? Colors.white.withValues(alpha: 0.18)
                    : Colors.white.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(icon, color: Colors.white, size: 27),
            ),

            const SizedBox(width: 16),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.55),
                      fontSize: 12.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 12),

            AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              width: 22,
              height: 22,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: Colors.white.withValues(alpha: selected ? 1 : 0.35),
                  width: 1.5,
                ),
              ),
              child: selected
                  ? const Icon(
                      Icons.check_rounded,
                      color: Colors.white,
                      size: 15,
                    )
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}

class LocationSetupScreen extends StatefulWidget {
  final String persona;

  const LocationSetupScreen({super.key, required this.persona});

  @override
  State<LocationSetupScreen> createState() => _LocationSetupScreenState();
}

class _LocationSetupScreenState extends State<LocationSetupScreen> {
  final _locationController = TextEditingController(text: 'Ghaziabad');

  @override
  void dispose() {
    _locationController.dispose();
    super.dispose();
  }

  void _useCurrentLocation() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Location permission will be connected next.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _continue() {
    Navigator.of(context).pushAndRemoveUntil(
      _darkRoute(page: MainShell(persona: widget.persona)),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      resizeToAvoidBottomInset: false,
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 18, 24, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),

                  const SizedBox(height: 42),

                  const Text(
                    'Where should we start?',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 30,
                      fontWeight: FontWeight.w700,
                      height: 1.15,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Text(
                    'Choose a location to get accurate weather and '
                    'personalized insights.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.62),
                      fontSize: 15,
                      height: 1.45,
                    ),
                  ),

                  const SizedBox(height: 34),

                  GestureDetector(
                    onTap: _useCurrentLocation,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(22),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.16),
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 54,
                            height: 54,
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.10),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: const Icon(
                              Icons.my_location_rounded,
                              color: Colors.white,
                              size: 27,
                            ),
                          ),

                          const SizedBox(width: 16),

                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Use my current location',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 5),
                                Text(
                                  'Get weather based on your device location.',
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.55),
                                    fontSize: 12.5,
                                    height: 1.35,
                                  ),
                                ),
                              ],
                            ),
                          ),

                          Icon(
                            Icons.chevron_right_rounded,
                            color: Colors.white.withValues(alpha: 0.55),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 26),

                  Row(
                    children: [
                      Expanded(
                        child: Container(
                          height: 1,
                          color: Colors.white.withValues(alpha: 0.12),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        child: Text(
                          'or',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.42),
                            fontSize: 12,
                          ),
                        ),
                      ),
                      Expanded(
                        child: Container(
                          height: 1,
                          color: Colors.white.withValues(alpha: 0.12),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 26),

                  Text(
                    'Choose a location manually',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.78),
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.14),
                      ),
                    ),
                    child: TextField(
                      controller: _locationController,
                      style: const TextStyle(color: Colors.white, fontSize: 15),
                      cursorColor: Colors.white,
                      decoration: InputDecoration(
                        hintText: 'Enter city',
                        hintStyle: TextStyle(
                          color: Colors.white.withValues(alpha: 0.35),
                        ),
                        prefixIcon: Icon(
                          Icons.location_on_outlined,
                          color: Colors.white.withValues(alpha: 0.60),
                        ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 18,
                          vertical: 17,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 28),

                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: _continue,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: const Color(0xFF182535),
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                        ),
                      ),
                      child: const Text(
                        'Continue to Mausam',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  Center(
                    child: Text(
                      'You can change your location anytime.',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.42),
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

PageRouteBuilder<void> _weatherDetailRoute({
  required CardDisplayData card,
  required String persona,
  required WeatherData weather,
}) {
  return PageRouteBuilder<void>(
    opaque: true,
    barrierColor: const Color(0xFF101C2C),
    pageBuilder: (context, animation, secondaryAnimation) {
      return WeatherDetailScreen(
        card: card,
        persona: persona,
        weather: weather,
      );
    },
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final curvedAnimation = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutCubic,
      );

      return FadeTransition(
        opacity: curvedAnimation,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.025),
            end: Offset.zero,
          ).animate(curvedAnimation),
          child: child,
        ),
      );
    },
  );
}

PageRouteBuilder<void> _darkRoute({required Widget page}) {
  return PageRouteBuilder<void>(
    opaque: true,
    barrierColor: const Color(0xFF101C2C),
    pageBuilder: (context, animation, secondaryAnimation) {
      return page;
    },
    transitionDuration: const Duration(milliseconds: 450),
    reverseTransitionDuration: const Duration(milliseconds: 350),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final curvedAnimation = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutCubic,
      );

      return FadeTransition(
        opacity: curvedAnimation,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.02),
            end: Offset.zero,
          ).animate(curvedAnimation),
          child: child,
        ),
      );
    },
  );
}

class WeatherDetailScreen extends StatelessWidget {
  final CardDisplayData card;
  final String persona;
  final WeatherData weather;

  const WeatherDetailScreen({
    super.key,
    required this.card,
    required this.persona,
    required this.weather,
  });

  String _meaningForCard() {
    switch (card.title) {
      case 'Air Quality':
        return 'This indicates the current level of air pollution. Higher values can '
            'make prolonged outdoor activity less comfortable or advisable.';
      case 'UV Index':
        return 'The UV Index indicates the strength of ultraviolet radiation. '
            'Higher levels mean greater need for sun protection.';
      case 'Temperature':
        return 'Temperature shows how warm or cool the air is, while the feels-like '
            'value accounts for how conditions may actually feel.';
      case 'Humidity':
        return 'Humidity describes how much moisture is present in the air. '
            'Very high humidity can make warm conditions feel more uncomfortable.';
      case 'Rainfall':
        return 'Rainfall shows the amount of rain currently being recorded at '
            'the selected location.';
      case 'Wind':
        return 'Wind speed describes how quickly air is moving. Stronger winds '
            'can affect outdoor activities and travel conditions.';
      case 'Soil Moisture':
        return 'Soil moisture indicates the current amount of water available '
            'in the soil and can help guide agricultural decisions.';
      case 'Condition':
        return 'This summarizes the current atmospheric condition at your '
            'selected location.';
      default:
        return 'This weather metric helps you understand current environmental '
            'conditions at your location.';
    }
  }

  String _uvCategory(double uv) {
    if (uv <= 2) return 'Low';
    if (uv <= 5) return 'Moderate';
    if (uv <= 7) return 'High';
    if (uv <= 10) return 'Very High';
    return 'Extreme';
  }

  String _uvRange(double uv) {
    if (uv <= 2) return '0 – 2';
    if (uv <= 5) return '3 – 5';
    if (uv <= 7) return '6 – 7';
    if (uv <= 10) return '8 – 10';
    return '11+';
  }

  String _uvGuidance(double uv) {
    if (uv <= 2) {
      return 'UV exposure is low. Normal outdoor activity generally requires minimal '
          'UV protection.';
    }
    if (uv <= 5) {
      return 'UV exposure is moderate. Consider basic sun protection during prolonged '
          'outdoor activity.';
    }
    if (uv <= 7) {
      return 'UV exposure is high. Use sun protection and consider limiting prolonged '
          'direct exposure.';
    }
    if (uv <= 10) {
      return 'UV exposure is very high. Protect yourself from direct sunlight and '
          'consider reducing prolonged outdoor exposure.';
    }
    return 'UV exposure is extreme. Minimize direct sunlight and use strong sun '
        'protection when outdoors.';
  }

  Widget _uvContent() {
    if (card.title != 'UV Index') {
      return const SizedBox.shrink();
    }

    final uv = weather.uvIndex;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'UV INDEX',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        uv.toStringAsFixed(0),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'DAYLIGHT',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        weather.isDaylight ? 'Yes' : 'No',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DetailGlassSection(
          title: 'UV CATEGORY',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _uvCategory(uv),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                _uvRange(uv),
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        _DetailGlassSection(
          title: 'PROTECTION',
          child: Text(
            _uvGuidance(uv),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _aqiCategory(double aqi) {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Satisfactory';
    if (aqi <= 200) return 'Moderate';
    if (aqi <= 300) return 'Poor';
    if (aqi <= 400) return 'Very Poor';
    return 'Severe';
  }

  String _aqiRange(double aqi) {
    if (aqi <= 50) return '0 – 50';
    if (aqi <= 100) return '51 – 100';
    if (aqi <= 200) return '101 – 200';
    if (aqi <= 300) return '201 – 300';
    if (aqi <= 400) return '301 – 400';
    return '401+';
  }

  String _aqiGuidance(double aqi) {
    if (aqi <= 50) {
      return 'Air quality is good and outdoor activity is generally comfortable.';
    }
    if (aqi <= 100) {
      return 'Air quality is generally acceptable, though sensitive people may notice '
          'some effects during prolonged outdoor activity.';
    }
    if (aqi <= 200) {
      return 'Air quality is moderately polluted. Consider reducing prolonged or '
          'intense outdoor activity if you are sensitive to pollution.';
    }
    if (aqi <= 300) {
      return 'Air quality is poor. Consider limiting prolonged outdoor activity, '
          'especially intense exercise.';
    }
    if (aqi <= 400) {
      return 'Air quality is very poor. Avoid prolonged outdoor exposure where possible.';
    }
    return 'Air quality is severe. Avoid outdoor exposure and follow local health guidance.';
  }

  Widget _aqiContent() {
    if (card.title != 'Air Quality') {
      return const SizedBox.shrink();
    }

    final aqi = weather.usAqi;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT AIR QUALITY',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'AQI',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        aqi.toStringAsFixed(0),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'PM2.5',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${weather.pm25.toStringAsFixed(0)} µg/m³',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'PARTICULATE MATTER',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'PM10',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${weather.pm10.toStringAsFixed(0)} µg/m³',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'STATUS',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: card.indicatorColor,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _aqiCategory(aqi),
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'AQI CATEGORY',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _aqiCategory(aqi),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                _aqiRange(aqi),
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _aqiGuidance(aqi),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _temperatureCategory(double temp) {
    if (temp < 10) return 'Cold';
    if (temp < 18) return 'Cool';
    if (temp <= 30) return 'Comfortable';
    if (temp <= 36) return 'Warm';
    return 'Hot';
  }

  String _temperatureGuidance(double temp) {
    if (temp < 10) {
      return 'Cold conditions can make extended outdoor activity uncomfortable. '
          'Dress appropriately and account for the lower temperature.';
    }
    if (temp < 18) {
      return 'Cool conditions are generally manageable outdoors, though some '
          'activities may require an extra layer for comfort.';
    }
    if (temp <= 30) {
      return 'Temperatures are generally comfortable for outdoor activity, '
          'depending on humidity and other conditions.';
    }
    if (temp <= 36) {
      return 'Warm conditions can increase heat discomfort, especially during '
          'prolonged or intense outdoor activity.';
    }
    return 'Hot conditions can increase heat stress. Limit prolonged outdoor '
        'exposure and stay hydrated.';
  }

  Widget _temperatureContent() {
    if (card.title != 'Temperature') {
      return const SizedBox.shrink();
    }

    final temp = weather.temperature;
    final feelsLike = weather.apparentTemperature;
    final difference = feelsLike - temp;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'TEMPERATURE',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${temp.toStringAsFixed(0)}°C',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'FEELS LIKE',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${feelsLike.toStringAsFixed(0)}°C',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'HOW IT FEELS',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _temperatureCategory(temp),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              if (difference.abs() >= 1)
                Text(
                  '${difference > 0 ? '+' : ''}${difference.toStringAsFixed(0)}°C feels',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.55),
                    fontSize: 13,
                  ),
                ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _temperatureGuidance(temp),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _humidityCategory(double humidity) {
    if (humidity < 30) return 'Very Dry';
    if (humidity < 40) return 'Dry';
    if (humidity <= 60) return 'Comfortable';
    if (humidity <= 80) return 'Humid';
    return 'Very Humid';
  }

  String _humidityGuidance(double humidity) {
    if (humidity < 30) {
      return 'Very dry air can feel uncomfortable and may increase moisture loss '
          'during prolonged outdoor activity.';
    }
    if (humidity < 40) {
      return 'Dry conditions may feel comfortable for some activities, though '
          'hydration remains important during exercise.';
    }
    if (humidity <= 60) {
      return 'Humidity is in a generally comfortable range for most outdoor activities.';
    }
    if (humidity <= 80) {
      return 'Higher humidity can make warm conditions feel more uncomfortable and '
          'may increase perceived exertion during outdoor activity.';
    }
    return 'Very high humidity can make the air feel heavy and significantly increase '
        'heat discomfort during outdoor activity.';
  }

  Widget _humidityContent() {
    if (card.title != 'Humidity') {
      return const SizedBox.shrink();
    }

    final humidity = weather.humidity;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'HUMIDITY',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${humidity.toStringAsFixed(0)}%',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CATEGORY',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        _humidityCategory(humidity),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'COMFORT LEVEL',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _humidityCategory(humidity),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                '${humidity.toStringAsFixed(0)}%',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _humidityGuidance(humidity),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _rainfallCategory(double rain) {
    if (rain <= 0.2) return 'No Significant Rain';
    if (rain <= 2.5) return 'Light Rain';
    if (rain <= 7.5) return 'Moderate Rain';
    if (rain <= 35) return 'Heavy Rain';
    return 'Very Heavy Rain';
  }

  String _rainfallGuidance(double rain) {
    if (rain <= 0.2) {
      return 'No significant rain is currently being recorded. Outdoor activities '
          'are less likely to be affected by rainfall.';
    }
    if (rain <= 2.5) {
      return 'Light rain is currently being recorded. Outdoor activities may still '
          'be possible with suitable protection.';
    }
    if (rain <= 7.5) {
      return 'Moderate rain can affect outdoor movement and visibility. Plan activities '
          'with wet conditions in mind.';
    }
    if (rain <= 35) {
      return 'Heavy rain can significantly affect outdoor activities, visibility, '
          'and local travel conditions.';
    }
    return 'Very heavy rain can create difficult outdoor and travel conditions. '
        'Exercise caution and monitor local weather updates.';
  }

  Widget _rainfallContent() {
    if (card.title != 'Rainfall') {
      return const SizedBox.shrink();
    }

    final rain = weather.rain;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'RAINFALL',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${rain.toStringAsFixed(1)} mm',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'STATUS',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        rain > 0.2 ? 'Rain Detected' : 'No Significant Rain',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'RAINFALL LEVEL',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _rainfallCategory(rain),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                '${rain.toStringAsFixed(1)} mm',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _rainfallGuidance(rain),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _windCategory(double wind) {
    if (wind < 10) return 'Light';
    if (wind < 25) return 'Moderate';
    if (wind < 40) return 'Strong';
    return 'Very Strong';
  }

  String _windGuidance(double wind) {
    if (wind < 10) {
      return 'Light winds are unlikely to significantly affect most outdoor '
          'activities or local movement.';
    }
    if (wind < 25) {
      return 'Moderate winds may be noticeable during outdoor activities but are '
          'generally manageable.';
    }
    if (wind < 40) {
      return 'Strong winds can affect outdoor comfort, cycling, travel, and other '
          'activities that are sensitive to wind.';
    }
    return 'Very strong winds can make outdoor activity difficult. Exercise caution '
        'and consider avoiding exposed areas.';
  }

  Widget _windContent() {
    if (card.title != 'Wind') {
      return const SizedBox.shrink();
    }

    final wind = weather.windSpeed;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'WIND SPEED',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${wind.toStringAsFixed(0)} km/h',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 23,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CATEGORY',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        _windCategory(wind),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WIND LEVEL',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _windCategory(wind),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                '${wind.toStringAsFixed(0)} km/h',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _windGuidance(wind),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _soilMoistureCategory(double moisture) {
    if (moisture < 20) return 'Very Dry';
    if (moisture < 35) return 'Dry';
    if (moisture <= 65) return 'Good';
    if (moisture <= 80) return 'High';
    return 'Very High';
  }

  String _soilMoistureGuidance(double moisture) {
    if (moisture < 20) {
      return 'Soil moisture is very low. Crops may experience water stress, so '
          'irrigation needs should be assessed based on crop and field conditions.';
    }
    if (moisture < 35) {
      return 'Soil moisture is low. Monitor the field closely and assess irrigation '
          'needs according to crop requirements.';
    }
    if (moisture <= 65) {
      return 'Soil moisture is in a generally favorable range. Continue monitoring '
          'conditions as weather and crop needs change.';
    }
    if (moisture <= 80) {
      return 'Soil moisture is relatively high. Monitor drainage and field conditions '
          'before adding more water.';
    }
    return 'Soil moisture is very high. Monitor for excess water and poor drainage, '
        'particularly after rainfall.';
  }

  Widget _soilMoistureContent() {
    if (card.title != 'Soil Moisture' || weather.soilMoisture == null) {
      return const SizedBox.shrink();
    }

    final moisture = weather.soilMoisture!;

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SOIL MOISTURE',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        '${moisture.toStringAsFixed(0)}%',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CATEGORY',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        _soilMoistureCategory(moisture),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'MOISTURE LEVEL',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  _soilMoistureCategory(moisture),
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                '${moisture.toStringAsFixed(0)}%',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _soilMoistureGuidance(moisture),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _conditionCategory(int code) {
    if (code >= 95) return 'Thunderstorm';
    if (code >= 80) return 'Rain Showers';
    if (code >= 71) return 'Snow';
    if (code >= 51) return 'Rain';
    if (code >= 45) return 'Foggy';
    if (code >= 1) return 'Cloudy';
    return 'Clear';
  }

  String _conditionGuidance(int code) {
    if (code >= 95) {
      return 'Thunderstorm conditions are present. Outdoor activity may become '
          'unsafe, particularly in exposed areas. Consider staying indoors until '
          'conditions improve.';
    }

    if (code >= 80) {
      return 'Rain showers are currently possible or occurring. Outdoor movement '
          'may be affected by wet surfaces and reduced visibility.';
    }

    if (code >= 71) {
      return 'Snow conditions are being reported. Cold and slippery conditions '
          'may affect outdoor movement and travel.';
    }

    if (code >= 51) {
      return 'Rain is currently affecting conditions. Consider suitable protection '
          'and allow for potentially wet outdoor surfaces.';
    }

    if (code >= 45) {
      return 'Fog can reduce visibility, especially during outdoor movement and '
          'travel. Use additional caution in low-visibility areas.';
    }

    if (code >= 1) {
      return 'Cloudy conditions are present. Outdoor activity can generally continue '
          'while other weather factors remain favorable.';
    }

    return 'Clear conditions are currently present and generally support normal '
        'outdoor activity.';
  }

  Widget _conditionContent() {
    if (card.title != 'Condition') {
      return const SizedBox.shrink();
    }

    final code = weather.weatherCode;
    final condition = _conditionCategory(code);

    return Column(
      children: [
        _DetailGlassSection(
          title: 'CURRENT CONDITIONS',
          child: Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CONDITION',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        condition,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    borderRadius: BorderRadius.circular(17),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.08),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'TIME OF DAY',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.50),
                          fontSize: 11,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        weather.isDaylight ? 'Daylight' : 'Night',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WEATHER STATUS',
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: card.indicatorColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: card.indicatorColor.withValues(alpha: 0.50),
                      blurRadius: 8,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  condition,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Text(
                'Code $code',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.45),
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        _DetailGlassSection(
          title: 'WHAT TO KNOW',
          child: Text(
            _conditionGuidance(code),
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.68),
              fontSize: 14,
              height: 1.55,
            ),
          ),
        ),
      ],
    );
  }

  String _personaContext() {
    switch (persona) {
      case 'Farmer':
        return 'Useful for planning farm activities and responding to changing '
            'environmental conditions.';
      case 'Traveler':
        return 'Useful for planning outdoor movement, travel timing, and daily activities.';
      case 'Fitness Enthusiast':
      default:
        return 'Useful for deciding when and how to plan outdoor exercise safely.';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),

                  const SizedBox(height: 22),

                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(26),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.16),
                      ),
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 58,
                              height: 58,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.10),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                card.icon,
                                color: Colors.white,
                                size: 28,
                              ),
                            ),

                            const SizedBox(width: 16),

                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    card.title,
                                    style: TextStyle(
                                      color: Colors.white.withValues(
                                        alpha: 0.75,
                                      ),
                                      fontSize: 14,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                  const SizedBox(height: 5),
                                  Text(
                                    card.status,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 15,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            Container(
                              width: 13,
                              height: 13,
                              decoration: BoxDecoration(
                                color: card.indicatorColor,
                                shape: BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(
                                    color: card.indicatorColor.withValues(
                                      alpha: 0.55,
                                    ),
                                    blurRadius: 9,
                                    spreadRadius: 1,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 30),

                        Text(
                          card.value,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 48,
                            fontWeight: FontWeight.w700,
                            letterSpacing: -1.5,
                          ),
                        ),

                        const SizedBox(height: 8),

                        Text(
                          card.status,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.60),
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 18),

                  if (card.title == 'Condition') ...[
                    _conditionContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'Soil Moisture') ...[
                    _soilMoistureContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'Wind') ...[
                    _windContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'Rainfall') ...[
                    _rainfallContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'Humidity') ...[
                    _humidityContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'Temperature') ...[
                    _temperatureContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'Air Quality') ...[
                    _aqiContent(),
                    const SizedBox(height: 18),
                  ],

                  if (card.title == 'UV Index') ...[
                    _uvContent(),
                    const SizedBox(height: 18),
                  ],

                  _DetailGlassSection(
                    title: 'INSIGHT',
                    child: Text(
                      card.insight,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        height: 1.5,
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  _DetailGlassSection(
                    title: 'WHAT THIS MEANS',
                    child: Text(
                      _meaningForCard(),
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.68),
                        fontSize: 14,
                        height: 1.55,
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  _DetailGlassSection(
                    title: 'FOR YOUR PROFILE',
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.auto_awesome_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _personaContext(),
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.68),
                              fontSize: 14,
                              height: 1.55,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 14),

                  _DetailGlassSection(
                    title: 'TREND',
                    child: Container(
                      width: double.infinity,
                      height: 150,
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.08),
                        ),
                      ),
                      child: Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.show_chart_rounded,
                              color: Colors.white.withValues(alpha: 0.45),
                              size: 28,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Trend data will appear here',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.45),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailGlassSection extends StatelessWidget {
  final String title;
  final Widget child;

  const _DetailGlassSection({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(19),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(21),
        border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.45),
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 11),
          child,
        ],
      ),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final GoogleAuthService _googleAuthService =
      GoogleAuthService(
    serverClientId: AppConfig.googleServerClientId,
  );
  final AuthApiService _authApiService =
    AuthApiService();
  final TokenStorageService _tokenStorageService =
    TokenStorageService();

  bool _isGoogleSigningIn = false;

  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor: const Color(0xFF263B52),
      ),
    );
  }

  void _login() {
    Navigator.of(context)
        .push(_darkRoute(page: const PersonaSelectionScreen()));
  }

  void _openSignUp() {
    Navigator.of(context).push(_darkRoute(page: const SignUpScreen()));
  }

  Future<void> _handleGoogleSignIn() async {
    if (AppConfig.googleServerClientId.isEmpty) {
      _showMessage(
        'Google Server Client ID is not configured.',
      );
      return;
    }

    if (_isGoogleSigningIn) {
      return;
    }

    setState(() {
      _isGoogleSigningIn = true;
    });

    try {
      final googleIdToken =
          await _googleAuthService
              .signInAndGetIdToken();

      final tokens =
          await _authApiService.loginWithGoogle(
        idToken: googleIdToken,
      );

      await _tokenStorageService.saveTokens(
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );

      if (!mounted) {
        return;
      }

      _showMessage(
        'Mausam login successful.',
      );

      Navigator.of(context).pushReplacement(
        _darkRoute(
          page: const PersonaSelectionScreen(),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      _showMessage(
        'Login failed: $error',
      );
    } finally {
      if (mounted) {
        setState(() {
          _isGoogleSigningIn = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      resizeToAvoidBottomInset: false,
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(26, 16, 26, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    icon: const Icon(
                      Icons.arrow_back_rounded,
                      color: Colors.white,
                      size: 25,
                    ),
                  ),

                  const SizedBox(height: 42),

                  const Text(
                    'Welcome to Mausam',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 32,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.6,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Text(
                    'Sign in to personalize your weather experience.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.65),
                      fontSize: 15,
                      height: 1.5,
                    ),
                  ),

                  const SizedBox(height: 34),

                  _AuthField(
                    label: 'Email',
                    hint: 'you@example.com',
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    prefixIcon: Icons.email_outlined,
                  ),

                  const SizedBox(height: 17),

                  _AuthField(
                    label: 'Password',
                    hint: 'Enter your password',
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    prefixIcon: Icons.lock_outline_rounded,
                    suffixIcon: IconButton(
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                        color: Colors.white.withValues(alpha: 0.55),
                        size: 20,
                      ),
                    ),
                  ),

                  const SizedBox(height: 8),

                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: () {
                        _showMessage(
                          'Password recovery will be available soon.',
                        );
                      },
                      child: Text(
                        'Forgot password?',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.72),
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 12),

                  _AuthPrimaryButton(
                    label: 'Login',
                    icon: Icons.arrow_forward_rounded,
                    onPressed: _login,
                  ),

                  const SizedBox(height: 28),

                  Row(
                    children: [
                      Expanded(
                        child: Container(
                          height: 1,
                          color: Colors.white.withValues(alpha: 0.12),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                        child: Text(
                          'or',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.42),
                            fontSize: 12,
                          ),
                        ),
                      ),
                      Expanded(
                        child: Container(
                          height: 1,
                          color: Colors.white.withValues(alpha: 0.12),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 22),

                  _AuthSecondaryButton(
                    label: 'Continue with Google',
                    icon: Icons.g_mobiledata_rounded,
                    onPressed:
                        _isGoogleSigningIn
                            ? null
                            : _handleGoogleSignIn,
                  ),

                  const SizedBox(height: 28),

                  Center(
                    child: Wrap(
                      alignment: WrapAlignment.center,
                      children: [
                        Text(
                          "Don't have an account? ",
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.52),
                            fontSize: 13,
                          ),
                        ),
                        GestureDetector(
                          onTap: _openSignUp,
                          child: const Text(
                            'Create account',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key});

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _obscurePassword = true;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _createAccount() {
    Navigator.of(context)
        .push(_darkRoute(page: const PersonaSelectionScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      resizeToAvoidBottomInset: false,
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(26, 16, 26, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                    icon: const Icon(
                      Icons.arrow_back_rounded,
                      color: Colors.white,
                      size: 25,
                    ),
                  ),

                  const SizedBox(height: 38),

                  const Text(
                    'Create your account',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 30,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.5,
                    ),
                  ),

                  const SizedBox(height: 10),

                  Text(
                    'A few details and we’ll start personalizing Mausam for you.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.65),
                      fontSize: 15,
                      height: 1.5,
                    ),
                  ),

                  const SizedBox(height: 32),

                  _AuthField(
                    label: 'Name',
                    hint: 'Your name',
                    controller: _nameController,
                    prefixIcon: Icons.person_outline_rounded,
                  ),

                  const SizedBox(height: 17),

                  _AuthField(
                    label: 'Email',
                    hint: 'you@example.com',
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    prefixIcon: Icons.email_outlined,
                  ),

                  const SizedBox(height: 17),

                  _AuthField(
                    label: 'Password',
                    hint: 'Create a password',
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    prefixIcon: Icons.lock_outline_rounded,
                    suffixIcon: IconButton(
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                        color: Colors.white.withValues(alpha: 0.55),
                        size: 20,
                      ),
                    ),
                  ),

                  const SizedBox(height: 28),

                  _AuthPrimaryButton(
                    label: 'Create account',
                    icon: Icons.arrow_forward_rounded,
                    onPressed: _createAccount,
                  ),

                  const SizedBox(height: 28),

                  Center(
                    child: Wrap(
                      alignment: WrapAlignment.center,
                      children: [
                        Text(
                          'Already have an account? ',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.52),
                            fontSize: 13,
                          ),
                        ),
                        GestureDetector(
                          onTap: () => Navigator.pop(context),
                          child: const Text(
                            'Login',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AuthField extends StatelessWidget {
  final String label;
  final String hint;
  final TextEditingController controller;
  final TextInputType? keyboardType;
  final bool obscureText;
  final IconData prefixIcon;
  final Widget? suffixIcon;

  const _AuthField({
    required this.label,
    required this.hint,
    required this.controller,
    required this.prefixIcon,
    this.keyboardType,
    this.obscureText = false,
    this.suffixIcon,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.76),
            fontSize: 13,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
            child: TextField(
              controller: controller,
              keyboardType: keyboardType,
              obscureText: obscureText,
              style: const TextStyle(color: Colors.white, fontSize: 15),
              cursorColor: Colors.white,
              decoration: InputDecoration(
                hintText: hint,
                hintStyle: TextStyle(
                  color: Colors.white.withValues(alpha: 0.34),
                ),
                prefixIcon: Icon(
                  prefixIcon,
                  color: Colors.white.withValues(alpha: 0.52),
                  size: 20,
                ),
                suffixIcon: suffixIcon,
                filled: true,
                fillColor: Colors.white.withValues(alpha: 0.075),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 16,
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: Colors.white.withValues(alpha: 0.12),
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide(
                    color: Colors.white.withValues(alpha: 0.30),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _AuthPrimaryButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onPressed;

  const _AuthPrimaryButton({
    required this.label,
    required this.icon,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(17),
          child: Ink(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(17),
              border: Border.all(color: Colors.white.withValues(alpha: 0.20)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(width: 10),
                Icon(icon, color: Colors.white, size: 19),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AuthSecondaryButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;

  const _AuthSecondaryButton({
    required this.label,
    required this.icon,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(17),
          child: Ink(
            padding: const EdgeInsets.symmetric(vertical: 15),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.055),
              borderRadius: BorderRadius.circular(17),
              border: Border.all(color: Colors.white.withValues(alpha: 0.13)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  icon,
                  color: Colors.white.withValues(alpha: 0.88),
                  size: 22,
                ),
                const SizedBox(width: 9),
                Text(
                  label,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.88),
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class MainShell extends StatefulWidget {
  final String persona;

  const MainShell({super.key, required this.persona});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  void _selectPage(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  void _openMenu() {
    showGeneralDialog<void>(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Close menu',
      barrierColor: Colors.black.withValues(alpha: 0.38),
      transitionDuration: const Duration(milliseconds: 380),
      pageBuilder: (context, animation, secondaryAnimation) {
        return _SideMenu(
          currentIndex: _currentIndex,
          onSelect: (index) {
            Navigator.pop(context);
            _selectPage(index);
          },
          onSettings: () {
            Navigator.pop(context);
            Navigator.push(context, _darkRoute(page: const SettingsPage()));
          },
        );
      },
      transitionBuilder: (context, animation, secondaryAnimation, child) {
        final curved = CurvedAnimation(
          parent: animation,
          curve: Curves.easeOutCubic,
          reverseCurve: Curves.easeInCubic,
        );

        return SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(-1, 0),
            end: Offset.zero,
          ).animate(curved),
          child: child,
        );
      },
    );
  }

  Widget _currentPage() {
    switch (_currentIndex) {
      case 0:
        return HomeScreen(
          showBottomNav: false,
          onMenuTap: _openMenu,
          persona: widget.persona,
        );

      case 1:
        return const _SimplePage(
          title: 'My Day',
          icon: Icons.calendar_today_rounded,
          message: 'Your personalized daily plan will appear here.',
        );

      case 2:
        return const MapComingSoonPage();

      case 3:
        return const ProfilePage();

      default:
        return const _SimplePage(
          title: 'Mausam',
          icon: Icons.cloud_outlined,
          message: 'Welcome to Mausam.',
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          _currentPage(),

          Positioned(
            left: 18,
            right: 18,
            bottom: 18,
            child: _FunctionalNavBar(
              currentIndex: _currentIndex,
              onSelected: _selectPage,
            ),
          ),
        ],
      ),
    );
  }
}

class _FunctionalNavBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onSelected;

  const _FunctionalNavBar({
    required this.currentIndex,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: Container(
          height: 70,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.40),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white.withValues(alpha: 0.22)),
          ),
          child: Row(
            children: [
              _FunctionalNavItem(
                icon: Icons.home_rounded,
                label: 'Home',
                active: currentIndex == 0,
                onTap: () => onSelected(0),
              ),
              _FunctionalNavItem(
                icon: Icons.calendar_today_rounded,
                label: 'My Day',
                active: currentIndex == 1,
                onTap: () => onSelected(1),
              ),
              _FunctionalNavItem(
                icon: Icons.map_outlined,
                label: 'Map',
                active: currentIndex == 2,
                onTap: () => onSelected(2),
              ),
              _FunctionalNavItem(
                icon: Icons.person_outline_rounded,
                label: 'Profile',
                active: currentIndex == 3,
                onTap: () => onSelected(3),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FunctionalNavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _FunctionalNavItem({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final iconColor = active
        ? Colors.white
        : Colors.white.withValues(alpha: 0.55);

    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: iconColor, size: 23),
            const SizedBox(height: 3),
            Text(
              label,
              style: TextStyle(
                color: iconColor,
                fontSize: 10,
                fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
            const SizedBox(height: 3),
            if (active)
              Container(
                width: 5,
                height: 5,
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const _OnboardingBackground(),
        SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 30, 20, 120),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _PageHeader(
                  title: 'Profile',
                  subtitle: 'Your Mausam personalization profile',
                  icon: Icons.person_outline_rounded,
                ),
                const SizedBox(height: 28),

                GlassContainer(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      Container(
                        width: 64,
                        height: 64,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.12),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.fitness_center_rounded,
                          color: Colors.white,
                          size: 29,
                        ),
                      ),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Fitness',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 21,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            SizedBox(height: 5),
                            Text(
                              'Your weather insights are personalized for an active lifestyle.',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 12,
                                height: 1.4,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                const _ProfileSectionTitle(title: 'PERSONALIZATION'),

                GlassContainer(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Column(
                    children: [
                      const _ProfileInfoRow(
                        icon: Icons.psychology_outlined,
                        title: 'Personalization',
                        value: 'Active',
                      ),
                      Divider(
                        height: 1,
                        indent: 52,
                        color: Colors.white.withValues(alpha: 0.08),
                      ),
                      const _ProfileInfoRow(
                        icon: Icons.location_on_outlined,
                        title: 'Location',
                        value: 'Ghaziabad, UP',
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                const _ProfileSectionTitle(title: 'PERSONA'),

                GlassContainer(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    children: [
                      const _PersonaOption(
                        icon: Icons.fitness_center_rounded,
                        title: 'Fitness',
                        subtitle:
                            'Health, UV, air quality and outdoor conditions.',
                        selected: true,
                      ),
                      const SizedBox(height: 10),
                      const _PersonaOption(
                        icon: Icons.agriculture_outlined,
                        title: 'Farmer',
                        subtitle: 'Weather conditions relevant to agricultural activity.',
                      ),
                      const SizedBox(height: 10),
                      const _PersonaOption(
                        icon: Icons.luggage_outlined,
                        title: 'Traveler',
                        subtitle: 'Travel-friendly weather and environmental information.',
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _PageBackground extends StatelessWidget {
  final Widget child;

  const _PageBackground({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF263B52), Color(0xFF3D5870), Color(0xFF667D90)],
        ),
      ),
      child: child,
    );
  }
}

class _PageHeader extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;

  const _PageHeader({
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.12),
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white.withValues(alpha: 0.14)),
          ),
          child: Icon(icon, color: Colors.white, size: 25),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 25,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: const TextStyle(color: Colors.white70, fontSize: 12),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ProfileSectionTitle extends StatelessWidget {
  final String title;

  const _ProfileSectionTitle({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 9),
      child: Text(
        title,
        style: const TextStyle(
          color: Colors.white70,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

class _ProfileInfoRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;

  const _ProfileInfoRow({
    required this.icon,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 52,
      child: Row(
        children: [
          const SizedBox(width: 14),
          Icon(icon, color: Colors.white70, size: 21),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(color: Colors.white, fontSize: 14),
            ),
          ),
          Text(
            value,
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
          const SizedBox(width: 14),
        ],
      ),
    );
  }
}

class _PersonaOption extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool selected;

  const _PersonaOption({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.selected = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: selected
            ? Colors.white.withValues(alpha: 0.12)
            : Colors.white.withValues(alpha: 0.055),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: selected
              ? Colors.white.withValues(alpha: 0.28)
              : Colors.white.withValues(alpha: 0.08),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.10),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: Colors.white, size: 21),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (selected) ...[
                      const SizedBox(width: 7),
                      const Icon(
                        Icons.check_circle,
                        color: Colors.white,
                        size: 16,
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(
                    color: Colors.white60,
                    fontSize: 11,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  String persona = 'Fitness';
  String interests = 'Outdoor Run, Air Quality';
  String location = 'Ghaziabad, UP';
  String weatherAlerts = 'Severe Only';
  String temperatureUnit = 'Celsius (°C)';
  String windSpeed = 'km/h';
  String language = 'English';

  bool personalizeHomepage = true;
  bool improveRecommendations = true;
  bool dailyBriefing = true;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const _OnboardingBackground(),
        Material(
          type: MaterialType.transparency,
          child: SafeArea(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 22, 20, 40),
              children: [
                Row(
                  children: [
                    GlassButton(
                      icon: Icons.arrow_back_ios_new_rounded,
                      onTap: () => Navigator.pop(context),
                    ),
                    const SizedBox(width: 14),
                    const Text(
                      'Settings',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 28),

                const _SettingsGlassSectionTitle(
                  title: 'PERSONA & PREFERENCES',
                ),
                GlassContainer(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Column(
                    children: [
                      _GlassActionRow(
                        title: 'Change persona',
                        value: persona,
                        onTap: _changePersona,
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'Edit interests',
                        value: interests,
                        onTap: _editInterests,
                      ),
                      const _GlassDivider(),
                      _GlassSwitchRow(
                        title: 'Personalize homepage',
                        value: personalizeHomepage,
                        onChanged: (value) {
                          setState(() => personalizeHomepage = value);
                        },
                      ),
                      const _GlassDivider(),
                      _GlassSwitchRow(
                        title: 'Improve recommendations',
                        value: improveRecommendations,
                        onChanged: (value) {
                          setState(() => improveRecommendations = value);
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                const _SettingsGlassSectionTitle(title: 'LOCATION'),
                GlassContainer(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Column(
                    children: [
                      _GlassActionRow(
                        title: 'Primary Location',
                        value: location,
                        onTap: _changeLocation,
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'Manage Saved Locations',
                        value: '3 Saved',
                        onTap: _manageLocations,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                const _SettingsGlassSectionTitle(title: 'NOTIFICATIONS'),
                GlassContainer(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Column(
                    children: [
                      _GlassActionRow(
                        title: 'Weather Alerts',
                        value: weatherAlerts,
                        onTap: _weatherAlertSettings,
                      ),
                      const _GlassDivider(),
                      _GlassSwitchRow(
                        title: 'Daily Briefing',
                        value: dailyBriefing,
                        onChanged: (value) {
                          setState(() => dailyBriefing = value);
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                const _SettingsGlassSectionTitle(title: 'UNITS & LANGUAGE'),
                GlassContainer(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Column(
                    children: [
                      _GlassActionRow(
                        title: 'Temperature Unit',
                        value: temperatureUnit,
                        onTap: _changeTemperatureUnit,
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'Wind Speed',
                        value: windSpeed,
                        onTap: _changeWindSpeed,
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'App Language',
                        value: language,
                        onTap: _changeLanguage,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                const _SettingsGlassSectionTitle(title: 'ABOUT'),
                GlassContainer(
                  padding: const EdgeInsets.symmetric(vertical: 5),
                  child: Column(
                    children: [
                      const _GlassInfoRow(
                        title: 'App Version',
                        value: 'SIH 2026 Prototype',
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'Terms of Service',
                        onTap: () => _showInfo(
                          'Terms of Service',
                          'Terms and conditions for the Mausam personalized weather experience.',
                        ),
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'Privacy Policy',
                        onTap: () => _showInfo(
                          'Privacy Policy',
                          'Your preferences are used to improve your personalized Mausam experience.',
                        ),
                      ),
                      const _GlassDivider(),
                      _GlassActionRow(
                        title: 'IMD Attribution',
                        onTap: () => _showInfo(
                          'IMD Attribution',
                          'Weather information is presented using data associated with the India Meteorological Department.',
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 28),

                SizedBox(
                  height: 50,
                  child: OutlinedButton(
                    onPressed: _signOut,
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(
                        color: Colors.white.withValues(alpha: 0.22),
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                      ),
                      backgroundColor: Colors.white.withValues(alpha: 0.06),
                    ),
                    child: const Text(
                      'Sign Out',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  void _changePersona() {
    _showChoiceSheet(
      title: 'Change persona',
      options: const ['Fitness', 'Farmer', 'Traveler'],
      selected: persona,
      onSelected: (value) => setState(() => persona = value),
    );
  }

  void _editInterests() {
    _showChoiceSheet(
      title: 'Edit interests',
      options: const [
        'Outdoor Run, Air Quality',
        'Outdoor Activities',
        'Air Quality',
        'Fitness & Health',
        'Travel',
      ],
      selected: interests,
      onSelected: (value) => setState(() => interests = value),
    );
  }

  void _changeLocation() {
    _showChoiceSheet(
      title: 'Primary Location',
      options: const ['Ghaziabad, UP', 'Delhi', 'Noida', 'Lucknow'],
      selected: location,
      onSelected: (value) => setState(() => location = value),
    );
  }

  void _manageLocations() {
    _showChoiceSheet(
      title: 'Saved Locations',
      options: const ['Ghaziabad, UP', 'Delhi', 'Noida'],
      selected: location,
      onSelected: (value) => setState(() => location = value),
    );
  }

  void _weatherAlertSettings() {
    _showChoiceSheet(
      title: 'Weather Alerts',
      options: const ['Severe Only', 'All Alerts', 'None'],
      selected: weatherAlerts,
      onSelected: (value) => setState(() => weatherAlerts = value),
    );
  }

  void _changeTemperatureUnit() {
    _showChoiceSheet(
      title: 'Temperature Unit',
      options: const ['Celsius (°C)', 'Fahrenheit (°F)'],
      selected: temperatureUnit,
      onSelected: (value) => setState(() => temperatureUnit = value),
    );
  }

  void _changeWindSpeed() {
    _showChoiceSheet(
      title: 'Wind Speed',
      options: const ['km/h', 'm/s', 'mph'],
      selected: windSpeed,
      onSelected: (value) => setState(() => windSpeed = value),
    );
  }

  void _changeLanguage() {
    _showChoiceSheet(
      title: 'App Language',
      options: const ['English', 'Hindi'],
      selected: language,
      onSelected: (value) => setState(() => language = value),
    );
  }

  void _showChoiceSheet({
    required String title,
    required List<String> options,
    required String selected,
    required ValueChanged<String> onSelected,
  }) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: const Color(0xFF263B52),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 12),
                ...options.map(
                  (option) => ListTile(
                    title: Text(
                      option,
                      style: const TextStyle(color: Colors.white),
                    ),
                    trailing: option == selected
                        ? const Icon(Icons.check_circle, color: Colors.white)
                        : const Icon(
                            Icons.chevron_right,
                            color: Colors.white54,
                          ),
                    onTap: () {
                      onSelected(option);
                      Navigator.pop(context);
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showInfo(String title, String message) {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF263B52),
        title: Text(title, style: const TextStyle(color: Colors.white)),
        content: Text(message, style: const TextStyle(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  void _signOut() {
    _showInfo(
      'Sign Out',
      'Authentication will be connected during the onboarding and login flow.',
    );
  }
}

class _SettingsGlassSectionTitle extends StatelessWidget {
  final String title;

  const _SettingsGlassSectionTitle({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 9),
      child: Text(
        title,
        style: const TextStyle(
          color: Colors.white70,
          fontSize: 11,
          fontWeight: FontWeight.w600,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

class _GlassDivider extends StatelessWidget {
  const _GlassDivider();

  @override
  Widget build(BuildContext context) {
    return Divider(
      height: 1,
      indent: 52,
      color: Colors.white.withValues(alpha: 0.08),
    );
  }
}

class _GlassActionRow extends StatelessWidget {
  final String title;
  final String? value;
  final VoidCallback onTap;

  const _GlassActionRow({required this.title, this.value, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: SizedBox(
        height: 54,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                ),
              ),
              if (value != null)
                Flexible(
                  child: Text(
                    value!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.right,
                    style: const TextStyle(color: Colors.white60, fontSize: 12),
                  ),
                ),
              const SizedBox(width: 7),
              const Icon(
                Icons.chevron_right_rounded,
                color: Colors.white54,
                size: 19,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _GlassSwitchRow extends StatelessWidget {
  final String title;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _GlassSwitchRow({
    required this.title,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 54,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
            Switch(
              value: value,
              onChanged: onChanged,
              activeThumbColor: Colors.white,
              activeTrackColor: Colors.white24,
              inactiveThumbColor: Colors.white54,
              inactiveTrackColor: Colors.white12,
            ),
          ],
        ),
      ),
    );
  }
}

class _GlassInfoRow extends StatelessWidget {
  final String title;
  final String value;

  const _GlassInfoRow({required this.title, required this.value});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 54,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Row(
          children: [
            Expanded(
              child: Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
            Text(
              value,
              style: const TextStyle(color: Colors.white60, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class MapComingSoonPage extends StatelessWidget {
  const MapComingSoonPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      body: Stack(
        fit: StackFit.expand,
        children: [
          const _OnboardingBackground(),
          SafeArea(
            child: Center(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(28, 24, 28, 40),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 118,
                      height: 118,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.075),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.12),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.18),
                            blurRadius: 30,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: Icon(
                        Icons.map_rounded,
                        size: 58,
                        color: Colors.white.withValues(alpha: 0.86),
                      ),
                    ),

                    const SizedBox(height: 30),

                    const Text(
                      'Weather Map',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 30,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 12),

                    Text(
                      'Explore weather conditions across India, '
                      'all in one place.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.66),
                        fontSize: 15,
                        height: 1.5,
                      ),
                    ),

                    const SizedBox(height: 24),

                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 18,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.12),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.auto_awesome_rounded,
                            size: 17,
                            color: Colors.white.withValues(alpha: 0.82),
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Coming soon',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 28),

                    Text(
                      'Interactive weather maps and live weather layers '
                      'will be available here.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.48),
                        fontSize: 13,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SimplePage extends StatelessWidget {
  final String title;
  final IconData icon;
  final String message;

  const _SimplePage({
    required this.title,
    required this.icon,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF101C2C), Color(0xFF30465A), Color(0xFF687D8D)],
        ),
      ),
      child: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, color: Colors.white, size: 52),
                const SizedBox(height: 24),
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 30,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.70),
                    fontSize: 15,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SideMenu extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onSelect;
  final VoidCallback onSettings;

  const _SideMenu({
    required this.currentIndex,
    required this.onSelect,
    required this.onSettings,
  });

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final drawerWidth = size.width * 0.80;

    return Material(
      color: Colors.transparent,
      child: SafeArea(
        right: false,
        child: Align(
          alignment: Alignment.centerLeft,
          child: Container(
            width: drawerWidth,
            height: double.infinity,
            decoration: BoxDecoration(
              color: const Color(0xFF101C2C).withValues(alpha: 0.97),
              borderRadius: const BorderRadius.only(
                topRight: Radius.circular(32),
                bottomRight: Radius.circular(32),
              ),
              border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.28),
                  blurRadius: 30,
                  offset: const Offset(12, 0),
                ),
              ],
            ),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(22, 22, 18, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    children: [
                      Container(
                        width: 46,
                        height: 46,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.10),
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.12),
                          ),
                        ),
                        child: const Icon(
                          Icons.cloud_rounded,
                          color: Colors.white,
                          size: 25,
                        ),
                      ),
                      const SizedBox(width: 13),
                      const Expanded(
                        child: Text(
                          'MAUSAM',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 21,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.3,
                          ),
                        ),
                      ),
                      GestureDetector(
                        onTap: () => Navigator.pop(context),
                        behavior: HitTestBehavior.opaque,
                        child: Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.07),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.close_rounded,
                            color: Colors.white.withValues(alpha: 0.78),
                            size: 22,
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 10),

                  Text(
                    'Your weather, your way.',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.55),
                      fontSize: 13,
                    ),
                  ),

                  const SizedBox(height: 28),

                  Text(
                    'NAVIGATION',
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.38),
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.3,
                    ),
                  ),

                  const SizedBox(height: 10),

                  _SideMenuItem(
                    icon: Icons.home_rounded,
                    title: 'Home',
                    selected: currentIndex == 0,
                    onTap: () => onSelect(0),
                  ),

                  _SideMenuItem(
                    icon: Icons.calendar_today_rounded,
                    title: 'My Day',
                    selected: currentIndex == 1,
                    onTap: () => onSelect(1),
                  ),

                  _SideMenuItem(
                    icon: Icons.map_outlined,
                    title: 'Map',
                    selected: currentIndex == 2,
                    onTap: () => onSelect(2),
                  ),

                  _SideMenuItem(
                    icon: Icons.person_outline_rounded,
                    title: 'Profile',
                    selected: currentIndex == 3,
                    onTap: () => onSelect(3),
                  ),

                  const Spacer(),

                  // Persona card
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(15),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.065),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.09),
                      ),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.09),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.auto_awesome_rounded,
                            color: Colors.white,
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 11),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Personalized for you',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              SizedBox(height: 3),
                              Text(
                                'Weather insights adapt to your profile',
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  color: Colors.white54,
                                  fontSize: 11,
                                  height: 1.3,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 12),

                  _SideMenuItem(
                    icon: Icons.settings_outlined,
                    title: 'Settings',
                    selected: false,
                    onTap: onSettings,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SideMenuItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final bool selected;
  final VoidCallback onTap;

  const _SideMenuItem({
    required this.icon,
    required this.title,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeOut,
            padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 13),
            decoration: BoxDecoration(
              color: selected
                  ? Colors.white.withValues(alpha: 0.105)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(16),
              border: selected
                  ? Border.all(color: Colors.white.withValues(alpha: 0.08))
                  : null,
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  color: selected
                      ? Colors.white
                      : Colors.white.withValues(alpha: 0.68),
                  size: 22,
                ),
                const SizedBox(width: 15),
                Text(
                  title,
                  style: TextStyle(
                    color: selected
                        ? Colors.white
                        : Colors.white.withValues(alpha: 0.78),
                    fontSize: 15,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                  ),
                ),
                const Spacer(),
                if (selected)
                  Container(
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  final bool showBottomNav;
  final VoidCallback? onMenuTap;
  final String persona;

  const HomeScreen({
    super.key,
    this.showBottomNav = true,
    this.onMenuTap,
    this.persona = 'Fitness Enthusiast',
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _selectedLocation = 'Ghaziabad, UP';

  void _openNotifications(WeatherData weather) {
    Navigator.of(context)
        .push(_darkRoute(page: NotificationsScreen(weather: weather)));
  }

  Future<void> _changeLocation() async {
    final result = await Navigator.of(context).push<String>(
      PageRouteBuilder<String>(
        opaque: true,
        barrierColor: const Color(0xFF101C2C),
        transitionDuration: const Duration(milliseconds: 450),
        reverseTransitionDuration: const Duration(milliseconds: 350),
        pageBuilder: (context, animation, secondaryAnimation) {
          return LocationSearchScreen(currentLocation: _selectedLocation);
        },
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          final curvedAnimation = CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutCubic,
          );

          return FadeTransition(
            opacity: curvedAnimation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0, 0.025),
                end: Offset.zero,
              ).animate(curvedAnimation),
              child: child,
            ),
          );
        },
      ),
    );

    if (result != null && result.isNotEmpty && mounted) {
      setState(() {
        _selectedLocation = result;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final WeatherData baseWeather = MockWeatherService.getWeather();

    final WeatherData weather = WeatherData(
      city: _selectedLocation,
      timestamp: baseWeather.timestamp,
      temperature: baseWeather.temperature,
      humidity: baseWeather.humidity,
      apparentTemperature: baseWeather.apparentTemperature,
      precipitation: baseWeather.precipitation,
      rain: baseWeather.rain,
      weatherCode: baseWeather.weatherCode,
      windSpeed: baseWeather.windSpeed,
      soilMoisture: baseWeather.soilMoisture,
      usAqi: baseWeather.usAqi,
      europeanAqi: baseWeather.europeanAqi,
      uvIndex: baseWeather.uvIndex,
      pm25: baseWeather.pm25,
      pm10: baseWeather.pm10,
      nitrogenDioxide: baseWeather.nitrogenDioxide,
      sulphurDioxide: baseWeather.sulphurDioxide,
      carbonMonoxide: baseWeather.carbonMonoxide,
      ozone: baseWeather.ozone,
      isDaylight: baseWeather.isDaylight,
    );

    final personalizedCards = MockWeatherService.getPersonalizedCards(
      widget.persona,
    );

    final mappedCards = personalizedCards
        .map((card) => CardMapper.map(card, weather))
        .whereType<CardDisplayData>()
        .toList();

    final priorityCards = mappedCards.take(4).toList();
    final secondaryCards = mappedCards.skip(4).take(4).toList();

    return Scaffold(
      body: Stack(
        children: [
          WeatherBackground(weather: weather),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(18, 12, 18, 120),
              child: Column(
                children: [
                  TopBar(
                    onMenuTap: widget.onMenuTap,
                    location: _selectedLocation,
                    onLocationTap: _changeLocation,
                    onNotificationsTap: () => _openNotifications(weather),
                    showNotificationDot: buildWeatherAlerts(weather).isNotEmpty,
                  ),
                  const SizedBox(height: 24),

                  MainWeather(weather: weather),

                  const SizedBox(height: 28),

                  SectionTitle(title: 'PERSONALIZED FOR YOU'),

                  const SizedBox(height: 12),

                  ...priorityCards.map(
                    (card) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: PriorityCard(
                        icon: card.icon,
                        title: card.title,
                        value: card.value,
                        status: card.status,
                        insight: card.insight,
                        indicatorColor: card.indicatorColor,
                        onTap: () {
                          Navigator.of(context).push(
                            _weatherDetailRoute(
                              card: card,
                              persona: widget.persona,
                              weather: weather,
                            ),
                          );
                        },
                      ),
                    ),
                  ),

                  const SizedBox(height: 8),

                  Row(
                    children: [
                      if (secondaryCards.isNotEmpty)
                        Expanded(
                          child: SmallMetricCard(
                            icon: secondaryCards[0].icon,
                            title: secondaryCards[0].title,
                            value: secondaryCards[0].value,
                            indicatorColor: secondaryCards[0].indicatorColor,
                            onTap: () {
                              Navigator.of(context).push(
                                _weatherDetailRoute(
                                  card: secondaryCards[0],
                                  persona: widget.persona,
                                  weather: weather,
                                ),
                              );
                            },
                          ),
                        ),
                      if (secondaryCards.length > 1) ...[
                        const SizedBox(width: 12),
                        Expanded(
                          child: SmallMetricCard(
                            icon: secondaryCards[1].icon,
                            title: secondaryCards[1].title,
                            value: secondaryCards[1].value,
                            indicatorColor: secondaryCards[1].indicatorColor,
                            onTap: () {
                              Navigator.of(context).push(
                                _weatherDetailRoute(
                                  card: secondaryCards[1],
                                  persona: widget.persona,
                                  weather: weather,
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ],
                  ),

                  const SizedBox(height: 12),

                  Row(
                    children: [
                      if (secondaryCards.length > 2)
                        Expanded(
                          child: SmallMetricCard(
                            icon: secondaryCards[2].icon,
                            title: secondaryCards[2].title,
                            value: secondaryCards[2].value,
                            indicatorColor: secondaryCards[2].indicatorColor,
                            onTap: () {
                              Navigator.of(context).push(
                                _weatherDetailRoute(
                                  card: secondaryCards[2],
                                  persona: widget.persona,
                                  weather: weather,
                                ),
                              );
                            },
                          ),
                        ),
                      if (secondaryCards.length > 3) ...[
                        const SizedBox(width: 12),
                        Expanded(
                          child: SmallMetricCard(
                            icon: secondaryCards[3].icon,
                            title: secondaryCards[3].title,
                            value: secondaryCards[3].value,
                            indicatorColor: secondaryCards[3].indicatorColor,
                            onTap: () {
                              Navigator.of(context).push(
                                _weatherDetailRoute(
                                  card: secondaryCards[3],
                                  persona: widget.persona,
                                  weather: weather,
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),

          if (widget.showBottomNav)
            const Positioned(
              left: 18,
              right: 18,
              bottom: 18,
              child: FloatingNavBar(),
            ),
        ],
      ),
    );
  }
}

class FloatingNavBar extends StatelessWidget {
  const FloatingNavBar({super.key});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: Container(
          height: 70,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.40),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white.withValues(alpha: 0.22)),
          ),
          child: Row(
            children: [
              _NavItem(icon: Icons.home_rounded, label: 'Home', active: true),
              _NavItem(icon: Icons.calendar_today_rounded, label: 'My Day'),
              _NavItem(icon: Icons.notifications_none_rounded, label: 'Alerts'),
              _NavItem(icon: Icons.person_outline_rounded, label: 'Profile'),
            ],
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;

  const _NavItem({
    required this.icon,
    required this.label,
    this.active = false,
  });

  @override
  Widget build(BuildContext context) {
    final iconColor = active
        ? Colors.white
        : Colors.white.withValues(alpha: 0.55);

    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: iconColor, size: 23),
          const SizedBox(height: 3),
          Text(
            label,
            style: TextStyle(
              color: iconColor,
              fontSize: 10,
              fontWeight: active ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
          const SizedBox(height: 3),
          if (active)
            Container(
              width: 5,
              height: 5,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
            ),
        ],
      ),
    );
  }
}

class WeatherBackground extends StatelessWidget {
  final WeatherData weather;

  const WeatherBackground({super.key, required this.weather});

  List<Color> _gradientColors() {
    if (!weather.isDaylight) {
      return const [Color(0xFF101C2C), Color(0xFF1E3045), Color(0xFF34495C)];
    }

    final code = weather.weatherCode;

    if (code == 95 || code == 96 || code == 99) {
      return const [Color(0xFF182535), Color(0xFF2D4052), Color(0xFF526678)];
    }

    if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
      return const [Color(0xFF263B50), Color(0xFF3B5368), Color(0xFF596F80)];
    }

    if (code == 45 || code == 48) {
      return const [Color(0xFF455665), Color(0xFF60717F), Color(0xFF7D8B94)];
    }

    if (code == 3) {
      return const [Color(0xFF30465A), Color(0xFF4A6275), Color(0xFF687D8D)];
    }

    return const [Color(0xFF263B52), Color(0xFF3D5870), Color(0xFF667D90)];
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 700),
      curve: Curves.easeInOut,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: _gradientColors(),
        ),
      ),
      child: Stack(
        children: [
          WeatherEffects(
            weatherCode: weather.weatherCode,
            isDaylight: weather.isDaylight,
          ),
        ],
      ),
    );
  }
}

class LocationSearchScreen extends StatefulWidget {
  final String currentLocation;

  const LocationSearchScreen({super.key, required this.currentLocation});

  @override
  State<LocationSearchScreen> createState() => _LocationSearchScreenState();
}

class _LocationSearchScreenState extends State<LocationSearchScreen> {
  final TextEditingController _searchController = TextEditingController();

  final List<String> _cities = const [
    'Ghaziabad, UP',
    'Delhi, Delhi',
    'Noida, UP',
    'Lucknow, UP',
    'Kanpur, UP',
    'Agra, UP',
    'Jaipur, Rajasthan',
    'Mumbai, Maharashtra',
    'Pune, Maharashtra',
    'Bengaluru, Karnataka',
    'Hyderabad, Telangana',
    'Chennai, Tamil Nadu',
    'Kolkata, West Bengal',
    'Ahmedabad, Gujarat',
    'Chandigarh, Chandigarh',
  ];

  String _query = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<String> get _filteredCities {
    if (_query.trim().isEmpty) {
      return _cities;
    }

    final query = _query.toLowerCase().trim();

    return _cities.where((city) => city.toLowerCase().contains(query)).toList();
  }

  void _selectLocation(String city) {
    Navigator.of(context).pop(city);
  }

  void _useCurrentLocation() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text('Current location access will be connected next.'),
        behavior: SnackBarBehavior.floating,
        backgroundColor: const Color(0xFF263B52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      body: Stack(
        children: [
          const _OnboardingBackground(),

          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 12, 18, 0),
                  child: Row(
                    children: [
                      GlassButton(
                        icon: Icons.arrow_back_rounded,
                        onTap: () => Navigator.of(context).pop(),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Text(
                          'Change Location',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 23,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.075),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.12),
                      ),
                    ),
                    child: TextField(
                      controller: _searchController,
                      onChanged: (value) {
                        setState(() {
                          _query = value;
                        });
                      },
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                      cursorColor: Colors.white,
                      decoration: InputDecoration(
                        hintText: 'Search city',
                        hintStyle: TextStyle(
                          color: Colors.white.withValues(alpha: 0.45),
                        ),
                        prefixIcon: Icon(
                          Icons.search_rounded,
                          color: Colors.white.withValues(alpha: 0.65),
                        ),
                        suffixIcon: _query.isNotEmpty
                            ? IconButton(
                                icon: Icon(
                                  Icons.close_rounded,
                                  color: Colors.white.withValues(alpha: 0.55),
                                ),
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() {
                                    _query = '';
                                  });
                                },
                              )
                            : null,
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 17,
                        ),
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 14),

                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  child: GestureDetector(
                    onTap: _useCurrentLocation,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 17,
                        vertical: 15,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.055),
                        borderRadius: BorderRadius.circular(17),
                        border: Border.all(
                          color: Colors.white.withValues(alpha: 0.09),
                        ),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.08),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.my_location_rounded,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 13),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Use Current Location',
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 15,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  'Use your device location',
                                  style: TextStyle(
                                    color: Colors.white54,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(
                            Icons.chevron_right_rounded,
                            color: Colors.white54,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 22),

                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(18, 0, 18, 30),
                    itemCount: _filteredCities.length,
                    itemBuilder: (context, index) {
                      final city = _filteredCities[index];
                      final selected = city == widget.currentLocation;

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 9),
                        child: GestureDetector(
                          onTap: () => _selectLocation(city),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 17,
                              vertical: 16,
                            ),
                            decoration: BoxDecoration(
                              color: selected
                                  ? Colors.white.withValues(alpha: 0.10)
                                  : Colors.white.withValues(alpha: 0.045),
                              borderRadius: BorderRadius.circular(17),
                              border: Border.all(
                                color: selected
                                    ? Colors.white.withValues(alpha: 0.20)
                                    : Colors.white.withValues(alpha: 0.07),
                              ),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  Icons.location_on_outlined,
                                  color: Colors.white.withValues(alpha: 0.72),
                                  size: 21,
                                ),
                                const SizedBox(width: 13),
                                Expanded(
                                  child: Text(
                                    city,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 15,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                                if (selected)
                                  const Icon(
                                    Icons.check_circle_rounded,
                                    color: Colors.white,
                                    size: 21,
                                  ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class WeatherAlert {
  final String title;
  final String message;
  final String severity;
  final IconData icon;
  final String location;
  final String status;

  const WeatherAlert({
    required this.title,
    required this.message,
    required this.severity,
    required this.icon,
    required this.location,
    this.status = 'Active now',
  });

  bool get isCritical => severity == 'Critical';
  bool get isWarning => severity == 'Warning';
}

List<WeatherAlert> buildWeatherAlerts(WeatherData weather) {
  final alerts = <WeatherAlert>[];

  if (weather.weatherCode >= 95) {
    alerts.add(
      WeatherAlert(
        title: 'Thunderstorm alert',
        message: 'Thunderstorms are active. Avoid exposed areas and consider staying indoors.',
        severity: 'Critical',
        icon: Icons.thunderstorm_rounded,
        location: weather.city,
      ),
    );
  }

  if (weather.usAqi >= 150) {
    alerts.add(
      WeatherAlert(
        title: 'Air quality alert',
        message: 'Air quality is elevated. Consider reducing prolonged outdoor exertion.',
        severity: 'Warning',
        icon: Icons.air_rounded,
        location: weather.city,
      ),
    );
  }

  if (weather.uvIndex >= 8) {
    alerts.add(
      WeatherAlert(
        title: 'Very high UV index',
        message: 'UV exposure is high. Limit prolonged midday exposure and use sun protection.',
        severity: 'Warning',
        icon: Icons.wb_sunny_rounded,
        location: weather.city,
      ),
    );
  }

  if (weather.humidity >= 85) {
    alerts.add(
      WeatherAlert(
        title: 'High humidity',
        message: 'Humidity is very high. Stay hydrated and allow extra ventilation during activity.',
        severity: 'Warning',
        icon: Icons.water_drop_rounded,
        location: weather.city,
      ),
    );
  }

  if (weather.rain > 5 || weather.precipitation > 5) {
    alerts.add(
      WeatherAlert(
        title: 'Heavy rain conditions',
        message: 'Rainfall is elevated. Plan outdoor travel carefully and watch for slippery conditions.',
        severity: 'Warning',
        icon: Icons.umbrella_rounded,
        location: weather.city,
      ),
    );
  }

  if (weather.windSpeed >= 25) {
    alerts.add(
      WeatherAlert(
        title: 'Strong wind alert',
        message: 'Strong winds are present. Take care around exposed areas and unsecured objects.',
        severity: 'Warning',
        icon: Icons.air_rounded,
        location: weather.city,
      ),
    );
  }

  return alerts;
}

class NotificationsScreen extends StatelessWidget {
  final WeatherData weather;

  const NotificationsScreen({super.key, required this.weather});

  @override
  Widget build(BuildContext context) {
    final alerts = buildWeatherAlerts(weather);

    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF101C2C), Color(0xFF263B52), Color(0xFF4A6275)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: Row(
                  children: [
                    GlassButton(
                      icon: Icons.arrow_back_rounded,
                      onTap: () => Navigator.of(context).pop(),
                    ),
                    const Expanded(
                      child: Text(
                        'Notifications',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    const SizedBox(width: 48),
                  ],
                ),
              ),

              Expanded(
                child: alerts.isEmpty
                    ? _NotificationsEmptyState(location: weather.city)
                    : ListView(
                        physics: const BouncingScrollPhysics(),
                        padding: const EdgeInsets.fromLTRB(16, 20, 16, 28),
                        children: [
                          Text(
                            'Weather alerts',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 26,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Important conditions for ${weather.city}',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.62),
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 20),
                          ...alerts.map(
                            (alert) => Padding(
                              padding: const EdgeInsets.only(bottom: 14),
                              child: _NotificationAlertCard(alert: alert),
                            ),
                          ),
                        ],
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationAlertCard extends StatelessWidget {
  final WeatherAlert alert;

  const _NotificationAlertCard({required this.alert});

  Color _severityColor() {
    if (alert.isCritical) {
      return const Color(0xFFFF6B6B);
    }

    return const Color(0xFFFFC857);
  }

  @override
  Widget build(BuildContext context) {
    final severityColor = _severityColor();

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.085),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withValues(alpha: 0.11)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: severityColor.withValues(alpha: 0.14),
                  shape: BoxShape.circle,
                ),
                child: Icon(alert.icon, color: severityColor, size: 25),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      alert.title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      alert.status,
                      style: TextStyle(
                        color: severityColor,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
                decoration: BoxDecoration(
                  color: severityColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  alert.severity,
                  style: TextStyle(
                    color: severityColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 15),
          Text(
            alert.message,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.76),
              fontSize: 14,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 13),
          Row(
            children: [
              Icon(
                Icons.location_on_outlined,
                size: 15,
                color: Colors.white.withValues(alpha: 0.48),
              ),
              const SizedBox(width: 5),
              Expanded(
                child: Text(
                  alert.location,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.52),
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _NotificationsEmptyState extends StatelessWidget {
  final String location;

  const _NotificationsEmptyState({required this.location});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 82,
              height: 82,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.08),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.notifications_none_rounded,
                size: 42,
                color: Colors.white.withValues(alpha: 0.72),
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'You’re all clear',
              style: TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'No active weather alerts for $location right now.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.62),
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class TopBar extends StatelessWidget {
  final VoidCallback? onMenuTap;
  final String location;
  final VoidCallback? onLocationTap;
  final VoidCallback? onNotificationsTap;
  final bool showNotificationDot;

  const TopBar({
    super.key,
    this.onMenuTap,
    this.location = 'Ghaziabad, UP',
    this.onLocationTap,
    this.onNotificationsTap,
    this.showNotificationDot = true,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 58,
      child: Row(
        children: [
          SizedBox(
            width: 52,
            height: 52,
            child: GlassButton(icon: Icons.menu, onTap: onMenuTap ?? () {}),
          ),

          const SizedBox(width: 8),

          Expanded(
            child: GestureDetector(
              onTap: onLocationTap,
              behavior: HitTestBehavior.opaque,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.location_on_outlined,
                          size: 18,
                          color: Colors.white,
                        ),
                        const SizedBox(width: 4),
                        Flexible(
                          child: Text(
                            location,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        const SizedBox(width: 3),
                        Icon(
                          Icons.keyboard_arrow_down_rounded,
                          size: 18,
                          color: Colors.white.withValues(alpha: 0.65),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(width: 8),

          SizedBox(
            width: 52,
            height: 52,
            child: GlassButton(
              icon: Icons.notifications_none_rounded,
              onTap: onNotificationsTap ?? () {},
              showNotificationDot: showNotificationDot,
            ),
          ),
        ],
      ),
    );
  }
}

class MainWeather extends StatelessWidget {
  final WeatherData weather;

  const MainWeather({super.key, required this.weather});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          '${weather.temperature.round()}°',
          style: TextStyle(
            color: Colors.white,
            fontSize: 92,
            height: 0.95,
            fontWeight: FontWeight.w300,
            letterSpacing: -4,
          ),
        ),

        const SizedBox(height: 8),

        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.wb_sunny_outlined, color: Colors.white, size: 27),
            const SizedBox(width: 8),
            Text(
              weatherCodeToCondition(weather.weatherCode),
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),

        const SizedBox(height: 12),

        ClipRRect(
          borderRadius: BorderRadius.circular(30),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: Colors.white.withValues(alpha: 0.35)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.thermostat_outlined,
                    color: Colors.white,
                    size: 19,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    'Feels like ${weather.apparentTemperature.round()}°',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class SectionTitle extends StatelessWidget {
  final String title;

  const SectionTitle({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: TextStyle(
          color: Colors.white.withValues(alpha: 0.90),
          fontSize: 13,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

class SmallMetricCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final Color indicatorColor;
  final VoidCallback? onTap;

  const SmallMetricCard({
    super.key,
    required this.icon,
    required this.title,
    required this.value,
    required this.indicatorColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: GlassContainer(
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: Colors.white, size: 22),
                const Spacer(),
                Container(
                  width: 9,
                  height: 9,
                  decoration: BoxDecoration(
                    color: indicatorColor,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: indicatorColor.withValues(alpha: 0.50),
                        blurRadius: 7,
                        spreadRadius: 0.5,
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 13),

            Text(
              title,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.70),
                fontSize: 12,
              ),
            ),

            const SizedBox(height: 3),

            Row(
              children: [
                Expanded(
                  child: Text(
                    value,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 17,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Icon(
                  Icons.chevron_right_rounded,
                  color: Colors.white.withValues(alpha: 0.35),
                  size: 20,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class GlassButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final bool showNotificationDot;

  const GlassButton({
    super.key,
    required this.icon,
    required this.onTap,
    this.showNotificationDot = false,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          ClipOval(
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
              child: Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.24),
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.35),
                  ),
                ),
                child: Icon(icon, color: Colors.white, size: 27),
              ),
            ),
          ),

          if (showNotificationDot)
            Positioned(
              top: 2,
              right: 2,
              child: Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(
                  color: Color(0xFFE53935),
                  shape: BoxShape.circle,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class GlassContainer extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;

  const GlassContainer({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Container(
          width: double.infinity,
          padding: padding,
          decoration: BoxDecoration(
            color: Colors.black.withValues(alpha: 0.16),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.28),
              width: 1,
            ),
          ),
          child: child,
        ),
      ),
    );
  }
}
