# Known issues

- OpenRouter's direct video modality returns HTTP 402 unless the account has at least $1 balance. RecallFrame avoids that route by sending deterministic JPEG frames with transcript context. The current free-tier key accepts image and text requests.
- The SwiftBuild promotional MP4 produced no transcript segments with the configured faster-whisper `small` model. This may be a silent/mostly-music clip or an ASR miss; it is not evidence that speech transcription works on every input.
- The current YouTube analysis produced six chapters and evidence-linked concepts, but no takeaways. Improve model prompting or handling if takeaways are expected for every kind of source.
- Tests emit a non-blocking Starlette deprecation warning for the httpx-backed `TestClient`.
