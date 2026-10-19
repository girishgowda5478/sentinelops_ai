from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    summary: str = Field(min_length=3, max_length=1000)
    logs: str = Field(min_length=1, max_length=200_000)
    deployment: str = Field(default="", max_length=1000)
