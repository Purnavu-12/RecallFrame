# RecallFrame engineering notes

## Product boundary

RecallFrame is a local-first, single-user video knowledge workspace. Keep the web server bound to loopback, media private, and AI output tied to stored source evidence. Never add public registration, remote media URLs outside validated YouTube IDs, or ungrounded citations.

## Development

- Frontend: `apps/web` (Next.js App Router, TypeScript, React).
- API and worker: `services/api` (FastAPI, SQLAlchemy, Alembic, Celery).
- Start the stack with `docker compose up --build`; configure the server-side provider key in ignored `.env`.
- Python timestamps and persisted timestamps are integer milliseconds. Convert to seconds only at a player boundary.
- Regenerate the API TypeScript types from `http://127.0.0.1:8000/openapi.json` after contract changes.
- Treat transcript, video, and model text as untrusted input. Validate every model reference against stored evidence before persistence or response.

## Verification

Run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build`. For Python changes, run `python -m pytest services/api/tests -q`. Docker integration checks need a running Docker Desktop Linux engine.

## Change practices

Keep secrets out of source and logs. Do not add fake indexed video content. When a capability is not configured, show an explicit state. Update the decision and research notes when behavior or assumptions change.
