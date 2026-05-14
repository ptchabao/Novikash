import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:novikash_app/services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  bool _isAuthenticated = false;
  String? _error;

  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;
  String? get error => _error;

  Future<bool> login(String phone, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.login(phone, password);
      final token = response.data['access_token'];
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', token);
      
      _isAuthenticated = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = 'Login failed. Please check your credentials.';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    _isAuthenticated = false;
    notifyListeners();
  }

  Future<void> checkAuth() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    if (token != null) {
      try {
        await _apiService.getWallet();
        _isAuthenticated = true;
      } catch (e) {
        await prefs.remove('access_token');
        _isAuthenticated = false;
      }
      notifyListeners();
    }
  }
}
