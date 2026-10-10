import pytest
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    InputParam,
    OutputParam,
    ComplexityTarget,
    TestCase
)
from nl2code.backend.app.languages import get_language_adapter
from nl2code.backend.app.llm import get_llm_provider

def test_ir_schema_validation():
    ir = IntermediateRepresentation(
        task_description="Calculate sum of two integers",
        target_language="python",
        function_name="add_numbers",
        signature="def add_numbers(a: int, b: int) -> int:",
        inputs=[
            InputParam(name="a", type="int", description="First number"),
            InputParam(name="b", type="int", description="Second number")
        ],
        outputs=OutputParam(type="int", description="Sum of a and b"),
        constraints=["-10^9 <= a, b <= 10^9"],
        edge_cases=["Zero inputs", "Negative numbers"],
        complexity_target=ComplexityTarget(
            time_complexity="O(1)",
            space_complexity="O(1)",
            explanation="Constant time addition"
        ),
        test_cases=[
            TestCase(id=1, input_args={"a": 2, "b": 3}, expected_output=5),
            TestCase(id=2, input_args={"a": -1, "b": 1}, expected_output=0)
        ]
    )
    assert ir.function_name == "add_numbers"
    assert len(ir.test_cases) == 2
    assert ir.complexity_target.time_complexity == "O(1)"

def test_python_adapter_ast_validation():
    adapter = get_language_adapter("python")
    valid_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    is_valid, err = adapter.validate_syntax(valid_code)
    assert is_valid is True
    assert err is None

    invalid_code = "def broken(a, b\n    return a +"
    is_valid, err = adapter.validate_syntax(invalid_code)
    assert is_valid is False
    assert err is not None

def test_javascript_adapter():
    adapter = get_language_adapter("javascript")
    code = "function test() { return 42; }"
    is_valid, _ = adapter.validate_syntax(code)
    assert is_valid is True

def test_mock_llm_provider_demo_prompt():
    import asyncio

    async def _run():
        provider = get_llm_provider("mock")
        prompt = "Write a function that returns the k most frequent elements in an array"
        
        intent = await provider.parse_intent(prompt)
        assert "frequent" in intent.task.lower()
        assert intent.target_language == "python"

        ir = await provider.build_ir(intent, "python")
        assert ir.function_name == "top_k_frequent"
        assert len(ir.test_cases) >= 2

        code = await provider.generate_code(ir, "python")
        assert "def top_k_frequent" in code
        assert "Counter" in code

    asyncio.run(_run())
