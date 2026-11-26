from agent.guardrails.pil_guardrails import redact_text
from agent.tool_policy import DATA_TOOL_NAMES



_RELEASE_BOUNDARY = re.compile(r"[.!?]\s+|\n+")



class StreamingOutputGuard:
    def __init__(
        self,
        max_characters: int,
        max_buffer_characters: int = 240,
    ) -> None:
        self.max_characters = max_characters
        self.max_buffer_characters = max_buffer_characters
        self.buffer = ""
        self.released_characters = 0

    def push(self, text: str) -> list[str]:
        if not text:
            return []

        self.buffer += text
        return self._release_ready_content(force=False)

    def finish(self) -> list[str]:
        return self._release_ready_content(force=True)

    def _release_ready_content(self, force: bool) -> list[str]:
        released_chunks = []

        while self.buffer:
            remaining = (
                self.max_characters
                - self.released_characters
            )

            if remaining <= 0:
                self.buffer = ""
                break

            boundary = _RELEASE_BOUNDARY.search(self.buffer)

            if boundary:
                release_index = boundary.end()
            elif len(self.buffer) >= self.max_buffer_characters:
                release_index = self.buffer.rfind(
                    " ",
                    0,
                    self.max_buffer_characters,
                )

                if release_index <= 0:
                    release_index = self.max_buffer_characters
                else:
                    release_index += 1

            elif force:
                release_index = len(self.buffer)

            else:
                break

            raw_chunk = self.buffer[:release_index]
            self.buffer = self.buffer[release_index:]

            safe_chunk = redact_text(raw_chunk)

            if len(safe_chunk) > remaining:
                safe_chunk = safe_chunk[:remaining]
                self.buffer = ""

            if safe_chunk:
                released_chunks.append(safe_chunk)
                self.released_characters += len(safe_chunk)

        return released_chunks




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