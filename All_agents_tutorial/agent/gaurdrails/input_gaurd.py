import re 


class InputGuardrailError(ValueError):
    pass



PROMPT_INJECTION_PATTERNS = [
    r"\bignore (all |any |the )?(previous|prior|above) instructions?\b",
    r"\b(system prompt|developer message|hidden instructions?)\b",
    r"\b(reveal|override|disregard)\b.*\b(prompt|instructions?)\b",
]


def validate_objective(
    objective: str,
    max_characters: int = 1000
    ) -> str:

    if not isinstance(objective, str):
        raise InputGuardrailError("Objective must be a string")
        

    if not objective or not objective.strip():
        raise InputGuardrailError("Objective cannot be empty")
    
    if len(objective) > max_characters:
        raise InputGuardrailError(f"Objective too long: {len(objective)} characters")
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, objective, re.IGNORECASE):
            raise InputGuardrailError(f"Potential prompt injection detected: {objective}")
    
    return objective.strip()