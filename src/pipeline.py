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
    tools = await client.get_tools()

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
    print("Got here")
    timestamp = datetime.datetime.now().isoformat()

    # 1️⃣ Extract chemical names from the query.
    chemicals = _extract_chemicals(query)

    # 2️⃣ Retrieve detailed chemical data (local PubChem client).
    chemical_data = _fetch_chemical_data(chemicals)

    # 3️⃣ Run the LangGraph agent to obtain protocol, papers,
    #    knowledge graph, and explanation.
    agent_result = asyncio.run(_run_agent(query, explain_mode))

    protocol = agent_result.get("protocol", {})
    papers = agent_result.get("papers", [])
    knowledge_graph = agent_result.get("knowledge_graph", {})
    explanation = agent_result.get("explanation", {})

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
