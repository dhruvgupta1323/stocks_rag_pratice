import sys
import os

# Ensure both workspace root and backend directory are in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.abspath(os.path.join(_current_dir, "../.."))
_backend_dir = os.path.abspath(os.path.join(_current_dir, ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.core.exceptions import (
    StockIntelligenceException,
    ProviderException,
    InstrumentNotFoundException,
    GuardrailViolationException,
)
from backend.app.db.session import init_db, close_db
from backend.app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting AI Stock Intelligence Platform backend...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down AI Stock Intelligence Platform backend...")
    await close_db()


app = FastAPI(
    title="AI Stock Intelligence Platform API",
    description="Automated Indian Equity Intelligence, Real-time Market Data, Financial Analytics & LangGraph Research Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(InstrumentNotFoundException)
async def instrument_not_found_handler(request: Request, exc: InstrumentNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"success": False, "error": "InstrumentNotFound", "message": exc.message},
    )


@app.exception_handler(ProviderException)
async def provider_exception_handler(request: Request, exc: ProviderException):
    return JSONResponse(
        status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
        content={
            "success": False,
            "error": "ProviderError",
            "provider": exc.provider,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(GuardrailViolationException)
async def guardrail_exception_handler(request: Request, exc: GuardrailViolationException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "error": "GuardrailViolation", "message": exc.message},
    )


@app.exception_handler(StockIntelligenceException)
async def domain_exception_handler(request: Request, exc: StockIntelligenceException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "error": "DomainError", "message": exc.message},
    )


# Health Check
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "data_provider": settings.DATA_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
    }


# Mount API Router
app.include_router(api_router)

