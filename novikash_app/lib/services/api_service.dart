import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

const String kApiBaseUrl = 'https://novikash.espacehotsi-int.fr';

class ApiService {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: kApiBaseUrl,
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 3),
  ));

  ApiService() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  Dio get client => _dio;

  // Auth
  Future<Response> login(String phone, String password) async {
    return await _dio.post('/auth/login', data: {
      'phone': phone,
      'password': password,
    });
  }

  Future<Response> register(String phone, String password, String email) async {
    return await _dio.post('/auth/register', data: {
      'phone': phone,
      'password': password,
      'email': email,
    });
  }

  Future<Response> verifyOtp(String phone, String code) async {
    return await _dio.post('/auth/verify-otp', data: {
      'phone': phone,
      'code': code,
    });
  }

  Future<Response> submitKyc(String identityType, String identityNumber, DateTime identityExpiry) async {
    return await _dio.post('/kyc/submit', data: {
      'identity_type': identityType,
      'identity_number': identityNumber,
      'identity_expiry': identityExpiry.toIso8601String(),
    });
  }

  // Wallet
  Future<Response> getWallet() async {
    return await _dio.get('/wallet/me');
  }

  Future<Response> transfer(String phone, double amount) async {
    return await _dio.post('/wallet/transfer', data: {
      'receiver_phone': phone,
      'amount': amount,
    });
  }

  Future<Response> checkUser(String phone) async {
    return await _dio.get('/wallet/check-user/$phone');
  }

  Future<Response> transferExternal(String phone, double amount) async {
    return await _dio.post('/wallet/transfer-external', data: {
      'receiver_phone': phone,
      'amount': amount,
    });
  }

  Future<Response> generatePaymentLink(double amount) async {
    return await _dio.post('/wallet/generate-payment-link', data: {
      'amount': amount,
    });
  }

  Future<Response> deposit(double amount) async {
    return await _dio.post('/payments/deposit', data: {
      'amount': amount,
    });
  }

  // Loans
  Future<Response> getLoansOverview() async {
    return await _dio.get('/loans/overview');
  }

  Future<Response> activateNoviPlus(Map<String, dynamic> data) async {
    return await _dio.post('/loans/novi-plus/activate', data: data);
  }

  Future<Response> simulateLoan(double amount, {int weeks = 4}) async {
    return await _dio.get('/loans/simulate', queryParameters: {
      'amount': amount,
      'weeks': weeks,
    });
  }

  Future<Response> acceptLoanTerms() async {
    return await _dio.post('/loans/terms/accept');
  }

  Future<Response> requestLoan(
    double amount,
    List<String> guarantors, {
    String loanType = 'ALOBA',
    bool termsAccepted = true,
  }) async {
    return await _dio.post('/loans/request', data: {
      'loan_type': loanType,
      'amount': amount,
      'guarantors': guarantors,
      'terms_accepted': termsAccepted,
    });
  }

  Future<Response> getLoanHistory() async {
    return await _dio.get('/loans/history');
  }

  Future<Response> getPendingGuarantees() async {
    return await _dio.get('/loans/guarantees/pending');
  }

  Future<Response> respondToGuarantee(int loanId, bool accept) async {
    return await _dio.post('/loans/$loanId/guarantee/respond', data: {
      'accept': accept,
    });
  }

  Future<Response> repayLoan(int loanId) async {
    return await _dio.post('/loans/$loanId/repay');
  }

  Future<Response> withdraw(double amount) async {
    return await _dio.post('/payments/withdraw', data: {
      'amount': amount,
    });
  }

  Future<Response> getNotifications() async {
    return await _dio.get('/notifications/');
  }

  Future<Response> markNotificationRead(int notificationId) async {
    return await _dio.post('/notifications/$notificationId/read');
  }

  // Tontine
  Future<Response> getTontine() async {
    return await _dio.get('/tontine/me');
  }

  Future<Response> depositToTontine(double amount) async {
    return await _dio.post('/tontine/deposit', data: {
      'amount': amount,
    });
  }

  Future<Response> lockTontine(int lockDurationDays) async {
    return await _dio.post('/tontine/lock', data: {
      'lock_duration_days': lockDurationDays,
    });
  }

  Future<Response> withdrawFromTontine(double amount) async {
    return await _dio.post('/tontine/withdraw', data: {
      'amount': amount,
    });
  }

  Future<Response> getTontineTransactions() async {
    return await _dio.get('/tontine/transactions');
  }

  Future<Response> getTontineStatus() async {
    return await _dio.get('/tontine/status');
  }
}
