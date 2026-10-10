from typing import Dict
from nl2code.backend.app.languages.base import LanguageAdapter
from nl2code.backend.app.languages.python_adapter import PythonAdapter
from nl2code.backend.app.languages.cpp_adapter import CppAdapter
from nl2code.backend.app.languages.java_adapter import JavaAdapter
from nl2code.backend.app.languages.js_adapter import JavaScriptAdapter

_ADAPTERS: Dict[str, LanguageAdapter] = {
    "python": PythonAdapter(),
    "py": PythonAdapter(),
    "cpp": CppAdapter(),
    "c++": CppAdapter(),
    "java": JavaAdapter(),
    "javascript": JavaScriptAdapter(),
    "js": JavaScriptAdapter(),
}

def get_language_adapter(lang: str) -> LanguageAdapter:
    normalized = lang.strip().lower()
    if normalized not in _ADAPTERS:
        raise ValueError(f"Unsupported target language: {lang}. Supported languages: {list(_ADAPTERS.keys())}")
    return _ADAPTERS[normalized]
