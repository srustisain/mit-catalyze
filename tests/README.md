# Tests Directory

This directory contains all test files for the Catalyze project.

## Test Files

### Opentrons Integration Tests
- **`test_opentrons_simple.py`** - Simple Opentrons protocol generation test based on specific criteria
- **`test_opentrons_integration.py`** - Integration tests for Opentrons code generation and validation
- **`test_opentrons_extensive.py`** - Comprehensive test suite for Opentrons functionality with performance benchmarks

### MCP (Model Context Protocol) Tests
- **`test_mcp_integration.py`** - Tests for MCP server integration (updated to use new PipelineManager)
- **`test_mcp_tools.py`** - Tests for available MCP tools

### Agent System Tests
- **`test_agent_system.py`** - Tests for the agent system architecture

### LLM Client Tests
- **`test_llm_client.py`** - Tests for LLM client functionality
- **`test_llm.py`** - Additional LLM-related tests

### PDF Processing Tests
- **`test_pdf_quick.py`** - Quick PDF processing tests
- **`test_pdf_simple.py`** - Simple PDF processing tests
- **`test_pdf_upload.py`** - PDF upload functionality tests
- **`test_pdf_processing.py`** - General PDF processing tests

### Development/Utility Tests
- **`test_pcr_fix.py`** - Test for PCR protocol generation fix
- **`test_mcp_client.py`** - Test MCP client tool inspection and methods
- **`test_opentrons_fix.py`** - Test Opentrons MCP tool calls fix
- **`test_guardrails_simple.py`** - Simple test for guardrails functionality
- **`test_improved_prompts.py`** - Test improved agent prompts and guardrails

## Test Results

- **`opentrons_test_results_*.json`** - JSON files containing detailed test results and timestamps

## Running Tests

To run specific tests:

```bash
# Run simple Opentrons tests
uv run python tests/test_opentrons_simple.py

# Run extensive Opentrons tests
uv run python tests/test_opentrons_extensive.py

# Run all tests in the directory
uv run python -m pytest tests/
```

## Test Structure

Each test file follows a consistent structure:
1. **Setup** - Initialize required components
2. **Test Execution** - Run specific test cases
3. **Validation** - Verify results against expected criteria
4. **Reporting** - Display results with detailed output

## Notes

- Tests use `asyncio` for asynchronous operations
- Opentrons tests require the `opentrons` package to be installed
- MCP tests require proper MCP server configuration
- Some tests may require API keys to be configured
