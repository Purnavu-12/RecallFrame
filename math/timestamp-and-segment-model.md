# Timestamp and segment model

Persist every source time as non-negative integer milliseconds. Word times arrive in seconds from faster-whisper and are rounded at the ingest boundary. Segment starts come from the first word; ends come from the final word and are never earlier than the start. UI player seconds are `milliseconds / 1000` only at the player boundary.

For citation seek, the UI compares a time to a validated segment interval, highlights that segment, then seeks the active player. Do not trust timestamps in model output for citations.
