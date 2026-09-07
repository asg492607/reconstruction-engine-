import json
import logging
import re
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    """
    Unified AI / LLM orchestration client for RRE.
    Supports:
    - Google Gemini (gemini-1.5-flash, gemini-2.0, etc.)
    - OpenAI / local vLLM / Ollama (via standard chat/completions)

    NO-AI-FALLBACK POLICY:
    When the required LLM/model capability is unavailable, methods return None.
    Calling engines MUST return BLOCKED status — never substitute deterministic
    or synthetic output for a missing required AI capability.
    """

    def __init__(self):
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.last_execution_info: Dict[str, Any] = {
            "provider": "UNAVAILABLE",
            "model": "NONE",
            "execution_path": "NOT_STARTED",
            "fallback_used": "NOT_APPLICABLE"
        }

    def get_active_provider_info(self) -> Dict[str, Any]:
        keys = settings.get_gemini_api_keys()
        if keys:
            return {
                "provider": "gemini",
                "model": settings.LLM_MODEL or "gemini-2.0-flash-lite",
                "configured": True,
                "key_count": len(keys)
            }
        elif settings.OPENAI_API_KEY:
            return {
                "provider": "openai",
                "model": settings.LLM_MODEL or "gpt-4o-mini",
                "configured": True
            }
        return {
            "provider": "UNAVAILABLE",
            "model": "NONE",
            "configured": False
        }

    def get_execution_telemetry(self) -> Dict[str, Any]:
        """
        Returns the truthful execution telemetry from the last LLM call.
        Engines should stamp this onto their EngineExecutionRecord after calling any AI method.

        Example record fields:
            record.actual_execution_path = telem["execution_path"]
            record.llm_provider = telem["provider"]
            record.llm_model = telem["model"]
            record.fallback_used = telem["fallback_used"]
        """
        return dict(self.last_execution_info)

    async def call_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        response_json: bool = False,
        timeout: float = 30.0
    ) -> Optional[str]:
        keys = settings.get_gemini_api_keys()
        if not keys:
            return None

        model = settings.LLM_MODEL or "gemini-2.0-flash-lite"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096
            }
        }
        if response_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        for idx, key in enumerate(keys):
            url = f"{self.gemini_url}/{model}:generateContent?key={key}"
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    elif resp.status_code == 429:
                        logger.warning(
                            f"Gemini API key #{idx+1} exceeded quota/rate limit (429). "
                            f"{'Trying next configured key...' if idx + 1 < len(keys) else 'All keys exhausted.'}"
                        )
                        continue
                    else:
                        logger.warning(f"Gemini API key #{idx+1} returned status {resp.status_code}: {resp.text}")
                        if resp.status_code in (400, 403) and idx + 1 < len(keys):
                            continue
            except Exception as e:
                logger.warning(f"Gemini API call failed for key #{idx+1}: {e}")
                if idx + 1 < len(keys):
                    continue
        return None

    async def call_openai(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        response_json: bool = False,
        timeout: float = 30.0
    ) -> Optional[str]:
        if not settings.OPENAI_API_KEY:
            return None

        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.LLM_MODEL if "gpt" in settings.LLM_MODEL.lower() else "gpt-4o-mini",
            "messages": messages,
            "temperature": temperature
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
        return None

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Queries active LLM backend requesting strictly valid JSON.
        Returns None if no LLM is available or the call fails.
        """
        raw_output = None
        if settings.get_gemini_api_keys():
            raw_output = await self.call_gemini(
                prompt=prompt,
                system_instruction=system_instruction,
                response_json=True,
                timeout=timeout
            )
        elif settings.OPENAI_API_KEY:
            raw_output = await self.call_openai(
                prompt=prompt,
                system_instruction=system_instruction,
                response_json=True,
                timeout=timeout
            )

        prov = self.get_active_provider_info()
        if not raw_output:
            self.last_execution_info = {
                "provider": prov.get("provider", "UNAVAILABLE"),
                "model": prov.get("model", "NONE"),
                "execution_path": "BLOCKED_LLM_FAILED",
                "fallback_used": "BLOCKED"
            }
            return None

        try:
            clean = raw_output.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            parsed = json.loads(clean.strip())
            self.last_execution_info = {
                "provider": prov.get("provider", "gemini"),
                "model": prov.get("model", settings.LLM_MODEL),
                "execution_path": "REAL_LLM",
                "fallback_used": "NO"
            }
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}\nRaw: {raw_output}")
            self.last_execution_info = {
                "provider": prov.get("provider", "gemini"),
                "model": prov.get("model", settings.LLM_MODEL),
                "execution_path": "BLOCKED_LLM_FAILED",
                "fallback_used": "BLOCKED"
            }
            return None

    # ---------------------------------------------------------------------------
    # Analytical AI Prompt Workflows
    # ---------------------------------------------------------------------------
    async def parse_witness_statement(self, text: str, witness_name: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Extracts factual claims, temporal references, described actors, and certainty from witness text.

        Returns a list of claim dicts if LLM is available and responds correctly.
        Returns None if LLM is unavailable — callers MUST return BLOCKED status in this case.

        NO-AI-FALLBACK POLICY: No deterministic extraction is performed here.
        """
        prov = self.get_active_provider_info()
        if not prov["configured"]:
            self.last_execution_info = {
                "provider": "UNAVAILABLE",
                "model": "NONE",
                "execution_path": "BLOCKED_LLM_UNAVAILABLE",
                "fallback_used": "BLOCKED"
            }
            return None

        system_prompt = (
            "You are a forensic testimonial analyst. Extract empirical observations from the witness statement. "
            "Output JSON with key 'claims': list of objects with fields: "
            "'claim_id', 'witness_name', 'stated_time', 'actor_described', 'action_observed', "
            "'clothing_color', 'clothing_type', 'perceived_urgency', 'credibility_heuristic', 'raw_excerpt'. "
            "Never invent facts not mentioned in the statement text."
        )
        user_prompt = f"Witness Name: {witness_name or 'Unknown'}\n\nStatement Text:\n{text}"

        llm_res = await self.generate_json(user_prompt, system_prompt)
        if llm_res and "claims" in llm_res and isinstance(llm_res["claims"], list):
            self.last_execution_info = {
                "provider": prov["provider"],
                "model": prov["model"],
                "execution_path": "REAL_LLM",
                "fallback_used": "NO"
            }
            return llm_res["claims"]

        # LLM was configured but returned unusable output (quota, error, malformed JSON)
        self.last_execution_info = {
            "provider": prov["provider"],
            "model": prov["model"],
            "execution_path": "BLOCKED_LLM_FAILED",
            "fallback_used": "BLOCKED"
        }
        return None

    async def generate_hypotheses(
        self,
        case_title: str,
        offense_type: str,
        evidence_summary: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Synthesizes competing evidence-backed reconstruction hypotheses.

        Returns a list of hypothesis dicts if LLM is available and responds correctly.
        Returns None if LLM is unavailable — caller (R01) MUST return BLOCKED.

        NO-AI-FALLBACK POLICY: No canned hypotheses are substituted here.
        """
        prov = self.get_active_provider_info()
        if not prov["configured"]:
            self.last_execution_info = {
                "provider": "UNAVAILABLE",
                "model": "NONE",
                "execution_path": "BLOCKED_LLM_UNAVAILABLE",
                "fallback_used": "BLOCKED"
            }
            return None

        system_prompt = (
            "You are the Lead Reconstruction AI. Generate mutually competing reconstruction hypotheses "
            "(Primary Probable, Alternative Inadvertent, Third-Party/Benign). "
            "Output JSON with key 'hypotheses': list of objects with fields: "
            "'hypothesis_id', 'hypothesis_title', 'hypothesis_category', 'narrative', "
            "'supporting_evidence_citations', 'unresolved_uncertainties', 'confidence_score', 'theft_conclusion_supported'. "
            "STRICT RULE: Every narrative claim MUST cite specific observations from the provided evidence. "
            "Never declare legal guilt or confirm theft autonomously."
        )
        user_prompt = (
            f"Case Title: {case_title}\nOffense: {offense_type}\n\n"
            f"Collected Evidence Observations:\n{json.dumps(evidence_summary, indent=2)}\n\n"
            f"Identified Gaps:\n{json.dumps(gaps, indent=2)}\n\n"
            f"Identified Conflicts:\n{json.dumps(conflicts, indent=2)}"
        )

        llm_res = await self.generate_json(user_prompt, system_prompt)
        if llm_res and "hypotheses" in llm_res and isinstance(llm_res["hypotheses"], list):
            self.last_execution_info = {
                "provider": prov["provider"],
                "model": prov["model"],
                "execution_path": "REAL_LLM",
                "fallback_used": "NO"
            }
            return llm_res["hypotheses"]

        self.last_execution_info = {
            "provider": prov["provider"],
            "model": prov["model"],
            "execution_path": "BLOCKED_LLM_FAILED",
            "fallback_used": "BLOCKED"
        }
        return None

    async def challenge_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Stress-tests hypotheses from an adversarial skeptical defense perspective.

        Returns a list of challenge dicts if LLM is available and responds correctly.
        Returns None if LLM is unavailable — caller (R03) MUST return BLOCKED.

        NO-AI-FALLBACK POLICY: No canned challenges are substituted here.
        """
        prov = self.get_active_provider_info()
        if not prov["configured"]:
            self.last_execution_info = {
                "provider": "UNAVAILABLE",
                "model": "NONE",
                "execution_path": "BLOCKED_LLM_UNAVAILABLE",
                "fallback_used": "BLOCKED"
            }
            return None

        system_prompt = (
            "You are an Adversarial Defense Examiner. Attack each hypothesis by exposing unsupported assumptions, "
            "unmonitored blind spots, missing biometric verifications, and alternative non-criminal explanations. "
            "Output JSON with key 'challenges': list of objects with fields: "
            "'target_hypothesis_id', 'challenge_vector', 'adversarial_objection', "
            "'counter_evidence_strength', 'rebuttal_grounding', 'evidentiary_vulnerability'."
        )
        user_prompt = (
            f"Hypotheses:\n{json.dumps(hypotheses, indent=2)}\n\n"
            f"Gaps:\n{json.dumps(gaps, indent=2)}\n\n"
            f"Conflicts:\n{json.dumps(conflicts, indent=2)}"
        )

        llm_res = await self.generate_json(user_prompt, system_prompt)
        if llm_res and "challenges" in llm_res and isinstance(llm_res["challenges"], list):
            self.last_execution_info = {
                "provider": prov["provider"],
                "model": prov["model"],
                "execution_path": "REAL_LLM",
                "fallback_used": "NO"
            }
            return llm_res["challenges"]

        self.last_execution_info = {
            "provider": prov["provider"],
            "model": prov["model"],
            "execution_path": "BLOCKED_LLM_FAILED",
            "fallback_used": "BLOCKED"
        }
        return None


ai_client = AIClient()
