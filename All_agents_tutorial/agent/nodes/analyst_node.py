from agent.graphstate import InvestigationGraphState
from agent.provider.factory import get_llm
from langchain_core.messages import SystemMessage

def analyst_node(state:InvestigationGraphState) -> InvestigationGraphState:
    system_prompt = SystemMessage(
        "You are an autonomous data analyst. "
        "Analyze the user's question carefully. "
        "For now, provide a concise response explaining "
        "what should be investigated."
    )


    messages = [system_prompt]+state['messages']
    llm = get_llm()
    response= llm.invoke(messages)
    return{
        "messages" : [response],
        "step_count" : state["step_count"]+1,
        # "findings":response.content
    }




    
