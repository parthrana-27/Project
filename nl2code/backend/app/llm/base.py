from abc import ABC, abstractmethod
from typing import List, Optional
from nl2code.backend.app.models.ir import IntermediateRepresentation, IntentParseResult

class LLMProvider(ABC):
    @abstractmethod
    async def parse_intent(self, prompt: str) -> IntentParseResult:
        """Parse natural language intent into structured problem specification."""
        pass

    @abstractmethod
    async def build_ir(self, intent: IntentParseResult, language: str) -> IntermediateRepresentation:
        """Compile parsed intent into strict Pydantic Intermediate Representation (IR)."""
        pass

    @abstractmethod
    async def generate_code(self, ir: IntermediateRepresentation, language: str) -> str:
        """Synthesize source code in the target language conforming to the IR."""
        pass

    @abstractmethod
    async def repair_code(
        self,
        code: str,
        errors: List[str],
        ir: IntermediateRepresentation,
        language: str,
        attempt: int
    ) -> str:
        """
        Compiler repair loop feedback: regenerate/fix the code given compiler
        diagnostics and failing test case outputs.
        """
        pass
