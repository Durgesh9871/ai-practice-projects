
from agent.graphstate import InvestigationGraphState
from agent.gaurdrails.pil_gaurdrails import redact_text


def final_report(state:InvestigationGraphState)->InvestigationGraphState:
    final_answer = state["messages"][-1].content

    if isinstance(final_answer, list) and len(final_answer) > 0:
        answer = final_answer[0]["text"]
    else:
        answer = " ".join(final_answer.split()) 
           
    final_answer = redact_text(answer)

     
    # print("\n\n-----------------FINAL ANSWER-----------------\n\n")
    # print(final_answer)

    return {
        "final_report": final_answer,
        "is_finished": True,
        # "step_count": state["step_count"] + 1,
    }

