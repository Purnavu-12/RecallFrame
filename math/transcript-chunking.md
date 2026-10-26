# Transcript chunking

Transcript grouping is deterministic and ends a segment on punctuation, an 850 ms pause, an 18 s span, or 420 characters. Retrieval windows target 30 s or 1,300 characters with two-segment overlap. Every retrieval window points to its first persisted segment and stores exact start/end bounds for navigation. Transcript input is treated as untrusted source text.
