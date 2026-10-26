# Architecture decisions

- **Local services in Compose:** PostgreSQL/pgvector persists source metadata and evidence; Redis/Celery handles long-running processing outside request handlers.
- **Evidence-first response construction:** The model returns claims and candidate evidence IDs. The API verifies those IDs and derives excerpt/timestamp fields from stored rows.
- **Local retrieval:** PostgreSQL FTS and a 384-dimensional multilingual MiniLM embedding are fused with RRF. Only eight items reach Q&A.
- **Private media:** Uploads are UUID-named under a non-public media volume. YouTube downloads and working files live in a task temp directory.
- **Provider disclosure:** A consent timestamp is persisted per source. The API key stays on the server.
- **No public accounts in v1:** Loopback binding is a core boundary, not an authentication substitute for network deployment.
