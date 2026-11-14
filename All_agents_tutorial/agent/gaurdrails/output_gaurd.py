from agent.guardrails.pii_guard import redact_text
from agent.tool_policy import DATA_TOOL_NAMES


def sanitize_final_report(
    report: str,
    findings: list[dict],
    tool_observations: list[dict],
    max_characters: int,
) -> str:
    clean_report = redact_text(str(report).strip())

    if not clean_report:
        return (
            "The investigation finished without a usable final report."
        )

    if len(clean_report) > max_characters:
        clean_report = (
            clean_report[:max_characters]
            + "\n\n[Report truncated for safety.]"
        )

    used_data_tools = any(
        observation["tool_name"] in DATA_TOOL_NAMES
        for observation in tool_observations
    )

    if used_data_tools and not findings:
        return (
            "The investigation is incomplete. Data was analyzed, "
            "but no evidence-backed finding was recorded, so a "
            "reliable conclusion cannot be returned."
        )

    return clean_report