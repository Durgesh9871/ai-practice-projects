
from agent.graphstate import InvestigationGraphState



def final_report(state:InvestigationGraphState)->InvestigationGraphState:
    final_answer = state["messages"][-1].content[0]["text"]
     
    # print("\n\n-----------------FINAL ANSWER-----------------\n\n")
    # print(final_answer)

    return {
        "final_report": final_answer,
        "is_finished": True,
        "step_count": state["step_count"] + 1,
    }

