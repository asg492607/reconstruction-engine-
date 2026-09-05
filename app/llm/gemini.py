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
    keys = settings.get_gemini_api_keys()
    if not keys:
        logger.warning("No GEMINI_API_KEY configured; returning None.")
        return None

    model = settings.LLM_MODEL or "gemini-1.5-flash"

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

    for idx, key in enumerate(keys):
        url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={key}"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if not parts:
                        continue

                    return parts[0].get("text", "").strip()
                elif resp.status_code == 429:
                    logger.warning(
                        f"Gemini API key #{idx+1} hit rate limit (429). "
                        f"{'Failing over to next key...' if idx + 1 < len(keys) else 'All keys exhausted.'}"
                    )
                    continue
                else:
                    logger.error(f"Gemini API key #{idx+1} returned HTTP {resp.status_code}: {resp.text}")
                    if resp.status_code in (400, 403) and idx + 1 < len(keys):
                        continue
        except Exception as e:
            logger.error(f"Gemini API invocation failed for key #{idx+1}: {e}")
            if idx + 1 < len(keys):
                continue

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
