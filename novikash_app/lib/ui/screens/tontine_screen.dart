import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:novikash_app/providers/tontine_provider.dart';
import 'package:novikash_app/providers/wallet_provider.dart';

class TontineScreen extends StatefulWidget {
  const TontineScreen({super.key});

  @override
  State<TontineScreen> createState() => _TontineScreenState();
}

class _TontineScreenState extends State<TontineScreen> {
  final TextEditingController _amountController = TextEditingController();
  int? _selectedLockDuration;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TontineProvider>().fetchTontine();
      context.read<TontineProvider>().fetchTontineStatus();
      context.read<WalletProvider>().fetchWallet();
    });
  }

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  void _showDepositDialog() {
    _amountController.clear();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Ajouter des fonds'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Entrez le montant à ajouter à votre tontine:'),
            const SizedBox(height: 16),
            TextField(
              controller: _amountController,
              decoration: InputDecoration(
                hintText: 'Montant (XOF)',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                prefixIcon: const Icon(Icons.attach_money),
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () async {
              final amount = double.tryParse(_amountController.text);
              if (amount == null || amount <= 0) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Montant invalide')),
                );
                return;
              }

              final provider = context.read<TontineProvider>();
              final success = await provider.depositToTontine(amount, context);
              if (mounted) {
                Navigator.pop(context);
                if (success) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('${amount.toStringAsFixed(0)} XOF déposé(s) avec succès'),
                      backgroundColor: Colors.green,
                    ),
                  );
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(provider.error ?? 'Erreur lors du dépôt'),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              }
            },
            child: const Text('Déposer'),
          ),
        ],
      ),
    );
  }

  void _showLockDialog() {
    final tontine = context.read<TontineProvider>().tontine;
    if (tontine == null || tontine.balance <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Vous devez d’abord déposer des fonds dans la tontine avant de la bloquer.'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    _selectedLockDuration = null;
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Bloquer votre tontine'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Sélectionnez la durée de blocage:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              const Text(
                '⚠️ Une fois bloquée, vous ne pourrez pas retirer vos fonds ni modifier la durée jusqu\'à la fin du blocage.',
                style: TextStyle(color: Colors.orange, fontSize: 12),
              ),
              const SizedBox(height: 20),
              RadioListTile<int>(
                title: const Text('10 jours'),
                value: 10,
                groupValue: _selectedLockDuration,
                onChanged: (value) {
                  setDialogState(() => _selectedLockDuration = value);
                },
              ),
              RadioListTile<int>(
                title: const Text('20 jours'),
                value: 20,
                groupValue: _selectedLockDuration,
                onChanged: (value) {
                  setDialogState(() => _selectedLockDuration = value);
                },
              ),
              RadioListTile<int>(
                title: const Text('30 jours'),
                value: 30,
                groupValue: _selectedLockDuration,
                onChanged: (value) {
                  setDialogState(() => _selectedLockDuration = value);
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Annuler'),
            ),
            ElevatedButton(
              onPressed: _selectedLockDuration == null
                  ? null
                  : () async {
                      final provider = context.read<TontineProvider>();
                      final success = await provider.lockTontine(_selectedLockDuration!);
                      if (mounted) {
                        Navigator.pop(context);
                        if (success) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                'Tontine bloquée pour $_selectedLockDuration jours',
                              ),
                              backgroundColor: Colors.green,
                            ),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(provider.error ?? 'Erreur lors du blocage'),
                              backgroundColor: Colors.red,
                            ),
                          );
                        }
                      }
                    },
              child: const Text('Confirmer'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mon Tontine'),
        elevation: 0,
      ),
      body: Consumer2<TontineProvider, WalletProvider>(
        builder: (context, tontineProvider, walletProvider, child) {
          if (tontineProvider.isLoading && tontineProvider.tontine == null) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          final tontine = tontineProvider.tontine;
          if (tontine == null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.wallet, size: 64, color: Colors.grey),
                  const SizedBox(height: 16),
                  const Text('Tontine non initialisée'),
                  const SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: () => tontineProvider.fetchTontine(),
                    child: const Text('Réessayer'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              await tontineProvider.refreshTontineData();
              await walletProvider.refreshWallet();
            },
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Balance Cards - Main Wallet and Tontine
                  Row(
                    children: [
                      // Main Wallet Card
                      Expanded(
                        child: Card(
                          elevation: 4,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              gradient: LinearGradient(
                                colors: [
                                  Colors.blue.shade400,
                                  Colors.blue.shade600,
                                ],
                              ),
                            ),
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Portefeuille Principal',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Consumer<WalletProvider>(
                                  builder: (context, walletProvider, child) {
                                    return Text(
                                      '${walletProvider.availableBalance.toStringAsFixed(0)} XOF',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 24,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    );
                                  },
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'Disponible',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 10,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      // Tontine Card
                      Expanded(
                        child: Card(
                          elevation: 4,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              gradient: LinearGradient(
                                colors: [
                                  Colors.purple.shade400,
                                  Colors.purple.shade600,
                                ],
                              ),
                            ),
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Compte Épargne',
                                  style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '${tontine.balance.toStringAsFixed(0)} XOF',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  tontine.isLocked ? 'Bloqué' : 'Actif',
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 10,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Lock Status Info
                  if (tontine.isLocked)
                    Card(
                      color: Colors.orange.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'ℹ️ Tontine Bloquée',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Temps restant: ${tontine.getTimeRemainingString()}',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: Colors.orange,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Débloquage prévu: ${tontine.lockEndDate?.toString().split(' ')[0] ?? 'N/A'}',
                              style: const TextStyle(fontSize: 12),
                            ),
                            const SizedBox(height: 12),
                            const Text(
                              '✗ Vous ne pouvez pas retirer vos fonds pendant cette période\n✗ Vous ne pouvez pas modifier la durée du blocage',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.red,
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              '✓ Vous pouvez ajouter des fonds',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.green,
                              ),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    Card(
                      color: Colors.green.shade50,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              '✓ Tontine Active',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                                color: Colors.green,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              tontine.balance <= 0
                                  ? 'Déposez d’abord des fonds dans la tontine avant de la bloquer.'
                                  : 'Vous pouvez bloquer ou ajouter des fonds à tout moment',
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ),
                  const SizedBox(height: 24),

                  // Action Buttons
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: tontineProvider.isLoading
                              ? null
                              : () => _showDepositDialog(),
                          icon: const Icon(Icons.arrow_forward),
                          label: const Text('Vers Épargne'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            backgroundColor: Colors.green,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: tontine.isLocked || tontine.balance <= 0 || tontineProvider.isLoading
                              ? null
                              : () => _showLockDialog(),
                          icon: const Icon(Icons.lock),
                          label: const Text('Bloquer'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            backgroundColor: tontine.isLocked ? Colors.grey : Colors.blue,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Transactions History
                  if (tontine.transactions.isNotEmpty)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Historique des transactions',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        ...tontine.transactions.map(
                          (transaction) => Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: transaction.type == 'DEPOSIT'
                                      ? Colors.green.shade100
                                      : Colors.blue.shade100,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(
                                  transaction.type == 'DEPOSIT'
                                      ? Icons.arrow_downward
                                      : Icons.trending_up,
                                  color: transaction.type == 'DEPOSIT'
                                      ? Colors.green
                                      : Colors.blue,
                                ),
                              ),
                              title: Text(
                                transaction.type == 'DEPOSIT'
                                    ? 'Dépôt depuis portefeuille principal'
                                    : 'Intérêt gagné',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    transaction.createdAt
                                        .toString()
                                        .split('T')[0],
                                    style: const TextStyle(fontSize: 12),
                                  ),
                                  if (transaction.description != null)
                                    Text(
                                      transaction.description!,
                                      style: const TextStyle(
                                        fontSize: 11,
                                        color: Colors.grey,
                                      ),
                                    ),
                                ],
                              ),
                              trailing: Text(
                                '${transaction.type == 'DEPOSIT' ? '+' : '+'}${transaction.amount.toStringAsFixed(0)} XOF',
                                style: TextStyle(
                                  color: transaction.type == 'DEPOSIT'
                                      ? Colors.green
                                      : Colors.blue,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
