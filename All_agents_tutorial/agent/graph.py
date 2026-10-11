from langgraph.graph import StateGraph,END,START
from agent.nodes.analyst_node import analyst_node
from agent.graphstate import InvestigationGraphState
from langchain_core.messages import HumanMessage

def build_graph():
    workflow = StateGraph(InvestigationGraphState)
    workflow.add_node("analyst",analyst_node)

    # workflow.set_entry_point("analyst")
    workflow.add_edge(START, "analyst")
    workflow.add_edge("analyst", END)
    return workflow.compile()




def run_investigation(objective:str):
    workflow = build_graph()
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
    for event in events:
        print(event)
        print("-"*100)



if __name__=="__main__":
    run_investigation("my name us durgesh")