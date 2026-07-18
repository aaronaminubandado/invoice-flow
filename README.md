# InvoiceFlow (Monorepo)

Small-business invoice and receipt management.

## Structure

```
apps/
  api/     FastAPI backend (Python)
  web/     React SPA (Vite)
packages/
  api-types/   TypeScript types generated from the API OpenAPI spec
```

## Quick start

### Backend

```bash
cd apps/api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # configure DATABASE_URL, Supabase, etc.
# Apply migrations in order (see apps/api/README.md)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
npm install
cp apps/web/.env.example apps/web/.env
npm run dev:web
```

### Regenerate API types

With the API running (or after exporting `apps/api/openapi.json`):

```bash
npm run generate:api-types
```

## Deploy

- **Web:** deploy `apps/web` to Vercel (root directory: `apps/web`)
- **API:** deploy `apps/api` to your Python host; set `FRONTEND_ORIGIN` and `PUBLIC_APP_URL`

## Migrations

Run SQL files in `apps/api/migrations/` in numeric order against PostgreSQL.

## Local quality checks

Backend tests always use `TEST_DATABASE_URL`; they will never fall back to the
development or production database. With PostgreSQL running:

```bash
cd apps/api
source venv/bin/activate
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/invoiceflow_test
bash scripts/test_backend.sh
```

The script applies every migration, runs Ruff, and then runs pytest. It is safe
to run repeatedly.

Frontend checks:

```bash
cd apps/web
npm run lint
npm test
npm run build
```
