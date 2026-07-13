---
name: NexBridge conftest.py Fixtures
description: Available fixtures in backend/tests/conftest.py for reuse
type: reference
---

Location: `/Users/ljayarathne/Desktop/My Projects/nexbridge/backend/tests/conftest.py`

**Available fixtures:**

1. `registry` - ClassificationRegistry instance loaded from default registry.json
   - Use for: Tests that need field classification lookups
   - Returns: ClassificationRegistry()

**Note:** The conftest.py is minimal. For interpreter tests, state fixtures need to be created inline because they require specific XML payloads and target schemas for each test scenario.

**Common pattern:** Create state dictionaries inline in test functions using NexBridgeState TypedDict pattern with all required fields initialized.
