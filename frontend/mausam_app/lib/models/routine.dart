class Routine {
  final String id;
  final String name;
  final String activityContext;
  final String? savedLocationId;
  final List<String> daysOfWeek;
  final String startTime;
  final int durationMinutes;
  final bool isEnabled;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Routine({
    required this.id,
    required this.name,
    required this.activityContext,
    required this.savedLocationId,
    required this.daysOfWeek,
    required this.startTime,
    required this.durationMinutes,
    required this.isEnabled,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Routine.fromJson(Map<String, dynamic> json) {
    return Routine(
      id: json['id'].toString(),
      name: json['name'].toString(),
      activityContext: json['activity_context'].toString(),
      savedLocationId: json['saved_location_id']?.toString(),
      daysOfWeek: (json['days_of_week'] as List<dynamic>? ?? const [])
          .map((day) => day.toString())
          .toList(),
      startTime: json['start_time'].toString(),
      durationMinutes: (json['duration_minutes'] as num).toInt(),
      isEnabled: json['is_enabled'] == true,
      createdAt: DateTime.parse(json['created_at'].toString()),
      updatedAt: DateTime.parse(json['updated_at'].toString()),
    );
  }
}
