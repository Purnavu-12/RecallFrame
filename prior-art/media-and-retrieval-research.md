# Media and retrieval research

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) provides local CTranslate2 transcription and word timestamps.
- [Celery task docs](https://docs.celeryq.dev/en/stable/userguide/tasks.html) recommend idempotent task behavior when late acknowledgements/redelivery are enabled.
- [PostgreSQL full-text search](https://www.postgresql.org/docs/current/textsearch.html) provides lexical matching/ranking; [pgvector](https://github.com/pgvector/pgvector) adds vector similarity in PostgreSQL.
- [MiniLM model card](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) describes a 384-dimensional multilingual sentence space.

RecallFrame uses local transcription/embeddings and reciprocal-rank fusion. Actual retrieval quality must be measured on a labeled set.
