import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../config/app_config.dart';
import '../models/weather_data.dart';
import '../models/weather_map_config.dart';
import '../services/location_search_service.dart';
import '../services/location_service.dart';
import '../services/weather_api_service.dart';
import '../services/weather_map_api_service.dart';

class WeatherMapScreen extends StatefulWidget {
  const WeatherMapScreen({
    super.key,
  });

  @override
  State<WeatherMapScreen> createState() =>
      _WeatherMapScreenState();
}

class _WeatherMapScreenState extends State<WeatherMapScreen> {
  static const LatLng _indiaCenter = LatLng(
    22.9734,
    78.6569,
  );

  final MapController _mapController = MapController();

  final WeatherMapApiService _weatherMapApiService =
      WeatherMapApiService();

  final LocationService _locationService =
      LocationService();

  final TextEditingController _searchController =
      TextEditingController();

  Timer? _searchDebounce;

  WeatherMapConfig? _config;

  Map<String, String>? _tileHeaders;

  String? _selectedLayerId;

  LatLng? _currentLocation;
  LatLng? _selectedPoint;

  WeatherData? _selectedWeather;

  List<LocationSearchResult> _searchResults = [];

  String _selectedLocationName = 'Selected Location';

  bool _isLoading = true;
  bool _isLocating = false;
  bool _isSearching = false;
  bool _isWeatherLoading = false;
  bool _showSearch = false;
  bool _mapReady = false;

  String? _error;

  String _activeSearchQuery = '';

  @override
  void initState() {
    super.initState();

    _loadMap();
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _searchController.dispose();
    _mapController.dispose();

    super.dispose();
  }

  // ----------------------------------------------------------
  // INITIAL MAP LOAD
  // ----------------------------------------------------------

  Future<void> _loadMap() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final config =
          await _weatherMapApiService.getConfig();

      if (config.layers.isEmpty) {
        throw Exception(
          'No weather map layers are available.',
        );
      }

      final headers =
          await _weatherMapApiService.getTileHeaders();

      if (!mounted) {
        return;
      }

      setState(() {
        _config = config;
        _tileHeaders = headers;

        _selectedLayerId =
            config.layerById(config.defaultLayer) != null
                ? config.defaultLayer
                : config.layers.first.id;

        _isLoading = false;
      });

