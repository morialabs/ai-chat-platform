"""FastAPI application entry point.

This module provides the FastAPI application for the AI Chat Platform.
Currently a placeholder - will be implemented after CLI agent is working.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI Chat Platform",
    description="Domain-specific AI chat platform with Claude Agent SDK",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
