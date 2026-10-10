import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from nl2code.backend.app.config import get_settings

Base = declarative_base()

class CompilationRecord(Base):
    __tablename__ = "compilation_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    prompt = Column(Text, nullable=False)
    language = Column(String(32), nullable=False)
    status = Column(String(32), default="pending")  # pending, completed, failed
    success = Column(Boolean, default=False)
    
    # Compiler stage artifacts stored as JSON text
    intent_json = Column(Text, nullable=True)
    ir_json = Column(Text, nullable=True)
    generated_code = Column(Text, nullable=True)
    total_attempts = Column(Integer, default=0)
    test_summary_json = Column(Text, nullable=True)
    attempt_history_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
