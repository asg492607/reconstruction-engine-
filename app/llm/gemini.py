import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

async def call_gemini(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    response_json: bool = False,
    timeout: float = 25.0
) -> Optional[str]:
    """
    Direct asynchronous call to Google Gemini 3.6 / Flash API using provided API key.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY configured; returning None.")
        return None

    model = settings.LLM_MODEL or "gemini-3.6-flash"
    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={settings.GEMINI_API_KEY}"

    payload: Dict[str, Any] = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 2048
        }
    }

    if response_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
                return None

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return None

            return parts[0].get("text", "").strip()

    except Exception as e:
        logger.error(f"Gemini API invocation failed: {e}")
        return None

async def query_gemini_json(
    prompt: str,
    system_instruction: Optional[str] = None,
    timeout: float = 25.0
) -> Optional[Dict[str, Any]]:
    """
    Calls Gemini API requesting valid JSON output and parses it.
    """
    raw_text = await call_gemini(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.1,
        response_json=True,
        timeout=timeout
    )
    if not raw_text:
        return None

    try:
        # Strip markdown fences if present
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        return json.loads(clean_text.strip())
    except Exception as e:
        logger.error(f"Failed to parse JSON from Gemini response: {e}\nRaw output:\n{raw_text}")
        return None
