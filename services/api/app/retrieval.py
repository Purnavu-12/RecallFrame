from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.embeddings import embed_texts
from app.models import EvidenceChunk
from app.segmentation import reciprocal_rank_fusion


def retrieve_evidence(db: Session, query: str, video_id: str | None = None, limit: int = 8) -> list[EvidenceChunk]:
    vector = embed_texts([query])[0]
    filters = []
    if video_id:
        filters.append(EvidenceChunk.video_id == video_id)

    lexical_query = func.plainto_tsquery("simple", query)
    lexical_stmt = select(EvidenceChunk).where(*filters, func.to_tsvector("simple", EvidenceChunk.text).op("@@")(lexical_query)).order_by(func.ts_rank(func.to_tsvector("simple", EvidenceChunk.text), lexical_query).desc()).limit(40)
    lexical_rows = list(db.scalars(lexical_stmt).all())

    semantic_stmt = select(EvidenceChunk).where(*filters, EvidenceChunk.embedding.is_not(None)).order_by(EvidenceChunk.embedding.cosine_distance(vector)).limit(40)
    semantic_rows = list(db.scalars(semantic_stmt).all())
    lexical_ids = [item.id for item in lexical_rows]
    semantic_ids = [item.id for item in semantic_rows]
    ranked = reciprocal_rank_fusion(lexical_ids, semantic_ids)
    rank_ids = [item_id for item_id, _ in ranked[:limit]]
    if not rank_ids:
        return []
    row_map = {item.id: item for item in [*lexical_rows, *semantic_rows]}
    return [row_map[item_id] for item_id in rank_ids if item_id in row_map]
