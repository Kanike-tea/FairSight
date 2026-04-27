import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import '../services/audit_service.dart';

class AdvancedAuditScreen extends StatefulWidget {
  const AdvancedAuditScreen({super.key});

  @override
  State<AdvancedAuditScreen> createState() => _AdvancedAuditScreenState();
}

class _AdvancedAuditScreenState extends State<AdvancedAuditScreen> {
  // Dataset upload state (required)
  String? _datasetFileName;
  Uint8List? _datasetBytes;

  // Model upload state (optional)
  String? _modelFileName;
  Uint8List? _modelBytes;

  // Optional form fields
  final _targetColCtrl = TextEditingController();
  final _sensitiveColsCtrl = TextEditingController();

  bool _running = false;

  static const _teal = Color(0xFF0D9488);
  static const _dark = Color(0xFF0A1628);

  String interpretBias(double diff) {
    if (diff >= 0.5) return 'High bias detected';
    if (diff >= 0.2) return 'Moderate bias detected';
    return 'Low or no significant bias';
  }

  Color _interpretationColor(double diff) {
    if (diff >= 0.5) return const Color(0xFFEF4444); // red
    if (diff >= 0.2) return const Color(0xFFF59E0B); // amber
    return const Color(0xFF10B981); // green
  }

  @override
  void dispose() {
    _targetColCtrl.dispose();
    _sensitiveColsCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDataset() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
      withData: true,
    );
    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _datasetFileName = result.files.single.name;
        _datasetBytes = result.files.single.bytes!;
      });
    }
  }

  Future<void> _pickModel() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      withData: true,
    );
    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _modelFileName = result.files.single.name;
        _modelBytes = result.files.single.bytes!;
      });
    }
  }

  Future<void> _runAdvancedAudit() async {
    if (_datasetBytes == null || _datasetFileName == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please upload a dataset'),
          backgroundColor: Color(0xFFEF4444),
        ),
      );
      return;
    }
    setState(() => _running = true);

    final svc = context.read<AuditService>();
    await svc.fullAudit(
      datasetBytes: _datasetBytes!,
      datasetFilename: _datasetFileName!,
      modelBytes: _modelBytes,
      modelFilename: _modelFileName,
      targetColumn: _targetColCtrl.text.isNotEmpty ? _targetColCtrl.text : null,
      sensitiveColumns:
          _sensitiveColsCtrl.text.isNotEmpty ? _sensitiveColsCtrl.text : null,
    );

    if (mounted) setState(() => _running = false);
  }

  @override
  Widget build(BuildContext context) {
    final svc = context.watch<AuditService>();
    final res = svc.fullAuditResult;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: _dark,
        title: const Text('Advanced Audit', style: TextStyle(color: Colors.white)),
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
            // ── Upload / Inputs section (AutoScan-style hero) ──────
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
                  const Icon(Icons.analytics, color: _teal, size: 40),
                  const SizedBox(height: 12),
                  const Text(
                    'Advanced Audit (Full)',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload a CSV and optionally a model file.\nAdd target/sensitive columns for more precise results.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                  ),
                  const SizedBox(height: 18),

                  // Reuse file picker card pattern from ExternalAuditScreen
                  _filePickerCard(
                    label: 'Dataset (.csv) — required',
                    fileName: _datasetFileName,
                    icon: Icons.table_chart,
                    onPick: _pickDataset,
                  ),
                  const SizedBox(height: 12),
                  _filePickerCard(
                    label: 'Model file (.pkl / .joblib) — optional',
                    fileName: _modelFileName,
                    icon: Icons.psychology,
                    onPick: _pickModel,
                  ),
                  const SizedBox(height: 12),

                  TextField(
                    controller: _targetColCtrl,
                    decoration: InputDecoration(
                      labelText: 'Target column (optional)',
                      hintText: 'e.g., approved, label, outcome',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _sensitiveColsCtrl,
                    decoration: InputDecoration(
                      labelText: 'Sensitive columns (optional)',
                      hintText: 'comma-separated (e.g., gender,race,age)',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: (_datasetBytes != null && !_running)
                          ? _runAdvancedAudit
                          : null,
                      icon: _running
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.play_arrow),
                      label: Text(
                        _running ? 'Running…' : 'Run Advanced Audit',
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _teal,
                        foregroundColor: Colors.white,
                        disabledBackgroundColor: const Color(0xFFCBD5E1),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 14,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
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
                child: Text(
                  svc.error!,
                  style: const TextStyle(color: Color(0xFFB91C1C)),
                ),
              ),
            ],

            if (res != null) ...[
              const SizedBox(height: 24),
              _buildSummaryCard(res),
              const SizedBox(height: 16),
              _buildContextCard(res),
              const SizedBox(height: 16),
              _buildAnalysisCard(res),
            ],
          ],
        ),
      ),
    );
  }

  // ── Shared file picker card (from ExternalAuditScreen pattern) ───
  Widget _filePickerCard({
    required String label,
    required String? fileName,
    required IconData icon,
    required VoidCallback onPick,
  }) {
    return GestureDetector(
      onTap: onPick,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: fileName != null ? _teal : const Color(0xFFE2E8F0),
            width: fileName != null ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: fileName != null ? _teal : const Color(0xFF94A3B8)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
                  Text(
                    fileName ?? 'Tap to select file',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: fileName != null ? _teal : const Color(0xFF94A3B8),
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              fileName != null ? Icons.check_circle : Icons.add_circle_outline,
              color: fileName != null ? _teal : const Color(0xFFCBD5E1),
            ),
          ],
        ),
      ),
    );
  }

  // ── Summary card (AutoScan-style) ───────────────────────────────
  Widget _buildSummaryCard(Map<String, dynamic> res) {
    final summary = res['summary']?.toString() ?? 'Basic audit completed.';
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _dark,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle, color: _teal, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Summary',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  summary,
                  style: const TextStyle(
                    color: Color(0xFF94A3B8),
                    fontSize: 13,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Context card ────────────────────────────────────────────────
  Widget _buildContextCard(Map<String, dynamic> res) {
    final details = (res['details'] is Map) ? Map<String, dynamic>.from(res['details']) : <String, dynamic>{};
    final ctx = (details['context'] is Map) ? Map<String, dynamic>.from(details['context']) : <String, dynamic>{};
    final rep = (ctx['representation'] is Map) ? Map<String, dynamic>.from(ctx['representation']) : <String, dynamic>{};
    final qual = (ctx['qualification'] is Map) ? Map<String, dynamic>.from(ctx['qualification']) : <String, dynamic>{};
    final qualByGroup = (qual['qualification_rate_by_group'] is Map) ? Map<String, dynamic>.from(qual['qualification_rate_by_group']) : <String, dynamic>{};

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Context', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 10),

          // Qualification metadata
          _kvRow('Method', qual['method']?.toString() ?? '—'),
          _kvRow('Target column', qual['target_column']?.toString() ?? '—'),
          if (qual['baseline_column'] != null) _kvRow('Baseline column', qual['baseline_column']?.toString() ?? '—'),

          const SizedBox(height: 12),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: const Text('Representation', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
            children: rep.entries.map((e) {
              final sensCol = e.key.toString();
              final dist = (e.value is Map) ? Map<String, dynamic>.from(e.value) : <String, dynamic>{};
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _simpleMapBlock(
                  title: sensCol,
                  map: dist,
                  valueSuffix: '',
                ),
              );
            }).toList(),
          ),

          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: const Text('Qualification rate by group', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
            children: qualByGroup.entries.map((e) {
              final sensCol = e.key.toString();
              final dist = (e.value is Map) ? Map<String, dynamic>.from(e.value) : <String, dynamic>{};
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _simpleMapBlock(
                  title: sensCol,
                  map: dist,
                  valueSuffix: '',
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  // ── Analysis card ───────────────────────────────────────────────
  Widget _buildAnalysisCard(Map<String, dynamic> res) {
    final details = (res['details'] is Map) ? Map<String, dynamic>.from(res['details']) : <String, dynamic>{};
    final analysis = (details['analysis'] is Map) ? Map<String, dynamic>.from(details['analysis']) : <String, dynamic>{};

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Analysis', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 10),
          ...analysis.entries.map((e) {
            final sensCol = e.key.toString();
            final payload = (e.value is Map) ? Map<String, dynamic>.from(e.value) : <String, dynamic>{};
            final diffNum = payload['selection_rate_diff'];
            final diff = (diffNum is num) ? diffNum.toDouble() : 0.0;
            final diffValid = diffNum is num;
            final byGroup = (payload['selection_rate_by_group'] is Map)
                ? Map<String, dynamic>.from(payload['selection_rate_by_group'])
                : <String, dynamic>{};
            final interpText = interpretBias(diff);
            final interpColor = _interpretationColor(diff);

            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          sensCol,
                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: _teal.withValues(alpha: 0.10),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          diffValid ? 'diff: ${diff.toStringAsFixed(3)}' : 'diff: —',
                          style: const TextStyle(fontSize: 11, color: _teal, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    interpText,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: interpColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  _simpleMapBlock(title: 'Selection rate by group', map: byGroup, valueSuffix: ''),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _kvRow(String k, String v) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(k, style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
          ),
          Expanded(
            child: Text(v, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _simpleMapBlock({
    required String title,
    required Map<String, dynamic> map,
    required String valueSuffix,
  }) {
    final entries = map.entries.toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        if (entries.isEmpty)
          const Text('—', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12))
        else
          ...entries.map((e) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        e.key.toString(),
                        style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                      ),
                    ),
                    Text(
                      '${e.value}$valueSuffix',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              )),
      ],
    );
  }
}

