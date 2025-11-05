from datetime import datetime
import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.combination_router import router as combination_router
from app.routers.compile_router import router as compile_router
from app.routers.run_router import router as run_router
from app.routers.download_router import router as download_router
from app.routers.github_router import router as github_router
from app.routers.health_router import router as health_router

# Fix for Windows: Set event loop policy to support subprocesses
# The default ProactorEventLoop on Windows doesn't support subprocess operations
if sys.platform == 'win32':
    # For Python 3.8+, use WindowsSelectorEventLoopPolicy
    # This policy uses the SelectorEventLoop which supports subprocess operations
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        # Fallback for Python versions where WindowsSelectorEventLoopPolicy doesn't exist
        # Create a new event loop with proper configuration
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# Configure FastAPI with explicit docs and OpenAPI URLs so Swagger UI and Redoc are
# available at /docs and /redoc respectively. Keep a named openapi url.
# Add multiple server options for Swagger UI dropdown
app = FastAPI(
	title="TestForge",
	version="0.1.0",
	description="TestForge API",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_url="/openapi.json",
	servers=[
		{
			"url": "http://localhost:3003",
			"description": "Mockoon Proxy (with logging) → Backend :3000"
		},
		{
			"url": "http://localhost:3000",
			"description": "Direct Backend (no logging)"
		}
	]
)

# Add CORS middleware to allow cross-origin requests from Swagger UI when calling through Mockoon
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],  # In production, replace with specific origins
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# record service start time for uptime reporting
app.state.start_time = datetime.utcnow()

app.include_router(health_router)
app.include_router(combination_router)
app.include_router(compile_router)
app.include_router(run_router)
app.include_router(download_router)
app.include_router(github_router)
