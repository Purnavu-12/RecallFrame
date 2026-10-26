# Next steps

1. Add a small rights-cleared, human-labeled evaluation set and report measured retrieval/citation results without claiming unmeasured accuracy.
2. Tune and evaluate takeaway generation; the current YouTube analysis produced none despite valid transcript evidence and a successful grounded answer.
3. Investigate alternate speech detection/transcription for the SwiftBuild promo, which yielded no Whisper segments.
4. Replace the deprecated httpx-backed FastAPI `TestClient` setup with the supported test transport when upgrading the test stack.
