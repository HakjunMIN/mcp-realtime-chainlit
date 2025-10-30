# Testing Guide

This project includes a comprehensive unit test suite using pytest.

## Test Setup

### Installing Dependencies

```bash
# Install pytest and required plugins
python3 -m pip install pytest pytest-asyncio pytest-mock

# Install project dependencies
python3 -m pip install -r requirements.txt
# Or using uv
uv sync
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest test_realtime_utils.py
pytest test_mcp_service.py
pytest test_realtime_classes.py
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test Class or Method

```bash
# Run a specific test class
pytest test_realtime_utils.py::TestFloat16BitPCM

# Run a specific test method
pytest test_realtime_utils.py::TestFloat16BitPCM::test_basic_conversion
```

## Test Structure

### test_realtime_utils.py
Tests for utility functions in `realtime.py`:
- **TestFloat16BitPCM**: Tests for float32 to int16 PCM conversion
- **TestBase64ArrayConversion**: Tests for base64 encoding/decoding functions
- **TestMergeInt16Arrays**: Tests for int16 array merging function

### test_mcp_service.py
Tests for MCP (Model Context Protocol) service components:
- **TestMCPTool**: Tests for MCPTool dataclass
- **TestMCPServerClient**: Tests for MCP server client functionality
  - Server startup/shutdown
  - JSON-RPC request/response handling
  - Tool management
- **TestMCPService**: Tests for high-level MCP service functionality
  - Initialization and configuration
  - Tool response handling
  - Error handling

### test_realtime_classes.py
Tests for realtime API classes:
- **TestRealtimeEventHandler**: Tests for event handler functionality
  - Event registration and dispatching
  - Async event waiting
- **TestRealtimeConversation**: Tests for conversation management
  - Item creation, deletion, and updates
  - Text and audio delta processing
  - Speech start/stop handling
- **TestRealtimeClient**: Tests for realtime client
  - Session configuration
  - Tool addition/removal
  - System prompt and token limit updates

## Test Coverage

The current test suite includes:
- 70 unit tests
- Coverage of utility functions, MCP service, and realtime classes
- Testing of both synchronous and asynchronous functions
- Isolation of external dependencies through mocking

## Best Practices

1. **Isolated Tests**: Each test should run independently and not depend on other tests
2. **Use Fixtures**: Use pytest fixtures to set up test data and instances
3. **Mocking**: Mock external services and API calls to ensure fast and reliable tests
4. **Async Testing**: Use pytest-asyncio for testing asynchronous code
5. **Clear Naming**: Test names should clearly describe what is being tested

## CI/CD Integration

To integrate tests into your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    python -m pip install pytest pytest-asyncio pytest-mock
    pytest -v
```

## Adding New Tests

When adding new features:
1. Write tests in the corresponding test file (or create a new one)
2. Follow pytest naming conventions (`test_*.py`, `Test*` classes, `test_*` methods)
3. Use fixtures and mocking as needed
4. Ensure tests pass: `pytest -v`

## Troubleshooting

### When Tests Fail
```bash
# Run with full stack traces
pytest -v --tb=long

# Stop at first failure
pytest -x

# Re-run only failed tests
pytest --lf
```

### Module Not Found
Ensure all required dependencies are installed:
```bash
python3 -m pip install -r requirements.txt
```
