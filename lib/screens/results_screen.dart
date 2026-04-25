import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/audit_service.dart';

class ResultsScreen extends StatefulWidget {
  const ResultsScreen({super.key});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  final Set<String> _mitStrategies = {};
  Map<String, dynamic>? _mitResult;
  static const _teal = Color(0xFF0D9488);

  Color _scoreColor(int score) {
    if (score >= 65) return const Color(0xFF10B981);
    if (score >= 40) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  Color _severityColor(String s) {
    switch (s) {
      case 'critical':
        return const Color(0xFFEF4444);
      case 'warning':
        return const Color(0xFFF59E0B);
      default:
        return const Color(0xFF3B82F6);
    }
  }

  @override
  Widget build(BuildContext context) {
    final svc = context.watch<AuditService>();
    final job = svc.currentJob;

    // ── Still running or result not ready ─────────────────────────
    if (job == null || job.status != 'complete' || job.result == null) {
      return Scaffold(
        backgroundColor: const Color(0xFFF8FAFC),
        appBar: AppBar(
          backgroundColor: const Color(0xFF0A1628),
          title: const Text(
            'Audit Running',
            style: TextStyle(color: Colors.white),
          ),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: () => context.go('/'),
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 20),
              Text(
                '${job?.progress ?? 0}% complete',
                style: const TextStyle(
                  fontSize: 16,
                  color: Color(0xFF64748B),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                job?.status ?? 'queued',
                style: const TextStyle(color: Color(0xFF94A3B8)),
              ),
            ],
          ),
        ),
      );
    }

    // ── Results ready ───────────────────────────────────────────
    final result = job.result!;
    
    // Robust data extraction
    final metricsRaw = result['metrics'];
    final metrics = (metricsRaw is Map) ? Map<String, dynamic>.from(metricsRaw) : <String, dynamic>{};
    
    final flagsRaw = result['flags'];
    final flags = (flagsRaw is List) ? List<dynamic>.from(flagsRaw) : <dynamic>[];
    
    final groupsRaw = result['group_metrics'];
    final groups = (groupsRaw is Map) ? Map<String, dynamic>.from(groupsRaw) : <String, dynamic>{};
    
