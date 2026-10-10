from typing import List, Any, Dict, Optional
from pydantic import BaseModel, Field

class InputParam(BaseModel):
    name: str = Field(description="Parameter variable name")
    type: str = Field(description="Data type in target language")
    description: Optional[str] = Field(default="", description="Description of the parameter")

class OutputParam(BaseModel):
    type: str = Field(description="Return data type in target language")
    description: Optional[str] = Field(default="", description="Description of the return value")

class ComplexityTarget(BaseModel):
    time_complexity: str = Field(default="O(n)", description="Expected asymptotic time complexity")
    space_complexity: str = Field(default="O(1)", description="Expected auxiliary space complexity")
    explanation: Optional[str] = Field(default="", description="Theoretical explanation of complexity")

class TestCase(BaseModel):
    __test__ = False
    id: int = Field(description="Unique test case identifier")
    name: Optional[str] = Field(default="", description="Test case name or label")
    input_args: Dict[str, Any] = Field(description="Mapping of argument names to values")
    expected_output: Any = Field(description="Expected output value")
    is_edge_case: bool = Field(default=False, description="Whether this targets a boundary condition")
    description: Optional[str] = Field(default="", description="Why this test case is included")

class IntermediateRepresentation(BaseModel):
    """
    Compiler Intermediate Representation (IR) capturing semantic specification
    derived from natural language intent prior to target code synthesis.
    """
    task_description: str = Field(description="Normalized English specification of the algorithm")
    target_language: str = Field(default="python", description="Target programming language")
    function_name: str = Field(description="Identifier for the main algorithmic function")
    signature: str = Field(description="Function signature string in target language")
    inputs: List[InputParam] = Field(default_factory=list, description="Input parameters and types")
    outputs: OutputParam = Field(description="Expected output type and description")
    constraints: List[str] = Field(default_factory=list, description="Problem constraints and bounds")
    edge_cases: List[str] = Field(default_factory=list, description="Identified edge cases to handle")
    complexity_target: ComplexityTarget = Field(default_factory=ComplexityTarget, description="Complexity bounds")
    test_cases: List[TestCase] = Field(default_factory=list, description="Strict unit test suite")

class IntentParseResult(BaseModel):
    task: str
    target_language: str = "python"
    identified_inputs: List[Dict[str, str]] = Field(default_factory=list)
    identified_outputs: Dict[str, str] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)
    suggested_function_name: str = "solve"
    confidence_score: float = 1.0
