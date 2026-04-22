import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../services/audit_service.dart';

class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});

  @override
  State<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends State<AuditScreen> {
  String? _selectedDataset;
  final List<String> _selectedAttrs = [];
  String _targetColumn = 'two_year_recid';
  String _predictionColumn = 'score_binary';

  static const _teal = Color(0xFF0D9488);

  final Map<String, Map<String, dynamic>> _datasetDefaults = {
    'compas': {
      'attrs': ['race', 'sex'],
      'target': 'two_year_recid',
      'prediction': 'score_binary',
    },
    'adult_income': {
      'attrs': ['gender', 'race'],
      'target': 'income',
      'prediction': 'predicted_income',
    },
    'lending': {
      'attrs': ['race', 'gender'],
      'target': 'approved',
      'prediction': 'predicted_approved',
    },
    'healthcare': {
      'attrs': ['race', 'socioeconomic_status'],
      'target': 'high_need',
      'prediction': 'predicted_need',
    },
  };

  void _onDatasetChanged(String? dsId) {
    if (dsId == null) return;
    final defaults = _datasetDefaults[dsId];
    setState(() {
      _selectedDataset = dsId;
      _selectedAttrs
        ..clear()
        ..addAll(List<String>.from(defaults?['attrs'] ?? []));
      _targetColumn = defaults?['target'] ?? '';
      _predictionColumn = defaults?['prediction'] ?? '';
    });
  }

  Future<void> _runAudit() async {
    if (_selectedDataset == null) return;
    final svc = context.read<AuditService>();
    await svc.startAudit(
      datasetId: _selectedDataset!,
      sensitiveAttributes: _selectedAttrs,
      targetColumn: _targetColumn,
      predictionColumn: _predictionColumn,
    );
    if (mounted) context.go('/results');
  }

  @override
  Widget build(BuildContext context) {
    final svc = context.watch<AuditService>();

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        title: const Text(
          'Configure Audit',
          style: TextStyle(color: Colors.white),
        ),
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
            // ── Step 1: Choose dataset ──────────────────────────
            const _SectionHeader(number: '1', title: 'Choose a Dataset'),
            const SizedBox(height: 12),
            if (svc.datasets.isEmpty)
              const Text(
                'Loading datasets…',
                style: TextStyle(color: Color(0xFF94A3B8)),
              )
            else
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: svc.datasets.map((ds) {
                  final id = ds['id'] as String? ?? '';
                  final selected = _selectedDataset == id;
                  return ChoiceChip(
                    label: Text(ds['name'] ?? id),
                    selected: selected,
                    onSelected: (_) => _onDatasetChanged(id),
                    selectedColor: _teal.withOpacity(0.15),
                    labelStyle: TextStyle(
                      color: selected ? _teal : const Color(0xFF374151),
                      fontWeight:
                          selected ? FontWeight.w600 : FontWeight.normal,
                    ),
                  );
                }).toList(),
              ),
            const SizedBox(height: 28),

            // ── Step 2: Sensitive attributes ────────────────────
            const _SectionHeader(number: '2', title: 'Sensitive Attributes'),
            const SizedBox(height: 8),
            const Text(
              'Demographic columns to audit for bias.',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 13),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                'race',
                'sex',
                'gender',
                'age',
                'socioeconomic_status',
              ].map((attr) {
                final on = _selectedAttrs.contains(attr);
                return FilterChip(
                  label: Text(attr),
                  selected: on,
                  onSelected: (v) => setState(() {
                    v ? _selectedAttrs.add(attr) : _selectedAttrs.remove(attr);
                  }),
                  selectedColor: _teal.withOpacity(0.15),
                  checkmarkColor: _teal,
                );
              }).toList(),
            ),
            const SizedBox(height: 28),

            // ── Step 3: Column configuration ────────────────────
            const _SectionHeader(number: '3', title: 'Column Configuration'),
            const SizedBox(height: 12),
            _ConfigField(
              label: 'Target (ground truth) column',
              value: _targetColumn,
              onChanged: (v) => setState(() => _targetColumn = v),
            ),
            const SizedBox(height: 12),
            _ConfigField(
              label: 'Prediction column',
              value: _predictionColumn,
              onChanged: (v) => setState(() => _predictionColumn = v),
            ),
            const SizedBox(height: 32),

            // ── Run button ──────────────────────────────────────
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed:
                    (_selectedDataset != null && _selectedAttrs.isNotEmpty)
                        ? _runAudit
                        : null,
                icon: const Icon(Icons.play_arrow),
                label: const Text(
                  'Run Bias Audit',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _teal,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor: const Color(0xFFCBD5E1),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Reusable section header ───────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String number;
  final String title;

  const _SectionHeader({required this.number, required this.title});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: const Color(0xFF0D9488),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Center(
            child: Text(
              number,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Text(
          title,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}

// ── Reusable config text field ────────────────────────────────────
class _ConfigField extends StatelessWidget {
  final String label;
  final String value;
  final ValueChanged<String> onChanged;

  const _ConfigField({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      initialValue: value,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
      ),
      onChanged: onChanged,
    );
  }
}
