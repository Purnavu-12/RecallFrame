from collections.abc import Iterable
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


def group_words(words: Iterable[Word], max_span_ms: int = 18_000, max_chars: int = 420) -> list[dict[str, int | str]]:
    """Group word timestamps into readable segments with deterministic bounds."""
    result: list[dict[str, int | str]] = []
    current: list[Word] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        pieces: list[str] = []
        for word in current:
            raw = word.text
            if not pieces:
                pieces.append(raw.strip())
            elif raw[:1].isspace() or re.match(r"^[,.;:!?%)\]}]", raw):
                pieces.append(raw)
            else:
                pieces.append(f" {raw}")
        text = "".join(pieces).strip()
        start_ms = max(0, round(current[0].start * 1000))
        end_ms = max(start_ms, round(current[-1].end * 1000))
        if text:
            result.append({"start_ms": start_ms, "end_ms": end_ms, "text": text})
        current = []

    for word in words:
        if not word.text.strip() or word.start < 0 or word.end < word.start:
            continue
        if current and (word.start - current[-1].end >= 0.85 or (word.end - current[0].start) * 1000 > max_span_ms or len(" ".join(w.text for w in current)) + len(word.text) > max_chars):
            flush()
        current.append(word)
        if re.search(r"[.!?][\"')\]]*$", word.text):
            flush()
    flush()
    return result


def make_evidence_windows(segments: list[dict], max_duration_ms: int = 30_000, max_chars: int = 1300, overlap_segments: int = 2) -> list[dict]:
    """Create retrieval windows that retain the exact segment interval and a small overlap."""
    windows: list[dict] = []
    start = 0
    while start < len(segments):
        end = start
        text_size = 0
        while end < len(segments):
            seg = segments[end]
            if end > start and (seg["end_ms"] - segments[start]["start_ms"] > max_duration_ms or text_size + len(seg["text"]) > max_chars):
                break
            text_size += len(seg["text"])
            end += 1
        group = segments[start:end]
        if group:
            windows.append({"segment_id": group[0]["id"], "start_ms": group[0]["start_ms"], "end_ms": group[-1]["end_ms"], "text": " ".join(item["text"] for item in group), "segment_ids": [item["id"] for item in group]})
        if end >= len(segments):
            break
        start = max(start + 1, end - overlap_segments)
    return windows


def normalize_chapters(chapters: list[dict], duration_ms: int) -> list[dict]:
    """Sort, clip and de-overlap model-suggested chapter windows."""
    if duration_ms <= 0:
        return []
    valid = []
    for chapter in chapters:
        try:
            start = max(0, min(duration_ms, int(chapter["start_ms"])))
            end = max(0, min(duration_ms, int(chapter["end_ms"])))
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start or end - start < 8_000:
            continue
        title = str(chapter.get("title", "")).strip()[:240]
        if title:
            valid.append({"title": title, "summary": str(chapter.get("summary", ""))[:2000], "start_ms": start, "end_ms": end})
    valid.sort(key=lambda item: item["start_ms"])
    normalized = []
    for item in valid:
        if normalized and item["start_ms"] < normalized[-1]["end_ms"]:
            item["start_ms"] = normalized[-1]["end_ms"]
        if item["end_ms"] > item["start_ms"]:
            normalized.append(item)
    if not normalized:
        return [{"title": "Full video", "summary": "Indexed source video.", "start_ms": 0, "end_ms": duration_ms}]
    normalized[0]["start_ms"] = 0
    normalized[-1]["end_ms"] = duration_ms
    return normalized


def reciprocal_rank_fusion(lexical: list[str], semantic: list[str], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in (lexical, semantic):
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
