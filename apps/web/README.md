# InvoiceFlow — Frontend

A modern React dashboard for invoice automation, built for small businesses. Create invoices, track payments, manage clients, and export financial data — all from a single, polished interface.

Built as a portfolio project demonstrating frontend engineering with React 19, TypeScript, and a modern SaaS design aesthetic inspired by Stripe and Linear.

## What It Does

- **Dashboard** — Real-time revenue charts, quick stats, and financial health overview
- **Invoice Management** — Create, send, track, and cancel invoices with a detailed drawer view
- **Payment Recording** — Record partial or full payments, mark invoices as paid with automatic receipt generation
- **Client Directory** — Add, edit, and search clients with inline table management
- **Financial Metrics** — Revenue breakdowns by month, status distribution pie charts, collection rates
- **Multi-Format Export** — Download invoices, clients, and metrics as CSV, Excel, or PDF
- **Business Settings** — Configure company name, email, phone, address, and currency
- **Authentication** — Email/password auth with Supabase (login, register, persistent sessions)
- **Dark / Light Mode** — Theme toggle with system preference detection

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 + TypeScript |
| Build | Vite 7 |
| Styling | Tailwind CSS v4 |
| Routing | React Router v7 |
| Server State | TanStack Query v5 |
| HTTP Client | Axios |
| Auth | Supabase JS |
| Charts | Recharts |
| Animations | Framer Motion |
| Icons | Lucide React |
| Typography | DM Sans + JetBrains Mono |

## Project Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── sidebar.tsx       # Collapsible sidebar with animated active indicator
│   │   └── main-layout.tsx   # Content area with responsive margin
│   └── ui/
│       ├── button.tsx         # CVA-based button variants
│       ├── confirm-dialog.tsx # Reusable confirmation modal
│       ├── export-dropdown.tsx # Multi-format export dropdown
│       ├── skeleton.tsx       # Loading placeholder
│       ├── toast.tsx          # Toast notification system
│       └── index.ts           # Barrel exports
├── pages/
│   ├── auth/
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── dashboard/dashboard.tsx   # Revenue charts and stats
│   ├── invoices/invoices.tsx     # Invoice CRUD, payments, modals, drawer
│   ├── clients/clients.tsx       # Client table with search and modals
│   ├── metrics/metrics.tsx       # Analytics with charts and exports
│   └── settings/settings.tsx     # Business profile form
├── services/
│   ├── invoices.ts   # Invoice API calls
│   ├── clients.ts    # Client API calls
│   ├── metrics.ts    # Metrics API calls
│   ├── settings.ts   # Business settings API calls
│   └── index.ts      # Barrel exports
├── lib/
│   ├── api.ts        # Axios instance with Supabase auth interceptor
│   ├── supabase.ts   # Supabase client initialization
│   └── utils.ts      # Currency formatting, date helpers
├── App.tsx           # Router and provider setup
└── index.css         # Tailwind theme, custom properties, animations
```

## Setup

### Prerequisites

- Node.js 18+
- A running instance of the [InvoiceFlow Backend API](../auto-invoice)
- Supabase project (for auth)

### Installation

```bash
git clone <repo-url>
cd invoice-frontend

npm install
```

### Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Then fill in your values:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_BASE_URL=http://localhost:8000
```

### Running

```bash
npm run dev
```

Opens at `http://localhost:5173`. Make sure the backend API is running at the URL specified in `VITE_API_BASE_URL`.

### Building for Production

```bash
npm run build
```

Output is in the `dist/` directory — a static bundle ready to deploy to any hosting provider.

## Design

The UI follows a modern SaaS dashboard aesthetic:

- **Typography** — DM Sans for UI text, JetBrains Mono for numbers and monetary values
- **Colors** — Deep dark theme with Stripe-inspired primary (#635bff), subtle glass morphism effects
- **Layout** — Collapsible sidebar, constrained content width (1400px), generous whitespace
- **Motion** — Framer Motion spring animations for page transitions, staggered card reveals, interactive hover states
- **Components** — Consistent design tokens via CSS custom properties, reusable CVA-based variants

## License

MIT
