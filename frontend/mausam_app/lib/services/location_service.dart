import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';

class LocationService {
  Future<String> getLocationName(Position position) async {
    try {
      final geocoding = Geocoding();
      final placemarks = await geocoding.placemarkFromCoordinates(
        position.latitude,
        position.longitude,
      );

      if (placemarks.isEmpty) {
        return 'Current Location';
      }

      final place = placemarks.first;

      final city = (place.locality?.trim().isNotEmpty ?? false)
          ? place.locality!.trim()
          : (place.subAdministrativeArea?.trim().isNotEmpty ?? false)
              ? place.subAdministrativeArea!.trim()
              : 'Current Location';

      final state = place.administrativeArea?.trim();

      if (state != null && state.isNotEmpty) {
        return '$city, $state';
      }

      return city;
    } catch (_) {
      return 'Current Location';
    }
  }

  Future<bool> hasLocationAccess() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();

    if (!serviceEnabled) {
      return false;
    }

    final permission = await Geolocator.checkPermission();

    return permission == LocationPermission.always ||
        permission == LocationPermission.whileInUse;
  }

  Future<Position> getCurrentLocation() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();

    if (!serviceEnabled) {
      throw Exception('Location services are disabled.');
    }

    LocationPermission permission = await Geolocator.checkPermission();

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();

      if (permission == LocationPermission.denied) {
        throw Exception('Location permission denied.');
      }
    }

    if (permission == LocationPermission.deniedForever) {
      throw Exception('Location permission permanently denied.');
    }

    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
      ),
    );
  }
}
