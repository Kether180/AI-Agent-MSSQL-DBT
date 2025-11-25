# Tests

This folder contains all test files for the SaaS platform.

## Test Files

### test_saas_platform.py
Comprehensive test suite for the SaaS platform components:
- Database connectivity
- Services layer (AuthService, UsageTracker, MigrationService)
- Flask application initialization
- FastAPI application initialization
- User authentication
- API key validation

**Run**: `python tests/test_saas_platform.py`

### test_langgraph_migration.py
Test suite for LangGraph agent workflows:
- Agent initialization
- Multi-agent orchestration
- Migration workflow execution
- State management

**Run**: `python tests/test_langgraph_migration.py`

## Running All Tests

```bash
# Run SaaS platform tests
python tests/test_saas_platform.py

# Run LangGraph migration tests
python tests/test_langgraph_migration.py
```

## Test Results

See [TEST_RESULTS.md](../TEST_RESULTS.md) for the latest test results and status.
