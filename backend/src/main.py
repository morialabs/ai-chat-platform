"""FastAPI application entry point.

This module provides the FastAPI application for the AI Chat Platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat_router
from src.config import settings

app = FastAPI(
    title="AI Chat Platform",
    description="Domain-specific AI chat platform with Claude Agent SDK",
    version="0.1.0",
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
