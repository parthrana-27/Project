from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class CompileRequest(BaseModel):
    prompt: str = Field(min_length=3, description="Natural language programming description")
    language: str = Field(default="python", description="Target language: python, cpp, java, javascript")
    max_repairs: int = Field(default=3, ge=0, le=5, description="Max self-repair feedback loop iterations")

class CompileResponse(BaseModel):
    job_id: str
    status: str
    stream_url: str

class CompilationSummaryItem(BaseModel):
    id: str
    created_at: datetime
    prompt: str
    language: str
    status: str
    success: bool
    total_attempts: int

class CompilationDetail(BaseModel):
    id: str
    created_at: datetime
    prompt: str
    language: str
    status: str
    success: bool
    intent: Optional[Dict[str, Any]] = None
    ir: Optional[Dict[str, Any]] = None
    generated_code: Optional[str] = None
    total_attempts: int = 0
    test_summary: Optional[Dict[str, Any]] = None
    attempt_history: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
