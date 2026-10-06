# myAccountant frontend

Minimal React + Vite dashboard for the myAccountant API: login/signup, add/list transactions, add categories, and a monthly spend-by-category chart.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api/*` to `http://127.0.0.1:8000`, so make sure the backend (`uvicorn app.main:app --reload`) is running first.

## Production build

```bash
npm run build
```

Set `VITE_API_BASE_URL` (see `.env.example`) to your deployed backend URL before building, since there's no dev proxy in production.
