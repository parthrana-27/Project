import json
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from nl2code.backend.app.models.db import get_db, CompilationRecord
from nl2code.backend.app.api.schemas import CompilationSummaryItem, CompilationDetail

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("", response_model=List[CompilationSummaryItem])
def list_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    records = db.query(CompilationRecord).order_by(desc(CompilationRecord.created_at)).offset(skip).limit(limit).all()
    results = []
    for r in records:
        results.append(CompilationSummaryItem(
            id=r.id,
            created_at=r.created_at,
            prompt=r.prompt,
            language=r.language,
            status=r.status,
            success=r.success or False,
            total_attempts=r.total_attempts or 0
        ))
    return results

@router.get("/{record_id}", response_model=CompilationDetail)
def get_compilation_record(record_id: str, db: Session = Depends(get_db)):
    record = db.query(CompilationRecord).filter(CompilationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Compilation record not found.")

    intent_data = json.loads(record.intent_json) if record.intent_json else None
    ir_data = json.loads(record.ir_json) if record.ir_json else None
    test_summary_data = json.loads(record.test_summary_json) if record.test_summary_json else None
    attempt_history_data = json.loads(record.attempt_history_json) if record.attempt_history_json else None

    return CompilationDetail(
        id=record.id,
        created_at=record.created_at,
        prompt=record.prompt,
        language=record.language,
        status=record.status,
        success=record.success or False,
        intent=intent_data,
        ir=ir_data,
        generated_code=record.generated_code,
        total_attempts=record.total_attempts or 0,
        test_summary=test_summary_data,
        attempt_history=attempt_history_data,
        error_message=record.error_message
    )

@router.delete("/{record_id}")
def delete_compilation_record(record_id: str, db: Session = Depends(get_db)):
    record = db.query(CompilationRecord).filter(CompilationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Compilation record not found.")
    db.delete(record)
    db.commit()
    return {"status": "deleted", "id": record_id}

@router.get("/{record_id}/export")
def export_compilation(record_id: str, db: Session = Depends(get_db)):
    record = db.query(CompilationRecord).filter(CompilationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Compilation record not found.")

    export_data = {
        "id": record.id,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "prompt": record.prompt,
        "language": record.language,
        "status": record.status,
        "success": record.success,
        "code": record.generated_code,
        "ir": json.loads(record.ir_json) if record.ir_json else None,
        "test_summary": json.loads(record.test_summary_json) if record.test_summary_json else None
    }
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": f"attachment; filename=compilation_{record_id[:8]}.json"}
    )
