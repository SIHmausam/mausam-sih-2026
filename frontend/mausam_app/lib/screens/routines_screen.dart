import 'dart:ui';

import 'package:flutter/material.dart';

import '../models/routine.dart';
import 'routine_form_screen.dart';
import '../services/routine_api_service.dart';

class RoutinesScreen extends StatefulWidget {
  final VoidCallback? onMenuTap;

  const RoutinesScreen({super.key, this.onMenuTap});

  @override
  State<RoutinesScreen> createState() => _RoutinesScreenState();
}

class _RoutinesScreenState extends State<RoutinesScreen> {
  final RoutineApiService _routineApiService = RoutineApiService();

  List<Routine> _routines = const [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadRoutines();
  }

  Future<void> _loadRoutines() async {
    if (mounted) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });
    }

    try {
      final routines = await _routineApiService.getRoutines();

      if (!mounted) return;

      setState(() {
        _routines = routines;
        _isLoading = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isLoading = false;
        _errorMessage = _cleanError(error);
      });
    }
  }

  Future<void> _deleteRoutine(Routine routine) async {
    final shouldDelete = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF17283A),
          title: const Text(
            'Delete routine?',
            style: TextStyle(color: Colors.white),
          ),
          content: Text(
            'Remove "${routine.name}" from your routines?',
            style: TextStyle(color: Colors.white.withValues(alpha: 0.72)),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );

    if (shouldDelete != true) return;

    try {
      await _routineApiService.deleteRoutine(routineId: routine.id);

      if (!mounted) return;

      setState(() {
        _routines = _routines.where((item) => item.id != routine.id).toList();
      });

      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Routine deleted')));
    } catch (error) {
      if (!mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(_cleanError(error))));
    }
  }

  Future<void> _toggleRoutine(Routine routine) async {
    try {
      final updated = await _routineApiService.updateRoutine(
        routineId: routine.id,
        isEnabled: !routine.isEnabled,
      );

      if (!mounted) return;

      setState(() {
        _routines = _routines
            .map((item) => item.id == updated.id ? updated : item)
            .toList();
      });
    } catch (error) {
      if (!mounted) return;

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(_cleanError(error))));
    }
  }

  String _cleanError(Object error) {
    final message = error.toString();

    if (message.startsWith('Exception: ')) {
      return message.substring(11);
    }

    return message;
  }

  String _formatTime(String value) {
    final parts = value.split(':');

    if (parts.length < 2) return value;

    final hour = int.tryParse(parts[0]);
    final minute = int.tryParse(parts[1]);

    if (hour == null || minute == null) {
      return value;
    }

    final isPm = hour >= 12;
    final displayHour = hour % 12 == 0 ? 12 : hour % 12;

    return '$displayHour:${minute.toString().padLeft(2, '0')} '
        '${isPm ? 'PM' : 'AM'}';
  }

  String _formatActivity(String value) {
    switch (value) {
      case 'outdoor_health':
        return 'Outdoor Health';
      case 'farming':
        return 'Farming';
      case 'irrigation':
        return 'Irrigation';
      case 'travel':
        return 'Travel';
      case 'commute':
        return 'Commute';
      case 'general':
        return 'General';
      default:
        return value;
    }
  }

  String _formatDay(String day) {
    switch (day) {
      case 'monday':
        return 'Mon';
      case 'tuesday':
        return 'Tue';
      case 'wednesday':
        return 'Wed';
      case 'thursday':
        return 'Thu';
      case 'friday':
        return 'Fri';
      case 'saturday':
        return 'Sat';
      case 'sunday':
        return 'Sun';
      default:
        return day;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const _RoutinesBackground(),
        SafeArea(child: _buildContent()),
        Positioned(
          left: 20,
          bottom: 92,
          child: _GlassAddButton(
            onPressed: () async {
              final created = await Navigator.push<bool>(
                context,
                PageRouteBuilder<bool>(
                  pageBuilder: (_, animation, secondaryAnimation) =>
                      const RoutineFormScreen(),
                  transitionsBuilder:
                      (_, animation, secondaryAnimation, child) {
                        return SlideTransition(
                          position: Tween<Offset>(
                            begin: const Offset(1, 0),
                            end: Offset.zero,
                          ).animate(animation),
                          child: child,
                        );
                      },
                ),
              );

              if (created == true && mounted) {
                await _loadRoutines();
              }
            },
          ),
        ),
      ],
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return SingleChildScrollView(
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 150),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _PageHeader(
              onMenuTap: widget.onMenuTap,
              title: 'Routines',
              subtitle: 'Your routines and weather-aware plans',
            ),
            const SizedBox(height: 28),
            const SizedBox(
              height: 220,
              child: Center(child: CircularProgressIndicator()),
            ),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 150),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _PageHeader(
              onMenuTap: widget.onMenuTap,
              title: 'Routines',
              subtitle: 'Your routines and weather-aware plans',
            ),
            const SizedBox(height: 28),
            _GlassMessageCard(
              icon: Icons.cloud_off_rounded,
              title: 'Couldn’t load your routines',
              message: _errorMessage!,
              actionLabel: 'Try Again',
              onAction: _loadRoutines,
            ),
          ],
        ),
      );
    }

    if (_routines.isEmpty) {
      return SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 150),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _PageHeader(
              onMenuTap: widget.onMenuTap,
              title: 'Routines',
              subtitle: 'Your routines and weather-aware plans',
            ),
            const SizedBox(height: 28),
            _GlassMessageCard(
              icon: Icons.event_available_rounded,
              title: 'No routines yet',
              message:
                  'Add your regular activities so Mausam can '
                  'help you plan around the weather.',
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadRoutines,
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 150),
        itemCount: _routines.length + 1,
        separatorBuilder: (_, _) => const SizedBox(height: 14),
        itemBuilder: (context, index) {
          if (index == 0) {
            return _PageHeader(
              onMenuTap: widget.onMenuTap,
              title: 'Routines',
              subtitle: 'Your routines and weather-aware plans',
            );
          }

          final routine = _routines[index - 1];

          return _RoutineCard(
            routine: routine,
            formattedTime: _formatTime(routine.startTime),
            formattedActivity: _formatActivity(routine.activityContext),
            formattedDays: routine.daysOfWeek.map(_formatDay).toList(),
            onToggle: () => _toggleRoutine(routine),
            onDelete: () => _deleteRoutine(routine),
            onEdit: () async {
              final updated = await Navigator.push<bool>(
                context,
                PageRouteBuilder<bool>(
                  pageBuilder: (_, animation, secondaryAnimation) =>
                      RoutineFormScreen(routine: routine),
                  transitionsBuilder:
                      (_, animation, secondaryAnimation, child) {
                        return SlideTransition(
                          position: Tween<Offset>(
                            begin: const Offset(1, 0),
                            end: Offset.zero,
                          ).animate(animation),
                          child: child,
                        );
                      },
                ),
              );

              if (updated == true && mounted) {
                await _loadRoutines();
              }
            },
          );
        },
      ),
    );
  }
}

