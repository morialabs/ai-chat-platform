"""FastAPI application entry point.

This module provides the FastAPI application for the AI Chat Platform
with session lifecycle management for multi-turn conversations.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat_router
from src.api.routes.chat import get_agent_manager
from src.config import settings

logger = logging.getLogger(__name__)


async def session_cleanup_loop() -> None:
    """Background task to periodically clean up expired sessions."""
    while True:
        try:
            await asyncio.sleep(settings.session_cleanup_interval_seconds)
            manager = get_agent_manager()
            count = await manager.session_manager.cleanup_expired()
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown.

    Manages the session cleanup background task and ensures proper
    cleanup of all sessions on shutdown.
    """
    logger.info("Starting AI Chat Platform...")

    # Start background session cleanup task
    cleanup_task = asyncio.create_task(session_cleanup_loop())

    yield

    # Shutdown: cancel cleanup task and clean up all sessions
    logger.info("Shutting down AI Chat Platform...")
    cleanup_task.cancel()
    with suppress(asyncio.CancelledError):
        await cleanup_task

    # Clean up all active sessions
    manager = get_agent_manager()
    await manager.cleanup()
    logger.info("Shutdown complete")


app = FastAPI(
    title="AI Chat Platform",
    description="Domain-specific AI chat platform with Claude Agent SDK",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
