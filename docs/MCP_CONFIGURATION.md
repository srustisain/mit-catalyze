# MCP Server Configuration Guide

This guide explains how to configure MCP (Model Context Protocol) servers for the Catalyze application, supporting both HTTP-based and stdio-based transports.

## Overview

The Catalyze application now supports both types of MCP servers:
- **HTTP-based servers** using `streamable_http` transport
- **stdio-based servers** using `stdio` transport

## Configuration Format

The MCP servers are configured in `config.py` using the following format:

```python
MCP_SERVERS = {
    "server_name": {
        "transport": "streamable_http",  # or "stdio"
        # Additional configuration based on transport type
    }
}
```

## HTTP-based Servers (streamable_http)

For HTTP-based MCP servers, use the following configuration:

```python
"server_name": {
    "transport": "streamable_http",
    "url": "http://localhost:8000/mcp",
    # Optional: headers for authentication
    "headers": {
        "Authorization": "Bearer YOUR_TOKEN",
        "X-Custom-Header": "value"
    }
}
```

### Examples:
```python
"chembl": {
    "transport": "streamable_http",
    "url": "http://localhost:8000/mcp"
},
"literature": {
    "transport": "streamable_http",
    "url": "http://localhost:8001/mcp",
    "headers": {
        "Authorization": "Bearer token123"
    }
}
```

## Stdio-based Servers (stdio)

For stdio-based MCP servers, use the following configuration:

```python
"server_name": {
    "transport": "stdio",
    "command": "python",  # or "node", "ruby", etc.
    "args": ["/path/to/server.py", "--port", "8000"],
    # Optional: environment variables
    "env": {
        "VARIABLE": "value"
    }
}
```

### Examples:
```python
"local_math": {
    "transport": "stdio",
    "command": "python",
    "args": ["./examples/math_server.py"]
},
"local_chem": {
    "transport": "stdio",
    "command": "python",
    "args": ["./examples/chem_server.py"],
    "env": {
        "DEBUG": "true"
    }
}
```

## Complete Configuration Example

```python
MCP_SERVERS = {
    # HTTP-based servers
    "chembl": {
        "transport": "streamable_http",
        "url": "http://localhost:8000/mcp"
    },
    "literature": {
        "transport": "streamable_http",
        "url": "http://localhost:8001/mcp"
    },
    "knowledge_graph": {
        "transport": "streamable_http",
        "url": "http://localhost:8002/mcp"
    },
    
    # Stdio-based servers
    "local_math": {
        "transport": "stdio",
        "command": "python",
        "args": ["./examples/math_server.py"]
    },
    "local_chem": {
        "transport": "stdio",
        "command": "python",
        "args": ["./examples/chem_server.py"]
    }
}
```

## Creating MCP Servers

### HTTP-based Server Example
```python
# math_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### Stdio-based Server Example
```python
# math_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Testing Configuration

Run the test suite to verify your MCP server configuration:

```bash
python test_mcp_integration.py
```

This will test connectivity to all configured MCP servers and report any issues.

## Troubleshooting

### Common Issues

1. **Connection refused for HTTP servers**
   - Ensure the server is running on the specified port
   - Check firewall settings
   - Verify the URL is correct

2. **Command not found for stdio servers**
   - Ensure the command is in your PATH
   - Use absolute paths for scripts
   - Check file permissions

3. **Import errors**
   - Ensure all required packages are installed
   - Check Python path for stdio servers

### Debug Mode

Enable debug logging by setting environment variables:

```bash
export DEBUG=true
python test_mcp_integration.py
```

## Migration from Old Format

If you were using the old format (simple URL strings), migrate to the new format:

**Old format:**
```python
MCP_SERVERS = {
    "chembl": "http://localhost:8000",
    "literature": "http://localhost:8001"
}
```

**New format:**
```python
MCP_SERVERS = {
    "chembl": {
        "transport": "streamable_http",
        "url": "http://localhost:8000/mcp"
    },
    "literature": {
        "transport": "streamable_http",
        "url": "http://localhost:8001/mcp"
    }
}
