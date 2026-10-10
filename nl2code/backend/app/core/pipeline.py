import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional

from nl2code.backend.app.models.ir import IntermediateRepresentation, IntentParseResult
from nl2code.backend.app.core.intent_parser import parse_user_intent
from nl2code.backend.app.core.ir_builder import build_compiler_ir
from nl2code.backend.app.core.code_generator import synthesize_code
from nl2code.backend.app.core.validator import validate_code
from nl2code.backend.app.core.sandbox import execute_in_sandbox
from nl2code.backend.app.core.repair_loop import run_repair_loop, CompileAttempt
from nl2code.backend.app.models.db import SessionLocal, CompilationRecord
from nl2code.backend.app.llm import get_llm_provider

logger = logging.getLogger("nl2code.pipeline")

class CompilationPipeline:
    def __init__(self, job_id: str, prompt: str, language: str, max_repairs: int = 3):
        self.job_id = job_id
        self.prompt = prompt
        self.language = language.lower().strip()
        self.max_repairs = max_repairs
        self.event_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def emit_event(self, stage: str, status: str, payload: Optional[Dict[str, Any]] = None):
        event = {
            "stage": stage,
            "status": status,
            "payload": payload or {}
        }
        await self.event_queue.put(event)

    async def run(self):
        db = SessionLocal()
        record = db.query(CompilationRecord).filter(CompilationRecord.id == self.job_id).first()
        if not record:
            record = CompilationRecord(
                id=self.job_id,
                prompt=self.prompt,
                language=self.language,
                status="running"
            )
            db.add(record)
            db.commit()

        provider = get_llm_provider()
        intent: Optional[IntentParseResult] = None
        ir: Optional[IntermediateRepresentation] = None
        code: Optional[str] = None

        try:
            # Stage 1: Intent Parser
            await self.emit_event("intent", "running", {"message": "Extracting task intent and constraints..."})
            intent = await parse_user_intent(self.prompt, self.language, provider)
            record.intent_json = intent.model_dump_json()
            db.commit()
            await self.emit_event("intent", "ok", {"intent": intent.model_dump()})

            # Stage 2: Spec / IR Builder
            await self.emit_event("ir", "running", {"message": "Building strict Intermediate Representation..."})
            ir = await build_compiler_ir(intent, self.language, provider)
            record.ir_json = ir.model_dump_json()
            db.commit()
            await self.emit_event("ir", "ok", {"ir": ir.model_dump()})

            # Stage 3: Code Generator
            await self.emit_event("codegen", "running", {"message": f"Synthesizing {self.language} code..."})
            code = await synthesize_code(ir, self.language, provider)
            record.generated_code = code
            db.commit()
            await self.emit_event("codegen", "ok", {"code": code})

            # Stage 4: Static Validator
            await self.emit_event("validate", "running", {"message": "Performing static syntax & lint checks..."})
            val_res = validate_code(code, self.language)
            if val_res.is_valid:
                await self.emit_event("validate", "ok", {"warnings": val_res.warnings})
            else:
                await self.emit_event("validate", "failed", {"errors": val_res.errors})

            # Stage 5 & 6: Sandbox Execution & Repair Loop
            await self.emit_event("sandbox", "running", {"message": "Executing unit tests in sandbox..."})

            async def attempt_callback(attempt: CompileAttempt):
                if attempt.attempt_number > 1:
                    await self.emit_event("repair", "running", {
                        "attempt": attempt.attempt_number,
                        "message": f"Repair cycle attempt {attempt.attempt_number}..."
                    })

            repair_res = await run_repair_loop(
                initial_code=code,
                ir=ir,
                language=self.language,
                max_repairs=self.max_repairs,
                provider=provider,
                on_attempt_callback=attempt_callback
            )

            record.total_attempts = repair_res.total_attempts
            record.generated_code = repair_res.final_code
            record.success = repair_res.success
            record.status = "completed" if repair_res.success else "failed"

            if repair_res.final_sandbox_result:
                record.test_summary_json = repair_res.final_sandbox_result.model_dump_json()
            record.attempt_history_json = json.dumps([a.model_dump() for a in repair_res.history])
            db.commit()

            if repair_res.success:
                await self.emit_event("sandbox", "ok", {
                    "test_summary": repair_res.final_sandbox_result.model_dump() if repair_res.final_sandbox_result else {}
                })
                await self.emit_event("done", "ok", {
                    "success": True,
                    "final_code": repair_res.final_code,
                    "total_attempts": repair_res.total_attempts,
                    "history": [a.model_dump() for a in repair_res.history]
                })
            else:
                await self.emit_event("sandbox", "failed", {
                    "errors": [a.errors for a in repair_res.history if a.errors]
                })
                await self.emit_event("done", "failed", {
                    "success": False,
                    "final_code": repair_res.final_code,
                    "total_attempts": repair_res.total_attempts,
                    "history": [a.model_dump() for a in repair_res.history]
                })

        except Exception as e:
            logger.error(f"Compilation pipeline failed: {e}", exc_info=True)
            err_msg = str(e)
            record.status = "failed"
            record.success = False
            record.error_message = err_msg
            db.commit()
            await self.emit_event("error", "failed", {"error": err_msg})
        finally:
            db.close()
            # Send sentinel None to close generator
            await self.event_queue.put(None)

    async def stream_events(self) -> AsyncGenerator[str, None]:
        while True:
            event = await self.event_queue.get()
            if event is None:
                break
            yield json.dumps(event)
