# Task log

- Greenfield RecallFrame initialized as a Git repository and implemented with Next.js, FastAPI, PostgreSQL 18/pgvector, Redis/Celery, local media, and project notes.
- Docker Compose is live on `127.0.0.1:3100`; migrations and all service health checks pass.
- Real user-provided MP4 and public YouTube imports succeeded through the consent flow. YouTube download, local ASR (20 transcript segments), retrieval/search, browser transcript highlighting, local video playback/seek, and 206 byte-range streaming were verified.
- Fixed Docker BFF same-origin validation to compare the browser-facing host rather than the internal `0.0.0.0:3000` listener.
- Fixed faster-whisper/PyAV 19 incompatibility by constraining PyAV to `<19`.
- Local video playback now remains available if downstream analysis fails; HTTP 402 provider failures now get a safe, actionable error message.
- API and worker container processes now run as unprivileged UID 10001. Existing upload and 922 MB model-cache volumes were preserved and re-owned; post-rebuild search, ffprobe, write permissions, and duplicate-upload deduplication passed.
- The replacement OpenRouter key authenticated; short text and image requests returned HTTP 200. Direct video requests returned HTTP 402 with a $1 minimum-balance requirement. Switched visual analysis to deterministic JPEG frames extracted locally from compressed five-minute chunks, with transcript context and exact frame IDs, and disabled unnecessary reasoning tokens for structured output.
- Live frame + JSON Schema contract check passed. Retried both existing sources: both reached `ready`; YouTube retained 20 transcript segments and 6 chapters, and grounded Q&A returned two evidence citations with source timestamps. The uploaded promo gained a chapter and visual concepts but still has no detected speech transcript.
- `pnpm verify` and `pnpm format:check` pass. Browser smoke passes at desktop and 390px mobile, including saved-insight create/reload/delete.