class _RoutinesBackground extends StatelessWidget {
  const _RoutinesBackground();

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

class _PageHeader extends StatelessWidget {
  final VoidCallback? onMenuTap;
  final String title;
  final String subtitle;

  const _PageHeader({
    required this.onMenuTap,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 58,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          SizedBox(
            width: 52,
            height: 52,
            child: _RoutineMenuButton(onTap: onMenuTap ?? () {}),
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
                    fontSize: 24,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  subtitle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.62),
                    fontSize: 12.5,
                    height: 1.3,
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

class _RoutineMenuButton extends StatelessWidget {
  final VoidCallback onTap;

  const _RoutineMenuButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: ClipOval(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.24),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white.withValues(alpha: 0.35)),
            ),
            child: const Icon(Icons.menu, color: Colors.white, size: 27),
          ),
        ),
      ),
    );
  }
}

class _GlassAddButton extends StatelessWidget {
  final VoidCallback onPressed;

  const _GlassAddButton({required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(22),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
          child: InkWell(
            onTap: onPressed,
            borderRadius: BorderRadius.circular(22),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 17, vertical: 13),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.30),
                borderRadius: BorderRadius.circular(22),
                border: Border.all(color: Colors.white.withValues(alpha: 0.20)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.30),
                    blurRadius: 28,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.add_rounded,
                    size: 20,
                    color: Colors.white.withValues(alpha: 0.90),
                  ),
                  const SizedBox(width: 7),
                  const Text(
                    'Add Routine',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
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

class _GlassMessageCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _GlassMessageCard({
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.075),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: 0.11)),
      ),
      child: Column(
        children: [
          Icon(icon, size: 48, color: Colors.white.withValues(alpha: 0.78)),
          const SizedBox(height: 16),
          Text(
            title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 21,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 9),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.64),
              fontSize: 14,
              height: 1.45,
            ),
          ),
          if (actionLabel != null) ...[
            const SizedBox(height: 18),
            _GlassActionButton(label: actionLabel!, onPressed: onAction!),
          ],
        ],
      ),
    );
  }
}

class _GlassActionButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const _GlassActionButton({required this.label, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
          ),
          child: Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }
}

class _RoutineCard extends StatelessWidget {
  final Routine routine;
  final String formattedTime;
  final String formattedActivity;
  final List<String> formattedDays;
  final VoidCallback onToggle;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const _RoutineCard({
    required this.routine,
    required this.formattedTime,
    required this.formattedActivity,
    required this.formattedDays,
    required this.onToggle,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.075),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.10),
                blurRadius: 18,
                spreadRadius: 1,
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      routine.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 19,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  Switch(
                    value: routine.isEnabled,
                    onChanged: (_) => onToggle(),
                    activeThumbColor: Colors.white,
                    activeTrackColor: Colors.white24,
                    inactiveThumbColor: Colors.white54,
                    inactiveTrackColor: Colors.white12,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(
                    Icons.schedule_rounded,
                    size: 18,
                    color: Colors.white.withValues(alpha: 0.72),
                  ),
                  const SizedBox(width: 7),
                  Text(
                    formattedTime,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.82),
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Icon(
                    Icons.category_outlined,
                    size: 18,
                    color: Colors.white.withValues(alpha: 0.72),
                  ),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      formattedActivity,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.82),
                        fontSize: 15,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 13),
              Wrap(
                spacing: 7,
                runSpacing: 7,
                children: formattedDays
                    .map(
                      (day) => Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.075),
                          borderRadius: BorderRadius.circular(11),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.08),
                          ),
                        ),
                        child: Text(
                          day,
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.72),
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  IconButton(
                    onPressed: onEdit,
                    tooltip: 'Edit',
                    icon: Icon(
                      Icons.edit_outlined,
                      color: Colors.white.withValues(alpha: 0.82),
                    ),
                  ),
                  IconButton(
                    onPressed: onDelete,
                    tooltip: 'Delete',
                    icon: Icon(
                      Icons.delete_outline_rounded,
                      color: Colors.white.withValues(alpha: 0.82),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
