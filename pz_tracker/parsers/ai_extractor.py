"""Extract structured applicant data from PDF text using Groq API (Llama 3)."""

import json
import logging
import os
import time

from groq import Groq
from dotenv import load_dotenv

from config import GROQ_MODEL

load_dotenv()

logger = logging.getLogger(__name__)

# Schema the model must return
_EXTRACTION_SCHEMA = {
    "applicant_name": "string or null – the person who submitted the application",
    "owner_name": "string or null – property owner if different from applicant",
    "general_contractor": "string or null – assigned general contractor / builder",
    "architect": "string or null – architect or engineering firm",
    "applicant_email": "string or null",
    "applicant_phone": "string or null",
    "construction_type": "string or null",
    "land_acres": "string or null",
    "location": "string or null",
    "description": "string or null",
    "pz_meeting_date": "string or null",
}

_SYSTEM_PROMPT = (
    "You are a data-extraction assistant. You will receive the text of a Planning & Zoning "
    "agenda or staff report PDF from a Texas city government. Extract the following fields and "
    "return ONLY valid JSON (no markdown, no explanation, no extra keys):\n\n"
    + json.dumps(_EXTRACTION_SCHEMA, indent=2)
    + "\n\nRules:\n"
    "- Use null for any field you cannot find.\n"
    "- For construction_type, choose one of: Residential, Commercial, Industrial, "
    "Mixed-Use, Restaurant, Retail, or Other.\n"
    "- For pz_meeting_date, format as YYYY-MM-DD if possible.\n"
    "- For land_acres, include the numeric value and unit (e.g. '12.5 acres').\n"
    "- owner_name is the property owner (may differ from applicant).\n"
    "- general_contractor is the builder or general contractor assigned to the project.\n"
    "- architect is the architect or engineering firm (e.g. the firm that prepared plans).\n"
    "- Return a JSON array if the document contains multiple distinct applications.\n"
)


def extract_from_text(pdf_text: str, city: str = "", meeting_date: str = "") -> list[dict]:
    """Send *pdf_text* to Groq (Llama 3) and return a list of extracted records.

    Each record is a dict matching ``_EXTRACTION_SCHEMA`` keys.
    Returns an empty list when extraction fails.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not set - skipping AI extraction")
        return []

    client = Groq(api_key=api_key)

    # Groq context window is ~128k for llama-3.3-70b; keep text reasonable
    user_content = (
        f"City: {city}\nMeeting date hint: {meeting_date}\n\n"
        f"--- BEGIN PDF TEXT ---\n{pdf_text[:25_000]}\n--- END PDF TEXT ---"
    )

    try:
        raw = None
        for attempt in range(1, 4):
            try:
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    max_tokens=4096,
                    temperature=0.1,
                )
                break  # success
            except Exception as exc:
                if "429" in str(exc) and attempt < 3:
                    wait = 20 * attempt
                    logger.warning("Rate limited (attempt %d/3) - waiting %ds", attempt, wait)
                    time.sleep(wait)
                else:
                    raise

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3].strip()

        data = json.loads(raw)

        # Normalise to a list
        if isinstance(data, dict):
            data = [data]

        logger.info("Groq extracted %d record(s) for %s", len(data), city)
        return data

    except json.JSONDecodeError:
        logger.error("Groq returned non-JSON response: %.200s", raw)
        return []
    except Exception:
        logger.exception("Unexpected error during AI extraction")
        return []
