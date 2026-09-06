class UserProfile {
  final String id;
  final String name;
  final String email;
  final bool isActive;
  final DateTime createdAt;

  const UserProfile({
    required this.id,
    required this.name,
    required this.email,
    required this.isActive,
    required this.createdAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'].toString(),
      name: json['name'].toString(),
      email: json['email'].toString(),
      isActive: json['is_active'] == true,
      createdAt: DateTime.parse(
        json['created_at'].toString(),
      ),
    );
  }
}
