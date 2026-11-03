# from langgraph.graph import StateGraph,END,START
# from agent.nodes.analyst_node import make_analyst_node
# from agent.graphstate import InvestigationGraphState
# from langchain_core.messages import HumanMessage
# from data.loader import DB_PATH, load_csv_data
# import duckdb
# from langgraph.prebuilt import ToolNode
# from agent.tool_register import bind_tools
# from agent.nodes.final_node import final_report
# from agent.nodes.budget_node import track_tool_usage
# from agent.nodes.safe_stop_node import safe_node
# from agent.config import setting


# max_tool_calls =setting.max_tool_calls
# max_steps = setting.max_steps


# def route_after_analyst(state:InvestigationGraphState):
#     """Conditional edge: decide whether to do tool call or stop the workflow."""

#     #check the latest message
#     last_message=state["messages"][-1]

#     if state["tool_calls"] > max_tool_calls or state["step_count"] >  max_steps:
#         return "safe_stop_node"
#     else:
#         if last_message.tool_calls:
#             return "tool"
#         else:
#             return "final_report"

# def build_graph(conn):
#     workflow = StateGraph(InvestigationGraphState)
#     analyst_node = make_analyst_node(conn)
#     tools = bind_tools(conn)
#     tools_node = ToolNode(tools)

#     workflow.add_node("analyst",analyst_node)
#     workflow.add_node("track_tool_usage",track_tool_usage)
#     workflow.add_node("safe_stop_node",safe_node)
#     workflow.add_node("tool",tools_node)
#     workflow.add_node("final_report",final_report)


#     # workflow.set_entry_point("analyst")
#     workflow.add_edge(START, "analyst")
#     workflow.add_edge("analyst","track_tool_usage")
#     workflow.add_conditional_edges(
#         "track_tool_usage",
#         route_after_analyst,
#         {
#             "safe_stop_node": "safe_stop_node",
#             "tool": "tool",
#             "final_report": "final_report"
#         }
#     )
#     workflow.add_edge("tool", "analyst")
#     workflow.add_edge("safe_stop_node", "final_report")
#     workflow.add_edge("final_report", END)


#     app = workflow.compile()


#     # print(app.get_graph().draw_mermaid())

#     return app


# def run_investigation(objective:str , conn):
#     workflow = build_graph(conn)
#     initial_state = InvestigationGraphState(
#         messages=[
#             HumanMessage(content=objective)
#         ],
#         hypotheses=[],
#         findings=[],
#         objective=objective,
#         tool_calls=0,
#         step_count=0,
#         is_finished=False,
#         final_report="",
#     )
#     events = workflow.stream(initial_state,stream_mode="values")
#     final_answer = ""
#     for event in events:
#         if "final_report" in event:
#             final_answer = event
#         # print(event)
#         # print("-"*100)
#     print("\n\n-----------------FINAL REPORT-----------------\n\n")
#     print(final_answer["final_report"])

#     print("\n\n-----------------TOOL CALLS-----------------\n\n")
#     print(final_answer["tool_calls"])

#     print("\n\n-----------------STEP COUNT-----------------\n\n")
#     print(final_answer["step_count"])

#     print("\n\n-----------------IS FINISHED-----------------\n\n")
#     print(final_answer["is_finished"])


# if __name__=="__main__":
#     from pathlib import Path
#     DATA_DIRECTORY = Path("data/ecommerce_demo")

#     conn, _ = load_csv_data(DATA_DIRECTORY)

#     run_investigation(
#         "Inspect the dataset and tell me what tables are available.", conn
#     )


from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from langchain_core.messages import HumanMessage

import duckdb

from agent.nodes.analyst_node import make_analyst_node
from agent.graphstate import InvestigationGraphState
from agent.tool_register import bind_tools
from agent.nodes.final_node import final_report
from agent.nodes.budget_node import track_tool_usage
from agent.nodes.safe_stop_node import safe_node
from agent.config import setting

from data.loader import DB_PATH, load_csv_data


max_tool_calls = setting.max_tool_calls
max_steps = setting.max_steps


# --------------------------------------------------
# 1. SAFETY CHECK AFTER ANALYST
# --------------------------------------------------


def route_after_analyst(state: InvestigationGraphState):
    """
    Check safety budget before executing requested tools.
    """

    last_message = state["messages"][-1]

    pending_calls = len(last_message.tool_calls)

    # Check whether the investigation exceeded its budget
    if (
        state["step_count"] >= max_steps
        or state["tool_calls"] + pending_calls > max_tool_calls
    ):
        return "safe_stop_node"

    return "track_tool_usage"


# --------------------------------------------------
# 2. ROUTE AFTER TRACKING TOOL USAGE
# --------------------------------------------------


def route_after_tracking(state: InvestigationGraphState):
    """
    Decide whether to execute tools or generate final report.
    """

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tool"

    return "final_report"


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
            "safe_stop_node": "safe_stop_node",
            "track_tool_usage": "track_tool_usage",
        },
    )

    # Track usage -> Tool or Final report
    workflow.add_conditional_edges(
        "track_tool_usage",
        route_after_tracking,
        {
            "tool": "tool",
            "final_report": "final_report",
        },
    )

    # Tool execution -> Analyst again
    workflow.add_edge("tool", "analyst")

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
    )

    events = workflow.stream(initial_state, stream_mode="values")

    final_state = None

    for event in events:
        final_state = event

    if final_state is None:
        print("Investigation returned no state.")
        return

    print("\n\n-----------------FINAL REPORT-----------------\n\n")
    print(final_state["final_report"])

    print("\n\n-----------------TOOL CALLS-----------------\n\n")
    print(final_state["tool_calls"])

    print("\n\n-----------------STEP COUNT-----------------\n\n")
    print(final_state["step_count"])

    print("\n\n-----------------IS FINISHED-----------------\n\n")
    print(final_state["is_finished"])


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
