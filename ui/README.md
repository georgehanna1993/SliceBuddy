# SliceBuddy UI

Next.js frontend for the SliceBuddy 3D print planner.

## Setup

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`.

The backend defaults to `http://127.0.0.1:8000`. Override it in `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Checks

```bash
npm run lint
npm run build
```
