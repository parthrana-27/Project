import logging
from typing import List, Optional, Callable, Any, Awaitable
from pydantic import BaseModel, Field

from nl2code.backend.app.models.ir import IntermediateRepresentation
from nl2code.backend.app.core.validator import validate_code, ValidationResult
from nl2code.backend.app.core.sandbox import execute_in_sandbox, SandboxResult
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.llm import get_llm_provider

logger = logging.getLogger("nl2code.repair")

class CompileAttempt(BaseModel):
    attempt_number: int
    code: str
    stage_failed: Optional[str] = None  # "validation" | "sandbox" | None
    errors: List[str] = Field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    sandbox_result: Optional[SandboxResult] = None
    is_successful: bool = False

class RepairLoopResult(BaseModel):
    success: bool
    total_attempts: int
    final_code: str
    final_sandbox_result: Optional[SandboxResult] = None
    history: List[CompileAttempt] = Field(default_factory=list)

async def run_repair_loop(
    initial_code: str,
    ir: IntermediateRepresentation,
    language: str,
    max_repairs: int = 3,
    provider: Optional[LLMProvider] = None,
    on_attempt_callback: Optional[Callable[[CompileAttempt], Awaitable[None]]] = None
) -> RepairLoopResult:
    """
    Stage 6: Repair Loop.
    Performs iterative compiler feedback loop. On validation or sandbox failure,
    diagnostics and test failures are fed back into the LLM up to max_repairs times.
    """
    llm = provider or get_llm_provider()
    current_code = initial_code
    history: List[CompileAttempt] = []

    for attempt_idx in range(1, max_repairs + 2):  # 1 initial + max_repairs
        attempt = CompileAttempt(
            attempt_number=attempt_idx,
            code=current_code
        )

        # 1. Static Validation
        val_res = validate_code(current_code, language)
        attempt.validation_result = val_res

        if not val_res.is_valid:
            attempt.stage_failed = "validation"
            attempt.errors = list(val_res.errors)
            attempt.is_successful = False
            history.append(attempt)

            if on_attempt_callback:
                await on_attempt_callback(attempt)

            if attempt_idx <= max_repairs:
                logger.info(f"Attempt {attempt_idx} failed static validation. Requesting LLM repair...")
                current_code = await llm.repair_code(
                    code=current_code,
                    errors=attempt.errors,
                    ir=ir,
                    language=language,
                    attempt=attempt_idx
                )
                continue
            else:
                break

        # 2. Dynamic Sandbox Execution
        sandbox_res = await execute_in_sandbox(current_code, ir, language)
        attempt.sandbox_result = sandbox_res

        if not sandbox_res.passed:
            attempt.stage_failed = "sandbox"
            errs = []
            if sandbox_res.error_summary:
                errs.append(sandbox_res.error_summary)
            for tc in sandbox_res.test_results:
                if tc.status == "fail":
                    errs.append(f"Test case #{tc.id} failed: Expected {tc.expected}, Got {tc.actual}. Error: {tc.error}")
            attempt.errors = errs
            attempt.is_successful = False
            history.append(attempt)

            if on_attempt_callback:
                await on_attempt_callback(attempt)

            if attempt_idx <= max_repairs:
                logger.info(f"Attempt {attempt_idx} failed sandbox tests. Requesting LLM repair...")
                current_code = await llm.repair_code(
                    code=current_code,
                    errors=attempt.errors,
                    ir=ir,
                    language=language,
                    attempt=attempt_idx
                )
                continue
            else:
                break

        # All tests passed!
        attempt.is_successful = True
        attempt.stage_failed = None
        history.append(attempt)

        if on_attempt_callback:
            await on_attempt_callback(attempt)

        return RepairLoopResult(
            success=True,
            total_attempts=attempt_idx,
            final_code=current_code,
            final_sandbox_result=sandbox_res,
            history=history
        )

    # If loop exited without passing
    last_attempt = history[-1] if history else None
    return RepairLoopResult(
        success=False,
        total_attempts=len(history),
        final_code=current_code,
        final_sandbox_result=last_attempt.sandbox_result if last_attempt else None,
        history=history
    )
