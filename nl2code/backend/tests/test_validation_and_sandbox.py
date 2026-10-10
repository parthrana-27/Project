import asyncio
import pytest
from nl2code.backend.app.core.validator import validate_code
from nl2code.backend.app.core.sandbox import execute_in_sandbox
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    InputParam,
    OutputParam,
    TestCase
)

def test_static_validation_security_policy():
    malicious_code = "import os\nos.system('echo hacked')"
    result = validate_code(malicious_code, "python")
    assert result.is_valid is False
    assert any("Security Policy Violation" in err for err in result.errors)

def test_static_validation_syntax_error():
    broken_code = "def foo(x):\n  return x +"
    result = validate_code(broken_code, "python")
    assert result.is_valid is False
    assert any("Syntax Error" in err or "SyntaxError" in err for err in result.errors)

def test_sandbox_execution_python_success():
    async def _test():
        ir = IntermediateRepresentation(
            task_description="Return square of a number",
            target_language="python",
            function_name="square",
            signature="def square(x: int) -> int:",
            inputs=[InputParam(name="x", type="int")],
            outputs=OutputParam(type="int"),
            test_cases=[
                TestCase(id=1, input_args={"x": 3}, expected_output=9),
                TestCase(id=2, input_args={"x": -4}, expected_output=16),
            ]
        )
        code = "def square(x: int) -> int:\n    return x * x\n"
        res = await execute_in_sandbox(code, ir, "python", timeout_seconds=5)
        assert res.passed is True
        assert res.total_tests == 2
        assert res.passed_tests == 2
        assert res.failed_tests == 0

    asyncio.run(_test())

def test_sandbox_execution_python_failure_detection():
    async def _test():
        ir = IntermediateRepresentation(
            task_description="Return square of a number",
            target_language="python",
            function_name="square",
            signature="def square(x: int) -> int:",
            inputs=[InputParam(name="x", type="int")],
            outputs=OutputParam(type="int"),
            test_cases=[
                TestCase(id=1, input_args={"x": 3}, expected_output=9),
            ]
        )
        wrong_code = "def square(x: int) -> int:\n    return x + 1\n"
        res = await execute_in_sandbox(wrong_code, ir, "python", timeout_seconds=5)
        assert res.passed is False
        assert res.failed_tests == 1
        assert "AssertionError" in str(res.test_results[0].error)

    asyncio.run(_test())

def test_sandbox_execution_timeout_enforcement():
    async def _test():
        ir = IntermediateRepresentation(
            task_description="Infinite loop function",
            target_language="python",
            function_name="infinite",
            signature="def infinite(x: int) -> int:",
            inputs=[InputParam(name="x", type="int")],
            outputs=OutputParam(type="int"),
            test_cases=[TestCase(id=1, input_args={"x": 1}, expected_output=1)]
        )
        inf_code = "def infinite(x: int) -> int:\n    while True:\n        pass\n"
        res = await execute_in_sandbox(inf_code, ir, "python", timeout_seconds=1)
        assert res.passed is False
        assert res.timed_out is True

    asyncio.run(_test())
