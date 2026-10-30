from agent.graphstate import InvestigationGraphState
from agent.provider.factory import get_llm
from langchain_core.messages import SystemMessage

from agent.tool_register import bind_tools
import duckdb


def make_analyst_node(conn:duckdb.DuckDBPyConnection):
    analyst_tools= bind_tools(conn)

    def analyst_node(state:InvestigationGraphState) -> InvestigationGraphState:
        system_prompt = SystemMessage(
            "You are an autonomous data analyst. "
            "Analyze the user's question carefully. "
            "For now, provide a concise response explaining "
            "what should be investigated."
        )


        messages = [system_prompt]+state['messages']
        llm = get_llm()
        llm_with_tools=llm.bind_tools(analyst_tools)

        response= llm_with_tools.invoke(messages)
        return{
            "messages" : [response],
            "step_count" : state["step_count"]+1,
            # "findings":response.content
        }

    return analyst_node
    






    
