"""
FastAPI Public API Entry Point

Run this to start the FastAPI public API on port 8000.

Usage:
    python run_fastapi.py
"""

import os
import uvicorn

# Ensure ANTHROPIC_API_KEY is set (optional for development)
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("WARNING: ANTHROPIC_API_KEY not set. Agents will use fallback mode.")
    print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("FastAPI Public API Starting...")
    print("=" * 60)
    print(f"API Base URL: http://localhost:8000")
    print(f"API Docs (Swagger): http://localhost:8000/docs")
    print(f"API Docs (ReDoc): http://localhost:8000/redoc")
    print()
    print("Authentication: Use API keys from Flask dashboard")
    print("Header: Authorization: Bearer <your_api_key>")
    print("=" * 60)
    print()

    uvicorn.run(
        "fastapi_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
