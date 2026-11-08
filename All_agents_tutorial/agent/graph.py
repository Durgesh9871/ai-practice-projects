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


def route_after_analyst(state: InvestigationGraphState):
    """
    Check safety budget before executing requested tools.
    """

    last_message = state["messages"][-1]

    reqested_calls = last_message.tool_calls
    
    if not reqested_calls:
        return "final_report"

    pending_calls = [
        call for call in last_message.tool_calls 
        if call["name"] in DATA_TOOL_NAMES
    ]

    if len(pending_calls) > 0 or pending_calls:
        return "track_tool_usage"    
    elif (
        state["step_count"] >= max_steps
        or state["tool_calls"] + len(pending_calls) > max_tool_calls
    ):
        return "safe_stop_node"

    return "tool"


# --------------------------------------------------
# 2. ROUTE AFTER TRACKING TOOL USAGE
# --------------------------------------------------




def route_after_tool(state: InvestigationGraphState):
    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        if last_message.name in DATA_TOOL_NAMES:
            return "observation_node"

    return "analyst"
# --------------------------------------------------
# 3. BUILD GRAPH
# --------------------------------------------------


def build_graph(conn):

    workflow = StateGraph(InvestigationGraphState)

    analyst_node = make_analyst_node(conn)

    tools = bind_tools(conn)
    tools_node = ToolNode(tools)

    # Register nodes
    workflow.add_node("analyst", analyst_node)
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
            "final_report": "final_report",
            "safe_stop_node": "safe_stop_node",
            "track_tool_usage": "track_tool_usage",
            "tool": "tool",
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

    workflow.add_edge("observation_node", "analyst")

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
        tool_observation=[]     
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
        "Inspect the dataset and tell me what tables are available.", conn
    )
