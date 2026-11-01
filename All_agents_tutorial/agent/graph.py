from langgraph.graph import StateGraph,END,START
from agent.nodes.analyst_node import make_analyst_node
from agent.graphstate import InvestigationGraphState
from langchain_core.messages import HumanMessage
from data.loader import DB_PATH, load_csv_data
import duckdb
from langgraph.prebuilt import ToolNode
from agent.tool_register import bind_tools
from agent.nodes.final_node import final_report


def route_after_analyst(state:InvestigationGraphState):
    """Conditional edge: decide whether to do tool call or stop the workflow."""

    #check the latest message
    last_message=state["messages"][-1]

    if last_message.tool_calls:
        return "tool"
    else:
        return "final_report"

def build_graph(conn):
    workflow = StateGraph(InvestigationGraphState)
    analyst_node = make_analyst_node(conn)
    tools = bind_tools(conn)
    tools_node = ToolNode(tools)

    workflow.add_node("analyst",analyst_node)
    workflow.add_node("tool",tools_node)
    workflow.add_node("final_report",final_report)



  
    # workflow.set_entry_point("analyst")
    workflow.add_edge(START, "analyst")
    workflow.add_conditional_edges(
        "analyst",
        route_after_analyst,
        {
            "tool": "tool",
            "final_report": "final_report"
        }
    )
    workflow.add_edge("tool", "analyst")
    workflow.add_edge("final_report", END)


    app = workflow.compile()



    # print(app.get_graph().draw_mermaid())

    return app 


def run_investigation(objective:str , conn):
    workflow = build_graph(conn)
    initial_state = InvestigationGraphState(
        messages=[
            HumanMessage(content=objective)
        ],
        hypotheses=[],
        findings=[],
        objective=objective,
        tool_calls=0,
        step_count=0,
        is_finished=False,
        final_report="",
    )
    events = workflow.stream(initial_state,stream_mode="values")
    final_answer = ""
    for event in events:
        if "final_report" in event:
            final_answer = event
        # print(event)
        # print("-"*100)
    print("\n\n-----------------FINAL ANSWER-----------------\n\n")
    print(final_answer["messages"][-1].content[0]["text"])


if __name__=="__main__":
    from pathlib import Path
    DATA_DIRECTORY = Path("data/ecommerce_demo")

    conn, _ = load_csv_data(DATA_DIRECTORY)

    run_investigation(
        "Inspect the dataset and tell me what tables are available.", conn
    )
