"""Research and draft leads for Vendorix using Claude + web search."""
import json
import re
from pathlib import Path

import anthropic

MODEL = "claude-opus-5"
MAX_TOOL_ROUNDS = 6

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_system_prompt() -> str:
    return (PROMPTS_DIR / "system_prompt.md").read_text()


def _extract_json_array(text: str) -> list[dict]:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in model output:\n{text[:500]}")
    return json.loads(text[start : end + 1])


def research_leads(
    client: anthropic.Anthropic, icp_text: str, limit: int, exclude_keys: set[str]
) -> list[dict]:
    system = _load_system_prompt()
    exclusions = "\n".join(sorted(exclude_keys)) or "(none yet)"
    user_prompt = (
        f"ICP:\n{icp_text}\n\n"
        f"Find up to {limit} NEW leads matching this ICP. Skip anyone already in this "
        f"list (match by LinkedIn URL, or by name+company):\n{exclusions}\n\n"
        "Respond with ONLY a JSON array (no prose, no markdown fences) using this exact "
        "shape per lead:\n"
        '[{"name": "...", "title": "...", "company": "...", "company_domain": "... or null", '
        '"linkedin_profile_url": "... or null", "contact_email": "... or null", '
        '"source_url": "...", "fit_reason": "...", "connection_note": "...", '
        '"followup_dm": "..."}]'
    )

    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 25}]
    messages = [{"role": "user", "content": user_prompt}]

    response = None
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=system,
            tools=tools,
            messages=messages,
        )
        if response.stop_reason == "pause_turn":
            messages = messages + [{"role": "assistant", "content": response.content}]
            continue
        break
    else:
        raise RuntimeError("Research loop did not finish within MAX_TOOL_ROUNDS")

    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json_array(text)
