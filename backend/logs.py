import hashlib
from backend.models import LogEntry, MongoLogEntry
from backend import mongodb_client


_logs: list[dict] = []


def compute_prompt_hash(prompt_content: str) -> str:
    """Compute 8-character SHA-256 hash of prompt content."""
    hash_obj = hashlib.sha256(prompt_content.encode('utf-8'))
    return hash_obj.hexdigest()[:8]


def add_log(entry: LogEntry) -> None:
    """Add log entry to in-memory storage (backward compatible)."""
    _logs.append(entry.model_dump())


def add_log_to_mongo(mongo_entry: MongoLogEntry) -> bool:
    """Add log entry to MongoDB. Returns True if successful, False otherwise."""
    try:
        collection = mongodb_client.get_collection()
        collection.insert_one(mongo_entry.model_dump())
        return True
    except Exception as e:
        print(f"Failed to store log in MongoDB: {e}")
        return False


def add_log_dual(in_memory_entry: LogEntry, mongo_entry: MongoLogEntry) -> None:
    """Add log to both in-memory and MongoDB storage."""
    # Always add to in-memory (fallback)
    add_log(in_memory_entry)
    
    # Try to add to MongoDB
    add_log_to_mongo(mongo_entry)


def get_logs() -> list[dict]:
    """Get logs from in-memory storage (backward compatible)."""
    return list(_logs)


def get_logs_from_mongo() -> list[dict]:
    """Get logs from MongoDB. Returns empty list if unavailable."""
    try:
        collection = mongodb_client.get_collection()
        # Get all logs sorted by timestamp descending (most recent first)
        logs = list(collection.find({}, {'_id': 0}).sort('timestamp', -1))
        return logs
    except Exception as e:
        print(f"Failed to retrieve logs from MongoDB: {e}")
        return []


def get_logs_with_fallback() -> list[dict]:
    """Get logs from MongoDB, fallback to in-memory if unavailable."""
    mongo_logs = get_logs_from_mongo()
    if mongo_logs:
        return mongo_logs
    return get_logs()


def logs_to_csv() -> str:
    """Convert logs to CSV format."""
    logs_data = get_logs_with_fallback()
    
    if not logs_data:
        return "timestamp,mr_url,prompt_name,prompt_hash,llm_model,tokens_used,elapsed_ms\n"
    
    # Check if we have MongoDB format (with prompt_hash) or in-memory format
    first_log = logs_data[0]
    is_mongo_format = 'prompt_hash' in first_log
    
    if is_mongo_format:
        header = "timestamp,mr_url,prompt_name,prompt_hash,llm_model,tokens_used,elapsed_ms"
        rows = [header]
        for log in logs_data:
            row = ",".join(
                f'"{str(log[col])}"' for col in
                ["timestamp", "mr_url", "prompt_name", "prompt_hash", "llm_model", "tokens_used", "elapsed_ms"]
            )
            rows.append(row)
    else:
        # Backward compatible format for in-memory logs
        header = "timestamp,prompt_name,mr_url,tokens_used,time_seconds,summary"
        rows = [header]
        for log in logs_data:
            row = ",".join(
                f'"{str(log[col])}"' for col in
                ["timestamp", "prompt_name", "mr_url", "tokens_used", "time_seconds", "summary"]
            )
            rows.append(row)
    
    return "\n".join(rows) + "\n"
