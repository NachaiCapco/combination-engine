from pydantic import BaseModel

class CompileRequest(BaseModel):
    testName: str
