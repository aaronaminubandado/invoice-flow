# InvoiceFlow — Backend API

A production-grade FastAPI backend for an invoice automation system designed for small businesses. Handles invoice lifecycle management, automated email delivery with PDF attachments, payment tracking, financial reporting, and multi-format data exports.

Built as a portfolio project demonstrating backend engineering with async Python, relational database design, background task processing, and third-party service integration.

## What It Does

- **Invoice Management** — Create, update, cancel, and track invoices through a state machine (draft → sent → partial → paid / overdue → cancelled)
- **Payment Processing** — Record partial or full payments, auto-update invoice status, prevent overpayment
- **Email Delivery** — Send invoice and receipt emails with PDF attachments via Resend, with delivery status tracking
- **PDF Generation** — Generate professional invoice and receipt PDFs with business branding using ReportLab
- **Automated Reminders** — Scheduled overdue detection (daily) and tiered reminder emails (3-day, 7-day)
- **Multi-Format Exports** — Export invoices, clients, and metrics as CSV, Excel (.xlsx), or PDF
- **Business Settings** — Configurable business profile (name, email, phone, address, currency) applied to all documents
- **Client Management** — CRUD operations with search and export capabilities
- **Financial Metrics** — Revenue summaries, monthly breakdowns, collection rates

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.135 |
| Database | PostgreSQL (Supabase) via asyncpg + SQLAlchemy 2.0 |
| Auth | Supabase JWT (ES256) with JWKS verification |
| Email | Resend API (console fallback for development) |
| PDF | ReportLab |
| Excel | openpyxl |
| Scheduler | APScheduler (async) |
| Validation | Pydantic v2 |

## Architecture

```
app/
├── api/              # Route handlers
│   ├── invoices.py   # Invoice CRUD, payments, PDF download, export
│   ├── clients.py    # Client CRUD, search, export
│   ├── metrics.py    # Revenue analytics, export
│   ├── settings.py   # Business settings CRUD
│   ├── payments.py   # Receipt PDF download
│   ├── dashboard.py  # Dashboard stats
│   ├── webhooks.py   # External payment webhook
│   └── middleware.py  # CORS, rate limiting, security headers, logging
├── core/
│   ├── config.py     # Environment-based settings (Pydantic)
│   ├── database.py   # Async SQLAlchemy engine + session
│   ├── security.py   # Supabase JWT verification via JWKS
│   └── exceptions.py # Custom exception classes
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic request/response schemas
├── services/
│   ├── email.py      # Email provider abstraction + templates + tracking
│   ├── pdf.py        # Invoice + receipt PDF generation
│   ├── export.py     # CSV, Excel, PDF table export utilities
│   ├── scheduler.py  # Overdue detection + reminder cron jobs
│   ├── reminders.py  # Overdue invoice processing
│   ├── invoice_number.py  # Concurrency-safe invoice numbering
│   ├── invoice_state.py   # Invoice status state machine
│   └── business_settings.py  # Business settings data access
├── deps.py           # FastAPI dependency injection
└── tests/            # Test suite
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database (Supabase recommended)
- Resend API key (optional — uses console output in development)

### Installation

```bash
git clone <repo-url>
cd auto-invoice

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
RESEND_API_KEY=re_your_api_key      # Optional for development
EMAIL_FROM=Invoices <noreply@yourdomain.com>
ENV=development
```

### Database Migrations

Run the SQL migration files in order against your database:

```bash
psql $DATABASE_URL -f migrations/001_metrics_indexes.sql
psql $DATABASE_URL -f migrations/002_invoice_number_and_reminder_count.sql
psql $DATABASE_URL -f migrations/003_email_tracking.sql
psql $DATABASE_URL -f migrations/004_business_settings.sql
```

### Running

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `/docs`.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/invoices` | Create invoice (sends email with PDF) |
| `GET` | `/invoices` | List user's invoices |
| `GET` | `/invoices/export?format=csv\|xlsx\|pdf` | Export invoices |
| `GET` | `/invoices/{id}/pdf` | Download invoice PDF |
| `POST` | `/invoices/{id}/payments` | Record payment |
| `POST` | `/invoices/{id}/mark-paid` | Mark fully paid (sends receipt) |
| `POST` | `/invoices/{id}/resend` | Resend invoice email |
| `POST` | `/invoices/{id}/cancel` | Cancel invoice |
| `GET` | `/invoices/{id}/payments/{pid}/receipt` | Download receipt PDF |
| `POST` | `/clients` | Create client |
| `GET` | `/clients` | List clients |
| `GET` | `/clients/export?format=csv\|xlsx\|pdf` | Export clients |
| `GET` | `/clients/search?q=` | Search clients |
| `GET` | `/metrics/revenue-summary` | Revenue metrics |
| `GET` | `/metrics/monthly-revenue` | Monthly breakdown |
| `GET` | `/metrics/export?format=csv\|xlsx\|pdf` | Export metrics |
| `GET/POST/PUT` | `/settings` | Business settings |
| `GET` | `/payments/{id}/receipt` | Download receipt PDF |
| `POST` | `/webhooks/payment` | Payment webhook |

All endpoints except `/health` and `/webhooks/payment` require a valid Supabase JWT in the `Authorization: Bearer` header.

## Testing

```bash
pytest
```

## License

MIT
