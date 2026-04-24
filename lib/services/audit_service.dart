import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:cloud_firestore/cloud_firestore.dart';

/// Base URL for the FairSight API backend.
/// Override via `--dart-define=API_URL=https://your-cloud-run-url`
const String _apiBase = String.fromEnvironment(
  'API_URL',
  defaultValue: 'https://fairsight-api-708608892119.us-central1.run.app',
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
/// AI report generation via Gemini, bias mitigation projection,
/// auto-scan bias detection, and model bias auditing.
class AuditService extends ChangeNotifier {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  List<Map<String, dynamic>> datasets = [];
  AuditJob? currentJob;
  String? reportContent;
  bool loading = false;
  String? error;

  // ── Auto-scan results ──────────────────────────────────────────
  Map<String, dynamic>? autoScanResult;

  // ── Model audit results ────────────────────────────────────────
  Map<String, dynamic>? modelAuditResult;

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

        // Persist to Firestore for audit trail (fire-and-forget)
        _db.collection('audits').doc(data['job_id']).set({
          'job_id': data['job_id'],
          'dataset_id': datasetId,
          'sensitive_attrs': sensitiveAttributes,
          'target_column': targetColumn,
          'status': 'queued',
          'created_at': FieldValue.serverTimestamp(),
        }).catchError((_) {});

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

      // Update Firestore audit record (fire-and-forget)
      _db.collection('audits').doc(jobId).update({
        'status': 'complete',
        'fairness_score': data['fairness_score'],
        'risk_level': data['risk_level'],
        'completed_at': FieldValue.serverTimestamp(),
      }).catchError((_) {});
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

        // Store report in Firestore (fire-and-forget)
        _db.collection('reports').add({
          'audit_id': currentJob!.jobId,
          'content': reportContent,
          'created_at': FieldValue.serverTimestamp(),
        }).then((_) {}).catchError((_) {});
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

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  //  AUTO-SCAN: Upload CSV and auto-detect bias
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Future<void> autoScanCSV(Uint8List fileBytes, String fileName) async {
    loading = true;
    error = null;
    autoScanResult = null;
    notifyListeners();

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_apiBase/api/auto-scan'),
      );
      request.files.add(http.MultipartFile.fromBytes(
        'file',
        fileBytes,
        filename: fileName,
      ));

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        autoScanResult = jsonDecode(response.body);

        // Also store as a currentJob so report generation works
        final jobId = autoScanResult?['job_id'];
        if (jobId != null) {
          currentJob = AuditJob(
            jobId: jobId,
            datasetId: autoScanResult?['dataset_id'] ?? 'auto_scan',
            sensitiveAttrs: List<String>.from(
              autoScanResult?['resolved_columns']?['sensitive_attributes'] ?? [],
            ),
            status: 'complete',
            progress: 100,
            result: autoScanResult,
          );
        }

        // Persist to Firestore (fire-and-forget)
        _db.collection('audits').add({
          'type': 'auto_scan',
          'filename': fileName,
          'status': 'complete',
          'overall_score': autoScanResult?['summary']?['overall_fairness_score'],
          'risk_level': autoScanResult?['summary']?['overall_risk_level'],
          'biased_attributes': autoScanResult?['summary']?['biased_attributes_found'],
          'created_at': FieldValue.serverTimestamp(),
        }).then((_) {}).catchError((_) {});
      } else {
        error = 'Auto-scan failed: ${response.body}';
      }
    } catch (e) {
      error = 'Auto-scan error: $e';
    }

    loading = false;
    notifyListeners();
  }

  // ── Auto-scan an existing/built-in dataset ──────────────────────
  Future<void> autoScanDataset(String datasetId) async {
    loading = true;
    error = null;
    autoScanResult = null;
    notifyListeners();

    try {
      final res = await http.post(
        Uri.parse('$_apiBase/api/auto-scan-dataset'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'dataset_id': datasetId}),
      );

      if (res.statusCode == 200) {
        autoScanResult = jsonDecode(res.body);

        final jobId = autoScanResult?['job_id'];
        if (jobId != null) {
          currentJob = AuditJob(
            jobId: jobId,
            datasetId: datasetId,
            sensitiveAttrs: List<String>.from(
              autoScanResult?['resolved_columns']?['sensitive_attributes'] ?? [],
            ),
            status: 'complete',
            progress: 100,
            result: autoScanResult,
          );
        }
      } else {
        error = 'Auto-scan failed: ${res.body}';
      }
    } catch (e) {
      error = 'Auto-scan error: $e';
    }

    loading = false;
    notifyListeners();
  }

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  //  MODEL AUDIT: Upload model + test data for bias detection
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Future<void> auditModel({
    required Uint8List modelBytes,
    required String modelFilename,
    required Uint8List testDataBytes,
    required String testDataFilename,
    String? targetColumn,
  }) async {
    loading = true;
    error = null;
    modelAuditResult = null;
    notifyListeners();

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$_apiBase/api/audit-model'),
      );

      request.files.add(http.MultipartFile.fromBytes(
        'model_file',
        modelBytes,
        filename: modelFilename,
      ));
      request.files.add(http.MultipartFile.fromBytes(
        'test_data_file',
        testDataBytes,
        filename: testDataFilename,
      ));

      if (targetColumn != null && targetColumn.isNotEmpty) {
        request.fields['target_column'] = targetColumn;
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        modelAuditResult = jsonDecode(response.body);

        final jobId = modelAuditResult?['job_id'];
        if (jobId != null) {
          currentJob = AuditJob(
            jobId: jobId,
            datasetId: 'model_audit',
            sensitiveAttrs: List<String>.from(
              modelAuditResult?['resolved_columns']?['sensitive_attributes'] ?? [],
            ),
            status: 'complete',
            progress: 100,
            result: modelAuditResult,
          );
        }

        // Persist to Firestore (fire-and-forget)
        _db.collection('audits').add({
          'type': 'model_audit',
          'model_filename': modelFilename,
          'test_data_filename': testDataFilename,
          'status': 'complete',
          'overall_score': modelAuditResult?['summary']?['overall_fairness_score'],
          'risk_level': modelAuditResult?['summary']?['overall_risk_level'],
          'created_at': FieldValue.serverTimestamp(),
        }).then((_) {}).catchError((_) {});
      } else {
        error = 'Model audit failed: ${response.body}';
      }
    } catch (e) {
      error = 'Model audit error: $e';
    }

    loading = false;
    notifyListeners();
  }

  // ── Audit external API endpoint ─────────────────────────────────
  Future<void> auditEndpoint({
    required String endpointUrl,
    required String datasetId,
    String? targetColumn,
    String responseKey = 'prediction',
  }) async {
    loading = true;
    error = null;
    modelAuditResult = null;
    notifyListeners();

    try {
      final res = await http.post(
        Uri.parse('$_apiBase/api/audit-endpoint'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'endpoint_url': endpointUrl,
          'dataset_id': datasetId,
          'target_column': targetColumn,
          'response_key': responseKey,
        }),
      );

      if (res.statusCode == 200) {
        modelAuditResult = jsonDecode(res.body);

        final jobId = modelAuditResult?['job_id'];
        if (jobId != null) {
          currentJob = AuditJob(
            jobId: jobId,
            datasetId: datasetId,
            sensitiveAttrs: List<String>.from(
              modelAuditResult?['resolved_columns']?['sensitive_attributes'] ?? [],
            ),
            status: 'complete',
            progress: 100,
            result: modelAuditResult,
          );
        }
      } else {
        error = 'Endpoint audit failed: ${res.body}';
      }
    } catch (e) {
      error = 'Endpoint audit error: $e';
    }

    loading = false;
    notifyListeners();
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
