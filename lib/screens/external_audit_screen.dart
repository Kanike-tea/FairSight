import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import '../services/audit_service.dart';

class ExternalAuditScreen extends StatefulWidget {
  const ExternalAuditScreen({super.key});
  @override
  State<ExternalAuditScreen> createState() => _ExternalAuditScreenState();
}

class _ExternalAuditScreenState extends State<ExternalAuditScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  // Model file upload state
  String? _modelFileName;
  List<int>? _modelBytes;
  String? _testFileName;
  List<int>? _testBytes;
  final _targetColCtrl = TextEditingController();

  // API endpoint state
  final _urlCtrl = TextEditingController(text: 'https://');
  final _responseKeyCtrl = TextEditingController(text: 'prediction');
  String? _selectedDatasetId;

  bool _auditing = false;

  static const _teal = Color(0xFF0D9488);
  static const _dark = Color(0xFF0A1628);

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _targetColCtrl.dispose();
    _urlCtrl.dispose();
    _responseKeyCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickModel() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.any,
      withData: true,
    );
    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _modelFileName = result.files.single.name;
        _modelBytes = result.files.single.bytes!.toList();
      });
    }
  }

  Future<void> _pickTestData() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['csv'],
      withData: true,
    );
    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _testFileName = result.files.single.name;
        _testBytes = result.files.single.bytes!.toList();
      });
    }
  }

  Future<void> _runModelAudit() async {
    if (_modelBytes == null || _testBytes == null) return;
    setState(() => _auditing = true);

    final svc = context.read<AuditService>();
    await svc.auditModel(
      modelBytes: _modelBytes! as dynamic,
      modelFilename: _modelFileName!,
      testDataBytes: _testBytes! as dynamic,
      testDataFilename: _testFileName!,
      targetColumn: _targetColCtrl.text.isNotEmpty ? _targetColCtrl.text : null,
    );

    if (mounted) setState(() => _auditing = false);
  }

  Future<void> _runEndpointAudit() async {
    if (_selectedDatasetId == null || _urlCtrl.text.isEmpty) return;
    setState(() => _auditing = true);

    final svc = context.read<AuditService>();
    await svc.auditEndpoint(
      endpointUrl: _urlCtrl.text,
      datasetId: _selectedDatasetId!,
      responseKey: _responseKeyCtrl.text.isNotEmpty ? _responseKeyCtrl.text : 'prediction',
    );

    if (mounted) setState(() => _auditing = false);
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

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: _dark,
        title: const Text('Audit Model for Bias', style: TextStyle(color: Colors.white)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => context.go('/'),
        ),
        bottom: TabBar(
          controller: _tabCtrl,
          indicatorColor: _teal,
          labelColor: Colors.white,
          unselectedLabelColor: const Color(0xFF94A3B8),
          tabs: const [
            Tab(icon: Icon(Icons.upload_file), text: 'Upload Model'),
            Tab(icon: Icon(Icons.api), text: 'API Endpoint'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          _buildModelUploadTab(svc),
          _buildEndpointTab(svc),
        ],
      ),
    );
  }

  // ── Tab 1: Upload Model File ──────────────────────────
  Widget _buildModelUploadTab(AuditService svc) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF0A1628), Color(0xFF1E293B)]),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Column(
              children: [
                Icon(Icons.model_training, color: _teal, size: 36),
                SizedBox(height: 8),
                Text('Model Bias Audit', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                SizedBox(height: 4),
                Text(
                  'Upload your trained model (.pkl / .joblib)\nand a test dataset to detect bias.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Model file picker
          _filePickerCard(
            label: 'Model File (.pkl / .joblib)',
            fileName: _modelFileName,
            icon: Icons.psychology,
            onPick: _pickModel,
          ),
          const SizedBox(height: 12),

          // Test data picker
          _filePickerCard(
            label: 'Test Dataset (.csv)',
            fileName: _testFileName,
            icon: Icons.table_chart,
            onPick: _pickTestData,
          ),
          const SizedBox(height: 12),

          // Target column (optional)
          TextField(
            controller: _targetColCtrl,
            decoration: InputDecoration(
              labelText: 'Target column (optional)',
              hintText: 'e.g., approved, income, label',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            ),
          ),
          const SizedBox(height: 20),

          // Run button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: (_modelBytes != null && _testBytes != null && !_auditing) ? _runModelAudit : null,
              icon: _auditing
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.play_arrow),
              label: Text(_auditing ? 'Auditing Model…' : 'Run Model Bias Audit'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _teal, foregroundColor: Colors.white,
                disabledBackgroundColor: const Color(0xFFCBD5E1),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),

          if (svc.error != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: const Color(0xFFFEF2F2), borderRadius: BorderRadius.circular(8)),
              child: Text(svc.error!, style: const TextStyle(color: Color(0xFFB91C1C), fontSize: 12)),
            ),
          ],

          if (svc.modelAuditResult != null) ...[
            const SizedBox(height: 24),
            _buildAuditResults(svc.modelAuditResult!),
          ],
        ],
      ),
    );
  }

  // ── Tab 2: API Endpoint ───────────────────────────────
  Widget _buildEndpointTab(AuditService svc) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF0A1628), Color(0xFF1E293B)]),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Column(
              children: [
                Icon(Icons.cloud_outlined, color: _teal, size: 36),
                SizedBox(height: 8),
                Text('API Endpoint Audit', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                SizedBox(height: 4),
                Text(
                  'Point to your model API. FairSight will\nprobe it with varied inputs to detect bias.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          TextField(
            controller: _urlCtrl,
            decoration: InputDecoration(
              labelText: 'Model API Endpoint URL',
              prefixIcon: const Icon(Icons.link),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            ),
          ),
          const SizedBox(height: 12),

          TextField(
            controller: _responseKeyCtrl,
            decoration: InputDecoration(
              labelText: 'Response JSON key for prediction',
              hintText: 'prediction',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            ),
          ),
          const SizedBox(height: 16),

          const Text('Test Dataset', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 8),
          if (svc.datasets.isEmpty)
            const Text('Loading datasets…', style: TextStyle(color: Color(0xFF94A3B8)))
          else
            Wrap(
              spacing: 8, runSpacing: 8,
              children: svc.datasets.map((ds) {
                final id = ds['id'] as String? ?? '';
                final selected = _selectedDatasetId == id;
                return ChoiceChip(
                  label: Text(ds['name'] ?? id),
                  selected: selected,
                  onSelected: (_) => setState(() => _selectedDatasetId = id),
                  selectedColor: _teal.withOpacity(0.15),
                );
              }).toList(),
            ),
          const SizedBox(height: 20),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: (_selectedDatasetId != null && _urlCtrl.text.isNotEmpty && !_auditing) ? _runEndpointAudit : null,
              icon: _auditing
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.radar),
              label: Text(_auditing ? 'Probing Endpoint…' : 'Audit Endpoint'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _teal, foregroundColor: Colors.white,
                disabledBackgroundColor: const Color(0xFFCBD5E1),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),

          if (svc.modelAuditResult != null) ...[
            const SizedBox(height: 24),
            _buildAuditResults(svc.modelAuditResult!),
          ],
        ],
      ),
    );
  }

  // ── Shared file picker card ───────────────────────────
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
                  Text(fileName ?? 'Tap to select file', style: TextStyle(fontWeight: FontWeight.w600, color: fileName != null ? _teal : const Color(0xFF94A3B8))),
                ],
              ),
            ),
            Icon(fileName != null ? Icons.check_circle : Icons.add_circle_outline, color: fileName != null ? _teal : const Color(0xFFCBD5E1)),
          ],
        ),
      ),
    );
  }

  // ── Audit results display ─────────────────────────────
  Widget _buildAuditResults(Map<String, dynamic> result) {
    final summary = result['summary'] as Map<String, dynamic>? ?? {};
    final score = summary['overall_fairness_score'] as int? ?? 0;
    final risk = summary['overall_risk_level'] as String? ?? 'unknown';
    final heatmap = result['bias_heatmap'] as List? ?? [];
    final auditType = result['audit_type'] as String? ?? '';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(color: _dark, borderRadius: BorderRadius.circular(16)),
          child: Row(
            children: [
              SizedBox(
                width: 70, height: 70,
                child: Stack(alignment: Alignment.center, children: [
                  CircularProgressIndicator(value: score / 100, strokeWidth: 7, backgroundColor: Colors.white24, valueColor: AlwaysStoppedAnimation(_scoreColor(score))),
                  Text('$score', style: TextStyle(color: _scoreColor(score), fontSize: 22, fontWeight: FontWeight.bold)),
                ]),
              ),
              const SizedBox(width: 16),
              Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    auditType == 'model_file' ? 'Model Bias Score' : 'Endpoint Bias Score',
                    style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: _riskColor(risk).withOpacity(0.2), borderRadius: BorderRadius.circular(20)),
                    child: Text('$risk risk', style: TextStyle(color: _riskColor(risk), fontSize: 12, fontWeight: FontWeight.w600)),
                  ),
                ],
              )),
            ],
          ),
        ),

        // Heatmap
        if (heatmap.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text('Bias by Attribute', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 8),
          ...heatmap.map((h) {
            final attr = h['attribute'] as String? ?? '';
            final s = h['fairness_score'] as int? ?? 0;
            final biased = h['is_biased'] as bool? ?? false;
            return Container(
              margin: const EdgeInsets.only(bottom: 6),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: biased ? const Color(0xFFFEF2F2) : const Color(0xFFF0FDF4),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(children: [
                Icon(biased ? Icons.warning_rounded : Icons.check_circle, size: 18, color: biased ? const Color(0xFFEF4444) : const Color(0xFF10B981)),
                const SizedBox(width: 8),
                Expanded(child: Text(attr, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13))),
                Text('$s/100', style: TextStyle(fontWeight: FontWeight.bold, color: _scoreColor(s), fontSize: 13)),
              ]),
            );
          }),
        ],

        const SizedBox(height: 16),
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
    );
  }
}
