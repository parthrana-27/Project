import json
import logging
from typing import List, Optional
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    IntentParseResult
)
from nl2code.backend.app.config import get_settings

logger = logging.getLogger("nl2code.llm.openai")

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model_name = model or settings.openai_model
        self.client = None
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    async def _chat(self, user_content: str, system_content: str = "") -> str:
        if not self.client:
            raise RuntimeError("OpenAI API key is not configured or client failed to initialize.")
        
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        
        resp = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.2
        )
        return resp.choices[0].message.content or ""

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
        sys_msg = (
            "You are a Compiler Frontend Intent Analyzer. Analyze the user's natural language algorithm request. "
            "Output strict JSON conforming to: {"
            "  \"task\": string, \"target_language\": string, \"suggested_function_name\": string, "
            "  \"identified_inputs\": [{\"name\": str, \"type\": str}], "
            "  \"identified_outputs\": {\"type\": str, \"description\": str}, "
            "  \"constraints\": [str], \"edge_cases\": [str], \"confidence_score\": float"
            "}"
        )
        raw = await self._chat(prompt, sys_msg)
        return IntentParseResult(**self._extract_json(raw))

    async def build_ir(self, intent: IntentParseResult, language: str) -> IntermediateRepresentation:
        sys_msg = (
            "You are a Compiler Intermediate Representation (IR) Builder. "
            "Construct a strict JSON IntermediateRepresentation covering test cases, constraints, and signature."
        )
        raw = await self._chat(f"Language: {language}\nIntent: {intent.model_dump_json()}", sys_msg)
        data = self._extract_json(raw)
        data["target_language"] = language
        return IntermediateRepresentation(**data)

    async def generate_code(self, ir: IntermediateRepresentation, language: str) -> str:
        sys_msg = f"You are a Compiler Code Synthesizer targeting {language}. Output ONLY raw runnable source code without markdown fences."
        code = await self._chat(f"IR:\n{ir.model_dump_json()}", sys_msg)
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
        sys_msg = f"You are a Compiler Repair Engine targeting {language}. Fix the code based on errors. Output ONLY raw source code."
        user_prompt = f"Attempt: {attempt}\nIR:\n{ir.model_dump_json()}\nBroken Code:\n{code}\nErrors:\n" + "\n".join(errors)
        repaired = await self._chat(user_prompt, sys_msg)
        repaired = repaired.strip()
        if repaired.startswith("```"):
            lines = repaired.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            repaired = "\n".join(lines).strip()
        return repaired