      // Do not request GPS permission automatically.
      // Only use location if permission already exists.
      await _centerOnCurrentLocation(
        requestPermission: false,
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
        _error = _cleanError(error);
      });
    }
  }

  // ----------------------------------------------------------
  // CURRENT GPS LOCATION
  // ----------------------------------------------------------

  Future<void> _centerOnCurrentLocation({
    required bool requestPermission,
  }) async {
    if (_isLocating) {
      return;
    }

    setState(() {
      _isLocating = true;
    });

    try {
      if (!requestPermission) {
        final hasAccess =
            await _locationService.hasLocationAccess();

        if (!hasAccess) {
          return;
        }
      }

      final position =
          await _locationService.getCurrentLocation();

      final locationName =
          await _locationService.getLocationName(
        position,
      );

      final point = LatLng(
        position.latitude,
        position.longitude,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _currentLocation = point;
        _selectedPoint = point;
        _selectedLocationName = locationName;
      });

      if (_mapReady) {
        _moveMapToPoint(point);
      }

      await _loadWeatherForPoint(
        point,
        locationName,
      );
    } catch (error) {
      if (!mounted || !requestPermission) {
        return;
      }

      _showMessage(
        _cleanError(error),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLocating = false;
        });
      }
    }
  }

  // ----------------------------------------------------------
  // CITY SEARCH
  // ----------------------------------------------------------

  void _onSearchChanged(
    String value,
  ) {
    _searchDebounce?.cancel();

    final query = value.trim();

    _activeSearchQuery = query;

    if (query.length < 2) {
      setState(() {
        _searchResults = [];
        _isSearching = false;
      });

      return;
    }

    setState(() {
      _isSearching = true;
    });

    _searchDebounce = Timer(
      const Duration(
        milliseconds: 400,
      ),
      () => _searchLocations(query),
    );
  }

  Future<void> _searchLocations(
    String query,
  ) async {
    try {
      final results =
          await LocationSearchService.search(
        query,
      );

      if (!mounted ||
          query != _activeSearchQuery) {
        return;
      }

      setState(() {
        _searchResults = results;
        _isSearching = false;
      });
    } catch (error) {
      if (!mounted ||
          query != _activeSearchQuery) {
        return;
      }

      setState(() {
        _isSearching = false;
      });

      _showMessage(
        _cleanError(error),
      );
    }
  }

  Future<void> _selectSearchResult(
    LocationSearchResult result,
  ) async {
    await _selectLocation(
      latitude: result.latitude,
      longitude: result.longitude,
      name: result.displayName,
    );
  }

  // ----------------------------------------------------------
  // SELECT LOCATION
  // ----------------------------------------------------------

  Future<void> _selectLocation({
    required double latitude,
    required double longitude,
    required String name,
  }) async {
    final point = LatLng(
      latitude,
      longitude,
    );

    if (!mounted) {
      return;
    }

    setState(() {
      _selectedPoint = point;
      _selectedLocationName = name;

      _showSearch = false;

      _searchController.clear();
      _searchResults = [];
      _activeSearchQuery = '';
    });

    _moveMapToPoint(point);

    await _loadWeatherForPoint(
      point,
      name,
    );
  }

  void _moveMapToPoint(
    LatLng point,
  ) {
    if (!_mapReady) {
      return;
    }

    final maxZoom =
        _config?.maxZoom.toDouble() ?? 8;

    final targetZoom =
        maxZoom < 7 ? maxZoom : 7.0;

    _mapController.move(
      point,
      targetZoom,
    );
  }

  // ----------------------------------------------------------
  // EXACT WEATHER DATA
  // ----------------------------------------------------------

  Future<void> _loadWeatherForPoint(
    LatLng point,
    String locationName,
  ) async {
    if (!mounted) {
      return;
    }

    setState(() {
      _isWeatherLoading = true;
      _selectedWeather = null;
    });

    try {
      final weather =
          await WeatherApiService.getWeather(
        latitude: point.latitude,
        longitude: point.longitude,
        city: locationName,
      );

      if (!mounted) {
        return;
      }

      // Do not display an old response if the user
      // selected another point while this was loading.
      if (_selectedPoint != point) {
        return;
      }

      setState(() {
        _selectedWeather = weather;
        _isWeatherLoading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isWeatherLoading = false;
      });

      _showMessage(
        _cleanError(error),
      );
    }
  }

  // ----------------------------------------------------------
  // HELPERS
  // ----------------------------------------------------------

  WeatherMapLayerConfig? get _selectedLayer {
    final config = _config;
    final selectedId = _selectedLayerId;

    if (config == null ||
        selectedId == null) {
      return null;
    }

    return config.layerById(
      selectedId,
    );
  }

  String _cleanError(
    Object error,
  ) {
    return error
        .toString()
        .replaceFirst(
          'Exception: ',
          '',
        );
  }

  void _showMessage(
    String message,
  ) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
        ),
      );
  }

  IconData _layerIcon(
    String id,
  ) {
    switch (id) {
      case 'temperature':
        return Icons.thermostat_rounded;

      case 'wind':
        return Icons.air_rounded;

      case 'clouds':
        return Icons.cloud_outlined;

      case 'precipitation':
      default:
        return Icons.water_drop_outlined;
    }
  }

  String _formatNumber(
    double value, {
    int decimals = 1,
  }) {
    return value.toStringAsFixed(
      decimals,
    );
  }

  // ----------------------------------------------------------
  // MAIN BUILD
  // ----------------------------------------------------------

  @override
  Widget build(
    BuildContext context,
  ) {
    if (_isLoading) {
      return const Scaffold(
        backgroundColor:
            Color(0xFF101C2C),
        body: Center(
          child:
              CircularProgressIndicator(
            color: Colors.white,
          ),
        ),
      );
    }

    if (_error != null ||
        _config == null ||
        _tileHeaders == null) {
      return _buildErrorState();
    }

    final config = _config!;

    final selectedLayer =
        _selectedLayer ??
            config.layers.first;

    final weatherTileUrl =
        _weatherMapApiService
            .resolveTileUrlTemplate(
      template:
          config.tileUrlTemplate,
      layer: selectedLayer.id,
    );

    return Scaffold(
      backgroundColor:
          const Color(
        0xFF101C2C,
      ),
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ------------------------------------------
          // MAP
          // ------------------------------------------

          FlutterMap(
            mapController:
                _mapController,
            options: MapOptions(
              initialCenter:
                  _indiaCenter,
              initialZoom: 4.6,
              minZoom:
                  config.minZoom
                      .toDouble(),
              maxZoom:
                  config.maxZoom
                      .toDouble(),
              backgroundColor:
                  const Color(
                0xFF101C2C,
              ),
              keepAlive: true,

              onMapReady: () {
                _mapReady = true;

                final point =
                    _selectedPoint ??
                        _currentLocation;

                if (point != null) {
                  _moveMapToPoint(
                    point,
                  );
                }
              },

              // Tap anywhere to load exact
              // weather for that coordinate.
              onTap: (
                tapPosition,
                point,
              ) {
                _selectLocation(
                  latitude:
                      point.latitude,
                  longitude:
                      point.longitude,
                  name:
                      'Selected Location',
                );
              },
            ),
            children: [
              // ------------------------------------
              // BASE MAP
              // ------------------------------------

              TileLayer(
                urlTemplate:
                    AppConfig
                        .baseMapTileUrl,
                userAgentPackageName:
                    AppConfig
                        .mapUserAgentPackageName,
                maxZoom:
                    config.maxZoom
                        .toDouble(),
                keepBuffer: 1,
                panBuffer: 0,
                retinaMode: false,
              ),

              // ------------------------------------
              // WEATHER OVERLAY
              // ------------------------------------

              TileLayer(
                key: ValueKey(
                  selectedLayer.id,
                ),
                urlTemplate:
                    weatherTileUrl,
                tileProvider:
                    NetworkTileProvider(
                  headers:
                      _tileHeaders,
                  silenceExceptions:
                      true,
                ),
                minZoom:
                    config.minZoom
                        .toDouble(),
                maxZoom:
                    config.maxZoom
                        .toDouble(),
                minNativeZoom:
                    config.minZoom,
                maxNativeZoom:
                    config.maxZoom,

                // Keep requests under control.
                keepBuffer: 1,
                panBuffer: 0,
                retinaMode: false,

                tileBuilder: (
                  context,
                  tileWidget,
                  tile,
                ) {
                  return Opacity(
                    opacity:
                        selectedLayer
                            .opacity
                            .clamp(
                              0.0,
                              1.0,
                            ),
                    child:
                        tileWidget,
                  );
                },
              ),

              // ------------------------------------
              // CURRENT GPS MARKER
              // ------------------------------------

              if (_currentLocation !=
                  null)
                MarkerLayer(
                  markers: [
                    Marker(
                      point:
                          _currentLocation!,
                      width: 46,
                      height: 46,
                      child: Center(
                        child:
                            Container(
                          width: 22,
                          height: 22,
                          decoration:
                              BoxDecoration(
                            color:
                                const Color(
                              0xFF4EA5FF,
                            ),
                            shape:
                                BoxShape
                                    .circle,
                            border:
                                Border.all(
                              color:
                                  Colors
                                      .white,
                              width: 3,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color:
                                    const Color(
                                  0xFF4EA5FF,
                                ).withValues(
                                  alpha:
                                      0.45,
                                ),
                                blurRadius:
                                    14,
                                spreadRadius:
                                    5,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

              // ------------------------------------
              // SEARCHED / TAPPED LOCATION MARKER
              // ------------------------------------

              if (_selectedPoint != null &&
                  _selectedPoint !=
                      _currentLocation)
                MarkerLayer(
                  markers: [
                    Marker(
                      point:
                          _selectedPoint!,
                      width: 48,
                      height: 48,
                      alignment:
                          Alignment
                              .topCenter,
                      child: const Icon(
                        Icons
                            .location_on_rounded,
                        color:
                            Color(
                          0xFFE74C4C,
                        ),
                        size: 44,
                      ),
                    ),
                  ],
                ),
            ],
          ),

          // ------------------------------------------
          // HEADER
          // ------------------------------------------

          _buildHeader(
            selectedLayer,
          ),

          // ------------------------------------------
          // LAYER SELECTOR
          // ------------------------------------------

          if (!_showSearch)
            _buildLayerSelector(
              config,
              selectedLayer,
            ),

          // ------------------------------------------
          // SEARCH PANEL
          // ------------------------------------------

          if (_showSearch)
            _buildSearchPanel(),

          // ------------------------------------------
          // WEATHER DETAILS CARD
          // ------------------------------------------

          if (_selectedPoint != null)
            Positioned(
              left: 16,
              right: 82,
              bottom: 150,
              child:
                  _buildWeatherCard(),
            ),

          // ------------------------------------------
          // CURRENT LOCATION BUTTON
          // ------------------------------------------

          Positioned(
            right: 18,
            bottom: 108,
            child:
                _buildGpsButton(),
          ),

          // ------------------------------------------
          // ATTRIBUTION
          // ------------------------------------------

          Positioned(
            left: 14,
            bottom: 112,
            child: IgnorePointer(
              child:
                  _buildAttribution(
                config,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ----------------------------------------------------------
  // HEADER
  // ----------------------------------------------------------

  Widget _buildHeader(
    WeatherMapLayerConfig selectedLayer,
  ) {
    return Positioned(
      left: 16,
      right: 16,
      top: 0,
      child: SafeArea(
        bottom: false,
        child: Container(
          margin:
              const EdgeInsets.only(
            top: 10,
          ),
          padding:
              const EdgeInsets.only(
            left: 16,
            right: 8,
            top: 11,
            bottom: 11,
          ),
          decoration:
              BoxDecoration(
            color:
                const Color(
              0xFF101C2C,
            ).withValues(
              alpha: 0.90,
            ),
            borderRadius:
                BorderRadius.circular(
              20,
            ),
            border: Border.all(
              color:
                  Colors.white
                      .withValues(
                alpha: 0.14,
              ),
            ),
          ),
          child: Row(
            children: [
              const Icon(
                Icons.map_rounded,
                color:
                    Colors.white,
                size: 27,
              ),

              const SizedBox(
                width: 13,
              ),

              Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment
                          .start,
                  children: [
                    const Text(
                      'Weather Map',
                      style:
                          TextStyle(
                        color:
                            Colors.white,
                        fontSize: 17,
                        fontWeight:
                            FontWeight
                                .w700,
                      ),
                    ),

                    const SizedBox(
                      height: 2,
                    ),

                    Text(
                      selectedLayer
                          .label,
                      maxLines: 1,
                      overflow:
                          TextOverflow
                              .ellipsis,
                      style:
                          const TextStyle(
                        color:
                            Colors
                                .white54,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),

              IconButton(
                tooltip:
                    'Search location',
                onPressed: () {
                  setState(() {
                    _showSearch =
                        !_showSearch;

                    if (!_showSearch) {
                      _searchController
                          .clear();

                      _searchResults =
                          [];

                      _activeSearchQuery =
                          '';
                    }
                  });
                },
                icon: Icon(
                  _showSearch
                      ? Icons
                          .close_rounded
                      : Icons
                          .search_rounded,
                  color:
                      Colors.white,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ----------------------------------------------------------
  // WEATHER LAYER SELECTOR
  // ----------------------------------------------------------

  Widget _buildLayerSelector(
    WeatherMapConfig config,
    WeatherMapLayerConfig selectedLayer,
  ) {
    return Positioned(
      left: 0,
      right: 0,
      top:
          MediaQuery.paddingOf(
                context,
              ).top +
              88,
      child: SizedBox(
        height: 50,
        child:
            ListView.separated(
          padding:
              const EdgeInsets
                  .symmetric(
            horizontal: 16,
          ),
          scrollDirection:
              Axis.horizontal,
          itemCount:
              config.layers.length,
          separatorBuilder:
              (_, _) =>
                  const SizedBox(
            width: 8,
          ),
          itemBuilder:
              (context, index) {
            final layer =
                config.layers[index];

            final selected =
                layer.id ==
                    selectedLayer.id;

            return GestureDetector(
              onTap: () {
                setState(() {
                  _selectedLayerId =
                      layer.id;
                });
              },
              child:
                  AnimatedContainer(
                duration:
                    const Duration(
                  milliseconds:
                      180,
                ),
                padding:
                    const EdgeInsets
                        .symmetric(
                  horizontal: 14,
                  vertical: 9,
                ),
                decoration:
                    BoxDecoration(
                  color: selected
                      ? Colors.white
                      : const Color(
                          0xFF101C2C,
                        ).withValues(
                          alpha: 0.90,
                        ),
                  borderRadius:
                      BorderRadius
                          .circular(
                    18,
                  ),
                  border: Border.all(
                    color: selected
                        ? Colors.white
                        : Colors.white
                            .withValues(
                            alpha:
                                0.08,
                          ),
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      _layerIcon(
                        layer.id,
                      ),
                      size: 18,
                      color: selected
                          ? const Color(
                              0xFF101C2C,
                            )
                          : Colors.white,
                    ),

                    const SizedBox(
                      width: 7,
                    ),

                    Text(
                      layer.label,
                      style:
                          TextStyle(
                        color: selected
                            ? const Color(
                                0xFF101C2C,
                              )
                            : Colors
                                .white,
                        fontSize: 12.5,
                        fontWeight:
                            selected
                                ? FontWeight
                                    .w700
                                : FontWeight
                                    .w500,
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  // ----------------------------------------------------------
  // SEARCH
  // ----------------------------------------------------------

  Widget _buildSearchPanel() {
    return Positioned(
      left: 16,
      right: 16,
      top:
          MediaQuery.paddingOf(
                context,
              ).top +
              88,
      child: Material(
        color: Colors.transparent,
        child: Container(
          constraints:
              const BoxConstraints(
            maxHeight: 360,
          ),
          decoration:
              BoxDecoration(
            color:
                const Color(
              0xFF172536,
            ).withValues(
              alpha: 0.97,
            ),
            borderRadius:
                BorderRadius.circular(
              20,
            ),
            border: Border.all(
              color:
                  Colors.white
                      .withValues(
                alpha: 0.12,
              ),
            ),
            boxShadow: const [
              BoxShadow(
                color:
                    Colors.black26,
                blurRadius: 20,
              ),
            ],
          ),
          child: Column(
            mainAxisSize:
                MainAxisSize.min,
            children: [
              Padding(
                padding:
                    const EdgeInsets
                        .all(
                  12,
                ),
                child: TextField(
                  controller:
                      _searchController,
                  autofocus: true,
                  onChanged:
                      _onSearchChanged,
                  textInputAction:
                      TextInputAction
                          .search,
                  style:
                      const TextStyle(
                    color:
                        Colors.white,
                  ),
                  decoration:
                      InputDecoration(
                    hintText:
                        'Search city or place...',
                    hintStyle:
                        const TextStyle(
                      color:
                          Colors
                              .white54,
                    ),
                    prefixIcon:
                        const Icon(
                      Icons
                          .search_rounded,
                      color:
                          Colors
                              .white70,
                    ),
                    suffixIcon:
                        _searchController
                                .text
                                .isEmpty
                            ? null
                            : IconButton(
                                onPressed:
                                    () {
                                  _searchController
                                      .clear();

                                  setState(
                                      () {
                                    _searchResults =
                                        [];

                                    _activeSearchQuery =
                                        '';
                                  });
                                },
                                icon:
                                    const Icon(
                                  Icons
                                      .clear_rounded,
                                  color:
                                      Colors
                                          .white70,
                                ),
                              ),
                    filled: true,
                    fillColor:
                        Colors.white
                            .withValues(
                      alpha: 0.08,
                    ),
                    border:
                        OutlineInputBorder(
                      borderRadius:
                          BorderRadius
                              .circular(
                        14,
                      ),
                      borderSide:
                          BorderSide
                              .none,
                    ),
                    enabledBorder:
                        OutlineInputBorder(
                      borderRadius:
                          BorderRadius
                              .circular(
                        14,
                      ),
                      borderSide:
                          BorderSide
                              .none,
                    ),
                    focusedBorder:
                        OutlineInputBorder(
                      borderRadius:
                          BorderRadius
                              .circular(
                        14,
                      ),
                      borderSide:
                          BorderSide(
                        color:
                            Colors.white
                                .withValues(
                          alpha:
                              0.25,
                        ),
                      ),
                    ),
                  ),
                ),
              ),

              if (_isSearching)
                const Padding(
                  padding:
                      EdgeInsets.all(
                    18,
                  ),
                  child:
                      CircularProgressIndicator(
                    color:
                        Colors.white,
                    strokeWidth: 2,
                  ),
                ),

              if (!_isSearching &&
                  _searchController
                      .text
                      .trim()
                      .length >=
                      2 &&
                  _searchResults
                      .isEmpty)
                const Padding(
                  padding:
                      EdgeInsets.only(
                    bottom: 18,
                    left: 20,
                    right: 20,
                  ),
                  child: Text(
                    'No matching locations found.',
                    style:
                        TextStyle(
                      color:
                          Colors.white54,
                    ),
                  ),
                ),

              if (!_isSearching &&
                  _searchResults
                      .isNotEmpty)
                Flexible(
                  child:
                      ListView.separated(
                    shrinkWrap: true,
                    padding:
                        const EdgeInsets
                            .only(
                      bottom: 10,
                    ),
                    itemCount:
                        _searchResults
                            .length,
                    separatorBuilder:
                        (_, _) =>
                            Divider(
                      height: 1,
                      color:
                          Colors.white
                              .withValues(
                        alpha: 0.07,
                      ),
                    ),
                    itemBuilder:
                        (
                      context,
                      index,
                    ) {
                      final result =
                          _searchResults[
                              index];

                      return ListTile(
                        leading:
                            Container(
                          width: 38,
                          height: 38,
                          decoration:
                              BoxDecoration(
                            color:
                                Colors.white
                                    .withValues(
                              alpha:
                                  0.08,
                            ),
                            borderRadius:
                                BorderRadius
                                    .circular(
                              12,
                            ),
                          ),
                          child:
                              const Icon(
                            Icons
                                .location_on_outlined,
                            color:
                                Colors
                                    .white70,
                            size: 20,
                          ),
                        ),
                        title: Text(
                          result.name,
                          style:
                              const TextStyle(
                            color:
                                Colors
                                    .white,
                            fontWeight:
                                FontWeight
                                    .w600,
                          ),
                        ),
                        subtitle:
                            result
                                    .subtitle
                                    .isEmpty
                                ? null
                                : Text(
                                    result
                                        .subtitle,
                                    maxLines:
                                        1,
                                    overflow:
                                        TextOverflow
                                            .ellipsis,
                                    style:
                                        const TextStyle(
                                      color:
                                          Colors
                                              .white54,
                                    ),
                                  ),
                        trailing:
                            const Icon(
                          Icons
                              .north_west_rounded,
                          size: 18,
                          color:
                              Colors
                                  .white38,
                        ),
                        onTap: () =>
                            _selectSearchResult(
                          result,
                        ),
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  // ----------------------------------------------------------
  // WEATHER CARD
  // ----------------------------------------------------------

  Widget _buildWeatherCard() {
    return AnimatedSwitcher(
      duration:
          const Duration(
        milliseconds: 250,
      ),
      child: _isWeatherLoading
          ? _buildWeatherLoadingCard()
          : _selectedWeather != null
              ? _buildWeatherDataCard(
                  _selectedWeather!,
                )
              : const SizedBox.shrink(),
    );
  }

  Widget _buildWeatherLoadingCard() {
    return Container(
      key: const ValueKey(
        'weather-loading',
      ),
      height: 94,
      padding:
          const EdgeInsets.all(
        18,
      ),
      decoration:
          _weatherCardDecoration(),
      child: const Row(
        children: [
          SizedBox(
            width: 22,
            height: 22,
            child:
                CircularProgressIndicator(
              color: Colors.white,
              strokeWidth: 2,
            ),
          ),
          SizedBox(
            width: 14,
          ),
          Text(
            'Loading weather...',
            style: TextStyle(
              color: Colors.white70,
              fontWeight:
                  FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeatherDataCard(
    WeatherData weather,
  ) {
    return Container(
      key: const ValueKey(
        'weather-data',
      ),
      padding:
          const EdgeInsets.all(
        16,
      ),
      decoration:
          _weatherCardDecoration(),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        mainAxisSize:
            MainAxisSize.min,
        children: [
          Row(
            children: [
              const Icon(
                Icons
                    .location_on_rounded,
                color:
                    Colors.white70,
                size: 17,
              ),

              const SizedBox(
                width: 6,
              ),

              Expanded(
                child: Text(
                  _selectedLocationName,
                  maxLines: 1,
                  overflow:
                      TextOverflow
                          .ellipsis,
                  style:
                      const TextStyle(
                    color:
                        Colors.white,
                    fontSize: 14,
                    fontWeight:
                        FontWeight
                            .w700,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(
            height: 13,
          ),

          SingleChildScrollView(
            scrollDirection:
                Axis.horizontal,
            child: Row(
              children: [
                _weatherMetric(
                  icon: Icons
                      .thermostat_rounded,
                  value:
                      '${_formatNumber(weather.temperature)}°C',
                  label:
                      'Temperature',
                ),

                _metricDivider(),

                _weatherMetric(
                  icon: Icons
                      .water_drop_outlined,
                  value:
                      '${_formatNumber(weather.rain)} mm',
                  label: 'Rain',
                ),

                _metricDivider(),

                _weatherMetric(
                  icon:
                      Icons.air_rounded,
                  value:
                      '${_formatNumber(weather.windSpeed)} km/h',
                  label: 'Wind',
                ),

                _metricDivider(),

                _weatherMetric(
                  icon:
                      Icons.eco_outlined,
                  value:
                      _formatNumber(
                    weather.usAqi,
                    decimals: 0,
                  ),
                  label: 'AQI',
                ),

                _metricDivider(),

                _weatherMetric(
                  icon: Icons
                      .wb_sunny_outlined,
                  value:
                      _formatNumber(
                    weather.uvIndex,
                  ),
                  label: 'UV',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _weatherMetric({
    required IconData icon,
    required String value,
    required String label,
  }) {
    return Padding(
      padding:
          const EdgeInsets
              .symmetric(
        horizontal: 5,
      ),
      child: Column(
        children: [
          Icon(
            icon,
            color:
                Colors.white70,
            size: 18,
          ),

          const SizedBox(
            height: 5,
          ),

          Text(
            value,
            style:
                const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight:
                  FontWeight.w700,
            ),
          ),

          const SizedBox(
            height: 2,
          ),

          Text(
            label,
            style:
                const TextStyle(
              color:
                  Colors.white54,
              fontSize: 9,
            ),
          ),
        ],
      ),
    );
  }

  Widget _metricDivider() {
    return Container(
      width: 1,
      height: 38,
      margin:
          const EdgeInsets
              .symmetric(
        horizontal: 4,
      ),
      color:
          Colors.white.withValues(
        alpha: 0.10,
      ),
    );
  }

  BoxDecoration _weatherCardDecoration() {
    return BoxDecoration(
      color:
          const Color(
        0xFF172536,
      ).withValues(
        alpha: 0.94,
      ),
      borderRadius:
          BorderRadius.circular(
        20,
      ),
      border: Border.all(
        color:
            Colors.white.withValues(
          alpha: 0.12,
        ),
      ),
      boxShadow: const [
        BoxShadow(
          color: Colors.black26,
          blurRadius: 16,
        ),
      ],
    );
  }

  // ----------------------------------------------------------
  // GPS BUTTON
  // ----------------------------------------------------------

  Widget _buildGpsButton() {
    return GestureDetector(
      onTap: _isLocating
          ? null
          : () =>
              _centerOnCurrentLocation(
                requestPermission:
                    true,
              ),
      child: Container(
        width: 54,
        height: 54,
        decoration:
            BoxDecoration(
          color:
              const Color(
            0xFF101C2C,
          ).withValues(
            alpha: 0.94,
          ),
          borderRadius:
              BorderRadius.circular(
            18,
          ),
          border: Border.all(
            color:
                Colors.white
                    .withValues(
              alpha: 0.16,
            ),
          ),
          boxShadow: const [
            BoxShadow(
              color:
                  Colors.black26,
              blurRadius: 12,
            ),
          ],
        ),
        child: Center(
          child: _isLocating
              ? const SizedBox(
                  width: 21,
                  height: 21,
                  child:
                      CircularProgressIndicator(
                    strokeWidth: 2,
                    color:
                        Colors.white,
                  ),
                )
              : const Icon(
                  Icons
                      .my_location_rounded,
                  color:
                      Colors.white,
                  size: 26,
                ),
        ),
      ),
    );
  }

  // ----------------------------------------------------------
  // ATTRIBUTION
  // ----------------------------------------------------------

  Widget _buildAttribution(
    WeatherMapConfig config,
  ) {
    return Container(
      constraints:
          const BoxConstraints(
        maxWidth: 310,
      ),
      padding:
          const EdgeInsets
              .symmetric(
        horizontal: 8,
        vertical: 5,
      ),
      decoration:
          BoxDecoration(
        color:
            const Color(
          0xFF101C2C,
        ).withValues(
          alpha: 0.78,
        ),
        borderRadius:
            BorderRadius.circular(
          8,
        ),
      ),
      child: Text(
        '${AppConfig.baseMapAttribution}'
        ' • '
        '${config.attribution}',
        maxLines: 1,
        overflow:
            TextOverflow.ellipsis,
        style:
            const TextStyle(
          color: Colors.white60,
          fontSize: 9,
        ),
      ),
    );
  }

  // ----------------------------------------------------------
  // ERROR STATE
  // ----------------------------------------------------------

  Widget _buildErrorState() {
    return Scaffold(
      backgroundColor:
          const Color(
        0xFF101C2C,
      ),
      body: SafeArea(
        child: Center(
          child: Padding(
            padding:
                const EdgeInsets.all(
              28,
            ),
            child: Column(
              mainAxisSize:
                  MainAxisSize.min,
              children: [
                const Icon(
                  Icons.map_outlined,
                  size: 52,
                  color:
                      Colors.white70,
                ),

                const SizedBox(
                  height: 18,
                ),

                const Text(
                  'Weather map unavailable',
                  textAlign:
                      TextAlign.center,
                  style:
                      TextStyle(
                    color:
                        Colors.white,
                    fontSize: 21,
                    fontWeight:
                        FontWeight
                            .w700,
                  ),
                ),

                const SizedBox(
                  height: 10,
                ),

                Text(
                  _error ??
                      'Unable to load map.',
                  textAlign:
                      TextAlign.center,
                  style:
                      const TextStyle(
                    color:
                        Colors.white60,
                  ),
                ),

                const SizedBox(
                  height: 22,
                ),

                FilledButton.icon(
                  onPressed:
                      _loadMap,
                  icon: const Icon(
                    Icons
                        .refresh_rounded,
                  ),
                  label:
                      const Text(
                    'Retry',
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