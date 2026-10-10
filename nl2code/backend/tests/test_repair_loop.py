import asyncio
from typing import List
import pytest
from nl2code.backend.app.core.repair_loop import run_repair_loop
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    InputParam,
    OutputParam,
    TestCase
)
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.models.ir import IntentParseResult

class ControlledRepairMockProvider(LLMProvider):
    def __init__(self, repaired_code: str):
        self.repaired_code = repaired_code
        self.repair_calls = 0

    async def parse_intent(self, prompt: str) -> IntentParseResult:
        raise NotImplementedError

    async def build_ir(self, intent: IntentParseResult, language: str) -> IntermediateRepresentation:
        raise NotImplementedError

    async def generate_code(self, ir: IntermediateRepresentation, language: str) -> str:
        raise NotImplementedError

    async def repair_code(
        self,
        code: str,
        errors: List[str],
        ir: IntermediateRepresentation,
        language: str,
        attempt: int
    ) -> str:
        self.repair_calls += 1
        return self.repaired_code

def test_repair_loop_immediate_success():
    async def _test():
        ir = IntermediateRepresentation(
            task_description="Return doubled number",
            target_language="python",
            function_name="double_val",
            signature="def double_val(x: int) -> int:",
            inputs=[InputParam(name="x", type="int")],
            outputs=OutputParam(type="int"),
            test_cases=[TestCase(id=1, input_args={"x": 5}, expected_output=10)]
        )
        working_code = "def double_val(x: int) -> int:\n    return x * 2\n"
        provider = ControlledRepairMockProvider(working_code)
        
        result = await run_repair_loop(working_code, ir, "python", max_repairs=3, provider=provider)
        assert result.success is True
        assert result.total_attempts == 1
        assert provider.repair_calls == 0
        assert len(result.history) == 1
        assert result.history[0].is_successful is True

    asyncio.run(_test())

def test_repair_loop_recovers_from_syntax_error():
    async def _test():
        ir = IntermediateRepresentation(
            task_description="Return doubled number",
            target_language="python",
            function_name="double_val",
            signature="def double_val(x: int) -> int:",
            inputs=[InputParam(name="x", type="int")],
            outputs=OutputParam(type="int"),
            test_cases=[TestCase(id=1, input_args={"x": 5}, expected_output=10)]
        )
        broken_syntax_code = "def double_val(x: int\n    return x *"
        working_code = "def double_val(x: int) -> int:\n    return x * 2\n"
        provider = ControlledRepairMockProvider(working_code)

        result = await run_repair_loop(broken_syntax_code, ir, "python", max_repairs=3, provider=provider)
        assert result.success is True
        assert result.total_attempts == 2
        assert provider.repair_calls == 1
        assert result.history[0].stage_failed == "validation"
        assert result.history[1].is_successful is True

    asyncio.run(_test())

def test_repair_loop_recovers_from_failing_tests():
    async def _test():
        ir = IntermediateRepresentation(
            task_description="Return doubled number",
            target_language="python",
            function_name="double_val",
            signature="def double_val(x: int) -> int:",
            inputs=[InputParam(name="x", type="int")],
            outputs=OutputParam(type="int"),
            test_cases=[TestCase(id=1, input_args={"x": 5}, expected_output=10)]
        )
        buggy_code = "def double_val(x: int) -> int:\n    return x + 1\n"
        working_code = "def double_val(x: int) -> int:\n    return x * 2\n"
        provider = ControlledRepairMockProvider(working_code)

        result = await run_repair_loop(buggy_code, ir, "python", max_repairs=3, provider=provider)
        assert result.success is True
        assert result.total_attempts == 2
        assert provider.repair_calls == 1
        assert result.history[0].stage_failed == "sandbox"
        assert result.history[1].is_successful is True

    asyncio.run(_test())
