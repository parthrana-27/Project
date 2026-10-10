from abc import ABC, abstractmethod
from typing import Tuple, Optional
from nl2code.backend.app.models.ir import IntermediateRepresentation

class LanguageAdapter(ABC):
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Name of the target language (e.g. python, cpp, java, javascript)"""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for source code files (e.g. .py, .cpp, .java, .js)"""
        pass

    @abstractmethod
    def format_signature(self, ir: IntermediateRepresentation) -> str:
        """Generate language-idiomatic function signature from IR."""
        pass

    @abstractmethod
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Perform static syntactic validation.
        Returns (is_valid, error_message).
        """
        pass

    @abstractmethod
    def generate_test_harness(self, code: str, ir: IntermediateRepresentation) -> str:
        """
        Embed source code into an executable unit test harness that evaluates
        all test cases declared in the IR and prints JSON formatted test results.
        """
        pass
