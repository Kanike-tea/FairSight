import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../services/audit_service.dart';

class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  static const _teal = Color(0xFF0D9488);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final svc = context.read<AuditService>();
      if (svc.reportContent == null && svc.currentJob != null) {
        svc.generateReport();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final svc = context.watch<AuditService>();

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        title: const Text(
          'AI Fairness Report',
          style: TextStyle(color: Colors.white),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => context.go('/results'),
        ),
        actions: [
          if (svc.reportContent != null)
            IconButton(
              icon: const Icon(Icons.share, color: Colors.white),
              tooltip: 'Share report',
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Report sharing coming soon')),
                );
              },
            ),
        ],
      ),
      body: _buildBody(svc),
    );
  }

  Widget _buildBody(AuditService svc) {
    // Loading state
    if (svc.loading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 20),
            Text(
              'Generating AI report with Gemini…',
              style: TextStyle(fontSize: 15, color: Color(0xFF64748B)),
            ),
            SizedBox(height: 8),
            Text(
              'Analyzing metrics and producing recommendations',
              style: TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
            ),
          ],
        ),
      );
    }

    // Error state
    if (svc.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Color(0xFFEF4444)),
              const SizedBox(height: 16),
              Text(
                svc.error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFFB91C1C)),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => svc.generateReport(),
                style: ElevatedButton.styleFrom(backgroundColor: _teal),
                child: const Text('Retry', style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ),
      );
    }

    // No report yet
    if (svc.reportContent == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.description_outlined,
              size: 64,
              color: Color(0xFFCBD5E1),
            ),
            const SizedBox(height: 16),
            const Text(
              'No report generated yet',
              style: TextStyle(fontSize: 16, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: svc.currentJob != null
                  ? () => svc.generateReport()
                  : null,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('Generate with Gemini'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _teal,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 14,
                ),
              ),
            ),
          ],
        ),
      );
    }

    // Report content
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _teal.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: _teal.withValues(alpha: 0.3)),
            ),
            child: const Row(
              children: [
                Icon(Icons.auto_awesome, color: _teal, size: 20),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Generated by Google Gemini via Vertex AI',
                    style: TextStyle(
                      color: _teal,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Report body
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: SelectableText(
              svc.reportContent!,
              style: const TextStyle(
                fontSize: 14,
                height: 1.7,
                color: Color(0xFF1E293B),
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Actions row
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => svc.generateReport(),
                  icon: const Icon(Icons.refresh, size: 18),
                  label: const Text('Regenerate'),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: _teal),
                    foregroundColor: _teal,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => context.go('/results'),
                  icon: const Icon(Icons.arrow_back, size: 18),
                  label: const Text('Back to Results'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _teal,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
