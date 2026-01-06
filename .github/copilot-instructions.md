# Copilot / AI Agent Instructions — Jan 6 project

Short, actionable guidance for AI coding agents working in this repository.

## Big picture
- Single-file FastAPI service: main entry is `main.py` which defines a FastAPI app with two endpoints: `/health` (GET) and `/query` (POST).
- Purpose: Convert a natural-language question into a safe SQLite `SELECT` query (against a single table `users`) using Google's Generative AI, validate the SQL, run it against `db.sqlite`, and return rows.

## Key files
- `main.py` — app entrypoint, contains functions: `nl_to_sql(question)`, `validate_sql(sql)`, `run_sql(sql)`, and the FastAPI routes.

## How to run (local dev)
- Requires Python and the `google.generativeai` package (Gemini). Run the FastAPI app with Uvicorn:

```bash
python3 -m uvicorn main:app --reload --port 8000
```

- Set the Gemini API key in the environment: `GEMINI_API_KEY`.

## Important conventions & constraints (do NOT change silently)
- The NL→SQL flow must always enforce safety rules implemented in `validate_sql`:
  - Only `SELECT` queries allowed (no INSERT/UPDATE/DELETE/DROP).
  - No semicolons allowed in input (single-statement enforcement).
  - Only the `users` table is permitted; allowed columns are: `id`, `name`, `created_at`.
  - Result sets are capped to `LIMIT 100` (the code appends/overrides limits to enforce this).

- When modifying `nl_to_sql`, preserve how the prompt and post-processing enforce `LIMIT 100` and returning only the SQL string. Avoid returning helper text or commentary from the model.

- DB file: `db.sqlite` in repo root — `run_sql` uses this path directly. Be careful with migrations or schema changes; they must be reflected in `validate_sql`'s allowed columns/table list.

## Integrations
- Google Generative AI: code imports `google.generativeai as genai` and configures with `GEMINI_API_KEY` inside `nl_to_sql`. Changes to auth or model selection should keep the env-var-based config.
- SQLite (`sqlite3`): used synchronously. If refactoring to async DB access, ensure the FastAPI endpoints are updated accordingly.

## Typical edit scenarios & examples
- Example: adding a new allowed column `email`
  - Update the `allowed_columns` set inside `validate_sql` to include `email`.
  - Update any tests and consider seed data in `db.sqlite`.

- Example: quick curl test against the running service

```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
  -d '{"question":"List id and name from users where name LIKE \"A%\""}'
```

Expected JSON response shape:

```json
{
  "sql": "SELECT id, name FROM users WHERE name LIKE 'A%' LIMIT 100;",
  "rows": [ /* sqlite rows array */ ]
}
```

## Debugging tips
- If the model generates invalid SQL, inspect `nl_to_sql` prompt and the returned `response.text`; debugging often involves tightening the prompt and post-processing.
- Local DB inspection: open `db.sqlite` with `sqlite3 db.sqlite` or a DB browser to seed/inspect test rows.

## What to watch for when changing behavior
- Do not relax the SQL validation rules without explicit rationale and test coverage — these are deliberate safety constraints.
- If you change the table name, update `validate_sql` and all code that assumes `users`.

## Tests & CI
- No tests or CI configs present in the repo. When adding features, include unit tests for `validate_sql` and integration tests for `/query`.

## Questions for the repo owner
- Preferred Python version and package manager? (add `requirements.txt` or `pyproject.toml` if desired)
- Should the API remain single-table `users`, or should it be generalized? If generalization is desired, specify new allowed schemas so `validate_sql` can be updated safely.

---
If any section is unclear or you want more examples (tests, CI, or a small data seed for `db.sqlite`), tell me which area to expand.
