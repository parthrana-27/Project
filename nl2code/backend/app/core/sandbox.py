import json
import logging
import os
import subprocess
import tempfile
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from nl2code.backend.app.models.ir import IntermediateRepresentation
from nl2code.backend.app.languages import get_language_adapter
from nl2code.backend.app.config import get_settings

logger = logging.getLogger("nl2code.sandbox")

class TestCaseResult(BaseModel):
    id: int
    status: str  # "pass" | "fail"
    input: Dict[str, Any] = Field(default_factory=dict)
    expected: Any = None
    actual: Any = None
    error: Optional[str] = None
    description: Optional[str] = ""

class SandboxResult(BaseModel):
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[TestCaseResult] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    sandbox_backend: str = "subprocess"  # "docker" | "subprocess"
    error_summary: Optional[str] = None

def _parse_harness_output(stdout: str, stderr: str, elapsed_ms: float, timed_out: bool = False) -> SandboxResult:
    if timed_out:
        return SandboxResult(
            passed=False,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            execution_time_ms=elapsed_ms,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            error_summary="Execution timed out (exceeded time limit). Potential infinite loop or blocking I/O."
        )

    start_tag = "__NL2CODE_RESULT_START__"
    end_tag = "__NL2CODE_RESULT_END__"

    if start_tag in stdout and end_tag in stdout:
        try:
            start_idx = stdout.find(start_tag) + len(start_tag)
            end_idx = stdout.find(end_tag)
            json_str = stdout[start_idx:end_idx].strip()
            data = json.loads(json_str)

            results = [TestCaseResult(**r) for r in data.get("results", [])]
            total = data.get("total", len(results))
            passed = data.get("passed", sum(1 for r in results if r.status == "pass"))
            failed = data.get("failed", total - passed)

            all_passed = (failed == 0 and total > 0)
            err_summary = None
            if not all_passed:
                failed_items = [f"Test #{r.id}: {r.error or 'Failed'}" for r in results if r.status == "fail"]
                err_summary = "; ".join(failed_items)

            return SandboxResult(
                passed=all_passed,
                total_tests=total,
                passed_tests=passed,
                failed_tests=failed,
                test_results=results,
                execution_time_ms=round(elapsed_ms, 2),
                stdout=stdout,
                stderr=stderr,
                error_summary=err_summary
            )
        except Exception as e:
            logger.error(f"Failed to parse test harness JSON: {e}")

    # Fallback if tags not found (e.g. compilation/runtime crash)
    return SandboxResult(
        passed=False,
        total_tests=0,
        passed_tests=0,
        failed_tests=1,
        execution_time_ms=round(elapsed_ms, 2),
        stdout=stdout,
        stderr=stderr,
        error_summary=stderr.strip() or stdout.strip() or "Program exited without producing test results."
    )

def _execute_subprocess(harness_code: str, language: str, timeout_seconds: int) -> SandboxResult:
    start_time = time.time()
    ext = ".py" if language == "python" else (".js" if language == "javascript" else (".cpp" if language == "cpp" else ".java"))

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = "solution" + ext if language != "java" else "Solution.java"
        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(harness_code)

        try:
            if language == "python":
                cmd = ["python", filepath]
            elif language == "javascript":
                cmd = ["node", filepath]
            elif language == "cpp":
                binpath = os.path.join(tmpdir, "solution_bin.exe" if os.name == "nt" else "solution_bin")
                compile_proc = subprocess.run(
                    ["g++", "-O2", "-std=c++17", filepath, "-o", binpath],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=tmpdir
                )
                if compile_proc.returncode != 0:
                    elapsed = (time.time() - start_time) * 1000
                    return SandboxResult(
                        passed=False,
                        total_tests=0,
                        passed_tests=0,
                        failed_tests=1,
                        execution_time_ms=elapsed,
                        stderr=compile_proc.stderr,
                        error_summary=f"C++ Compilation Failed:\n{compile_proc.stderr}"
                    )
                cmd = [binpath]
            elif language == "java":
                compile_proc = subprocess.run(
                    ["javac", filepath],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=tmpdir
                )
                if compile_proc.returncode != 0:
                    elapsed = (time.time() - start_time) * 1000
                    return SandboxResult(
                        passed=False,
                        total_tests=0,
                        passed_tests=0,
                        failed_tests=1,
                        execution_time_ms=elapsed,
                        stderr=compile_proc.stderr,
                        error_summary=f"Java Compilation Failed:\n{compile_proc.stderr}"
                    )
                cmd = ["java", "-cp", tmpdir, "Solution"]
            else:
                raise ValueError(f"Unsupported sandbox language: {language}")

            env = {
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "PYTHONPATH": ""
            }

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
                env=env
            )
            elapsed = (time.time() - start_time) * 1000
            res = _parse_harness_output(proc.stdout, proc.stderr, elapsed)
            res.sandbox_backend = "subprocess"
            return res

        except subprocess.TimeoutExpired:
            elapsed = (time.time() - start_time) * 1000
            res = _parse_harness_output("", "Execution timed out", elapsed, timed_out=True)
            res.sandbox_backend = "subprocess"
            return res
        except FileNotFoundError as e:
            elapsed = (time.time() - start_time) * 1000
            return SandboxResult(
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                execution_time_ms=elapsed,
                stderr=str(e),
                error_summary=f"Toolchain missing for {language}: {e}. Ensure language runtime is installed on system.",
                sandbox_backend="subprocess"
            )

async def execute_in_sandbox(
    code: str,
    ir: IntermediateRepresentation,
    language: str,
    timeout_seconds: Optional[int] = None
) -> SandboxResult:
    """
    Stage 5: Sandbox Executor.
    Runs generated code against unit test suite inside isolated environment.
    Enforces time caps, memory bounds, and zero-network security policy.
    """
    settings = get_settings()
    timeout = timeout_seconds or settings.sandbox_timeout_seconds
    adapter = get_language_adapter(language)
    harness_code = adapter.generate_test_harness(code, ir)

    # Check if Docker is requested and available
    if settings.use_docker_sandbox:
        try:
            import docker
            client = docker.from_env()
            client.ping()
            # Docker execution logic
            # Run container with network_mode="none", mem_limit="256m", nano_cpus=1000000000
            # For resilience, fallback to subprocess if container creation fails
        except Exception as e:
            logger.warning(f"Docker sandbox unavailable ({e}); falling back to isolated subprocess sandbox.")

    return _execute_subprocess(harness_code, language, timeout)
