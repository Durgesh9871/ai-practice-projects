from agent.graphstate import InvestigationGraphState
from agent.provider.factory import get_llm
from langchain_core.messages import SystemMessage, AIMessage

from agent.tool_register import bind_tools
import duckdb
from agent.tool_policy import DATA_TOOL_NAMES
import json
from agent.config import setting


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


        system_text = """
You are a self-driving data analyst.

Rules:
- For non-trivial analytical questions, create a hypothesis first.
- Inspect the database before assuming table or column names.
- Use run_sql for quantitative analysis.
- Record a finding only when supported by tool evidence.
- Every finding must use an exact tool_call_id from the evidence inventory.
- Never record unsupported assumptions as findings.
- If SQL fails, study the error and generate corrected SQL.
- Never repeat an SQL query that has already failed.
- When sufficient evidence exists, provide the final answer.
"""

        completion_feedback = state.get("completion_feedback", "")
        last_sql_error = state.get("last_sql_error", "")

        if completion_feedback:
            system_text += (
                "\nYour previous completion attempt was rejected: "
                f"{completion_feedback} "
                "Correct the issue before attempting the final answer again."
            )
            
        if last_sql_error:
            system_text += (
                "\nThe previous SQL query failed with this error:\n"
                f"{last_sql_error}\n"
                "Diagnose the error and submit corrected SQL. "
                "Do not repeat the failed query.\n"
            )
        
        system_prompt = SystemMessage(content=system_text)

        # messages = [system_prompt , evidence_message] + state["messages"]
        recent_messages = state["messages"][
            -setting.recent_messages_to_keep:
        ]

        memory_message = SystemMessage(
            content=(
                "CONVERSATION MEMORY:\n"
                f"{state.get('conversation_summary', 'No summary yet.')}"
            )
        )

        messages = [
            system_prompt,
            memory_message,
            evidence_message,
        ] + recent_messages


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
            "completion_valid": False,
            "completion_feedback": "",
            # "findings":response.content
        }

    return analyst_node
