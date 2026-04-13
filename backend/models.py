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


class CreatePromptRequest(BaseModel):
    prompt_name: str
    content: str


class DiffRequest(BaseModel):
    mr_url: str


class LogEntry(BaseModel):
    timestamp: str
    prompt_name: str
    mr_url: str
    tokens_used: int
    time_seconds: float  # Kept for backward compatibility with in-memory logs
    summary: str


class MongoLogEntry(BaseModel):
    """Extended log entry for MongoDB storage."""
    timestamp: str
    mr_url: str
    prompt_name: str
    prompt_hash: str  # 8-character SHA-256 hash of prompt content
    llm_model: str
    tokens_used: int
    elapsed_ms: int  # Time in milliseconds
    review_json: dict  # Full JSON response from LLM
    
    @classmethod
    def from_log_entry(cls, log_entry: LogEntry, prompt_hash: str, llm_model: str, review_json: dict):
        """Convert LogEntry to MongoLogEntry."""
        return cls(
            timestamp=log_entry.timestamp,
            mr_url=log_entry.mr_url,
            prompt_name=log_entry.prompt_name,
            prompt_hash=prompt_hash,
            llm_model=llm_model,
            tokens_used=log_entry.tokens_used,
            elapsed_ms=int(log_entry.time_seconds * 1000),
            review_json=review_json
        )
