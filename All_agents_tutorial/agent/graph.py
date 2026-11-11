from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from langchain_core.messages import HumanMessage

import duckdb
from agent.config import setting
from agent.nodes.analyst_node import make_analyst_node
from agent.graphstate import InvestigationGraphState
from agent.tool_register import bind_tools
from agent.nodes.final_node import final_report
from agent.nodes.budget_node import track_tool_usage
from agent.nodes.safe_stop_node import safe_node
from agent.nodes.observation_node import observation_node
from agent.tool_policy import DATA_TOOL_NAMES

from data.loader import DB_PATH, load_csv_data
from rich.console import Console
from rich.panel import Panel
from langchain_core.messages import ToolMessage
from agent.nodes.completion_node import validate_completion

from agent.nodes.duplicate_sql_node import duplicate_sql_node
from agent.nodes.sql_failure_node import sql_failure_node
from agent.sql_utils import normalize_sql

console = Console()


max_tool_calls = setting.max_tool_calls
max_steps = setting.max_steps



# --------------------------------------------------
# 1. SAFETY CHECK AFTER ANALYST
# --------------------------------------------------
def display_ai_message(message):

    from rich.pretty import pprint
    pprint(message)
    console.rule("[bold cyan]LLM RESPONSE[/bold cyan]")


# Display tool calls

# helper function to check sql query is duplicated or not 
def contains_duplicate_failed_sql(state: InvestigationGraphState) -> bool:
    failed_queries = {
        attempt["normalized_query"]
        for attempt in state["sql_attempts"]
        if not attempt["success"]
    }

    latest_message = state["messages"][-1]

    for tool_call in latest_message.tool_calls:
        if tool_call["name"] != "run_sql":
            continue

        query = tool_call["args"].get("query", "")

        if normalize_sql(query) in failed_queries:
            return True

    return False




def route_after_analyst(state: InvestigationGraphState):
    last_message = state["messages"][-1]
    requested_calls = last_message.tool_calls

    if not requested_calls:
        return "completion_validator"

    if state["step_count"] >= setting.max_steps:
        return "safe_stop_node"

    pending_data_calls = [
        call
        for call in requested_calls
        if call["name"] in DATA_TOOL_NAMES
    ]

    if contains_duplicate_failed_sql(state):
        return "duplicate_sql_node"

    if (
        state["tool_calls"] + len(pending_data_calls)
        > setting.max_tool_calls
    ):
        return "safe_stop_node"

    if pending_data_calls:
        return "track_tool_usage"

    return "tool"


# --------------------------------------------------
# 2. ROUTE AFTER completion
# --------------------------------------------------
def route_after_completion(state: InvestigationGraphState):
    if state["completion_valid"]:
        return "final_report"

    if state["completion_attempts"] >= 2:
        return "safe_stop_node"

    return "analyst"



def route_after_tool(state: InvestigationGraphState):
    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        if last_message.name in DATA_TOOL_NAMES:
            return "observation_node"

    return "analyst"
# --------------------------------------------------

def route_after_observation(state: InvestigationGraphState):
    if state["sql_error_count"] >= setting.max_sql_errors:
        return "sql_failure_node"

    return "analyst"




def build_graph(conn):

    workflow = StateGraph(InvestigationGraphState)

    analyst_node = make_analyst_node(conn)

    tools = bind_tools(conn)
    tools_node = ToolNode(tools)

    # Register nodes
    workflow.add_node("analyst", analyst_node)

    workflow.add_node("completion_validator", validate_completion)
    workflow.add_node("duplicate_sql_node", duplicate_sql_node)
    workflow.add_node("sql_failure_node", sql_failure_node)

    workflow.add_node("track_tool_usage", track_tool_usage)
    workflow.add_node("observation_node", observation_node)
    workflow.add_node("safe_stop_node", safe_node)
    workflow.add_node("tool", tools_node)
    workflow.add_node("final_report", final_report)

    # Entry point
    workflow.add_edge(START, "analyst")

    # Analyst -> Safety check
    workflow.add_conditional_edges(
        "analyst",
        route_after_analyst,
        {
            "completion_validator": "completion_validator",
            "duplicate_sql_node": "duplicate_sql_node",
            "safe_stop_node": "safe_stop_node",
            "track_tool_usage": "track_tool_usage",
            "tool": "tool",
        },
    )

    workflow.add_conditional_edges(
    "completion_validator",
    route_after_completion,
    {
        "final_report": "final_report",
        "analyst": "analyst",
        "safe_stop_node": "safe_stop_node",
    },
    )

    workflow.add_edge("track_tool_usage", "tool")
    # Tool execution -> Analyst again
    workflow.add_conditional_edges(
        "tool",
        route_after_tool,
        {
            "observation_node": "observation_node",
            "analyst": "analyst",
        },
    )

    workflow.add_conditional_edges(
    "observation_node",
    route_after_observation,
    {
        "analyst": "analyst",
        "sql_failure_node": "sql_failure_node",
    },
    )

    workflow.add_edge("duplicate_sql_node", "observation_node")
    workflow.add_edge("sql_failure_node", "final_report")
    # Safe stop -> Final report
    workflow.add_edge("safe_stop_node", "final_report")

    # Final report -> END
    workflow.add_edge("final_report", END)

    app = workflow.compile()

    return app


# --------------------------------------------------
# 4. RUN INVESTIGATION
# --------------------------------------------------


def run_investigation(objective: str, conn):

    workflow = build_graph(conn)

    initial_state = InvestigationGraphState(
        messages=[HumanMessage(content=objective)],
        hypotheses=[],
        findings=[],
        objective=objective,
        tool_calls=0,
        step_count=0,
        is_finished=False,
        final_report="",
        tool_observation=[] ,
        completion_valid=False,
        completion_feedback="",
        completion_attempts=0,    
        sql_attempts=[],
        sql_error_count=0,
        last_sql_error="",
    )

    events = workflow.stream(initial_state, stream_mode="values")

    final_state = None

    for event in events:
        final_state = event
        display_ai_message(event)

    if final_state is None:
        print("Investigation returned no state.")
        return

    # print("\n\n-----------------FINAL REPORT-----------------\n\n")
    # print(final_state["final_report"])

    # print("\n\n-----------------TOOL CALLS-----------------\n\n")
    # print(final_state["tool_calls"])

    # print("\n\n-----------------STEP COUNT-----------------\n\n")
    # print(final_state["step_count"])

    # print("\n\n-----------------IS FINISHED-----------------\n\n")
    # print(final_state["is_finished"])


# --------------------------------------------------
# 5. MAIN
# --------------------------------------------------


if __name__ == "__main__":

    from pathlib import Path

    DATA_DIRECTORY = Path("data/ecommerce_demo")

    conn, _ = load_csv_data(DATA_DIRECTORY)

    run_investigation(
        "Inspect the database and tell me how many records exist in each table.", conn
    )
