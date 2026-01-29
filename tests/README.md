# G-Utils Test Suite

Comprehensive test suite for gutils CLI tools implementing the "Logic + Boundaries" testing strategy.

## Overview

This test suite validates:
- **Business Logic**: Internal functions, security filters, output formatting
- **Boundaries**: Mocked external calls with argument verification (yt-dlp, Whisper, Gemini APIs)
- **CLI Wiring**: Command registration and parameter passing

## Running Tests

### Run all tests
```bash
pytest -v tests/
```

### Run specific test file
```bash
pytest tests/test_dictation.py -v
```

### Run with coverage
```bash
pytest --cov=gutils --cov-report=html tests/
```

### Run specific test class or function
```bash
pytest tests/test_dictation.py::TestSecurityFilter::test_dangerous_rm_command -v
```

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── assets/               # Test files (tiny.pdf, dummy.wav)
├── test_core.py          # Config, I/O, and logging tests
├── test_tube.py          # YouTube download tests
├── test_audio.py         # Audio transcription tests
├── test_dictation.py     # Dictation and security filter tests (CRITICAL)
├── test_pdf.py           # PDF processing tests
└── test_image.py         # QR code and AI image generation tests
```

## Key Fixtures

### `temp_config`
Provides a clean Config instance with temporary directories for each test.

### `mock_stdin`
Helper to simulate piping input via stdin.

### `sample_assets`
Path to the `tests/assets/` directory containing test files.

### `temp_output_dir`
Temporary directory for test outputs that's automatically cleaned up.

## Critical Tests

### Security Filter (test_dictation.py)
Tests the command injection prevention system:
- Dangerous commands (rm, sudo, etc.) are blocked
- Safe text passes through
- Case-insensitive detection

### Format Validation (test_audio.py, test_pdf.py)
Verifies JSON output is valid and matches expected schema.

### Backend Selection (test_audio.py)
Ensures correct backend (OpenAI Whisper vs MLX Whisper) is loaded based on flags.

## CI/CD

Tests run automatically on:
- Push to main or feature branches
- Pull requests

Tested on:
- Ubuntu Latest (Python 3.10, 3.11)
- macOS Latest (Python 3.10, 3.11)

## Adding New Tests

1. Create test file: `tests/test_<module>.py`
2. Use fixtures from `conftest.py`
3. Mock external dependencies (APIs, file I/O, heavy models)
4. Verify arguments passed to mocks, not just that they were called
5. Test both success and failure cases

## Test Philosophy

**Mock external dependencies, test our code:**
- Mock: API calls, model loading, file downloads
- Don't Mock: Our business logic, security filters, format converters

**Verify the right thing happened:**
- Bad: `assert mock.called`
- Good: `assert mock.called_with(expected_args)`

**Keep tests fast:**
- No actual downloads
- No GPU operations
- No API calls
- Use lightweight fixtures
