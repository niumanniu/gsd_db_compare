"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import connections, compare, reports, data_compare
from app.api import scheduled_tasks, history, critical_tables, notifications
from app.scheduler import get_scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup: Initialize and start scheduler
    scheduler = get_scheduler_service()
    scheduler.start()
    await scheduler.load_persisted_tasks()
    print("Scheduler started successfully")

    yield

    # Shutdown: Stop scheduler
    scheduler.stop()
    print("Scheduler stopped")


app = FastAPI(
    title="DB Compare API",
    description="Database schema and data comparison tool",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(connections.router)
app.include_router(compare.router)
app.include_router(reports.router)
app.include_router(data_compare.router)
app.include_router(scheduled_tasks.router)
app.include_router(history.router)
app.include_router(critical_tables.router)
app.include_router(notifications.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "DB Compare API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
