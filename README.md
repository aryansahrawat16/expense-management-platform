# Expense Management Platform

[![CI](https://github.com/aryansahrawat16/expense-management-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/aryansahrawat16/expense-management-platform/actions/workflows/ci.yml)

Personal finance app for tracking spending. You can set monthly budgets per category, see how this month compares to last month, add recurring bills, import a bank statement CSV, and fill in expenses from a photo of a receipt.

React (Vite, Tailwind, Recharts) frontend, FastAPI + SQLAlchemy backend, PostgreSQL, all run with Docker Compose. Tests are pytest and run on GitHub Actions.

## Running it

You need Docker.

```bash
cp .env.example .env
docker compose up --build
```

Then open http://localhost:5173. The API docs are at http://localhost:8000/docs.

Put a random string in `SECRET_KEY` in `.env` (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"` works). `AI_API_KEY` is optional and only needed for receipt scanning.

## Features

### Dashboard
Totals, spending by category, and a table breakdown. You can filter by category and date range and export whatever you're looking at to CSV. It refreshes every 15 seconds and when you switch back to the tab.

### Budgets
Set a monthly limit for a category and it shows a progress bar for the current month. At 80% it turns yellow, over 100% it turns red and shows a banner on the dashboard. The totals are calculated with a `GROUP BY` query instead of looping in Python.

### Trends
Shows a line chart of the last 6 months and how this month compares to last month. It also guesses where the month will end up based on what you've spent so far, and lists which categories went up or down the most.

### Recurring expenses
Weekly, monthly or yearly charges (Spotify, rent, gym, etc). There's no cron job. When you load a page the backend checks for anything that's due and adds it, so it still works if the server was asleep for a few days.

A couple of things that took some thought:

- Monthly charges keep their original day. Something that starts on Jan 31 goes to Feb 28 and then back to Mar 31 instead of staying on the 28th. The original day is stored in `anchor_day`.
- The due rows are locked with `SELECT ... FOR UPDATE` so two requests at the same time can't create the same charge twice.
- If you pause something and resume it later, it skips the months it was paused.

### Bank CSV import
Upload the CSV you download from your bank. The tests cover RBC and TD style exports, and other banks should work as long as their columns have normal names like Date and Amount. It looks for the date, description and amount columns by name, or assumes the TD layout if there's no header row. It handles both a single amount column and separate debit/credit columns.

Deposits and refunds get skipped. Each transaction gets a category from what you picked for that merchant before, or from a keyword list of about 130 store names and words like "pizza" or "pharmacy". If nothing matches it goes in "Other". Rows that match an expense you already have get flagged as possible duplicates and are unchecked. You go through everything on a review screen before it saves.

For dates, it picks the one format that works for every row in the file, so something like 03/04/2026 isn't read as March in one row and April in another.

### Receipt scanning
On the Add Expense page you can upload a photo of a receipt. The backend sends it to an AI vision model and gets back the store, total, date and category. The response has to match a Pydantic model and the category has to be one of the app's categories. It only fills in the form, so you can fix anything before saving.

The upload is checked by its file header (not just the extension) and limited to 5 MB. If there's no API key the button just doesn't show up.

### Security
- Passwords are hashed with bcrypt and login uses JWT tokens
- Every query filters by the logged in user, and there are tests that check one user can't read or edit another user's data
- CSV exports put a `'` in front of cells starting with `=`, `+`, `-` or `@` so Excel doesn't run them as formulas
- Secrets go in `.env`, which is in `.gitignore`

## Project layout

```
backend/
  main.py          app setup and routers
  models.py        database tables
  schemas.py       request/response models
  auth.py          password hashing and JWT
  recurring.py     recurring charge dates
  stats.py         monthly totals used by budgets and trends
  importer.py      bank CSV parsing
  categories.py    categories and merchant keywords
  routers/         endpoints, one file per feature
  tests/
frontend/src/
  pages/
  components/
  api/             functions that call the backend
```

## Tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

By default the tests use SQLite. Set `DATABASE_URL` to a Postgres URL to run them on Postgres (that's what CI does). The receipt tests use a fake client so they don't call the real API.

GitHub Actions runs three jobs on every push: the backend tests against Postgres 16, a frontend build, and a `docker compose build`.

## Deploying

`render.yaml` sets up the database, API and frontend on Render. In Render go to New, then Blueprint, and pick this repo. It'll ask for `VITE_API_URL` (the API's URL) and `CORS_ORIGINS` (the frontend's URL).

On the free plan the API goes to sleep when it's not being used, so the first request can take up to a minute. Render's free Postgres also expires after a while, so check their current limits.

## Environment variables

| Name | Needed | What it's for |
|---|---|---|
| `SECRET_KEY` | yes | signs login tokens |
| `DATABASE_URL` | yes | Postgres connection (Compose and Render set this) |
| `CORS_ORIGINS` | yes | frontend URL(s) allowed to call the API, comma separated |
| `VITE_API_URL` | yes | API URL the frontend uses, set at build time |
| `AI_API_KEY` | no | turns on receipt scanning |
