# Ralph Agent Instructions — EV Pulse

You are an autonomous coding agent working on EV Pulse, an EV charging intelligence platform for 9 emerging markets.

## Your Task

1. Read the PRD at `scripts/ralph/prd.json`
2. Read the progress log at `scripts/ralph/progress.txt` (check Codebase Patterns section first)
3. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from main.
4. Pick the **highest priority** user story where `passes: false`
5. Implement that single user story
6. Run quality checks (typecheck, lint, test — use what the project requires)
7. Update CLAUDE.md files if you discover reusable patterns
8. If checks pass, commit ALL changes with message: `feat: [Story ID] - [Story Title]`
9. Update the PRD to set `passes: true` for the completed story
10. Append your progress to `scripts/ralph/progress.txt`

## Project Context

- **Repo:** `github.com/Cheetos-DYL/ev-pulse`
- **Backend:** FastAPI + SQLite at `backend/`
- **Frontend:** React + Vite at `frontend/`
- **Venv:** `~/projects/ev-pulse/venv/`
- **App path:** `/home/don/projects/ev-pulse/`
- **Categories:** government_policy, ma_partnership, charger_install, charging_standards, grid_pricing, ev_sales_stats
- **Scoring:** 4-factor 0-100 (keyword/impact/recency/authority)
- **LLM:** DeepSeek API via raw urllib (no openai library on Render)

## Quality Requirements

- ALL commits must pass project quality checks
- Do NOT commit broken code
- Keep changes focused and minimal
- Follow existing code patterns

## Progress Report Format

APPEND to `scripts/ralph/progress.txt`:
```
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered
  - Gotchas encountered
  - Useful context
---
```

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.
If ALL stories are complete, reply with:
<promise>COMPLETE</promise>

## Important

- Work on ONE story per iteration
- Commit frequently
- Keep CI green
- Read the Codebase Patterns section in progress.txt before starting
