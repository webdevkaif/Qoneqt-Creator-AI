"""
Qoneqt Creator AI — FastAPI Backend Entry Point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
from loguru import logger
import sys

from app.core.config import settings
from app.core.database import connect_db, close_db
from app.api import api_router
from app.utils.storage import ensure_storage_dirs

# Configure loguru
logger.remove()
logger.add(sys.stderr, level="DEBUG" if settings.APP_ENV == "development" else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Qoneqt Creator AI Backend — {settings.APP_ENV} mode")
    ensure_storage_dirs()
    await connect_db()
    if settings.demo_mode:
        logger.warning("⚠️  DEMO MODE: No AI API keys configured. Using local demo data.")
    yield
    await close_db()
    logger.info("Backend shutdown complete")


app = FastAPI(
    title="Qoneqt Creator AI",
    description="AI-powered video creation platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage as static files
storage_path = Path(settings.LOCAL_STORAGE_PATH).resolve()
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")

# Include API routes
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


@app.get("/")
async def root():
    return {
        "name": "Qoneqt Creator AI",
        "version": "1.0.0",
        "docs": "/api/docs",
        "demo_mode": settings.demo_mode,
    }
