from datetime import datetime
import asyncio
import sys
from fastapi import FastAPI
from app.routers.combination_router import router as combination_router
from app.routers.compile_router import router as compile_router
from app.routers.run_router import router as run_router
from app.routers.download_router import router as download_router
from app.routers.github_router import router as github_router
from app.routers.health_router import router as health_router

# Fix for Windows: Use WindowsSelectorEventLoopPolicy to support subprocesses
# The default ProactorEventLoop on Windows doesn't support subprocess operations
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure FastAPI with explicit docs and OpenAPI URLs so Swagger UI and Redoc are
# available at /docs and /redoc respectively. Keep a named openapi url.
app = FastAPI(
	title="TestForge",
	version="0.1.0",
	description="TestForge API",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_url="/openapi.json",
)

# record service start time for uptime reporting
app.state.start_time = datetime.utcnow()

app.include_router(health_router)
app.include_router(combination_router)
app.include_router(compile_router)
app.include_router(run_router)
app.include_router(download_router)
app.include_router(github_router)
