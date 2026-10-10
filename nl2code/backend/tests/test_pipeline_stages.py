import asyncio
import pytest
from nl2code.backend.app.core.intent_parser import parse_user_intent
from nl2code.backend.app.core.ir_builder import build_compiler_ir
from nl2code.backend.app.core.code_generator import synthesize_code
from nl2code.backend.app.llm.mock import MockLLMProvider

def test_pipeline_stages_top_k_frequent():
    async def _test():
        provider = MockLLMProvider()
        prompt = "Write a function that returns the k most frequent elements in an array"
        
        # 1. Intent Parse
        intent = await parse_user_intent(prompt, "python", provider)
        assert "frequent" in intent.task.lower()
        assert intent.target_language == "python"

        # 2. IR Builder
        ir = await build_compiler_ir(intent, "python", provider)
        assert ir.function_name == "top_k_frequent"
        assert len(ir.test_cases) >= 3
        assert ir.complexity_target.time_complexity != ""

        # 3. Code Generator
        code = await synthesize_code(ir, "python", provider)
        assert "def top_k_frequent" in code
        assert "Counter" in code

    asyncio.run(_test())

def test_pipeline_stages_palindrome_cpp():
    async def _test():
        provider = MockLLMProvider()
        prompt = "Check if a string is a valid palindrome ignoring punctuation and case"
        
        intent = await parse_user_intent(prompt, "cpp", provider)
        ir = await build_compiler_ir(intent, "cpp", provider)
        code = await synthesize_code(ir, "cpp", provider)
        
        assert ir.function_name == "is_palindrome"
        assert "bool is_palindrome" in code

    asyncio.run(_test())

def test_pipeline_stages_debounce_js():
    async def _test():
        provider = MockLLMProvider()
        prompt = "Debounce a function by N milliseconds"
        
        intent = await parse_user_intent(prompt, "javascript", provider)
        ir = await build_compiler_ir(intent, "javascript", provider)
        code = await synthesize_code(ir, "javascript", provider)
        
        assert ir.function_name == "debounce_tester"
        assert "function debounce_tester" in code

    asyncio.run(_test())

def test_pipeline_error_on_empty_prompt():
    async def _test():
        with pytest.raises(ValueError, match="cannot be empty"):
            await parse_user_intent("   ", "python")

    asyncio.run(_test())
