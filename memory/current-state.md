# Current state

RecallFrame is running as a localhost-only Docker Compose app at `http://127.0.0.1:3100`. PostgreSQL 18 with pgvector, Redis, the API, worker, and web containers are healthy. OpenRouter is configured from the ignored local `.env` file; the API reports the selected Nemotron model and healthy database/queue.

## Real source check

- Imported the user-provided 26.005-second SwiftBuild MP4. FFprobe validation succeeded, and the browser video player, current-time seeking, and HTTP byte-range streaming work. Faster-whisper decoded the audio after pinning PyAV below 19; this clip yielded no transcript segments in the current model run.
- Imported the user-provided public YouTube video (76.115 seconds). yt-dlp downloaded it, faster-whisper transcribed it locally into 20 timestamped segments, and local transcript search returned matching results. Transcript timestamp selection highlights the selected passage.
- Both source jobs reached external visual analysis and received HTTP 402 from OpenRouter. The account credits endpoint showed no positive balance. The sources and completed local transcript/evidence remain stored; neither job has model-derived chapters, takeaways, concepts, or grounded Q&A yet.
- The user affirmatively consented to sending these two sources to OpenRouter/NVIDIA. The model request was attempted for each source. A successful provider contract or structured response has not been verified.

## Verification

- `pnpm verify` passes: lint, typecheck, 3 frontend tests, 12 API tests, and production build. `pnpm format:check` passes.
- Browser smoke passes for upload/import, media playback and seeking, YouTube transcript highlighting, search, saved-insight create/reload/delete, and 390px mobile layout. The BFF forwards valid same-origin writes and rejects a foreign origin.
- The local test suite emits a non-blocking Starlette `TestClient`/httpx deprecation warning.
