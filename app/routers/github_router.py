from fastapi import APIRouter, HTTPException
from app.services.github_service import trigger_workflow

router = APIRouter(prefix="/api/v1/github", tags=["github"])

@router.post("/run/{testName}")
async def gh_run(testName: str):
    ok, msg = trigger_workflow(testName)
    if not ok:
        raise HTTPException(status_code=500, detail=msg)
    return {"status": "triggered", "testName": testName, "message": msg}
