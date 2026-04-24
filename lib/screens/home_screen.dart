import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../services/audit_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuditService>().loadDatasets();
    });
  }

  @override
  Widget build(BuildContext context) {
    final svc = context.watch<AuditService>();
    const teal = Color(0xFF0D9488);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: teal,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.balance, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 10),
            const Text(
              'FairSight',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        actions: [
          TextButton.icon(
            onPressed: () => context.go('/auto-scan'),
            icon: const Icon(Icons.auto_fix_high, color: Color(0xFF0D9488)),
            label: const Text(
              'Auto-Detect',
              style: TextStyle(color: Color(0xFF0D9488), fontWeight: FontWeight.w600),
            ),
          ),
          TextButton.icon(
            onPressed: () => context.go('/external-audit'),
            icon: const Icon(Icons.model_training, color: Colors.white),
            label: const Text(
              'Audit Model',
              style: TextStyle(color: Colors.white),
            ),
          ),
          TextButton.icon(
            onPressed: () => context.go('/audit'),
            icon: const Icon(Icons.play_arrow, color: Colors.white),
            label: const Text(
              'Manual Audit',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
      body: svc.loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Hero section ──────────────────────────────────
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(32),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0A1628),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'AI bias is not inevitable.',
                          style: Theme.of(context)
                              .textTheme
                              .headlineMedium
                              ?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'It is measurable. Flaggable. Fixable.',
                          style: TextStyle(
                            color: teal,
                            fontSize: 16,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            ElevatedButton.icon(
                              onPressed: () => context.go('/auto-scan'),
                              icon: const Icon(Icons.auto_fix_high, size: 18),
                              label: const Text(
                                'Auto-Detect Bias',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: teal,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 20,
                                  vertical: 14,
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            OutlinedButton.icon(
                              onPressed: () => context.go('/audit'),
                              icon: const Icon(Icons.tune, size: 18, color: Colors.white70),
                              label: const Text(
                                'Manual Audit',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                              style: OutlinedButton.styleFrom(
                                side: const BorderSide(color: Colors.white30),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 20,
                                  vertical: 14,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 28),

                  // ── Stats row ─────────────────────────────────────
                  const Row(
                    children: [
                      _StatCard('Auto', 'Bias detection', teal),
                      SizedBox(width: 12),
                      _StatCard('4', 'Fairness metrics', Color(0xFF3B82F6)),
                      SizedBox(width: 12),
                      _StatCard('Model', 'Audit support', Color(0xFF8B5CF6)),
                    ],
                  ),
                  const SizedBox(height: 28),

                  // ── Available datasets ────────────────────────────
                  Text(
                    'Available Datasets',
                    style: Theme.of(context)
                        .textTheme
                        .titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 12),

                  if (svc.error != null)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEF2F2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        svc.error!,
                        style: const TextStyle(color: Color(0xFFB91C1C)),
                      ),
                    )
                  else
                    GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate:
                          const SliverGridDelegateWithMaxCrossAxisExtent(
                        maxCrossAxisExtent: 280,
                        childAspectRatio: 1.6,
                        crossAxisSpacing: 12,
                        mainAxisSpacing: 12,
                      ),
                      itemCount: svc.datasets.length,
                      itemBuilder: (ctx, i) {
                        final ds = svc.datasets[i];
                        final isHigh = ds['risk'] == 'high';
                        return GestureDetector(
                          onTap: () => context.go('/audit'),
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: const Color(0xFFE2E8F0),
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.05),
                                  blurRadius: 8,
                                ),
                              ],
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  ds['name'] ?? '',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 14,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  (ds['domain'] ?? '')
                                      .toString()
                                      .replaceAll('_', ' '),
                                  style: const TextStyle(
                                    color: Color(0xFF64748B),
                                    fontSize: 12,
                                  ),
                                ),
                                const Spacer(),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 3,
                                  ),
                                  decoration: BoxDecoration(
                                    color: isHigh
                                        ? const Color(0xFFFEF2F2)
                                        : const Color(0xFFFFFBEB),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    '${ds['risk']} risk',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w500,
                                      color: isHigh
                                          ? const Color(0xFFB91C1C)
                                          : const Color(0xFFB45309),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                ],
              ),
            ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String value;
  final String label;
  final Color color;

  const _StatCard(this.value, this.label, this.color);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                color: Color(0xFF64748B),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
