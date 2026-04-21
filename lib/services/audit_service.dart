import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:cloud_firestore/cloud_firestore.dart';

/// Base URL for the FairSight API backend.
/// Override via `--dart-define=API_URL=https://your-cloud-run-url`
const String _apiBase = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://localhost:8000',
);

/// Represents a single bias audit job.
class AuditJob {
  final String jobId;
  final String datasetId;
  final List<String> sensitiveAttrs;
  String status;
  int progress;
  Map<String, dynamic>? result;

  AuditJob({
    required this.jobId,
    required this.datasetId,
    required this.sensitiveAttrs,
    this.status = 'queued',
    this.progress = 0,
    this.result,
  });
}

/// Service layer handling all API communication and Firestore persistence.
///
/// Provides dataset listing, audit orchestration (start → poll → result),
/// AI report generation via Gemini, and bias mitigation projection.
class AuditService extends ChangeNotifier {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  List<Map<String, dynamic>> datasets = [];
  AuditJob? currentJob;
  String? reportContent;
  bool loading = false;
  String? error;

  // ── Load available datasets ─────────────────────────────────────
  Future<void> loadDatasets() async {
    loading = true;
    notifyListeners();

    try {
      final res = await http.get(Uri.parse('$_apiBase/api/datasets'));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        datasets = List<Map<String, dynamic>>.from(data['datasets']);
      }
    } catch (e) {
      error = 'Cannot connect to API: $e';
    }

    loading = false;
    notifyListeners();
  }

  // ── Run a bias audit ────────────────────────────────────────────
  Future<void> startAudit({
    required String datasetId,
    required List<String> sensitiveAttributes,
    required String targetColumn,
    String? predictionColumn,
  }) async {
    loading = true;
    error = null;
    reportContent = null;
    notifyListeners();

    try {
      final res = await http.post(
        Uri.parse('$_apiBase/api/audit'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'dataset_id': datasetId,
          'sensitive_attributes': sensitiveAttributes,
          'target_column': targetColumn,
          if (predictionColumn != null) 'prediction_column': predictionColumn,
        }),
      );

      if (res.statusCode == 202) {
        final data = jsonDecode(res.body);
        currentJob = AuditJob(
          jobId: data['job_id'],
          datasetId: datasetId,
          sensitiveAttrs: sensitiveAttributes,
        );

        // Persist to Firestore for audit trail
        await _db.collection('audits').doc(data['job_id']).set({
          'job_id': data['job_id'],
          'dataset_id': datasetId,
          'sensitive_attrs': sensitiveAttributes,
          'target_column': targetColumn,
          'status': 'queued',
          'created_at': FieldValue.serverTimestamp(),
        });

        _pollStatus(data['job_id']);
      } else {
        error = 'Failed to start audit: ${res.body}';
      }
    } catch (e) {
      error = 'Network error: $e';
    }

    loading = false;
    notifyListeners();
  }

  // ── Poll job status ─────────────────────────────────────────────
  void _pollStatus(String jobId) async {
    while (true) {
      await Future.delayed(const Duration(seconds: 2));

      try {
        final res = await http.get(
          Uri.parse('$_apiBase/api/audit/$jobId/status'),
        );

        if (res.statusCode == 200) {
          final data = jsonDecode(res.body);
          currentJob?.status = data['status'];
          currentJob?.progress = data['progress'] ?? 0;
          notifyListeners();

          if (data['status'] == 'complete') {
            await _fetchResult(jobId);
            break;
          }
          if (data['status'] == 'failed') {
            error = data['error'] ?? 'Audit failed';
            break;
          }
        }
      } catch (e) {
        error = 'Polling error: $e';
        break;
      }
    }
    notifyListeners();
  }

  // ── Fetch completed result ──────────────────────────────────────
  Future<void> _fetchResult(String jobId) async {
    final res = await http.get(
      Uri.parse('$_apiBase/api/audit/$jobId/result'),
    );

    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      currentJob?.result = data;

      // Update Firestore audit record
      await _db.collection('audits').doc(jobId).update({
        'status': 'complete',
        'fairness_score': data['fairness_score'],
        'risk_level': data['risk_level'],
        'completed_at': FieldValue.serverTimestamp(),
      });
    }
    notifyListeners();
  }

  // ── Generate AI report via Gemini ───────────────────────────────
  Future<void> generateReport() async {
    if (currentJob == null) return;
    loading = true;
    notifyListeners();

    try {
      final res = await http.post(
        Uri.parse('$_apiBase/api/report'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'audit_id': currentJob!.jobId}),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        reportContent = data['content'];

        // Store report in Firestore
        await _db.collection('reports').add({
          'audit_id': currentJob!.jobId,
          'content': reportContent,
          'created_at': FieldValue.serverTimestamp(),
        });
      }
    } catch (e) {
      error = 'Report generation failed: $e';
    }

    loading = false;
    notifyListeners();
  }

  // ── Apply mitigation strategies ─────────────────────────────────
  Future<Map<String, dynamic>?> applyMitigation(
    List<String> strategies,
  ) async {
    if (currentJob == null) return null;

    try {
      final res = await http.post(
        Uri.parse('$_apiBase/api/mitigate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'audit_id': currentJob!.jobId,
          'strategies': strategies,
        }),
      );
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (e) {
      error = 'Mitigation failed: $e';
    }
    return null;
  }

  // ── Audit history stream from Firestore ─────────────────────────
  Stream<QuerySnapshot> auditHistory() {
    return _db
        .collection('audits')
        .orderBy('created_at', descending: true)
        .limit(20)
        .snapshots();
  }
}
