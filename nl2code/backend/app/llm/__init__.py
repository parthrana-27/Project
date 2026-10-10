import os
from typing import Optional
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.llm.mock import MockLLMProvider
from nl2code.backend.app.llm.gemini import GeminiProvider
from nl2code.backend.app.llm.openai_client import OpenAIProvider
from nl2code.backend.app.llm.anthropic_client import AnthropicProvider
from nl2code.backend.app.config import get_settings

def get_llm_provider(override_provider: Optional[str] = None) -> LLMProvider:
    settings = get_settings()
    provider_name = (override_provider or settings.llm_provider).lower().strip()

    # Automatic fallback if provider is gemini/openai/anthropic but no API key is provided
    if provider_name == "gemini":
        if settings.gemini_api_key or os.getenv("GEMINI_API_KEY"):
            return GeminiProvider()
        return MockLLMProvider()
    elif provider_name == "openai":
        if settings.openai_api_key or os.getenv("OPENAI_API_KEY"):
            return OpenAIProvider()
        return MockLLMProvider()
    elif provider_name == "anthropic":
        if settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"):
            return AnthropicProvider()
        return MockLLMProvider()
    else:
        return MockLLMProvider()
