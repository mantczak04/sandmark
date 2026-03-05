from backend.models import LogEntry


_logs: list[dict] = []


def add_log(entry: LogEntry) -> None:
    _logs.append(entry.model_dump())


def get_logs() -> list[dict]:
    return list(_logs)


def logs_to_csv() -> str:
    if not _logs:
        return "timestamp,prompt_name,mr_url,tokens_used,time_seconds,summary\n"
    header = "timestamp,prompt_name,mr_url,tokens_used,time_seconds,summary"
    rows = [header]
    for log in _logs:
        row = ",".join(
            f'"{str(log[col])}"' for col in
            ["timestamp", "prompt_name", "mr_url", "tokens_used", "time_seconds", "summary"]
        )
        rows.append(row)
    return "\n".join(rows) + "\n"
