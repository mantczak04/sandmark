from pydantic import BaseModel


class ReviewComment(BaseModel):
    file: str
    line: int
    type: str
    comment: str


class ReviewResult(BaseModel):
    comments: list[ReviewComment]
    summary: str


class ReviewRequest(BaseModel):
    mr_url: str
    prompt_name: str


class DiffRequest(BaseModel):
    mr_url: str


class LogEntry(BaseModel):
    timestamp: str
    prompt_name: str
    mr_url: str
    tokens_used: int
    time_seconds: float
    summary: str
