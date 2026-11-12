from langchain_core.messages import HumanMessage, SystemMessage

from agent.config import setting
from agent.graphstate import InvestigationGraphState
from agent.provider.factory import get_llm


def get_text(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        ).strip()

    return str(content).strip()


def format_messages(messages) -> str:
    formatted = []

    for message in messages:
        text = get_text(message.content)

        if text:
            formatted.append(
                f"{message.type.upper()}: {text[:2000]}"
            )

    return "\n\n".join(formatted)


def context_manager_node(
    state: InvestigationGraphState,
) -> dict:
    messages = state["messages"]
    total_messages = len(messages)

    if total_messages <= setting.max_context_messages:
        return {}

    cutoff = total_messages - setting.recent_messages_to_keep
    summarized_count = state.get("summarized_message_count", 0)

    if cutoff <= summarized_count:
        return {}

    messages_to_summarize = messages[summarized_count:cutoff]

    if not messages_to_summarize:
        return {}

    previous_summary = state.get("conversation_summary", "")
    history_text = format_messages(messages_to_summarize)

    prompt = f"""
You maintain compact memory for a self-driving data analyst.

Existing memory:
{previous_summary or "No earlier summary exists."}

New conversation history:
{history_text}

Create an updated factual summary. Preserve:
- user objectives and follow-up questions
- inspected tables and SQL results
- confirmed findings and evidence
- SQL errors and repairs
- unresolved tasks

Do not invent facts. Keep it concise.
"""

    response = get_llm().invoke(
        [SystemMessage(content=prompt)]
    )

    return {
        "conversation_summary": get_text(response.content),
        "summarized_message_count": cutoff,
    }