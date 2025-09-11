import asyncio
import datetime
from typing import Any, Dict, List

from src.generators.automation_generator import AutomationGenerator
from src.clients.pubchem_client import PubChemClient
from src.config.config import MCP_SERVERS, OPENAI_MODEL
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


# ----------------------------------------------------------------------
# Helper functions that do not require MCP services.
# ----------------------------------------------------------------------
def _extract_chemicals(query: str) -> List[str]:
    client = PubChemClient()
    return client.extract_chemicals(query)


def _fetch_chemical_data(chemicals: List[str]) -> Dict[str, Any]:
    client = PubChemClient()
    data: Dict[str, Any] = {}
    for chem in chemicals:
        info = client.get_chemical_data(chem)
        if info:
            data[chem] = info
    return data


def _generate_automation_script(protocol: Dict[str, Any], chemical_data: Dict[str, Any]) -> str:
    generator = AutomationGenerator()
    return generator.generate_script(protocol, chemical_data)


# ----------------------------------------------------------------------
# Core async routine that drives the LangGraph React agent using the
# LangChain MCP adapters.  The agent receives a natural‑language
# instruction and calls the appropriate MCP tools (protocol generation,
# literature search, knowledge‑graph creation, reaction explanation).
# ----------------------------------------------------------------------
async def _run_agent(query: str, explain_mode: bool) -> Dict[str, Any]:
    # Build the MultiServerMCPClient configuration from the MCP_SERVERS mapping.
    # The new format directly supports both stdio and streamable_http transports
    client = MultiServerMCPClient(MCP_SERVERS)
    all_tools = await client.get_tools()

    # Limit tools to essential ones to avoid context length issues
    essential_tool_names = [
        "search_compounds",
        "get_compound_info", 
        "search_targets",
        "get_target_info",
        "search_activities"
    ]
    
    tools = [tool for tool in all_tools if tool.name in essential_tool_names]
    print(f"Using {len(tools)} essential tools out of {len(all_tools)} available")

    # Create a LangGraph React agent that uses the OpenAI model configured
    # in ``config.py`` (default gpt‑3.5‑turbo).
    agent = create_react_agent(OPENAI_MODEL, tools)

    # Instruction for the agent.  It will call the MCP tools as needed and
    # return a JSON string containing the required artefacts.
    instruction = (
        f"Generate a detailed protocol for the query: '{query}'. "
        f"Include a brief explanation if explain_mode={explain_mode}. "
        "Also fetch up to 5 relevant literature papers, build a knowledge graph, "
        "and provide a beginner‑friendly reaction explanation. "
        "Return a JSON object with the keys: protocol, papers, knowledge_graph, explanation."
    )

    # The LangGraph React agent expects a dict with a ``messages`` key.
    response = await agent.ainvoke({"messages": instruction})

    # The final message should be a JSON string – parse it.
    if isinstance(response, str):
        try:
            import json
            return json.loads(response)
        except Exception:
            return {"raw_response": response}
    elif isinstance(response, dict):
        return response
    else:
        return {"raw_response": str(response)}


# ----------------------------------------------------------------------
# Public synchronous entry point used by Flask.
# ----------------------------------------------------------------------
def run_pipeline(query: str, explain_mode: bool = False) -> Dict[str, Any]:
    """
    Execute the full Catalyze pipeline using a LangGraph React agent that
    orchestrates multiple external MCP servers.

    Returns a dictionary compatible with the original Flask ``/api/query``
    response format, enriched with the additional MCP‑derived artefacts.
    """
    print(f"🚀 Starting pipeline for query: {query}")
    timestamp = datetime.datetime.now().isoformat()

    # 1️⃣ Extract chemical names from the query.
    print("🔍 Extracting chemicals from query...")
    chemicals = _extract_chemicals(query)
    print(f"🧪 Extracted chemicals: {chemicals}")

    # 2️⃣ Retrieve detailed chemical data (local PubChem client).
    print("📊 Fetching chemical data from PubChem...")
    chemical_data = _fetch_chemical_data(chemicals)
    print(f"📋 Chemical data retrieved: {list(chemical_data.keys())}")

    # 3️⃣ Run the LangGraph agent to obtain protocol, papers,
    #    knowledge graph, and explanation.
    print("🤖 Running MCP agent...")
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an event loop, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run_agent(query, explain_mode))
                agent_result = future.result()
        else:
            # If no event loop is running, use asyncio.run
            agent_result = asyncio.run(_run_agent(query, explain_mode))
    except RuntimeError:
        # Fallback: create a new event loop
        agent_result = asyncio.run(_run_agent(query, explain_mode))
    
    print(f"📊 Agent result keys: {list(agent_result.keys())}")
    protocol = agent_result.get("protocol", {})
    papers = agent_result.get("papers", [])
    knowledge_graph = agent_result.get("knowledge_graph", {})
    explanation = agent_result.get("explanation", {})
    
    print(f"📋 Protocol: {bool(protocol)}")
    print(f"📚 Papers: {len(papers)}")
    print(f"🕸️  Knowledge graph: {bool(knowledge_graph)}")
    print(f"💡 Explanation: {bool(explanation)}")

    # 4️⃣ Generate the Opentrons automation script locally.
    automation_script = _generate_automation_script(protocol, chemical_data)

    # 5️⃣ Assemble the final response – mirrors the original API shape.
    response = {
        "query": query,
        "timestamp": timestamp,
        "chemicals": chemicals,
        "chemical_data": chemical_data,
        "protocol": protocol,
        "automation_script": automation_script,
        "safety_info": {},  # Safety info can be added later if needed.
        "analysis": {
            "chemicals_found": len(chemical_data),
            "protocol_steps": len(protocol.get("steps", [])),
            "safety_hazards": 0,
            "automation_operations": automation_script.count("transfer(") + automation_script.count("mix(")
        },
        "papers": papers,
        "knowledge_graph": knowledge_graph,
        "explanation": explanation,
    }

    return response
