from typing import List, Optional
from pydantic import BaseModel, Field
from nl2code.backend.app.languages import get_language_adapter

class ValidationResult(BaseModel):
    is_valid: bool = Field(description="True if code passes static syntax validation")
    errors: List[str] = Field(default_factory=list, description="Compiler syntax diagnostic errors")
    warnings: List[str] = Field(default_factory=list, description="Static analysis lint warnings")

def validate_code(code: str, language: str) -> ValidationResult:
    """
    Stage 4: Static Validator.
    Performs abstract syntax analysis, token structure validation,
    and security/lint checks.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not code or not code.strip():
        return ValidationResult(is_valid=False, errors=["Empty source code received."])

    # 1. Security static check
    dangerous_patterns = [
        "__import__('os')", "import os", "import subprocess", "require('child_process')",
        "system(", "Runtime.getRuntime().exec", "popen(", "socket."
    ]
    for pattern in dangerous_patterns:
        if pattern in code:
            errors.append(f"Security Policy Violation: Forbidden system call or import '{pattern}' detected.")

    # 2. Syntax validation via Language Adapter
    try:
        adapter = get_language_adapter(language)
        syntax_ok, syntax_err = adapter.validate_syntax(code)
        if not syntax_ok:
            errors.append(f"Static Syntax Error: {syntax_err}")
    except ValueError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected validator failure: {str(e)}")

    # 3. Basic style / complexity lint checks
    lines = code.split("\n")
    if len(lines) > 200:
        warnings.append("Code length exceeds 200 lines; consider modular decomposition.")

    return ValidationResult(
        is_valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings
    )
