import asyncio, json
from typing import AsyncGenerator, Dict, Any

def sse_event(event: str, data: Dict[str, Any]) -> str:
    """
    Format data as Server-Sent Event (synchronous).
    Returns SSE-formatted string with event type and JSON data.
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
