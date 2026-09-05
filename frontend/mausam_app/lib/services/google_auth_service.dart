import 'package:google_sign_in/google_sign_in.dart';

class GoogleAuthService {
  GoogleAuthService({
    required this.serverClientId,
  });

  final String serverClientId;

  final GoogleSignIn _googleSignIn =
      GoogleSignIn.instance;

  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) {
      return;
    }

    await _googleSignIn.initialize(
      serverClientId: serverClientId,
    );

    _initialized = true;
  }

  Future<String> signInAndGetIdToken() async {
    await initialize();

    final account =
        await _googleSignIn.authenticate();

    final authentication =
        account.authentication;

    final idToken =
        authentication.idToken;

    if (idToken == null || idToken.isEmpty) {
      throw Exception(
        'Google did not return an ID token',
      );
    }

    return idToken;
  }

  Future<void> signOut() async {
    await initialize();
    await _googleSignIn.signOut();
  }
}