class AppConfig {
  static const googleServerClientId = String.fromEnvironment(
    'GOOGLE_SERVER_CLIENT_ID',
  );

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const baseMapTileUrl = String.fromEnvironment(
    'BASE_MAP_TILE_URL',
    defaultValue: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  );

  static const baseMapAttribution = String.fromEnvironment(
    'BASE_MAP_ATTRIBUTION',
    defaultValue: '© OpenStreetMap',
  );

  static const mapUserAgentPackageName = String.fromEnvironment(
    'MAP_USER_AGENT_PACKAGE_NAME',
    defaultValue: 'mausam_app',
  );
}
