from tools.inspect_data import inspect_table
from tools.run_sql import run_sql_query
from langchain_core.tools import tool , InjectedToolCallId
import duckdb
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated

from agent.tool_policy import DATA_TOOL_NAMES
from langgraph.prebuilt import InjectedState


def bind_tools(conn:duckdb.DuckDBPyConnection):

    @tool("inspect_db")
    def inspect_db()->dict:
        """
        Inspect all persistent tables in DuckDB.
        Returns table names, columns, data types, row counts,
        and a small sample of rows.
        """
        return inspect_table(conn)

    @tool("run_sql")
    def run_sql(query:str)->dict:
        """
        Execute a read-only SQL query against the DuckDB analytics database and return bounded results.
        """
        return run_sql_query(query,conn)


    @tool("record_hypothesis")
    def record_hypothesis(statement:str,tool_call_id: Annotated[str, InjectedToolCallId])->Command:
        """
        Record a possible explanation that needs investigation.
        """
        return Command(update={
            "hypotheses": [{"statement": statement, "status": "open"}],
            "messages": [ToolMessage(content=f"Hypothesis recorded: {statement}", tool_call_id=tool_call_id)]
        })

    @tool("record_finding")
    def record_finding(statement:str, tool_call_id: Annotated[str, InjectedToolCallId], evidence_ids:list[str], confidence:float, state: Annotated[dict, InjectedState])->Command:
        """
        Record a confirmed finding with evidence.
        """
        valid_evidence_ids = {
            item["tool_call_id"]
            for item in state["tool_observation"]
            if item["tool_name"] in DATA_TOOL_NAMES
        }
        invalid_ids = [
        evidence_id
        for evidence_id in evidence_ids
        if evidence_id not in valid_evidence_ids
        ]
        
        if invalid_ids or not 0.0 <= confidence <= 1.0:
            return Command(
                update={
                "messages": [
                    ToolMessage(
                        content=(
                            f"Finding rejected. Invalid evidence IDs: {invalid_ids}. "
                            f"Valid IDs are: {sorted(valid_evidence_ids)}"
                        ),
                        tool_call_id=tool_call_id,
                    )
                ]
            }
        )

        return Command(update={
            "findings": [{"statement": statement, "evidence_ids": evidence_ids, "confidence": confidence}],
            "messages": [ToolMessage(content=f"Finding recorded: {statement}", tool_call_id=tool_call_id)]
        })

    return [inspect_db, run_sql, record_hypothesis, record_finding]
