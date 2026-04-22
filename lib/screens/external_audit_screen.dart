import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ExternalAuditScreen extends StatefulWidget {
  const ExternalAuditScreen({super.key});

  @override
  State<ExternalAuditScreen> createState() => _ExternalAuditScreenState();
}

class _ExternalAuditScreenState extends State<ExternalAuditScreen> {
  final _urlController = TextEditingController(text: "https://example-model-api.com/predict");
  final _dataController = TextEditingController(text: '{\n  "age": 35,\n  "income": 50000,\n  "credit_score": 650\n}');
  String _result = "";
  bool _isLoading = false;

  static const _teal = Color(0xFF0D9488);

  Future<void> _runAudit() async {
    setState(() {
      _isLoading = true;
      _result = "";
    });
    try {
      final response = await http.post(
        Uri.parse(_urlController.text),
        headers: {"Content-Type": "application/json"},
        body: _dataController.text,
      );
      setState(() {
        _result = "Status: ${response.statusCode}\n\nResponse:\n${response.body}";
      });
    } catch (e) {
      setState(() {
        _result = "Error: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        title: const Text('Audit External Model', style: TextStyle(color: Colors.white)),
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
            const Text(
              'Test External Endpoints',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Pass sample data to an external URL to test live predictions.',
              style: TextStyle(color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'External Model URL',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _dataController,
              maxLines: 5,
              decoration: const InputDecoration(
                labelText: 'JSON Payload',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _runAudit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: _teal,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Text('Run Live Prediction', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 24),
            if (_result.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Result', style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(_result, style: const TextStyle(fontFamily: 'monospace')),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
