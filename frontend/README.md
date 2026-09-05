# Frontend

Next.js App Router chat UI for the customer support triage demo.

## Prerequisites

- Node.js 20+
- Backend running on `http://localhost:8000` (see [`../backend/README.md`](../backend/README.md))

## Setup

```bash
cd frontend
cp .env.example .env.local   # if present; otherwise create .env.local
```

`.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

```bash
npm install
```

## Run

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Local Next.js server |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Vitest |

## Features

- Session create / new conversation
- Stream or full reply mode
- Triage badges, citations, lookup indicator
- Sample prompt chips (prefill draft)

Data fetching uses **TanStack Query** only.

Validation scenarios: [`../specs/001-ticket-triage/quickstart.md`](../specs/001-ticket-triage/quickstart.md)
