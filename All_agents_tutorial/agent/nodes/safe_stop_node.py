from langchain_core.messages import AIMessage
from agent.graphstate import InvestigationGraphState


def safe_node(state:InvestigationGraphState)->InvestigationGraphState:

    ai_message = AIMessage(
        """
        The investigation was stopped because it reached limit"
        the configured safety budget is reached. "
        The analysis may be incomplete but these are the current findings"""

        f"{state["findings"]}"
        
    )

      


    return {
        "messages": [ai_message],
        "is_finished": True,
    }
