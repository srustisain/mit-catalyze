#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import * as path from "path";
import { fileURLToPath } from "url";
import { DocsFetcher } from "./docs-fetcher.js";
import { DocsStorage } from "./storage.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR = path.join(__dirname, "..", "data");

const server = new Server(
  {
    name: "opentrons-python-api-mcp-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Initialize storage and fetcher
const storage = new DocsStorage(path.join(DATA_DIR, "docs.db"));
const fetcher = new DocsFetcher(storage);

// Initialize docs on startup (check and update if needed)
let initialized = false;
async function ensureInitialized() {
  if (initialized) return;
  
  try {
    await fetcher.ensureDocsUpdated();
    initialized = true;
  } catch (error) {
    console.error("Failed to initialize docs:", error);
    // Continue anyway - tools will work with cached data
  }
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  await ensureInitialized();
  
  return {
    tools: [
      {
        name: "search_opentrons_docs",
        description:
          "Search Opentrons Python API v2 documentation semantically. Use this when you need to find information about Opentrons API methods, classes, examples, or concepts. Returns relevant documentation sections.",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query (e.g., 'how to load labware', 'pipette aspirate', 'deck slots')",
            },
            limit: {
              type: "number",
              description: "Maximum number of results to return (default: 5)",
              minimum: 1,
              maximum: 20,
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_opentrons_api_reference",
        description:
          "Get specific Opentrons Python API reference documentation for a topic, class, or method. Use this when you know the exact API element you need (e.g., 'ProtocolContext', 'load_labware', 'pipette.transfer').",
        inputSchema: {
          type: "object",
          properties: {
            topic: {
              type: "string",
              description: "API topic, class name, or method name (e.g., 'ProtocolContext', 'load_labware', 'aspirate', 'deck slots')",
            },
          },
          required: ["topic"],
        },
      },
      {
        name: "get_opentrons_example",
        description:
          "Get code examples from Opentrons Python API documentation. Use this when you need example code for common operations like transferring liquids, using modules, or working with labware.",
        inputSchema: {
          type: "object",
          properties: {
            example_type: {
              type: "string",
              description: "Type of example (e.g., 'transfer', 'module', 'labware', 'protocol', 'pipette')",
            },
          },
          required: ["example_type"],
        },
      },
      {
        name: "update_opentrons_docs",
        description:
          "Update Opentrons Python API documentation from the official website. Use this to refresh the cached documentation. This may take a minute.",
        inputSchema: {
          type: "object",
          properties: {},
          required: [],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  await ensureInitialized();
  
  try {
    if (request.params.name === "search_opentrons_docs") {
      const { query, limit = 5 } = request.params.arguments as {
        query: string;
        limit?: number;
      };

      if (!query || typeof query !== "string") {
        throw new McpError(
          ErrorCode.InvalidParams,
          "Query parameter is required and must be a string"
        );
      }

      const results = storage.searchDocs(query, limit);
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                query,
                results: results.map((r) => ({
                  title: r.title,
                  url: r.url,
                  content: r.content.substring(0, 2000), // Limit content length
                  section: r.section,
                })),
                total: results.length,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (request.params.name === "get_opentrons_api_reference") {
      const { topic } = request.params.arguments as { topic: string };

      if (!topic || typeof topic !== "string") {
        throw new McpError(
          ErrorCode.InvalidParams,
          "Topic parameter is required and must be a string"
        );
      }

      const results = storage.getApiReference(topic);
      
      if (results.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  topic,
                  message: "No documentation found for this topic. Try searching with search_opentrons_docs instead.",
                },
                null,
                2
              ),
            },
          ],
        };
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                topic,
                results: results.map((r) => ({
                  title: r.title,
                  url: r.url,
                  content: r.content,
                  section: r.section,
                })),
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (request.params.name === "get_opentrons_example") {
      const { example_type } = request.params.arguments as {
        example_type: string;
      };

      if (!example_type || typeof example_type !== "string") {
        throw new McpError(
          ErrorCode.InvalidParams,
          "example_type parameter is required and must be a string"
        );
      }

      const results = storage.getExamples(example_type);
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                example_type,
                examples: results.map((r) => ({
                  title: r.title,
                  url: r.url,
                  code: r.content,
                  description: r.section,
                })),
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (request.params.name === "update_opentrons_docs") {
      await fetcher.fetchAndStoreDocs();
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                success: true,
                message: "Opentrons Python API documentation updated successfully",
                timestamp: new Date().toISOString(),
              },
              null,
              2
            ),
          },
        ],
      };
    }

    throw new McpError(
      ErrorCode.MethodNotFound,
      `Unknown tool: ${request.params.name}`
    );
  } catch (error) {
    if (error instanceof McpError) {
      throw error;
    }
    throw new McpError(
      ErrorCode.InternalError,
      `Tool execution failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Opentrons Python API MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});

