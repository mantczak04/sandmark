import json
import os
import time

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"


def run_review(prompt_text: str, diff_data: dict) -> dict:
    """Send the diff to Gemini with the master prompt and return structured review."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    diff_payload = json.dumps(diff_data, indent=2)

    full_prompt = (
        f"{prompt_text}\n\n"
        f"--- MERGE REQUEST DIFF ---\n"
        f"{diff_payload}\n"
        f"--- END DIFF ---\n\n"
        f"Respond ONLY with valid JSON in this exact format:\n"
        f'{{\n'
        f'  "comments": [\n'
        f'    {{\n'
        f'      "file": "path/to/file",\n'
        f'      "line": 42,\n'
        f'      "type": "bug|style|performance|security|suggestion",\n'
        f'      "comment": "Description of the issue and suggested fix."\n'
        f'    }}\n'
        f'  ],\n'
        f'  "summary": "Brief overall assessment of the merge request."\n'
        f'}}\n'
    )

    start_time = time.time()
    response = model.generate_content(full_prompt)
    elapsed = time.time() - start_time

    response_text = response.text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    review = json.loads(response_text)

    tokens_used = 0
    if response.usage_metadata:
        tokens_used = (
            getattr(response.usage_metadata, "prompt_token_count", 0)
            + getattr(response.usage_metadata, "candidates_token_count", 0)
        )

    return {
        "review": review,
        "tokens_used": tokens_used,
        "time_seconds": round(elapsed, 2),
    }
