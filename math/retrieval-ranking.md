# Retrieval ranking

Run lexical `plainto_tsquery('simple', query)` and cosine vector ranking independently, retrieve at most 40 candidates from each, then fuse with reciprocal-rank fusion:

`score(d) = Σ_r 1 / (k + rank_r(d))`, with `k = 60`.

Sort by descending score and stable evidence ID as a tie-break. Q&A takes no more than the top eight. This is a rank-fusion heuristic, not a calibrated relevance probability.
