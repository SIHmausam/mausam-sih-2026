class SavedLocation {
  final String id;
  final String label;
  final String city;
  final double latitude;
  final double longitude;
  final String locationType;
  final bool isPrimary;
  final DateTime createdAt;
  final DateTime updatedAt;

  const SavedLocation({
    required this.id,
    required this.label,
    required this.city,
    required this.latitude,
    required this.longitude,
    required this.locationType,
    required this.isPrimary,
    required this.createdAt,
    required this.updatedAt,
  });

  factory SavedLocation.fromJson(Map<String, dynamic> json) {
    return SavedLocation(
      id: json['id'].toString(),
      label: json['label'].toString(),
      city: json['city'].toString(),
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      locationType: json['location_type'].toString(),
      isPrimary: json['is_primary'] == true,
      createdAt: DateTime.parse(json['created_at'].toString()),
      updatedAt: DateTime.parse(json['updated_at'].toString()),
    );
  }
}
