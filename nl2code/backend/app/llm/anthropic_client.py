import json
import logging
import httpx
from typing import List, Optional
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    IntentParseResult
)
from nl2code.backend.app.config import get_settings

logger = logging.getLogger("nl2code.llm.anthropic")

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model_name = model or settings.anthropic_model

    async def _call_api(self, user_content: str, system_content: str = "") -> str:
        if not self.api_key:
            raise RuntimeError("Anthropic API key is not configured.")
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": user_content}]
        }
        if system_content:
            payload["system"] = system_content

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    async def parse_intent(self, prompt: str) -> IntentParseResult:
        sys_msg = "Extract compiler intent in JSON: {task, target_language, suggested_function_name, identified_inputs, identified_outputs, constraints, edge_cases, confidence_score}"
        raw = await self._call_api(prompt, sys_msg)
        return IntentParseResult(**self._extract_json(raw))

    async def build_ir(self, intent: IntentParseResult, language: str) -> IntermediateRepresentation:
        sys_msg = "Build strict JSON IntermediateRepresentation covering test cases, constraints, and signature."
        raw = await self._call_api(f"Language: {language}\nIntent: {intent.model_dump_json()}", sys_msg)
        data = self._extract_json(raw)
        data["target_language"] = language
        return IntermediateRepresentation(**data)

    async def generate_code(self, ir: IntermediateRepresentation, language: str) -> str:
        sys_msg = f"Synthesize pure source code in {language} for IR. Return ONLY code without markdown."
        code = await self._call_api(f"IR:\n{ir.model_dump_json()}", sys_msg)
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines).strip()
        return code

    async def repair_code(
        self,
        code: str,
        errors: List[str],
        ir: IntermediateRepresentation,
        language: str,
        attempt: int
    ) -> str:
        sys_msg = f"Repair code in {language}. Output ONLY fixed raw source code."
        user_prompt = f"Attempt: {attempt}\nIR:\n{ir.model_dump_json()}\nCode:\n{code}\nErrors:\n" + "\n".join(errors)
        repaired = await self._call_api(user_prompt, sys_msg)
        repaired = repaired.strip()
        if repaired.startswith("```"):
            lines = repaired.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            repaired = "\n".join(lines).strip()
        return repaired
