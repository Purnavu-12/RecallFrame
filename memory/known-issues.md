# Known issues

- OpenRouter returns HTTP 402 with the configured key, and the account credits check reports no positive balance. Add credits or increase the key's available budget in OpenRouter, then retry the two failed source jobs. The selected endpoint is listed as free, but access/rate limits can still depend on account credits.
- Until OpenRouter accepts requests, visual evidence extraction, model-derived chapters/takeaways/concepts, and grounded Q&A cannot be verified. Local uploads, YouTube import, transcription, transcript indexing/search, and media navigation work.
- The SwiftBuild promotional MP4 produced no transcript segments with the configured faster-whisper `small` model. This may be a silent/mostly-music clip or an ASR miss; it is not evidence that speech transcription works on every input.
- Celery emits its standard warning that the worker runs as root inside its container. The stack is restricted to localhost; review container user/volume permissions before adapting it for network access.
- Tests emit a non-blocking Starlette deprecation warning for the httpx-backed `TestClient`.
