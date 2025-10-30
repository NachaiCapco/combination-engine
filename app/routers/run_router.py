from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.services.compile_service import setup_workspace
from app.services.run_service import run_robot_streaming
from app.core.utils_sse import sse_event
from urllib.parse import urljoin
from pathlib import Path
import asyncio

router = APIRouter(prefix="/api/v1", tags=["run"])

@router.get("/run-test-case/{testName}/stream")
async def run_stream(request: Request, testName: str):
    """
    Stream Robot Framework test execution in real-time.
    
    SSE Events:
        - connect: Initial connection established
        - process: Test case is running
        - pass: Test case passed
        - fail: Test case failed (with error message)
        - skip: Test case skipped
        - done: Execution completed with summary
    """
    root, gen, rep = setup_workspace(testName)
    if not gen.exists() or not any(gen.glob("*.robot")):
        raise HTTPException(status_code=404, detail="no generated tests found")

    base_url = str(request.base_url).rstrip("/")
    
    async def event_gen():
        """SSE generator with explicit flushing for real-time streaming."""
        timestamp = None
        
        async for event in run_robot_streaming(gen, rep):
            event_type = event['type']
            data = event['data']
            
            if event_type == 'connect':
                # Initial connection
                yield sse_event("connect", data)
                
            elif event_type == 'process':
                # Test case started running
                yield sse_event("process", data)
                await asyncio.sleep(0.01)
                
            elif event_type == 'pass':
                # Test case passed
                yield sse_event("pass", data)
                await asyncio.sleep(0.01)
                
            elif event_type == 'fail':
                # Test case failed with message
                yield sse_event("fail", data)
                await asyncio.sleep(0.01)
                
            elif event_type == 'skip':
                # Test case skipped
                yield sse_event("skip", data)
                await asyncio.sleep(0.01)
                
            elif event_type == 'done':
                # Final summary with download URL
                timestamp = data.get('timestamp')
                summary = data.get('summary', {})
                download_url = urljoin(base_url + "/", f"api/v1/download/{testName}/{timestamp}")
                yield sse_event("done", {
                    "status": "completed",
                    "summary": summary,
                    "message": data.get('message', 'Execution completed'),
                    "download_url": download_url
                })

    return StreamingResponse(
        event_gen(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
