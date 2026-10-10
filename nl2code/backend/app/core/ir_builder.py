from typing import Optional
from nl2code.backend.app.models.ir import IntentParseResult, IntermediateRepresentation
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.llm import get_llm_provider
from nl2code.backend.app.languages import get_language_adapter

async def build_compiler_ir(
    intent: IntentParseResult,
    target_language: str,
    provider: Optional[LLMProvider] = None
) -> IntermediateRepresentation:
    """
    Stage 2: IR Builder.
    Produces strict JSON IR validated by Pydantic schema.
    """
    llm = provider or get_llm_provider()
    ir = await llm.build_ir(intent, target_language)
    
    # Ensure target language matches
    ir.target_language = target_language.lower().strip()
    
    # Ensure signature is consistent with adapter if missing or generic
    try:
        adapter = get_language_adapter(target_language)
        if not ir.signature or ir.signature.strip() == "":
            ir.signature = adapter.format_signature(ir)
    except Exception:
        pass
        
    if not ir.test_cases:
        raise ValueError("IR validation error: at least one test case must be specified.")
        
    return ir
