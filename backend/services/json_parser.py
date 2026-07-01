import json
import re


def parse_llm_json(text: str):
    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text.strip())
    except Exception:
        raise ValueError(f"Invalid JSON:\n{text}")