    final score = result['fairness_score'] as int? ?? 0;
    final risk = result['risk_level'] as String? ?? 'unknown';

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        title: const Text(
          'Audit Results v2.1',
          style: TextStyle(color: Colors.white),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => context.go('/'),
        ),
        actions: [
          TextButton.icon(
            onPressed: () => context.go('/report'),
            icon: const Icon(Icons.description, color: Colors.white),
            label: const Text(
              'Report',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Score hero ──────────────────────────────────────
            _buildScoreHero(result, score, risk),
            const SizedBox(height: 20),

            // ── Metrics grid ────────────────────────────────────
            _buildMetricsGrid(metrics),
            const SizedBox(height: 20),

            // ── Group breakdown chart ───────────────────────────
            if (groups.isNotEmpty) _buildGroupCharts(groups),

            // ── Flags ───────────────────────────────────────────
            if (flags.isNotEmpty) _buildFlags(flags),

            // ── Mitigation ──────────────────────────────────────
            _buildMitigationSection(svc),
            const SizedBox(height: 24),

            // ── Generate report button ──────────────────────────
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => context.go('/report'),
                icon: const Icon(Icons.description),
                label: const Text('Generate AI Report'),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: _teal),
                  foregroundColor: _teal,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Score hero card ─────────────────────────────────────────────
  Widget _buildScoreHero(Map<String, dynamic> result, int score, String risk) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0A1628),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            height: 80,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: score / 100,
                  strokeWidth: 8,
                  backgroundColor: Colors.white24,
                  valueColor: AlwaysStoppedAnimation(_scoreColor(score)),
                ),
                Text(
                  '$score',
                  style: TextStyle(
                    color: _scoreColor(score),
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  result['dataset_id']?.toString().toUpperCase() ?? '',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: _scoreColor(score).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '$risk risk',
                    style: TextStyle(
                      color: _scoreColor(score),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Attrs: ${(result['sensitive_attrs'] as List?)?.join(', ') ?? ''}',
                  style: const TextStyle(
                    color: Color(0xFF94A3B8),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Metrics grid ────────────────────────────────────────────────
  Widget _buildMetricsGrid(Map<String, dynamic> metrics) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      childAspectRatio: 1.8,
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      children: [
        _MetricCard(
          'Disparate Impact',
          (metrics['disparate_impact'] as num? ?? 0).toStringAsFixed(3),
          '≥ 0.80',
          (metrics['disparate_impact'] as num? ?? 0) >= 0.80,
        ),
        _MetricCard(
          'Parity Gap',
          '${(((metrics['demographic_parity_diff'] as num? ?? 0) * 100)).toStringAsFixed(1)}%',
          '≤ 5%',
          (metrics['demographic_parity_diff'] as num? ?? 1) <= 0.05,
        ),
        _MetricCard(
          'Equal Odds',
          '${(((metrics['equalized_odds_diff'] as num? ?? 0) * 100)).toStringAsFixed(1)}%',
          '≤ 10%',
          (metrics['equalized_odds_diff'] as num? ?? 1) <= 0.10,
        ),
        _MetricCard(
          'Accuracy',
          '${(((metrics['model_accuracy'] as num? ?? 0) * 100)).toStringAsFixed(1)}%',
          'Overall',
          null,
        ),
      ],
    );
  }

  // ── Group breakdown charts ──────────────────────────────────────
  Widget _buildGroupCharts(Map<String, dynamic> groups) {
    const chartColors = [
      _teal,
      Color(0xFF3B82F6),
      Color(0xFFF59E0B),
      Color(0xFFEF4444),
      Color(0xFF8B5CF6),
    ];

    // Build labels and values from the flat group_metrics structure
    // e.g. {"0": {"count": 2530, "outcome_rate": 0.34}, "1": {...}}
    final labels = <String>[];
    final values = <double>[];

    for (final entry in groups.entries) {
      labels.add('Group ${entry.key}');
      final v = entry.value;
      if (v is Map) {
        values.add(((v['outcome_rate'] as num?) ?? 0).toDouble());
      } else {
        values.add(0);
      }
    }

    if (labels.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Outcome Rate by Group',
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: SizedBox(
            height: labels.length * 36.0 + 20,
            child: BarChart(
              BarChartData(
                barGroups: List.generate(
                  labels.length,
                  (i) => BarChartGroupData(
                    x: i,
                    barRods: [
                      BarChartRodData(
                        toY: values[i] * 100,
                        color: chartColors[i % chartColors.length],
                        width: 18,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ],
                  ),
                ),
                titlesData: FlTitlesData(
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      getTitlesWidget: (v, _) {
                        final idx = v.toInt();
                        if (idx < 0 || idx >= labels.length) {
                          return const SizedBox.shrink();
                        }
                        return Text(
                          labels[idx],
                          style: const TextStyle(fontSize: 11),
                        );
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 36,
                      getTitlesWidget: (v, _) => Text(
                        '${v.toInt()}%',
                        style: const TextStyle(fontSize: 10),
                      ),
                    ),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                ),
                gridData: const FlGridData(drawVerticalLine: false),
                borderData: FlBorderData(show: false),
                maxY: 100,
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  // ── Flags list ──────────────────────────────────────────────────
  Widget _buildFlags(List<dynamic> flags) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Detected Issues',
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        ...flags.map((f) {
          final flag = f as Map<String, dynamic>;
          final sev = flag['severity'] as String? ?? 'info';
          final col = _severityColor(sev);
          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: col.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: col.withValues(alpha: 0.3)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(top: 5),
                  decoration: BoxDecoration(
                    color: col,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        flag['message'] ?? '',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: col,
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        flag['recommendation'] ?? '',
                        style: const TextStyle(
                          color: Color(0xFF64748B),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }),
        const SizedBox(height: 20),
      ],
    );
  }

  // ── Mitigation section ──────────────────────────────────────────
  Widget _buildMitigationSection(AuditService svc) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Apply Mitigation',
          style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            'reweight',
            'resample',
            'threshold',
            'adversarial',
            'fairloss',
          ].map((s) {
            final on = _mitStrategies.contains(s);
            return FilterChip(
              label: Text(s),
              selected: on,
              onSelected: (v) => setState(
                () => v ? _mitStrategies.add(s) : _mitStrategies.remove(s),
              ),
              selectedColor: _teal.withValues(alpha: 0.15),
              checkmarkColor: _teal,
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        if (_mitStrategies.isNotEmpty)
          ElevatedButton(
            onPressed: () async {
              final res =
                  await svc.applyMitigation(_mitStrategies.toList());
              setState(() => _mitResult = res);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: _teal,
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 12,
              ),
            ),
            child: const Text(
              'Apply Strategies',
              style: TextStyle(color: Colors.white),
            ),
          ),
        if (_mitResult != null) ...[
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: _teal.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: _teal.withValues(alpha: 0.3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Projected improvement',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: _teal,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Score: ${_mitResult!['projected']?['projected_score'] ?? 0}  /100',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Disparate Impact: ${((_mitResult!['projected']?['disparate_impact'] ?? 0) as num).toStringAsFixed(3)}',
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

// ── Metric card widget ────────────────────────────────────────────
class _MetricCard extends StatelessWidget {
  final String label;
  final String value;
  final String threshold;
  final bool? pass;

  const _MetricCard(this.label, this.value, this.threshold, this.pass);

  @override
  Widget build(BuildContext context) {
    final color = pass == null
        ? const Color(0xFF374151)
        : pass!
            ? const Color(0xFF10B981)
            : const Color(0xFFEF4444);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: Color(0xFF94A3B8),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            threshold,
            style: const TextStyle(
              fontSize: 10,
              color: Color(0xFF94A3B8),
            ),
          ),
        ],
      ),
    );
  }
}
