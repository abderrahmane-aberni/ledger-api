# myAccountant API

**Live demo:** [myaccountant-api-eight.vercel.app](https://myaccountant-api-eight.vercel.app) &middot; **API docs:** [myaccountant-api.onrender.com/docs](https://myaccountant-api.onrender.com/docs)

> The backend runs on Render's free tier and spins down after inactivity — the first request after a quiet period can take up to ~50 seconds to wake up. Everything after that is normal speed.

A personal finance tracking REST API built with FastAPI, PostgreSQL, and SQLAlchemy — JWT-authenticated, with budgets, CSV import/export, and real SQL aggregation reporting.

## Problem statement

Most personal-finance demo projects stop at "CRUD for transactions." This one goes one step further: every user's transactions are scoped behind JWT auth, spending is rolled up with real `GROUP BY` / aggregate SQL (not pulled into Python and summed), and budgets are checked against that same aggregation so "am I over budget this month" is answered by the database, not the client.

## Architecture

```
Client (Swagger UI / React dashboard / curl)
        |
        v
  FastAPI app  (app/main.py)
        |
        +-- app/routers/auth.py          -> /signup, /login            (JWT issuance)
        +-- app/routers/categories.py    -> /categories                (CRUD, user-scoped)
        +-- app/routers/transactions.py  -> /transactions               (CRUD + CSV import/export)
        +-- app/routers/budgets.py       -> /budgets                   (CRUD)
        +-- app/routers/reports.py       -> /reports                   (SQL aggregation)
        |
        v
  app/deps.py  -> get_current_user()  (decodes JWT, loads the user, every protected route depends on this)
        |
        v
  SQLAlchemy ORM (app/models.py: User -> Category -> Transaction, Budget)
        |
        v
  PostgreSQL  (Docker Compose locally, or your own instance)
```

Tests (`tests/`) run against a throwaway SQLite file instead of Postgres, so `pytest` needs no running database and CI needs no database service.

## Frontend

A minimal React + Vite dashboard lives in `frontend/` — login/signup, add/list transactions, add categories, and a monthly spend-by-category chart (hand-rolled SVG bar chart, no charting library). See `frontend/README.md` for setup; in short:

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173 and proxies API calls to the backend at http://127.0.0.1:8000.

## Setup

### Option A — local Python + your own Postgres

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# .env needs:
#   DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/<db>
#   JWT_SECRET=<any long random string>

uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive Swagger UI.

### Option B — Docker Compose (API + Postgres, one command)

```bash
docker compose up --build
```

API is then at http://localhost:8000/docs; Postgres data persists in a named Docker volume between runs.

### Running tests

```bash
pytest -v
```

## Key technical decisions

- **FastAPI over Flask/Django** — native async support, automatic OpenAPI docs, and Pydantic validation out of the box, which matters more for an API-first project than Django's batteries-included admin/templating.
- **JWT (python-jose) over session cookies** — a stateless token is the right fit for an API meant to be consumed by a separate frontend (and later, other clients) rather than server-rendered pages.
- **Real SQL aggregation for reports** — `/reports/monthly-summary`, `/reports/category-breakdown`, and `/reports/budget-alerts` all use SQLAlchemy's `func.sum()` / `extract()` so PostgreSQL does the grouping, instead of fetching every transaction and summing in Python. This is also why the schema indexes `category_id` and `user_id`.
- **SQLite for tests, Postgres for real use** — `tests/conftest.py` points `DATABASE_URL` at a temp SQLite file before the app is imported, so the test suite is hermetic and CI needs no database service at all.
- **User-scoped everything** — every query filters on `user_id` (via `get_current_user`), so there's no endpoint where one user can read or modify another user's data by guessing an ID.

## What I'd improve with more time

- Swap the hand-rolled SQL filters for an Alembic migration history instead of `Base.metadata.create_all()`, which doesn't handle schema changes after the first run.
- Add rate limiting on `/login` to slow down credential-stuffing attempts.
- Add pagination to `GET /transactions` — fine for a demo account, not fine for a year of real transactions.
- Replace the 24h-flat JWT expiry with short-lived access tokens + refresh tokens.
