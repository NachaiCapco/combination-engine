from datetime import datetime
from fastapi import APIRouter, Request

router = APIRouter()


def _compute_uptime_seconds(start_time: datetime | None) -> float | None:
    if not start_time:
        return None
    return (datetime.utcnow() - start_time).total_seconds()


@router.get("/health", tags=["health"])
async def health(request: Request):
    """Basic health endpoint.

    Returns service status, uptime in seconds (if available), and the app version.
    """
    start = getattr(request.app.state, "start_time", None)
    return {
        "status": "ok",
        "uptime_seconds": _compute_uptime_seconds(start),
        "version": getattr(request.app, "version", None),
    }


@router.get("/healthz", tags=["health"])
async def healthz(request: Request):
    """Alias for `/health` to support different readiness probes."""
    return await health(request)
