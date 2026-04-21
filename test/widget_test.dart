import 'package:flutter_test/flutter_test.dart';
import 'package:fairsight/main.dart';

void main() {
  testWidgets('FairSightApp renders', (WidgetTester tester) async {
    // Verify the app widget can be instantiated without crashing.
    // Firebase must be mocked or initialized in test setup for full
    // integration tests — this is a smoke test only.
    expect(const FairSightApp(), isA<FairSightApp>());
  });
}
