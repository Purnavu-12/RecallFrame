# Task log

- Greenfield RecallFrame initialized as a Git repository and implemented with Next.js, FastAPI, PostgreSQL 18/pgvector, Redis/Celery, local media, and project notes.
- Docker Compose is live on `127.0.0.1:3100`; migrations and all service health checks pass.
- Real user-provided MP4 and public YouTube imports succeeded through the consent flow. YouTube download, local ASR (20 transcript segments), retrieval/search, browser transcript highlighting, local video playback/seek, and 206 byte-range streaming were verified.
- Fixed Docker BFF same-origin validation to compare the browser-facing host rather than the internal `0.0.0.0:3000` listener.
- Fixed faster-whisper/PyAV 19 incompatibility by constraining PyAV to `<19`.
- Local video playback now remains available if downstream analysis fails; HTTP 402 provider failures now get a safe, actionable error message.
- OpenRouter accepted the key but returned HTTP 402 for both analyzed sources; the credits check returned no positive balance. Full model-derived analysis and Q&A remain blocked until the account/key has available credits. Source data and completed transcripts remain local.
- `pnpm verify` and `pnpm format:check` pass. Browser smoke passes at desktop and 390px mobile, including saved-insight create/reload/delete.
