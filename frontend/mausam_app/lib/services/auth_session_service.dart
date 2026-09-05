import 'auth_api_service.dart';
import 'token_storage_service.dart';

class AuthSessionService {
  AuthSessionService({
    AuthApiService? authApiService,
    TokenStorageService? tokenStorageService,
  }) : _authApiService =
           authApiService ?? AuthApiService(),
       _tokenStorageService =
           tokenStorageService ??
           TokenStorageService();

  final AuthApiService _authApiService;
  final TokenStorageService _tokenStorageService;

  Future<bool> restoreSession() async {
    final refreshToken =
        await _tokenStorageService
            .getRefreshToken();

    if (refreshToken == null ||
        refreshToken.isEmpty) {
      return false;
    }

    try {
      final tokens =
          await _authApiService.refreshSession(
        refreshToken: refreshToken,
      );

      await _tokenStorageService.saveTokens(
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );

      return true;
    } catch (_) {
      await _tokenStorageService.clearTokens();
      return false;
    }
  }
}