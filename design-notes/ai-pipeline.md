# AI pipeline and data boundary

1. Validate file streams with FFprobe or normalize a YouTube URL to an 11-character video ID before yt-dlp sees it.
2. Extract mono 16 kHz audio locally; transcribe with faster-whisper small/int8.
3. Group word timestamps deterministically and persist transcript/evidence windows.
4. Compute local normalized multilingual embeddings and index lexical/vector retrieval.
5. Send at most one compressed five-minute video chunk plus that chunk’s transcript context per visual analysis request after per-source consent.
6. Retrieve at most eight evidence windows for a Q&A request.
7. Reject malformed output, foreign IDs, or factual claims without evidence IDs; derive citation timestamps and excerpts from database rows.

Provider transport, model limits, and external inference are configuration-dependent. No answer quality guarantee is made without a measured evaluation set.
