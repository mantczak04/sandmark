## Overview
This document outlines the project purpose, context behind it and specific requirements.

## Project name
This project is SANDMARK. Sandmark stands for Sandra Benchmark - a benchmark for AI Agent called Sandra that is supposed to be an AI Code Review solution.

## General purpose of SANDMARK
SANDMARK is a tool made to test different master prompts and LLM model providers, compare them, benchmark using specific metrics.

## How it would be used (steps)
1. User picks specific link of merge request from Gitlab, lets call it MR.
2. User is getting git code diff from MR.
3. User picks one master prompt which is just basically .txt file given by the user.
4. User picks an LLM provider (e.g. Gemini, Claude, GPT) that will be executing master prompt.
5. User clicks button "test review" which cause executing choosen master prompt on the MR.
6. User can see a review made by Sandra, in similar way like it's done on Gitlab (The review comment made under a specific line of code or multiple lines of code)
7. User can see how many tokens were consumed and how much time Sandra needed to make the code review.
8. User can see "logs" of currently made test and previous ones - timestamp, prompt used (name of .txt file), tokens consumed, time Sandra needed to make the review.
9. User can click a button that saves a CSV file from of logs, OR user can click a button that copy the logs in CSV file format.

## Tech Stack
Backend: Python, FastAPI
Frontend: HTML + CSS + Javascript
LLMs: Only gemini-2.0-flash-lite-preview for now. 

## Technical specification
- User paste a raw URL from Gitlab, SANDMARK fetches the diff via Gitlab API.
- Make a place for all tokens (gitlab, LLMs) in .env.example
- Sandra output format would be a JSON structured like this:
<sandra_output_structure>
{
  "comments": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "type": "bug",
      "comment": "Description of the issue and suggested fix."
    }
  ],
  "summary": "Brief overall assessment of the pull request."
}
</sandra_output_structure>
- Logs are stored only in memory (to be enhanced in the future)
- If an error appears, just print the error message in console and on frontend.
- Comparision feature - there is "benchmark" in the name, but for now we only check single master prompt, not side-by-side comparision is in the scope.
- Don't worry about handling large diffs for now.
- Sandra is an AI agent but for now we only focus on testing its master prompt.
- Master prompts are stored in a /prompts catalog
- Frontend should be separated from backend.