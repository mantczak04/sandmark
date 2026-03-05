import os
import re
from urllib.parse import quote_plus

import httpx


GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")


def parse_mr_url(mr_url: str) -> tuple[str, str]:
    """Extract project path and MR IID from a GitLab merge request URL.

    Supports URLs like:
        https://gitlab.com/group/project/-/merge_requests/123
        https://gitlab.example.com/group/subgroup/project/-/merge_requests/456
    """
    pattern = re.compile(
        r"https?://[^/]+/(.+?)/-/merge_requests/(\d+)"
    )
    match = pattern.match(mr_url.strip())
    if not match:
        raise ValueError(
            "Invalid GitLab MR URL. Expected format: "
            "https://gitlab.com/<project_path>/-/merge_requests/<id>"
        )
    project_path = match.group(1)
    mr_iid = match.group(2)
    return project_path, mr_iid


async def fetch_mr_diff(mr_url: str) -> dict:
    """Fetch merge request changes (diff) from GitLab API."""
    project_path, mr_iid = parse_mr_url(mr_url)
    encoded_project = quote_plus(project_path)

    api_url = f"{GITLAB_URL}/api/v4/projects/{encoded_project}/merge_requests/{mr_iid}/changes"

    headers = {}
    if GITLAB_TOKEN:
        headers["PRIVATE-TOKEN"] = GITLAB_TOKEN

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

    changes = data.get("changes", [])
    files = []
    for change in changes:
        files.append({
            "old_path": change.get("old_path", ""),
            "new_path": change.get("new_path", ""),
            "diff": change.get("diff", ""),
            "new_file": change.get("new_file", False),
            "renamed_file": change.get("renamed_file", False),
            "deleted_file": change.get("deleted_file", False),
        })

    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "author": data.get("author", {}).get("username", ""),
        "source_branch": data.get("source_branch", ""),
        "target_branch": data.get("target_branch", ""),
        "files": files,
    }
