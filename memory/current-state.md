# Current state

RecallFrame is running as a localhost-only Docker Compose app at `http://127.0.0.1:3100`. PostgreSQL 18 with pgvector, Redis, the API, worker, and web containers are healthy. OpenRouter is configured from the ignored local `.env` file; the API reports the selected Nemotron model and healthy database/queue. The API and worker run as UID 10001; their existing media and model-cache volumes were preserved and re-owned for that account.

## Real source check

- Imported the user-provided 26.005-second SwiftBuild MP4. FFprobe validation succeeded, and the browser video player, current-time seeking, and HTTP byte-range streaming work. Faster-whisper decoded the audio after pinning PyAV below 19; this clip yielded no transcript segments in the current model run.
- Imported the user-provided public YouTube video (76.115 seconds). yt-dlp downloaded it, faster-whisper transcribed it locally into 20 timestamped segments, and local transcript search returned matching results. Transcript timestamp selection highlights the selected passage.
- The user replaced the local OpenRouter API key. Its `/api/v1/key` endpoint authenticates, and the configured Nemotron model accepted live text and image requests. The video modality returned HTTP 402 because OpenRouter currently requires at least $1 balance for video inputs, even though this model endpoint is free. RecallFrame now sends compressed five-minute chunks as deterministic timestamped JPEG frames plus local transcript evidence, avoiding that video route.
- Both source jobs completed successfully through the frame-based structured-analysis path. The YouTube source has 20 timestamped transcript segments, 6 chapters, and evidence-linked concepts; a grounded Q&A response returned two timestamped citations. The uploaded SwiftBuild promo is playable, has a model-derived chapter and evidence-linked visual concepts, but faster-whisper produced no transcript segments for it. Both sources are indexed in the library.
- The user affirmatively consented to send both specified sources to OpenRouter/NVIDIA, and that existing per-video consent was used for the frame and Q&A requests. The frame + JSON Schema contract was live-verified.

## Verification

- `pnpm verify` passes: lint, typecheck, 3 frontend tests, 12 API tests, and production build. `pnpm format:check` passes.
- Browser smoke passes for upload/import, media playback and seeking, YouTube transcript highlighting, search, saved-insight create/reload/delete, and 390px mobile layout. The BFF forwards valid same-origin writes and rejects a foreign origin.
- The local test suite emits a non-blocking Starlette `TestClient`/httpx deprecation warning.
- The current YouTube run produced no takeaway records; chapter, visual-concept, and grounded-answer flows succeeded. The promo transcript remains empty because this clip yielded no detected speech.
