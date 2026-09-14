class WeatherMapLayerConfig {
  final String id;
  final String label;
  final double opacity;

  const WeatherMapLayerConfig({
    required this.id,
    required this.label,
    required this.opacity,
  });

  factory WeatherMapLayerConfig.fromJson(
    Map<String, dynamic> json,
  ) {
    final opacity = json['opacity'];

    return WeatherMapLayerConfig(
      id: json['id']?.toString() ?? '',
      label: json['label']?.toString() ?? '',
      opacity: opacity is num
          ? opacity.toDouble()
          : double.tryParse(
                  opacity?.toString() ?? '',
                ) ??
                1.0,
    );
  }
}


class WeatherMapConfig {
  final String defaultLayer;
  final String tileUrlTemplate;

  final int minZoom;
  final int maxZoom;

  final int cacheTtlSeconds;

  final String attribution;

  final List<WeatherMapLayerConfig> layers;

  const WeatherMapConfig({
    required this.defaultLayer,
    required this.tileUrlTemplate,
    required this.minZoom,
    required this.maxZoom,
    required this.cacheTtlSeconds,
    required this.attribution,
    required this.layers,
  });

  factory WeatherMapConfig.fromJson(
    Map<String, dynamic> json,
  ) {
    final rawLayers = json['layers'];

    return WeatherMapConfig(
      defaultLayer:
          json['default_layer']?.toString() ??
              'precipitation',

      tileUrlTemplate:
          json['tile_url_template']?.toString() ??
              '',

      minZoom: _toInt(
        json['min_zoom'],
      ),

      maxZoom: _toInt(
        json['max_zoom'],
        fallback: 8,
      ),

      cacheTtlSeconds: _toInt(
        json['cache_ttl_seconds'],
        fallback: 600,
      ),

      attribution:
          json['attribution']?.toString() ??
              'Weather data © OpenWeather',

      layers: rawLayers is List
          ? rawLayers
              .whereType<Map<String, dynamic>>()
              .map(
                WeatherMapLayerConfig.fromJson,
              )
              .where(
                (layer) => layer.id.isNotEmpty,
              )
              .toList()
          : const [],
    );
  }

  WeatherMapLayerConfig? layerById(
    String id,
  ) {
    for (final layer in layers) {
      if (layer.id == id) {
        return layer;
      }
    }

    return null;
  }

  static int _toInt(
    dynamic value, {
    int fallback = 0,
  }) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(
          value?.toString() ?? '',
        ) ??
        fallback;
  }
}