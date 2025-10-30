from pydantic import BaseModel

class TestSummary(BaseModel):
    total: int
    passed: int
    failed: int
