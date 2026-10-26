# Quality strategy

Pure tests cover timestamp bounds, deterministic grouping/chunking, chapter normalization, reciprocal-rank fusion, URL host/playlist validation, citation allowlists, and HTTP byte-range boundaries. Browser checks cover responsive source navigation, import consent, status/error states, and citation seeking. Database, real media, provider contract, and full Compose checks require PostgreSQL/Redis/FFmpeg and (for inference) a configured OpenRouter key.

Evaluation metrics should separately report retrieval recall, answerable/unanswerable handling, citation validity, and timestamp error. No accuracy is claimed until a rights-cleared, human-labeled set has been run.
