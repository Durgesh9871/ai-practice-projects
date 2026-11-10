from agent.graphstate import InvestigationGraphState
from agent.tool_policy import DATA_TOOL_NAMES


def extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        ).strip()

    return str(content).strip()


def validate_completion(state: InvestigationGraphState) -> dict:
    errors = []

    latest_answer = extract_text(state["messages"][-1].content)

    if not latest_answer:
        errors.append("Final answer is missing.")

    valid_evidence_ids = {
        observation["tool_call_id"]
        for observation in state["tool_observation"]
        if observation["tool_name"] in DATA_TOOL_NAMES
    }

    used_run_sql = any(
        observation["tool_name"] == "run_sql"
        for observation in state["tool_observation"]
    )

    if used_run_sql and not state["findings"]:
        errors.append(
            "SQL analysis was performed, but no evidence-backed finding was recorded."
        )

    for finding in state["findings"]:
        invalid_ids = [
            evidence_id
            for evidence_id in finding["evidence_ids"]
            if evidence_id not in valid_evidence_ids
        ]

        if invalid_ids:
            errors.append(
                f"Finding contains invalid evidence IDs: {invalid_ids}"
            )

        if not 0.0 <= finding["confidence"] <= 1.0:
            errors.append(
                "Finding confidence must be between 0 and 1."
            )

    return {
        "completion_valid": not errors,
        "completion_feedback": " ".join(errors),
        "completion_attempts": state["completion_attempts"] + 1,
    }