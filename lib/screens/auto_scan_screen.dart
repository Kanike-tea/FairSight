import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import '../services/audit_service.dart';

class AutoScanScreen extends StatefulWidget {
  const AutoScanScreen({super.key});
  @override
  State<AutoScanScreen> createState() => _AutoScanScreenState();
}

class _AutoScanScreenState extends State<AutoScanScreen> {
  String? _fileName;
  bool _scanning = false;

  static const _teal = Color(0xFF0D9488);
  static const _dark = Color(0xFF0A1628);

  Future<void> _pickAndScan() async {
    final svc = context.read<AuditService>();
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
      withData: true,
    );
    if (result == null || result.files.single.bytes == null) return;

    setState(() {
      _fileName = result.files.single.name;
      _scanning = true;
    });

    await svc.autoScanCSV(result.files.single.bytes!, _fileName!);

    if (mounted) setState(() => _scanning = false);
  }

  Color _scoreColor(int score) {
    if (score >= 65) return const Color(0xFF10B981);
    if (score >= 40) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  Color _riskColor(String risk) {
    switch (risk) {
      case 'critical': return const Color(0xFFEF4444);
      case 'medium': return const Color(0xFFF59E0B);
      default: return const Color(0xFF10B981);
    }
  }

  @override
  Widget build(BuildContext context) {
    final svc = context.watch<AuditService>();
    final scan = svc.autoScanResult;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: _dark,
        title: const Text('Auto-Detect Bias', style: TextStyle(color: Colors.white)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => context.go('/'),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Upload section ─────────────────────────
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF0A1628), Color(0xFF1E293B)],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  const Icon(Icons.auto_fix_high, color: _teal, size: 40),
                  const SizedBox(height: 12),
                  const Text(
                    'Automatic Bias Detection',
                    style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload a CSV — no need to specify attributes.\nFairSight auto-detects where bias exists.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton.icon(
                    onPressed: _scanning ? null : _pickAndScan,
                    icon: _scanning
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.upload_file),
                    label: Text(_scanning ? 'Scanning…' : (_fileName ?? 'Upload CSV Dataset')),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _teal,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ],
              ),
            ),

            if (svc.error != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF2F2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(svc.error!, style: const TextStyle(color: Color(0xFFB91C1C))),
              ),
            ],

            if (scan != null) ...[
              if (scan['status'] == 'success') ...[
                const SizedBox(height: 24),
                _buildSummaryCard(scan),
              ] else if (scan['status'] == 'warning') ...[
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: const Color(0xFFFEF3C7), borderRadius: BorderRadius.circular(12)),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Color(0xFFD97706)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          scan['message'] ?? 'Could not automatically detect bias in this dataset.',
                          style: const TextStyle(color: Color(0xFF92400E)),
                        ),
                      ),
                    ],
                  ),
                ),
              ] else if (scan['status'] == 'error') ...[
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: const Color(0xFFFEE2E2), borderRadius: BorderRadius.circular(12)),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Color(0xFFDC2626)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          scan['message'] ?? 'An error occurred during auto-scan.',
                          style: const TextStyle(color: Color(0xFF991B1B)),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              
              if (scan['status'] == 'success') ...[
                if (scan['ai_interpretation'] != null) ...[
                  const SizedBox(height: 20),
                  _buildAIAssessmentCard(scan['ai_interpretation']),
                ],
                const SizedBox(height: 20),
                _buildDetectedColumns(scan),
                const SizedBox(height: 20),
                _buildBiasHeatmap(scan),
                const SizedBox(height: 20),
                _buildAttributeDetails(scan),
                const SizedBox(height: 20),
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
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard(Map<String, dynamic> scan) {
    final summary = scan['summary'] as Map<String, dynamic>? ?? {};
    final score = summary['overall_fairness_score'] as int? ?? 0;
    final risk = summary['overall_risk_level'] as String? ?? 'unknown';
    final biasedCount = summary['biased_attributes_found'] as int? ?? 0;
    final totalScanned = summary['total_attributes_scanned'] as int? ?? 0;
    final mostBiased = summary['most_biased_attribute'] as String?;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _dark,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 80, height: 80,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: score / 100, strokeWidth: 8,
                  backgroundColor: Colors.white24,
                  valueColor: AlwaysStoppedAnimation(_scoreColor(score)),
                ),
                Text('$score', style: TextStyle(color: _scoreColor(score), fontSize: 24, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Overall Fairness', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: _riskColor(risk).withValues(alpha: 0.2), borderRadius: BorderRadius.circular(20)),
                  child: Text('$risk risk', style: TextStyle(color: _riskColor(risk), fontSize: 12, fontWeight: FontWeight.w600)),
                ),
                const SizedBox(height: 6),
                Text('$biasedCount of $totalScanned attributes biased', style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12)),
                if (mostBiased != null)
                  Text('Most biased: $mostBiased', style: const TextStyle(color: Color(0xFFF59E0B), fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIAssessmentCard(Map<String, dynamic> ai) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.psychology, color: _teal, size: 24),
              const SizedBox(width: 8),
              const Text('Gemma 4 AI Assessment', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: _dark)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: _teal.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
                child: const Text('Powered by Gemini API', style: TextStyle(fontSize: 10, color: _teal, fontWeight: FontWeight.w600)),
              )
            ],
          ),
          const SizedBox(height: 16),
          _aiSection('Interpretation', ai['overall_interpretation'] ?? '', Icons.analytics),
          const SizedBox(height: 12),
          _aiSection('Harm Assessment', ai['harm_assessment'] ?? '', Icons.warning_amber),
          const SizedBox(height: 12),
          _aiSection('Regulatory Risk', ai['regulatory_risk'] ?? '', Icons.gavel),
          if (ai['top_recommendation'] != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: const Color(0xFFF0FDF4), borderRadius: BorderRadius.circular(8)),
              child: Row(
                children: [
                  const Icon(Icons.lightbulb_outline, color: Color(0xFF10B981), size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Top Recommendation', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF065F46))),
                        const SizedBox(height: 4),
                        Text(ai['top_recommendation'], style: const TextStyle(fontSize: 13, color: Color(0xFF064E3B))),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _aiSection(String title, String content, IconData icon) {
    if (content.isEmpty) return const SizedBox.shrink();
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: const Color(0xFF64748B)),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF64748B))),
              const SizedBox(height: 2),
              Text(content, style: const TextStyle(fontSize: 13, color: _dark, height: 1.4)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildDetectedColumns(Map<String, dynamic> scan) {
    final resolved = scan['resolved_columns'] as Map<String, dynamic>? ?? {};
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Auto-Detected Column Roles', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 12),
          _roleChip('Target', resolved['target'] ?? '—', const Color(0xFF3B82F6)),
          const SizedBox(height: 6),
          _roleChip('Prediction', resolved['prediction'] ?? '—', const Color(0xFF8B5CF6)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6, runSpacing: 6,
            children: [
              const Text('Sensitive: ', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              ...(resolved['sensitive_attributes'] as List? ?? []).map((a) =>
                Chip(label: Text(a.toString(), style: const TextStyle(fontSize: 11)), backgroundColor: _teal.withValues(alpha: 0.1), padding: EdgeInsets.zero, materialTapTargetSize: MaterialTapTargetSize.shrinkWrap),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _roleChip(String role, String value, Color color) {
    return Row(children: [
      Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
      const SizedBox(width: 8),
      Text('$role: ', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
      Text(value, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w500)),
    ]);
  }

  Widget _buildBiasHeatmap(Map<String, dynamic> scan) {
    final heatmap = scan['bias_heatmap'] as List? ?? [];
    if (heatmap.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Bias Heatmap', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        const Text('Red = biased, Green = fair', style: TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
        const SizedBox(height: 12),
        ...heatmap.map((h) {
          final attr = h['attribute'] as String? ?? '';
          final score = h['fairness_score'] as int? ?? 0;
          final biased = h['is_biased'] as bool? ?? false;
          final di = (h['disparate_impact'] as num? ?? 0).toDouble();
          return Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: biased ? const Color(0xFFFEF2F2) : const Color(0xFFF0FDF4),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: biased ? const Color(0xFFFCA5A5) : const Color(0xFFA7F3D0)),
            ),
            child: Row(
              children: [
                Icon(biased ? Icons.warning_rounded : Icons.check_circle, color: biased ? const Color(0xFFEF4444) : const Color(0xFF10B981), size: 20),
                const SizedBox(width: 10),
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(attr, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    Text('DI: ${di.toStringAsFixed(3)} · Score: $score/100', style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                  ],
                )),
                Container(
                  width: 48, height: 28,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(color: _scoreColor(score).withValues(alpha: 0.15), borderRadius: BorderRadius.circular(6)),
                  child: Text('$score', style: TextStyle(fontWeight: FontWeight.bold, color: _scoreColor(score), fontSize: 13)),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  Widget _buildAttributeDetails(Map<String, dynamic> scan) {
    final results = scan['attribute_results'] as List? ?? [];
    if (results.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Per-Attribute Breakdown', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
        const SizedBox(height: 12),
        ...results.map((r) {
          final attr = r['attribute'] as String? ?? '';
          final score = r['fairness_score'] as int? ?? 0;
          final risk = r['risk_level'] as String? ?? '';
          final metrics = r['metrics'] as Map<String, dynamic>? ?? {};
          final flags = r['flags'] as List? ?? [];

          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
            child: ExpansionTile(
              title: Row(children: [
                Text(attr, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(color: _riskColor(risk).withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
                  child: Text('$score/100', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: _riskColor(risk))),
                ),
              ]),
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _metricRow('Disparate Impact', metrics['disparate_impact'], '>= 0.80'),
                      _metricRow('Demographic Parity', metrics['demographic_parity_diff'], '<= 0.05'),
                      _metricRow('Equalized Odds', metrics['equalized_odds_diff'], '<= 0.10'),
                      if (flags.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        ...flags.map((f) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(children: [
                            Icon(Icons.circle, size: 6, color: f['severity'] == 'critical' ? const Color(0xFFEF4444) : const Color(0xFFF59E0B)),
                            const SizedBox(width: 6),
                            Expanded(child: Text(f['message'] ?? '', style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)))),
                          ]),
                        )),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  Widget _metricRow(String label, dynamic value, String threshold) {
    final num v = (value is num) ? value : 0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
        const Spacer(),
        Text(v.toStringAsFixed(4), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
        const SizedBox(width: 8),
        Text('($threshold)', style: const TextStyle(fontSize: 10, color: Color(0xFF94A3B8))),
      ]),
    );
  }
}
