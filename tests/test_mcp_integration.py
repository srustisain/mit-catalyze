#!/usr/bin/env python3
"""
Standalone test script for MCP integration with LLM client
Tests the complete pipeline including MCP servers, LLM integration, and chemical data retrieval
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, List
import traceback
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
try:
    from src.pipeline import PipelineManager
    from src.clients.llm_client import LLMClient
    from src.clients.pubchem_client import PubChemClient
    from src.config.config import MCP_SERVERS, OPENAI_API_KEY
    print("✅ All required modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class MCPIntegrationTester:
    """Comprehensive tester for MCP integration functionality"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        
    async def test_mcp_server_connectivity(self):
        """Test connectivity to MCP servers"""
        print("\n🔍 Testing MCP server connectivity...")
        
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            
            # Test each configured MCP server
            for server_name, server_config in MCP_SERVERS.items():
                try:
                    client = MultiServerMCPClient({server_name: server_config})
                    
                    # Try to get tools from the server
                    tools = await client.get_tools()
                    
                    # Get server info for logging
                    if server_config.get("transport") == "stdio":
                        server_info = f"stdio: {server_config.get('command', 'python')} {' '.join(server_config.get('args', []))}"
                    else:
                        server_info = server_config.get("url", "unknown")
                    
                    self.log_result(
                        f"MCP Server: {server_name}",
                        True,
                        f"Connected to {server_info}, found {len(tools)} tools",
                        {"config": server_config, "tools_count": len(tools)}
                    )
                    
                except Exception as e:
                    server_info = server_config.get("url", server_config.get("command", "stdio"))
                    self.log_result(
                        f"MCP Server: {server_name}",
                        False,
                        f"Failed to connect: {str(e)}",
                        {"config": server_config, "error": str(e)}
                    )
                    
        except ImportError as e:
            self.log_result(
                "MCP Server Connectivity",
                False,
                f"Failed to import MCP client: {str(e)}"
            )
            
    def test_llm_client_providers(self):
        """Test LLM client with different providers"""
        print("\n🔍 Testing LLM client providers...")
        
        # Test default provider
        try:
            client = LLMClient()
            self.log_result(
                "LLM Client Default",
                True,
                f"Initialized with provider: {client.provider}"
            )
            
            # Test provider switching
            providers = ["openai", "cerebras", "huggingface"]
            for provider in providers:
                try:
                    client.set_provider(provider)
                    self.log_result(
                        f"LLM Provider: {provider}",
                        True,
                        f"Successfully switched to {provider}"
                    )
                except Exception as e:
                    self.log_result(
                        f"LLM Provider: {provider}",
                        False,
                        f"Failed to switch to {provider}: {str(e)}"
                    )
                    
        except Exception as e:
            self.log_result(
                "LLM Client Initialization",
                False,
                f"Failed to initialize LLM client: {str(e)}"
            )
            
    def test_pubchem_integration(self):
        """Test PubChem client integration"""
        print("\n🔍 Testing PubChem integration...")
        
        try:
            client = PubChemClient()
            
            # Test chemical extraction
            test_queries = [
                "Synthesize benzyl alcohol from benzyl chloride",
                "Prepare sodium hydroxide solution",
                "Create aspirin from salicylic acid"
            ]
            
            for query in test_queries:
                try:
                    chemicals = client.extract_chemicals(query)
                    self.log_result(
                        f"PubChem Extraction: {query[:30]}...",
                        len(chemicals) > 0,
                        f"Found {len(chemicals)} chemicals: {', '.join(chemicals[:3])}",
                        {"chemicals": chemicals}
                    )
                    
                    # Test chemical data retrieval
                    if chemicals:
                        data = client.get_chemical_data(chemicals[0])
                        self.log_result(
                            f"PubChem Data: {chemicals[0]}",
                            data is not None,
                            f"Retrieved data with {len(data)} fields" if data else "No data retrieved",
                            {"chemical_data_keys": list(data.keys()) if data else []}
                        )
                        
                except Exception as e:
                    self.log_result(
                        f"PubChem Test: {query[:30]}...",
                        False,
                        f"Error: {str(e)}"
                    )
                    
        except Exception as e:
            self.log_result(
                "PubChem Integration",
                False,
                f"Failed to initialize PubChem client: {str(e)}"
            )
            
    async def test_pipeline_integration(self):
        """Test complete pipeline integration"""
        print("\n🔍 Testing complete pipeline integration...")
        
        try:
            # Initialize pipeline manager
            pipeline_manager = PipelineManager()
            await pipeline_manager.initialize()
            
            test_queries = [
                "Synthesize benzyl alcohol from benzyl chloride",
                "How to prepare a 1M NaOH solution"
            ]
            
            for query in test_queries:
                try:
                    print(f"  Testing query: {query}")
                    result = await pipeline_manager.process_query(query, {"mode": "research"})
                    
                    # Validate result structure
                    if result and isinstance(result, dict):
                        self.log_result(
                            f"Pipeline: {query[:30]}...",
                            True,
                            f"Pipeline executed successfully",
                            result
                        )
                    else:
                        self.log_result(
                            f"Pipeline: {query[:30]}...",
                            False,
                            "Pipeline returned invalid result",
                            result
                        )
                        
                except Exception as e:
                    self.log_result(
                        f"Pipeline: {query[:30]}...",
                        False,
                        f"Pipeline execution failed: {str(e)}"
                    )
                    
        except Exception as e:
            self.log_result(
                "Pipeline Integration",
                False,
                f"Pipeline initialization failed: {str(e)}"
            )
                
    def test_mcp_tools_availability(self):
        """Test availability of MCP tools"""
        print("\n🔍 Testing MCP tools availability...")
        
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            
            async def check_tools():
                try:
                    client = MultiServerMCPClient(MCP_SERVERS)
                    tools = await client.get_tools()
                    
                    if tools:
                        tool_names = [tool.name for tool in tools]
                        self.log_result(
                            "MCP Tools Available",
                            True,
                            f"Found {len(tools)} tools: {', '.join(tool_names[:5])}",
                            {"tools": tool_names}
                        )
                    else:
                        self.log_result(
                            "MCP Tools Available",
                            False,
                            "No tools found in MCP servers"
                        )
                        
                except Exception as e:
                    self.log_result(
                        "MCP Tools Available",
                        False,
                        f"Error accessing tools: {str(e)}"
                    )
                    
            # Run async check
            asyncio.run(check_tools())
            
        except ImportError as e:
            self.log_result(
                "MCP Tools Test",
                False,
                f"Failed to import MCP client: {str(e)}"
            )
            
    async def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        print("\n🔍 Testing error handling...")
        
        try:
            # Initialize pipeline manager
            pipeline_manager = PipelineManager()
            await pipeline_manager.initialize()
            
            # Test with invalid query
            try:
                result = await pipeline_manager.process_query("invalid chemical query xyz123", {"mode": "research"})
                self.log_result(
                    "Error Handling: Invalid Query",
                    True,
                    "Gracefully handled invalid query",
                    {"result_keys": list(result.keys()) if result else []}
                )
            except Exception as e:
                self.log_result(
                    "Error Handling: Invalid Query",
                    False,
                    f"Failed to handle invalid query: {str(e)}"
                )
                
            # Test with empty query
            try:
                result = await pipeline_manager.process_query("", {"mode": "research"})
                self.log_result(
                    "Error Handling: Empty Query",
                    True,
                    "Gracefully handled empty query",
                    {"result_keys": list(result.keys()) if result else []}
                )
            except Exception as e:
                self.log_result(
                    "Error Handling: Empty Query",
                    False,
                    f"Failed to handle empty query: {str(e)}"
                )
                
        except Exception as e:
            self.log_result(
                "Error Handling",
                False,
                f"Pipeline initialization failed: {str(e)}"
            )
            
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 MCP INTEGRATION TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {datetime.now() - self.start_time}")
        
        print("\n📋 Detailed Results:")
        print("-" * 60)
        
        for result in self.test_results:
            status = "PASS" if result["success"] else "FAIL"
            print(f"{status:4} | {result['test']}")
            if result["details"]:
                print(f"     | {result['details']}")
        
        # Save detailed report to file
        report_file = f"mcp_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100,
                    "duration": str(datetime.now() - self.start_time)
                },
                "results": self.test_results
            }, f, indent=2)
            
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests


async def main():
    """Main test runner"""
    print("🧪 MCP Integration Test Suite")
    print("=" * 60)
    print("Testing MCP integration with LLM client and chemical pipeline")
    
    tester = MCPIntegrationTester()
    
    # Run all tests
    print("\n🚀 Starting tests...")
    
    # Test individual components
    await tester.test_mcp_server_connectivity()
    tester.test_llm_client_providers()
    tester.test_pubchem_integration()
    tester.test_mcp_tools_availability()
    await tester.test_pipeline_integration()
    await tester.test_error_handling()
    
    # Generate final report
    success = tester.generate_report()
    
    print("\n" + "="*60)
    if success:
        print("🎉 All tests passed! MCP integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the report for details.")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
