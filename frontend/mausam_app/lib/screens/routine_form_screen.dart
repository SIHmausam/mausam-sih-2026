import 'package:flutter/material.dart';

import '../models/routine.dart';
import '../models/saved_location.dart';
import '../services/location_api_service.dart';
import '../services/location_search_service.dart';
import '../services/routine_api_service.dart';

class RoutineFormScreen extends StatefulWidget {
  final Routine? routine;

  const RoutineFormScreen({super.key, this.routine});

  bool get isEditing => routine != null;

  @override
  State<RoutineFormScreen> createState() => _RoutineFormScreenState();
}

class _RoutineFormScreenState extends State<RoutineFormScreen> {
  final _formKey = GlobalKey<FormState>();

  final RoutineApiService _routineApiService = RoutineApiService();
  final LocationApiService _locationApiService = LocationApiService();

  late final TextEditingController _nameController;

  String _activityContext = 'general';
  final Set<String> _selectedDays = {};
  TimeOfDay _startTime = const TimeOfDay(hour: 8, minute: 0);
  int _durationMinutes = 60;
  bool _isEnabled = true;

  List<SavedLocation> _locations = const [];
  SavedLocation? _selectedLocation;

  bool _isLoadingLocations = true;
  bool _isSaving = false;
  String? _locationError;

  final TextEditingController _locationSearchController =
      TextEditingController();

  List<LocationSearchResult> _searchResults = const [];
  bool _isSearching = false;
  String? _searchError;

  static const List<String> _activities = [
    'general',
    'outdoor_health',
    'farming',
    'irrigation',
    'travel',
    'commute',
  ];

