# Opentrons Python API MCP Server

MCP server providing access to Opentrons Python API v2 documentation for LLM agents.

## Features

- Fetches and caches Opentrons Python API v2 documentation from https://docs.opentrons.com/v2/
- Full-text search using SQLite FTS5
- Automatic updates (checks daily for new docs)
- Provides tools for:
  - Semantic search across all documentation
  - API reference lookup
  - Code examples retrieval

## Installation

```bash
cd mcp_servers/opentrons-python-api-mcp-server
npm install
npm run build
```

## Tools

### `search_opentrons_docs`
Search Opentrons Python API documentation semantically.

**Parameters:**
- `query` (string, required): Search query
- `limit` (number, optional): Max results (default: 5, max: 20)

### `get_opentrons_api_reference`
Get specific API reference documentation.

**Parameters:**
- `topic` (string, required): API topic, class, or method name

### `get_opentrons_example`
Get code examples from documentation.

**Parameters:**
- `example_type` (string, required): Type of example (e.g., "transfer", "module", "labware")

### `update_opentrons_docs`
Manually trigger documentation update from source.

## Configuration

Add to `src/config/config.py`:

```python
"opentrons_python_api": {
    "transport": "stdio",
    "command": "node",
    "args": ["path/to/opentrons-python-api-mcp-server/dist/index.js"]
}
```

## Data Storage

Documentation is cached in `data/docs.db` (SQLite database with FTS5 index).

## License

MIT

