import 'package:flutter/foundation.dart';
import 'package:firebase_auth/firebase_auth.dart';

/// Authentication service wrapping Firebase Auth.
///
/// Provides sign-in, sign-up, sign-out, and auth-state tracking
/// for user and organization management.
class AuthService extends ChangeNotifier {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  User? _user;
  bool _loading = false;
  String? _error;

  /// The currently authenticated Firebase user (null if signed out).
  User? get user => _user;

  /// Whether an auth operation is in progress.
  bool get loading => _loading;

  /// Last auth error message (null if none).
  String? get error => _error;

  /// Whether a user is currently signed in.
  bool get isAuthenticated => _user != null;

  AuthService() {
    // Listen to auth state changes
    _auth.authStateChanges().listen((user) {
      _user = user;
      notifyListeners();
    });
  }

  // ── Sign in with email & password ───────────────────────────────
  Future<void> signIn({
    required String email,
    required String password,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final credential = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );
      _user = credential.user;
    } on FirebaseAuthException catch (e) {
      _error = _mapAuthError(e.code);
    } catch (e) {
      _error = 'Authentication failed: $e';
    }

    _loading = false;
    notifyListeners();
  }

  // ── Sign up with email & password ───────────────────────────────
  Future<void> signUp({
    required String email,
    required String password,
    String? displayName,
  }) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      final credential = await _auth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );
      _user = credential.user;

      if (displayName != null) {
        await _user?.updateDisplayName(displayName);
      }
    } on FirebaseAuthException catch (e) {
      _error = _mapAuthError(e.code);
    } catch (e) {
      _error = 'Registration failed: $e';
    }

    _loading = false;
    notifyListeners();
  }

  // ── Sign out ────────────────────────────────────────────────────
  Future<void> signOut() async {
    await _auth.signOut();
    _user = null;
    notifyListeners();
  }

  // ── Password reset ──────────────────────────────────────────────
  Future<void> resetPassword(String email) async {
    _loading = true;
    _error = null;
    notifyListeners();

    try {
      await _auth.sendPasswordResetEmail(email: email);
    } on FirebaseAuthException catch (e) {
      _error = _mapAuthError(e.code);
    } catch (e) {
      _error = 'Password reset failed: $e';
    }

    _loading = false;
    notifyListeners();
  }

  // ── Map Firebase error codes to user-friendly messages ──────────
  String _mapAuthError(String code) {
    switch (code) {
      case 'user-not-found':
        return 'No account found with this email.';
      case 'wrong-password':
        return 'Incorrect password. Please try again.';
      case 'email-already-in-use':
        return 'An account with this email already exists.';
      case 'weak-password':
        return 'Password must be at least 6 characters.';
      case 'invalid-email':
        return 'Please enter a valid email address.';
      case 'too-many-requests':
        return 'Too many attempts. Please try again later.';
      default:
        return 'Authentication error ($code).';
    }
  }
}
