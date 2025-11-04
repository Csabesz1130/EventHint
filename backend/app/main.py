"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.core.db import engine, Base
from app.api import auth, events, ingestion, calendars

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting EventHint backend...")
    # Create tables (in production, use Alembic migrations)
    # Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down EventHint backend...")


app = FastAPI(
    title="EventHint API",
    description="Intelligent inbox-to-calendar extraction system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Ingestion"])
app.include_router(calendars.router, prefix="/api/calendars", tags=["Calendars"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "EventHint API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }

