import 'package:flutter/material.dart';
import 'package:novikash_app/services/api_service.dart';
import 'package:url_launcher/url_launcher.dart';

class ChargerScreen extends StatefulWidget {
  const ChargerScreen({super.key});

  @override
  State<ChargerScreen> createState() => _ChargerScreenState();
}

class _ChargerScreenState extends State<ChargerScreen> {
  final _apiService = ApiService();
  final _amountController = TextEditingController();
  bool _isLoading = false;
  String? _selectedNetwork = 'FLOOZ'; // Default to FLOOZ

  Future<void> _showNetworkSelectionDialog() async {
    final selected = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Choisir un réseau'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            GestureDetector(
              onTap: () => Navigator.pop(context, 'FLOOZ'),
              child: Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: _selectedNetwork == 'FLOOZ' ? Colors.blue : Colors.grey,
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Radio<String>(
                      value: 'FLOOZ',
                      groupValue: _selectedNetwork,
                      onChanged: (value) {
                        if (value != null) Navigator.pop(context, value);
                      },
                    ),
                    const Text('FLOOZ'),
                  ],
                ),
              ),
            ),
            GestureDetector(
              onTap: () => Navigator.pop(context, 'TMONEY'),
              child: Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.symmetric(vertical: 8),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: _selectedNetwork == 'TMONEY' ? Colors.blue : Colors.grey,
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Radio<String>(
                      value: 'TMONEY',
                      groupValue: _selectedNetwork,
                      onChanged: (value) {
                        if (value != null) Navigator.pop(context, value);
                      },
                    ),
                    const Text('TMONEY'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );

    if (selected != null) {
      setState(() => _selectedNetwork = selected);
    }
  }

  Future<void> _personalRecharge() async {
    final amount = _amountController.text.trim();
    if (amount.isEmpty) {
      _showError('Veuillez entrer un montant');
      return;
    }

    // Show network selection before proceeding
    await _showNetworkSelectionDialog();

    setState(() => _isLoading = true);
    try {
      final parsedAmount = double.parse(amount);
      final response = await _apiService.deposit(
        parsedAmount,
        network: _selectedNetwork,
      );

      if (mounted) {
        final action = response.data['action'] ?? '';
        
        if (action == 'show_ussd_prompt') {
          // Backend will trigger USSD on device, just confirm to user
          _showSuccess(
            'Rechargement initié via $_selectedNetwork!\n\n'
            'Veuillez confirmer le paiement sur votre téléphone.\n'
            'Une notification USSD devrait apparaître.'
          );
        } else {
          _showSuccess('Rechargement initié. Veuillez confirmer sur votre téléphone.');
        }
        _amountController.clear();
      }
    } catch (e) {
      if (mounted) {
        final errorMsg = e.toString();
        if (errorMsg.contains('400')) {
          _showError('Réseau requis. Veuillez sélectionner FLOOZ ou TMONEY');
        } else if (errorMsg.contains('401')) {
          _showError('Session expirée. Veuillez vous reconnecter');
        } else {
          _showError('Échec du rechargement: $e');
        }
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _generatePaymentLink() async {
    final amount = _amountController.text.trim();
    if (amount.isEmpty) {
      _showError('Veuillez entrer un montant');
      return;
    }

    // Show network selection for payment link too
    await _showNetworkSelectionDialog();

    setState(() => _isLoading = true);
    try {
      final parsedAmount = double.parse(amount);
      final response = await _apiService.generatePaymentLink(
        parsedAmount,
        network: _selectedNetwork,
      );

      if (mounted) {
        final paymentLink = response.data['payment_link'] as String?;
        final action = response.data['action'] ?? '';
        final instructions = response.data['instructions'] as String?;

        if (paymentLink != null && action == 'open_browser') {
          // Auto-open the payment link
          final Uri url = Uri.parse(paymentLink);
          if (await canLaunchUrl(url)) {
            await launchUrl(url, mode: LaunchMode.externalApplication);
            _showSuccess(
              'Lien de paiement ouvert!\n\n'
              '${instructions ?? 'Veuillez sélectionner $_selectedNetwork et compléter le paiement.'}'
            );
          } else {
            // If can't launch URL, show it to user
            _showInfo('Lien de paiement généré:\n\n$paymentLink\n\n${instructions ?? ''}');
          }
        } else if (paymentLink != null) {
          _showInfo('Lien de paiement:\n\n$paymentLink');
        }
        _amountController.clear();
      }
    } catch (e) {
      if (mounted) {
        _showError('Échec de génération du lien: $e');
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  void _showInfo(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Lien de Paiement'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Charger')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const Text('Options de rechargement', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            TextField(
              controller: _amountController,
              decoration: const InputDecoration(
                hintText: 'Montant (XOF)',
                prefixIcon: Icon(Icons.attach_money),
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            // Network selection display
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Réseau: $_selectedNetwork', style: const TextStyle(fontWeight: FontWeight.w500)),
                  ElevatedButton.icon(
                    onPressed: _showNetworkSelectionDialog,
                    icon: const Icon(Icons.edit),
                    label: const Text('Changer'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            const Text('Rechargement personnel', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            const Text('Via votre numéro mobile money', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isLoading ? null : _personalRecharge,
              child: _isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Text('Recharger'),
            ),
            const SizedBox(height: 32),
            const Text('Lien de paiement Novikash', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            const Text('Générez un lien pour recevoir des fonds', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isLoading ? null : _generatePaymentLink,
              child: const Text('Générer Lien de Paiement'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }
}