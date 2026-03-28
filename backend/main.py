import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.models import DiffRequest, LogEntry, MongoLogEntry, ReviewRequest
from backend.gitlab_client import fetch_mr_diff
from backend.llm_client import run_review
from backend import logs

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

app = FastAPI(title="SANDMARK", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/prompts")
def list_prompts():
    """List all available master prompt files."""
    if not PROMPTS_DIR.exists():
        return {"prompts": []}
    prompt_files = sorted(f.name for f in PROMPTS_DIR.glob("*.txt"))
    return {"prompts": prompt_files}


@app.post("/api/diff")
async def get_diff(req: DiffRequest):
    """Fetch the MR diff from GitLab."""
    try:
        diff_data = await fetch_mr_diff(req.mr_url)
        return diff_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review")
async def run_review_endpoint(req: ReviewRequest):
    """Run Sandra review on the MR using the selected prompt."""
    # Load prompt
    prompt_path = PROMPTS_DIR / req.prompt_name
    if not prompt_path.exists() or not prompt_path.is_file():
        raise HTTPException(status_code=400, detail=f"Prompt file '{req.prompt_name}' not found.")
    # Ensure the resolved path is still within PROMPTS_DIR
    if not prompt_path.resolve().is_relative_to(PROMPTS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid prompt name.")

    prompt_text = prompt_path.read_text(encoding="utf-8")
    prompt_hash = logs.compute_prompt_hash(prompt_text)

    # Fetch diff
    try:
        diff_data = await fetch_mr_diff(req.mr_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch diff: {e}")

    # Run LLM review
    try:
        result = run_review(prompt_text, diff_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM review failed: {e}")

    # Store log in-memory (backward compatible)
    log_entry = LogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        prompt_name=req.prompt_name,
        mr_url=req.mr_url,
        tokens_used=result["tokens_used"],
        time_seconds=result["time_seconds"],
        summary=result["review"].get("summary", ""),
    )
    
    # Store log in MongoDB with extended fields
    mongo_log_entry = MongoLogEntry.from_log_entry(
        log_entry=log_entry,
        prompt_hash=prompt_hash,
        llm_model="gemini-3.1-flash-lite-preview",
        review_json=result["review"]
    )
    
    logs.add_log_dual(log_entry, mongo_log_entry)

    return result


@app.get("/api/logs")
def get_logs():
    """Return all stored log entries from MongoDB (with in-memory fallback)."""
    return {"logs": logs.get_logs_with_fallback()}


@app.get("/api/logs/csv")
def get_logs_csv():
    """Return logs as CSV."""
    csv_content = logs.logs_to_csv()
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sandmark_logs.csv"},
    )
