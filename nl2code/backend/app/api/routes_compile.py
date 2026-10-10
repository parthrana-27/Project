import asyncio
import json
import uuid
import logging
from typing import Dict
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from nl2code.backend.app.api.schemas import CompileRequest, CompileResponse
from nl2code.backend.app.api.rate_limiter import rate_limiter
from nl2code.backend.app.core.pipeline import CompilationPipeline
from nl2code.backend.app.models.db import SessionLocal, CompilationRecord

logger = logging.getLogger("nl2code.api.compile")
router = APIRouter(prefix="/api/compile", tags=["compile"])

# In-memory store for active streaming pipelines
_active_pipelines: Dict[str, CompilationPipeline] = {}

@router.post("", response_model=CompileResponse)
async def start_compilation(request: CompileRequest, req: Request, background_tasks: BackgroundTasks):
    rate_limiter.check_rate_limit(req)
    job_id = str(uuid.uuid4())
    pipeline = CompilationPipeline(
        job_id=job_id,
        prompt=request.prompt,
        language=request.language,
        max_repairs=request.max_repairs
    )
    _active_pipelines[job_id] = pipeline

    # Run compilation pipeline in background task
    async def run_and_cleanup():
        try:
            await pipeline.run()
        finally:
            # Leave pipeline in memory briefly for stream consumers to finish
            await asyncio.sleep(60)
            _active_pipelines.pop(job_id, None)

    asyncio.create_task(run_and_cleanup())

    return CompileResponse(
        job_id=job_id,
        status="started",
        stream_url=f"/api/compile/{job_id}/stream"
    )

@router.get("/{job_id}/stream")
async def stream_compilation_progress(job_id: str):
    pipeline = _active_pipelines.get(job_id)
    if not pipeline:
        # Check if already completed in DB
        db = SessionLocal()
        record = db.query(CompilationRecord).filter(CompilationRecord.id == job_id).first()
        db.close()
        if not record:
            raise HTTPException(status_code=404, detail="Compilation job not found or expired.")
        
        # If already done, yield single complete event
        async def done_generator():
            yield {
                "event": "message",
                "data": json.dumps({
                    "stage": "done",
                    "status": "ok" if record.success else "failed",
                    "payload": {
                        "final_code": record.generated_code,
                        "success": record.success,
                        "total_attempts": record.total_attempts
                    }
                })
            }
        return EventSourceResponse(done_generator())

    async def event_generator():
        async for event_json in pipeline.stream_events():
            yield {
                "event": "message",
                "data": event_json
            }

    return EventSourceResponse(event_generator())

@router.post("/sync")
async def compile_synchronous(request: CompileRequest, req: Request):
    """
    Synchronous compilation endpoint for tests and direct evaluation.
    """
    rate_limiter.check_rate_limit(req)
    job_id = str(uuid.uuid4())
    pipeline = CompilationPipeline(
        job_id=job_id,
        prompt=request.prompt,
        language=request.language,
        max_repairs=request.max_repairs
    )
    events = []

    async def collector():
        async for evt in pipeline.stream_events():
            events.append(evt)

    collect_task = asyncio.create_task(collector())
    await pipeline.run()
    await collect_task

    db = SessionLocal()
    record = db.query(CompilationRecord).filter(CompilationRecord.id == job_id).first()
    db.close()

    if not record:
        raise HTTPException(status_code=500, detail="Compilation failed to record.")

    return {
        "job_id": job_id,
        "success": record.success,
        "status": record.status,
        "language": record.language,
        "generated_code": record.generated_code,
        "total_attempts": record.total_attempts,
        "ir": json.loads(record.ir_json) if record.ir_json else None,
        "test_summary": json.loads(record.test_summary_json) if record.test_summary_json else None,
        "error_message": record.error_message
    }
