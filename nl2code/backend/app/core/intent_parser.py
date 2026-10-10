from typing import Optional
from nl2code.backend.app.models.ir import IntentParseResult
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.llm import get_llm_provider

async def parse_user_intent(
    prompt: str,
    target_language: Optional[str] = None,
    provider: Optional[LLMProvider] = None
) -> IntentParseResult:
    """
    Stage 1: Intent Parser.
    Extracts algorithmic task, parameters, returns, constraints, and edge cases.
    """
    cleaned_prompt = prompt.strip()
    if not cleaned_prompt:
        raise ValueError("Prompt cannot be empty. Please provide an algorithmic description.")
    
    if len(cleaned_prompt) < 5:
        raise ValueError("Prompt is too ambiguous or short. Please provide more detail.")

    llm = provider or get_llm_provider()
    intent = await llm.parse_intent(cleaned_prompt)
    
    if target_language:
        intent.target_language = target_language.lower().strip()
        
    return intent
