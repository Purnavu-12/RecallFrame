from functools import lru_cache

from app.settings import settings


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model, device="cpu", trust_remote_code=False)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = model().encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return vectors.tolist()
