import os
import sys

# Ensure root directories are in sys.path
_cur = os.path.dirname(os.path.abspath(__file__))
_backend = os.path.dirname(_cur)
_nl2code = os.path.dirname(_backend)
_root = os.path.dirname(_nl2code)
for _p in [_root, _nl2code, _backend]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nl2code.backend.app.config import get_settings
from nl2code.backend.app.models.db import init_db
from nl2code.backend.app.api.routes_compile import router as compile_router
from nl2code.backend.app.api.routes_history import router as history_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nl2code")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database tables exist
    init_db()
    logger.info("Database initialized successfully.")
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Natural Language-to-Code Compiler with structured IR, static analysis, sandboxing, and repair loop.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compile_router)
app.include_router(history_router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "provider": settings.llm_provider,
        "docker_available": settings.use_docker_sandbox
    }
