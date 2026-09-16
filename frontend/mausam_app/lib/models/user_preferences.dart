class NotificationSettings {
  final bool officialAlerts;
  final bool routineAlerts;
  final bool rainAlerts;
  final bool aqiAlerts;
  final bool dailySummary;

  const NotificationSettings({
    required this.officialAlerts,
    required this.routineAlerts,
    required this.rainAlerts,
    required this.aqiAlerts,
    required this.dailySummary,
  });

  factory NotificationSettings.fromJson(Map<String, dynamic> json) {
    return NotificationSettings(
      officialAlerts: json['official_alerts'] == true,
      routineAlerts: json['routine_alerts'] == true,
      rainAlerts: json['rain_alerts'] == true,
      aqiAlerts: json['aqi_alerts'] == true,
      dailySummary: json['daily_summary'] == true,
    );
  }
}

class PersonalizationSettings {
  final bool personalizedHomepage;
  final bool routineImpact;
  final bool learnFromActivity;

  const PersonalizationSettings({
    required this.personalizedHomepage,
    required this.routineImpact,
    required this.learnFromActivity,
  });

  factory PersonalizationSettings.fromJson(Map<String, dynamic> json) {
    return PersonalizationSettings(
      personalizedHomepage: json['personalized_homepage'] == true,
      routineImpact: json['routine_impact'] == true,
      learnFromActivity: json['learn_from_activity'] == true,
    );
  }
}

class UserPreferences {
  final String? preferredLanguage;
  final String? temperatureUnit;
  final List<String> personas;
  final String? primaryPersona;
  final int? preferredStartHour;
  final int? preferredEndHour;
  final List<String> interests;
  final List<String> activityContexts;
  final NotificationSettings notifications;
  final PersonalizationSettings personalization;
  final bool onboardingCompleted;

  const UserPreferences({
    required this.preferredLanguage,
    required this.temperatureUnit,
    required this.personas,
    required this.primaryPersona,
    required this.preferredStartHour,
    required this.preferredEndHour,
    required this.interests,
    required this.activityContexts,
    required this.notifications,
    required this.personalization,
    required this.onboardingCompleted,
  });

  String? get persona => primaryPersona;

  factory UserPreferences.fromJson(Map<String, dynamic> json) {
    final legacyPersona = json['persona']?.toString();
    final parsedPersonas = (json['personas'] as List<dynamic>? ?? const [])
        .map((item) => item.toString())
        .toList();
    final parsedPrimaryPersona =
        json['primary_persona']?.toString() ?? legacyPersona;

    return UserPreferences(
      preferredLanguage: json['preferred_language']?.toString(),
      temperatureUnit: json['temperature_unit']?.toString(),
      personas: parsedPersonas.isNotEmpty
          ? parsedPersonas
          : (legacyPersona == null ? const [] : [legacyPersona]),
      primaryPersona: parsedPrimaryPersona,
      preferredStartHour: (json['preferred_start_hour'] as num?)?.toInt(),
      preferredEndHour: (json['preferred_end_hour'] as num?)?.toInt(),
      interests: (json['interests'] as List<dynamic>? ?? const [])
          .map((item) => item.toString())
          .toList(),
      activityContexts:
          (json['activity_contexts'] as List<dynamic>? ?? const [])
              .map((item) => item.toString())
              .toList(),
      notifications: NotificationSettings.fromJson(
        json['notifications'] as Map<String, dynamic>? ?? const {},
      ),
      personalization: PersonalizationSettings.fromJson(
        json['personalization'] as Map<String, dynamic>? ?? const {},
      ),
      onboardingCompleted: json['onboarding_completed'] == true,
    );
  }
}
