# Provider and model research

Checked 2026-10-26 against OpenRouter’s current docs and model page. OpenRouter supports video through `video_url` with URL or base64 data URL; routing is provider-dependent and model-specific limits vary. Nemotron 3.5 Super VL (free) currently advertises video input and JSON Schema structured outputs. Its free-endpoint notice says no confidential/personal data and that NVIDIA logs submissions for security and service improvement. See [video inputs](https://openrouter.ai/docs/guides/overview/multimodal/videos) and [model page](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free).

The application uses the configured model ID, compressed local video data URLs, and a per-source notice. No live request was verified without an API key.