  static const List<String> _days = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
  ];

  @override
  void initState() {
    super.initState();

    final routine = widget.routine;

    _nameController = TextEditingController(text: routine?.name ?? '');

    if (routine != null) {
      _activityContext = routine.activityContext;
      _selectedDays.addAll(routine.daysOfWeek);
      _startTime = _parseTime(routine.startTime);
      _durationMinutes = routine.durationMinutes;
      _isEnabled = routine.isEnabled;
    } else {
      _selectedDays.addAll([
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
      ]);
    }

    _loadLocations();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _locationSearchController.dispose();
    super.dispose();
  }

  Future<void> _loadLocations() async {
    try {
      final locations = await _locationApiService.getLocations();

      if (!mounted) return;

      SavedLocation? selected;

      if (widget.routine?.savedLocationId != null) {
        for (final location in locations) {
          if (location.id == widget.routine!.savedLocationId) {
            selected = location;
            break;
          }
        }
      }

      setState(() {
        _locations = locations;
        _selectedLocation = selected;
        _isLoadingLocations = false;
        _locationError = null;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isLoadingLocations = false;
        _locationError = _cleanError(error);
      });
    }
  }

  Future<void> _searchLocations() async {
    final query = _locationSearchController.text.trim();

    if (query.length < 2) {
      setState(() {
        _searchResults = const [];
        _searchError = 'Enter at least 2 characters.';
      });
      return;
    }

    FocusScope.of(context).unfocus();

    setState(() {
      _isSearching = true;
      _searchError = null;
      _searchResults = const [];
    });

    try {
      final results = await LocationSearchService.search(query);

      if (!mounted) return;

      setState(() {
        _searchResults = results;
        _isSearching = false;

        if (results.isEmpty) {
          _searchError = 'No matching locations found.';
        }
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isSearching = false;
        _searchError = _cleanError(error);
      });
    }
  }

  Future<void> _saveSearchResult(LocationSearchResult result) async {
    final details = await _showLocationDetailsDialog(result);

    if (details == null) return;

    setState(() {
      _isSaving = true;
    });

    try {
      final location = await _locationApiService.createLocation(
        label: details.label,
        city: result.name,
        latitude: result.latitude,
        longitude: result.longitude,
        locationType: details.locationType,
        isPrimary: false,
      );

      if (!mounted) return;

      setState(() {
        _locations = [..._locations, location];
        _selectedLocation = location;
        _searchResults = const [];
        _locationSearchController.clear();
        _isSaving = false;
      });

      _showMessage('Location saved.');
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isSaving = false;
      });

      _showMessage(_cleanError(error));
    }
  }

  Future<_LocationDetails?> _showLocationDetailsDialog(
    LocationSearchResult result,
  ) async {
    final labelController = TextEditingController(text: result.name);
    String locationType = 'destination';

    final details = await showDialog<_LocationDetails>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.62),
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return Dialog(
              backgroundColor: Colors.transparent,
              insetPadding: const EdgeInsets.symmetric(horizontal: 26),
              child: Container(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 14),
                decoration: BoxDecoration(
                  color: const Color(0xFF17273A).withValues(alpha: 0.97),
                  borderRadius: BorderRadius.circular(25),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.14),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.32),
                      blurRadius: 30,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(13),
                            border: Border.all(
                              color: Colors.white.withValues(alpha: 0.10),
                            ),
                          ),
                          child: Icon(
                            Icons.location_on_outlined,
                            color: Colors.white.withValues(alpha: 0.82),
                            size: 21,
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text(
                            'Save Location',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 19,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 18),

                    Text(
                      result.displayName,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.68),
                        fontSize: 13,
                      ),
                    ),

                    const SizedBox(height: 16),

                    TextField(
                      controller: labelController,
                      style: const TextStyle(color: Colors.white),
                      cursorColor: Colors.white,
                      decoration: _inputDecoration(
                        'Location name',
                        Icons.bookmark_outline_rounded,
                      ),
                    ),

                    const SizedBox(height: 16),

                    Text(
                      'Location type',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.72),
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),

                    const SizedBox(height: 9),

                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: ['home', 'farm', 'destination', 'work', 'other']
                          .map((type) {
                            final selected = locationType == type;

                            return GestureDetector(
                              onTap: () {
                                setDialogState(() {
                                  locationType = type;
                                });
                              },
                              child: AnimatedContainer(
                                duration: const Duration(milliseconds: 160),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 9,
                                ),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(
                                    alpha: selected ? 0.12 : 0.045,
                                  ),
                                  borderRadius: BorderRadius.circular(14),
                                  border: Border.all(
                                    color: Colors.white.withValues(
                                      alpha: selected ? 0.72 : 0.10,
                                    ),
                                    width: selected ? 1.2 : 1,
                                  ),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    AnimatedContainer(
                                      duration: const Duration(
                                        milliseconds: 160,
                                      ),
                                      width: 7,
                                      height: 7,
                                      decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        color: selected
                                            ? Colors.white
                                            : Colors.white.withValues(
                                                alpha: 0.35,
                                              ),
                                        boxShadow: selected
                                            ? [
                                                BoxShadow(
                                                  color: Colors.white
                                                      .withValues(alpha: 0.60),
                                                  blurRadius: 6,
                                                  spreadRadius: 1,
                                                ),
                                              ]
                                            : null,
                                      ),
                                    ),
                                    const SizedBox(width: 7),
                                    Text(
                                      _formatLocationType(type),
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 12,
                                        fontWeight: selected
                                            ? FontWeight.w700
                                            : FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          })
                          .toList(),
                    ),

                    const SizedBox(height: 18),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        GestureDetector(
                          onTap: () => Navigator.pop(dialogContext),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 10,
                            ),
                            child: Text(
                              'Cancel',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.62),
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        GestureDetector(
                          onTap: () {
                            final label = labelController.text.trim();

                            if (label.isEmpty) return;

                            Navigator.pop(
                              dialogContext,
                              _LocationDetails(
                                label: label,
                                locationType: locationType,
                              ),
                            );
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 9,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(13),
                              border: Border.all(
                                color: Colors.white.withValues(alpha: 0.18),
                              ),
                            ),
                            child: const Text(
                              'Save',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    labelController.dispose();

    return details;
  }

  Future<void> _pickTime() async {
    int selectedHour = _startTime.hourOfPeriod;
    int selectedMinute = _startTime.minute;
    bool isPm = _startTime.period == DayPeriod.pm;

    final picked = await showDialog<TimeOfDay>(
      context: context,
      barrierColor: Colors.black.withValues(alpha: 0.62),
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            final hourValues = List<int>.generate(12, (index) => index + 1);
            final minuteValues = List<int>.generate(12, (index) => index * 5);

            return Dialog(
              backgroundColor: Colors.transparent,
              insetPadding: const EdgeInsets.symmetric(horizontal: 28),
              child: Container(
                padding: const EdgeInsets.fromLTRB(22, 22, 22, 18),
                decoration: BoxDecoration(
                  color: const Color(0xFF17273A).withValues(alpha: 0.97),
                  borderRadius: BorderRadius.circular(26),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.14),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.35),
                      blurRadius: 30,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(13),
                            border: Border.all(
                              color: Colors.white.withValues(alpha: 0.10),
                            ),
                          ),
                          child: Icon(
                            Icons.schedule_rounded,
                            color: Colors.white.withValues(alpha: 0.82),
                            size: 21,
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text(
                            'Start time',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 19,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 22),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _TimeSelectionBox(
                          value: selectedHour.toString().padLeft(2, '0'),
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          child: Text(
                            ':',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.65),
                              fontSize: 30,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        _TimeSelectionBox(
                          value: selectedMinute.toString().padLeft(2, '0'),
                        ),
                      ],
                    ),

                    const SizedBox(height: 18),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _TimePeriodButton(
                          label: 'AM',
                          selected: !isPm,
                          onTap: () {
                            setDialogState(() {
                              isPm = false;
                            });
                          },
                        ),
                        const SizedBox(width: 8),
                        _TimePeriodButton(
                          label: 'PM',
                          selected: isPm,
                          onTap: () {
                            setDialogState(() {
                              isPm = true;
                            });
                          },
                        ),
                      ],
                    ),

                    const SizedBox(height: 22),

                    Row(
                      children: [
                        Expanded(
                          child: _TimePickerColumn(
                            title: 'Hour',
                            values: hourValues,
                            selectedValue: selectedHour,
                            labelBuilder: (value) =>
                                value.toString().padLeft(2, '0'),
                            onSelected: (value) {
                              setDialogState(() {
                                selectedHour = value;
                              });
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _TimePickerColumn(
                            title: 'Minute',
                            values: minuteValues,
                            selectedValue: selectedMinute,
                            labelBuilder: (value) =>
                                value.toString().padLeft(2, '0'),
                            onSelected: (value) {
                              setDialogState(() {
                                selectedMinute = value;
                              });
                            },
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: () => Navigator.pop(dialogContext),
                          child: Text(
                            'Cancel',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.65),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        TextButton(
                          onPressed: () {
                            final hour24 = isPm
                                ? (selectedHour == 12 ? 12 : selectedHour + 12)
                                : (selectedHour == 12 ? 0 : selectedHour);

                            Navigator.pop(
                              dialogContext,
                              TimeOfDay(hour: hour24, minute: selectedMinute),
                            );
                          },
                          child: const Text(
                            'Set',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    if (picked == null || !mounted) return;

    setState(() {
      _startTime = picked;
    });
  }

  Future<void> _saveRoutine() async {
    if (!_formKey.currentState!.validate()) return;

    if (_selectedDays.isEmpty) {
      _showMessage('Select at least one day.');
      return;
    }

    setState(() {
      _isSaving = true;
    });

    try {
      final startTime = _formatBackendTime(_startTime);

      if (widget.isEditing) {
        await _routineApiService.updateRoutine(
          routineId: widget.routine!.id,
          name: _nameController.text.trim(),
          activityContext: _activityContext,
          savedLocationId: _selectedLocation?.id,
          clearSavedLocation: _selectedLocation == null,
          daysOfWeek: _selectedDays.toList(),
          startTime: startTime,
          durationMinutes: _durationMinutes,
          isEnabled: _isEnabled,
        );
      } else {
        await _routineApiService.createRoutine(
          name: _nameController.text.trim(),
          activityContext: _activityContext,
          savedLocationId: _selectedLocation?.id,
          daysOfWeek: _selectedDays.toList(),
          startTime: startTime,
          durationMinutes: _durationMinutes,
          isEnabled: _isEnabled,
        );
      }

      if (!mounted) return;

      Navigator.pop(context, true);
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _isSaving = false;
      });

      _showMessage(_cleanError(error));
    }
  }

  String _formatBackendTime(TimeOfDay time) {
    return '${time.hour.toString().padLeft(2, '0')}:'
        '${time.minute.toString().padLeft(2, '0')}:00';
  }

  TimeOfDay _parseTime(String value) {
    final parts = value.split(':');

    if (parts.length < 2) {
      return const TimeOfDay(hour: 8, minute: 0);
    }

    final hour = int.tryParse(parts[0]);
    final minute = int.tryParse(parts[1]);

    if (hour == null || minute == null) {
      return const TimeOfDay(hour: 8, minute: 0);
    }

    return TimeOfDay(hour: hour.clamp(0, 23), minute: minute.clamp(0, 59));
  }

  String _formatTime(TimeOfDay time) {
    final hour = time.hour;
    final minute = time.minute;
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

  String _formatLocationType(String value) {
    switch (value) {
      case 'home':
        return 'Home';
      case 'farm':
        return 'Farm';
      case 'destination':
        return 'Destination';
      case 'work':
        return 'Work';
      case 'other':
        return 'Other';
      default:
        return value;
    }
  }

  String _formatDay(String value) {
    switch (value) {
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
        return value;
    }
  }

  String _cleanError(Object error) {
    final message = error.toString();

    if (message.startsWith('Exception: ')) {
      return message.substring(11);
    }

    return message;
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101C2C),
      body: Stack(
        children: [
          const _FormBackground(),
          SafeArea(
            child: Form(
              key: _formKey,
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 40),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 28),
                    _buildNameField(),
                    const SizedBox(height: 18),
                    _buildActivitySection(),
                    const SizedBox(height: 18),
                    _buildDaysSection(),
                    const SizedBox(height: 18),
                    _buildTimeSection(),
                    const SizedBox(height: 18),
                    _buildDurationSection(),
                    const SizedBox(height: 18),
                    _buildLocationSection(),
                    const SizedBox(height: 18),
                    _buildEnabledSection(),
                    const SizedBox(height: 28),
                    _buildSaveButton(),
                  ],
                ),
              ),
            ),
          ),
          if (_isSaving)
            Positioned.fill(
              child: Container(
                color: Colors.black.withValues(alpha: 0.22),
                child: const Center(child: CircularProgressIndicator()),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        _GlassIconButton(
          icon: Icons.arrow_back_rounded,
          onPressed: _isSaving ? null : () => Navigator.pop(context),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.isEditing ? 'Edit Routine' : 'Create Routine',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Tell Mausam how you plan your day',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.62),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildNameField() {
    return _GlassSection(
      title: 'Routine name',
      icon: Icons.edit_note_rounded,
      child: TextFormField(
        controller: _nameController,
        maxLength: 100,
        style: const TextStyle(color: Colors.white),
        decoration: _inputDecoration(
          'e.g. Morning Walk',
          Icons.label_outline_rounded,
        ),
        validator: (value) {
          if (value == null || value.trim().isEmpty) {
            return 'Enter a routine name.';
          }

          return null;
        },
      ),
    );
  }

  Widget _buildActivitySection() {
    const activityIcons = {
      'general': Icons.auto_awesome_rounded,
      'outdoor_health': Icons.directions_run_rounded,
      'farming': Icons.agriculture_rounded,
      'irrigation': Icons.water_drop_rounded,
      'travel': Icons.flight_takeoff_rounded,
      'commute': Icons.directions_car_rounded,
    };

    return _GlassSection(
      title: 'Activity',
      icon: Icons.category_outlined,
      child: Wrap(
        spacing: 9,
        runSpacing: 9,
        children: _activities.map((activity) {
          final selected = _activityContext == activity;

          return GestureDetector(
            onTap: () {
              setState(() {
                _activityContext = activity;
              });
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: selected ? 0.12 : 0.045),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(
                  color: Colors.white.withValues(alpha: selected ? 0.72 : 0.10),
                  width: selected ? 1.2 : 1,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: selected
                          ? Colors.white
                          : Colors.white.withValues(alpha: 0.35),
                      boxShadow: selected
                          ? [
                              BoxShadow(
                                color: Colors.white.withValues(alpha: 0.65),
                                blurRadius: 6,
                                spreadRadius: 1,
                              ),
                            ]
                          : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    activityIcons[activity] ?? Icons.circle_outlined,
                    size: 16,
                    color: selected
                        ? Colors.white
                        : Colors.white.withValues(alpha: 0.62),
                  ),
                  const SizedBox(width: 7),
                  Text(
                    _formatActivity(activity),
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildDaysSection() {
    return _GlassSection(
      title: 'Days',
      icon: Icons.calendar_month_rounded,
      child: Wrap(
        spacing: 9,
        runSpacing: 9,
        children: _days.map((day) {
          final selected = _selectedDays.contains(day);

          return GestureDetector(
            onTap: () {
              setState(() {
                if (selected) {
                  _selectedDays.remove(day);
                } else {
                  _selectedDays.add(day);
                }
              });
            },
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: selected ? 0.12 : 0.045),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(
                  color: Colors.white.withValues(alpha: selected ? 0.72 : 0.10),
                  width: selected ? 1.2 : 1,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: selected
                          ? Colors.white
                          : Colors.white.withValues(alpha: 0.35),
                      boxShadow: selected
                          ? [
                              BoxShadow(
                                color: Colors.white.withValues(alpha: 0.65),
                                blurRadius: 6,
                                spreadRadius: 1,
                              ),
                            ]
                          : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatDay(day),
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildTimeSection() {
    return _GlassSection(
      title: 'Start time',
      icon: Icons.schedule_rounded,
      child: _GlassValueButton(
        icon: Icons.access_time_rounded,
        label: _formatTime(_startTime),
        onPressed: _pickTime,
      ),
    );
  }

  Widget _buildDurationSection() {
    return _GlassSection(
      title: 'Duration',
      icon: Icons.timer_outlined,
      child: Column(
        children: [
          Row(
            children: [
              Text(
                '$_durationMinutes min',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const Spacer(),
              Text(
                '5–720 min',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.48),
                  fontSize: 12,
                ),
              ),
            ],
          ),
          Slider(
            value: _durationMinutes.toDouble(),
            min: 5,
            max: 720,
            divisions: 143,
            onChanged: (value) {
              setState(() {
                _durationMinutes = value.round();
              });
            },
          ),
        ],
      ),
    );
  }

  Widget _buildLocationSection() {
    return _GlassSection(
      title: 'Location',
      icon: Icons.location_on_outlined,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_isLoadingLocations)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_locations.isNotEmpty) ...[
            DropdownButtonFormField<String?>(
              initialValue: _selectedLocation?.id,
              dropdownColor: const Color(0xFF17283A),
              decoration: _inputDecoration(
                'Choose a saved location',
                Icons.bookmark_outline_rounded,
              ),
              style: const TextStyle(color: Colors.white, fontSize: 14),
              items: [
                const DropdownMenuItem<String?>(
                  value: null,
                  child: Text('No saved location'),
                ),
                ..._locations.map(
                  (location) => DropdownMenuItem<String?>(
                    value: location.id,
                    child: Text(
                      '${location.label} • ${location.city}',
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              ],
              onChanged: (value) {
                setState(() {
                  _selectedLocation = value == null
                      ? null
                      : _locations.firstWhere(
                          (location) => location.id == value,
                        );
                });
              },
            ),
          ],
          if (_locationError != null) ...[
            const SizedBox(height: 8),
            Text(
              _locationError!,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.55),
                fontSize: 12,
              ),
            ),
          ],
          const SizedBox(height: 14),
          Text(
            'Or search for a new city',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.60),
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _locationSearchController,
                  style: const TextStyle(color: Colors.white),
                  textInputAction: TextInputAction.search,
                  onSubmitted: (_) => _searchLocations(),
                  decoration: _inputDecoration(
                    'Search city',
                    Icons.search_rounded,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              _GlassIconButton(
                icon: _isSearching
                    ? Icons.hourglass_top_rounded
                    : Icons.search_rounded,
                onPressed: _isSearching ? null : _searchLocations,
              ),
            ],
          ),
          if (_searchError != null) ...[
            const SizedBox(height: 8),
            Text(
              _searchError!,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.55),
                fontSize: 12,
              ),
            ),
          ],
          if (_searchResults.isNotEmpty) ...[
            const SizedBox(height: 12),
            ..._searchResults.map(
              (result) => _LocationSearchTile(
                result: result,
                onTap: () => _saveSearchResult(result),
              ),
            ),
          ],
          if (_selectedLocation != null) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.07),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(color: Colors.white.withValues(alpha: 0.09)),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.check_circle_outline_rounded,
                    color: Colors.white.withValues(alpha: 0.78),
                    size: 19,
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      '${_selectedLocation!.label} • '
                      '${_selectedLocation!.city}',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.78),
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      setState(() {
                        _selectedLocation = null;
                      });
                    },
                    child: const Text('Clear'),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildEnabledSection() {
    return _GlassSection(
      title: 'Routine status',
      icon: Icons.notifications_active_outlined,
      child: Row(
        children: [
          Expanded(
            child: Text(
              _isEnabled ? 'Enabled' : 'Disabled',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.78),
                fontSize: 15,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Switch(
            value: _isEnabled,
            onChanged: (value) {
              setState(() {
                _isEnabled = value;
              });
            },
            thumbColor: WidgetStateProperty.resolveWith<Color?>((states) {
              return Colors.white;
            }),
            trackColor: WidgetStateProperty.resolveWith<Color?>((states) {
              if (states.contains(WidgetState.selected)) {
                return Colors.white.withValues(alpha: 0.28);
              }
              return Colors.white.withValues(alpha: 0.10);
            }),
            trackOutlineColor: WidgetStateProperty.resolveWith<Color?>((
              states,
            ) {
              return Colors.white.withValues(
                alpha: states.contains(WidgetState.selected) ? 0.42 : 0.16,
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildSaveButton() {
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _isSaving ? null : _saveRoutine,
          borderRadius: BorderRadius.circular(20),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.13),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.16),
                  blurRadius: 20,
                  spreadRadius: 1,
                ),
              ],
            ),
            child: Center(
              child: Text(
                widget.isEditing ? 'Save Changes' : 'Create Routine',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint, IconData icon) {
    return InputDecoration(
      hintText: hint,
      hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.38)),
      prefixIcon: Icon(icon, color: Colors.white.withValues(alpha: 0.60)),
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.065),
      counterStyle: TextStyle(color: Colors.white.withValues(alpha: 0.40)),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.22)),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.18)),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.22)),
      ),
    );
  }
}

class _LocationDetails {
  final String label;
  final String locationType;

  const _LocationDetails({required this.label, required this.locationType});
}

class _GlassSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget child;

  const _GlassSection({
    required this.title,
    required this.icon,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.075),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: 0.11)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 19, color: Colors.white.withValues(alpha: 0.72)),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 13),
          child,
        ],
      ),
    );
  }
}

class _TimeSelectionBox extends StatelessWidget {
  final String value;

  const _TimeSelectionBox({required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 78,
      height: 62,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(17),
        border: Border.all(color: Colors.white.withValues(alpha: 0.20)),
      ),
      child: Text(
        value,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 28,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _TimePeriodButton extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _TimePeriodButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        width: 70,
        height: 38,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: selected ? 0.16 : 0.055),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: Colors.white.withValues(alpha: selected ? 0.42 : 0.10),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

class _TimePickerColumn extends StatelessWidget {
  final String title;
  final List<int> values;
  final int selectedValue;
  final String Function(int value) labelBuilder;
  final ValueChanged<int> onSelected;

  const _TimePickerColumn({
    required this.title,
    required this.values,
    required this.selectedValue,
    required this.labelBuilder,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          title,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.55),
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 7),
        SizedBox(
          height: 116,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: values.length,
            separatorBuilder: (_, _) => const SizedBox(width: 7),
            itemBuilder: (context, index) {
              final value = values[index];
              final selected = value == selectedValue;

              return GestureDetector(
                onTap: () => onSelected(value),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 160),
                  width: 48,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(
                      alpha: selected ? 0.15 : 0.045,
                    ),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: Colors.white.withValues(
                        alpha: selected ? 0.42 : 0.08,
                      ),
                    ),
                  ),
                  child: Text(
                    labelBuilder(value),
                    style: TextStyle(
                      color: Colors.white.withValues(
                        alpha: selected ? 1.0 : 0.55,
                      ),
                      fontSize: 13,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _GlassValueButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const _GlassValueButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.065),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withValues(alpha: 0.10)),
          ),
          child: Row(
            children: [
              Icon(icon, color: Colors.white.withValues(alpha: 0.70), size: 20),
              const SizedBox(width: 10),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              Icon(
                Icons.chevron_right_rounded,
                color: Colors.white.withValues(alpha: 0.45),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _GlassIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onPressed;

  const _GlassIconButton({required this.icon, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(15),
        child: Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.09),
            borderRadius: BorderRadius.circular(15),
            border: Border.all(color: Colors.white.withValues(alpha: 0.11)),
          ),
          child: Icon(
            icon,
            color: Colors.white.withValues(alpha: 0.82),
            size: 21,
          ),
        ),
      ),
    );
  }
}

class _LocationSearchTile extends StatelessWidget {
  final LocationSearchResult result;
  final VoidCallback onTap;

  const _LocationSearchTile({required this.result, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(15),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.065),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(color: Colors.white.withValues(alpha: 0.09)),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.location_on_outlined,
                  color: Colors.white.withValues(alpha: 0.65),
                  size: 19,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        result.name,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        result.subtitle,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.52),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(
                  Icons.add_circle_outline_rounded,
                  color: Colors.white.withValues(alpha: 0.62),
                  size: 20,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _FormBackground extends StatelessWidget {
  const _FormBackground();

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
