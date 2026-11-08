from agent.graphstate import InvestigationGraphState
from agent.provider.factory import get_llm
from langchain_core.messages import SystemMessage, AIMessage

from agent.tool_register import bind_tools
import duckdb
from agent.tool_policy import DATA_TOOL_NAMES
import json


def make_analyst_node(conn: duckdb.DuckDBPyConnection):
    analyst_tools = bind_tools(conn)
     
   
    
    def analyst_node(state: InvestigationGraphState) -> InvestigationGraphState:

        evidence_inventory = [
        {
        "tool_call_id": observation["tool_call_id"],
        "tool_name": observation["tool_name"],
        }
        for observation in state["tool_observation"]
        ]

        evidence_message = SystemMessage(
            content=(
        "VALID EVIDENCE INVENTORY:\n"
        f"{json.dumps(evidence_inventory)}\n\n"
        "When calling record_finding, use only an exact "
        "tool_call_id from this inventory."
        )
        )
        
        system_prompt = SystemMessage(
            """- For non-trivial analytical questions, create a hypothesis before investigating.
            - Record a finding only when it is supported by tool evidence.
            - Every finding must include the related tool_call_id as evidence.
            - Never record unsupported assumptions as findings.
            - When sufficient evidence exists, provide the final answer."""
        )

        messages = [system_prompt , evidence_message] + state["messages"]
        llm = get_llm()
        llm_with_tools = llm.bind_tools(analyst_tools)

        response = llm_with_tools.invoke(messages)

        # data_tool_calls = sum(
        #     call["name"] in DATA_TOOL_NAMES
        #     for call in response.tool_calls
        # )

        return {
            "messages": [response],
            "step_count": state["step_count"] + 1,
            # "findings":response.content
        }

    return analyst_node
