
from agent.gaurdrails.pil_gaurdrails import redact_text
from agent.config import setting
from agent.graphstate import InvestigationGraphState
from agent.guardrails.output_guard import sanitize_final_report


def final_report(state:InvestigationGraphState)->InvestigationGraphState:
    final_answer = state["messages"][-1].content

    if isinstance(final_answer, list) and len(final_answer) > 0:
        answer = final_answer[0]["text"]
    else:
        answer = " ".join(final_answer.split()) 
           
    final_answer = sanitize_final_report(
    report=answer,
    findings=state["findings"],
    tool_observations=state["tool_observation"],
    max_characters=setting.max_final_report_characters,
)

     
    # print("\n\n-----------------FINAL ANSWER-----------------\n\n")
    # print(final_answer)

    return {
        "final_report": final_answer,
        "is_finished": True,
        # "step_count": state["step_count"] + 1,
    }

