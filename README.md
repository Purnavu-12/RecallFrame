# RecallFrame

RecallFrame is an evidence-first video knowledge workspace. It is designed to run locally with Docker Compose and indexes private uploads or individual public YouTube videos into a searchable, timestamped library.

## Local development

1. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` if you want video analysis and grounded Q&A. The key is consumed by the API and worker only.
2. Start Docker Desktop with its Linux engine enabled.
3. Run `docker compose up --build` from this folder.
4. Open [http://127.0.0.1:3100](http://127.0.0.1:3100). Set `RECALLFRAME_WEB_PORT` in `.env` to choose another loopback port.

The web port is bound to loopback. The API, PostgreSQL, and Redis are internal to the Compose network. Uploaded media and PostgreSQL data use persistent Docker volumes. Uploaded media is retained until a video is deleted; downloaded YouTube media and temporary processing data are removed after analysis. Failed processing jobs can be retried from the video workspace after correcting the reported configuration or source issue.

The **Try preprocessed demo** page is an illustrative walkthrough separate from your library. Its transcript, diagram, timestamps, and answer are authored sample data; no source video was processed and no model inference ran for that page. This keeps the demo distinct from indexed, evidence-backed content.

To explicitly live-check the selected provider’s video and structured-output contract, place a short, non-sensitive clip in the private media volume and run `docker compose exec worker python check_openrouter_contract.py /data/media/short-nonsensitive-clip.mp4`. The script limits the clip to 15 seconds, prints the external data notice, and requires typing `SEND`; use media you have permission to send. External inference has not been verified unless this check completes successfully.

## Data and model notice

Speech transcription, embeddings, and retrieval run locally. For video analysis and Q&A, a per-video consent is required before content is sent to OpenRouter’s `nvidia/nemotron-3.5-super-vl:free` endpoint. OpenRouter’s current endpoint notice says not to upload confidential information or personal data and states that NVIDIA logs submissions for security and service improvement. Do not use the free endpoint with sensitive media. See [model and data notice](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free).

## Stack

- Next.js App Router, TypeScript, and a same-origin API proxy.
- FastAPI, PostgreSQL 18 with pgvector, Redis, Celery, and Alembic.
- FFprobe/FFmpeg validation and media preparation; faster-whisper `small` on CPU int8.
- Local multilingual MiniLM embeddings, PostgreSQL full-text search, cosine retrieval, and reciprocal-rank fusion.
- OpenRouter video requests use compressed five-minute clips and structured output. Provider limits and free-tier availability may change.

## Verification

```powershell
pnpm install
pnpm lint
pnpm typecheck
pnpm test
pnpm build
python -m pytest services/api/tests -q
```

The Docker Compose app is not a network-authenticated deployment. Do not expose it outside localhost without adding and reviewing authentication, authorization, and deployment security.

## Project notes

See `design-notes/`, `prior-art/`, `math/`, and `memory/` for architecture, research, retrieval/timestamp decisions, and current implementation status. An API-derived frontend client can be refreshed with `pnpm generate:api` while the local API is running.
