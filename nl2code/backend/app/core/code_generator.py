from typing import Optional
from nl2code.backend.app.models.ir import IntermediateRepresentation
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.llm import get_llm_provider

async def synthesize_code(
    ir: IntermediateRepresentation,
    target_language: str,
    provider: Optional[LLMProvider] = None
) -> str:
    """
    Stage 3: Code Generator.
    Synthesizes code from the verified IR via LLM provider.
    """
    llm = provider or get_llm_provider()
    code = await llm.generate_code(ir, target_language)
    
    # Strip unnecessary markdown fences if returned by external LLMs
    code = code.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines).strip()
        
    return code
