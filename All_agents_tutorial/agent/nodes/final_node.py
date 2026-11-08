
from agent.graphstate import InvestigationGraphState



def final_report(state:InvestigationGraphState)->InvestigationGraphState:
    final_answer = state["messages"][-1].content

    if isinstance(final_answer, list) and len(final_answer) > 0:
        final_answer = final_answer[0]["text"]
    else:
        final_answer = " ".join(final_answer.split()) 
           



     
    # print("\n\n-----------------FINAL ANSWER-----------------\n\n")
    # print(final_answer)

    return {
        "final_report": final_answer,
        "is_finished": True,
        # "step_count": state["step_count"] + 1,
    }

