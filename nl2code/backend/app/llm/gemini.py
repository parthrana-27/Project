import json
import logging
from typing import List, Optional
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    IntentParseResult
)
from nl2code.backend.app.config import get_settings

logger = logging.getLogger("nl2code.llm.gemini")

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model or settings.gemini_model
        self.client = None
        
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize google.genai: {e}")

    async def _generate_content(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise RuntimeError("Gemini API key is not configured or client failed to initialize.")
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={"system_instruction": system_instruction} if system_instruction else None
        )
        return response.text or ""

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
        raw = await self._generate_content(f"Analyze request:\n{prompt}", sys_msg)
        data = self._extract_json(raw)
        return IntentParseResult(**data)

    async def build_ir(self, intent: IntentParseResult, language: str) -> IntermediateRepresentation:
        sys_msg = (
            "You are a Compiler Intermediate Representation (IR) Builder. "
            "Given the parsed intent, construct a strict, comprehensive Intermediate Representation. "
            "Include 3-5 diverse test cases covering normal and boundary conditions. "
            "Output JSON conforming strictly to the IntermediateRepresentation schema."
        )
        user_prompt = f"Target Language: {language}\nIntent: {intent.model_dump_json()}"
        raw = await self._generate_content(user_prompt, sys_msg)
        data = self._extract_json(raw)
        data["target_language"] = language
        return IntermediateRepresentation(**data)

    async def generate_code(self, ir: IntermediateRepresentation, language: str) -> str:
        sys_msg = (
            f"You are a Code Synthesis Compiler Backend targeting {language}. "
            "Generate ONLY pure, runnable source code without markdown fences, without explanations. "
            "The function signature and parameter names must strictly match the provided IR."
        )
        user_prompt = f"Synthesize implementation for IR:\n{ir.model_dump_json()}"
        code = await self._generate_content(user_prompt, sys_msg)
        # Strip potential markdown fences
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
        sys_msg = (
            f"You are an Automatic Program Repair engine for a Compiler targeting {language}. "
            "Given the previous code attempt, the compiler diagnostics and failed test outputs, "
            "repair and regenerate the complete, fixed source code. Output ONLY raw source code."
        )
        user_prompt = (
            f"Attempt: {attempt}\n"
            f"Target IR:\n{ir.model_dump_json()}\n\n"
            f"Previous Broken Code:\n{code}\n\n"
            f"Compiler Diagnostics / Failed Tests:\n" + "\n".join(errors)
        )
        repaired = await self._generate_content(user_prompt, sys_msg)
        repaired = repaired.strip()
        if repaired.startswith("```"):
            lines = repaired.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            repaired = "\n".join(lines).strip()
        return repaired
