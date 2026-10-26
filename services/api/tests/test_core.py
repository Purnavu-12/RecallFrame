from math import isclose

from app.inference import validate_claims
from app.job_state import JobSnapshot, retry, transition
from app.media import MediaError, parse_youtube_url
from app.main import _range_header, app
from app.segmentation import Word, group_words, make_evidence_windows, normalize_chapters, reciprocal_rank_fusion
from fastapi import HTTPException
from fastapi.testclient import TestClient


def test_group_words_respects_bounds_and_punctuation():
    result = group_words([Word(0, 0.2, "Hello"), Word(0.2, 0.4, " world."), Word(1.5, 1.8, "Again!")])
    assert result == [
        {"start_ms": 0, "end_ms": 400, "text": "Hello world."},
        {"start_ms": 1500, "end_ms": 1800, "text": "Again!"},
    ]


def test_group_words_skips_invalid_and_negative_timestamps():
    result = group_words([Word(-1, -0.5, "bad"), Word(0.2, 0.1, "bad"), Word(0, 0.3, "good")])
    assert result == [{"start_ms": 0, "end_ms": 300, "text": "good"}]


def test_evidence_windows_overlap_and_preserve_bounds():
    segments = [{"id": str(i), "start_ms": i * 1000, "end_ms": i * 1000 + 900, "text": f"line {i}"} for i in range(8)]
    windows = make_evidence_windows(segments, max_duration_ms=3000, max_chars=100, overlap_segments=1)
    assert windows[0]["segment_ids"] == ["0", "1", "2"]
    assert windows[1]["segment_ids"][0] == "2"
    assert windows[0]["start_ms"] == 0 and windows[0]["end_ms"] == 2900


def test_chapters_clip_sort_and_fill_source_extent():
    result = normalize_chapters([
        {"title": "later", "start_ms": 50000, "end_ms": 120000},
        {"title": "first", "start_ms": -1000, "end_ms": 60000},
        {"title": "invalid", "start_ms": 3, "end_ms": 5},
    ], 100000)
    assert result[0]["start_ms"] == 0
    assert result[-1]["end_ms"] == 100000
    assert all(item["end_ms"] > item["start_ms"] for item in result)


def test_rrf_uses_both_lists_and_stable_ties():
    result = reciprocal_rank_fusion(["a", "b"], ["b", "a"])
    assert [item_id for item_id, _ in result] == ["a", "b"]
    assert all(isclose(score, 1 / 61 + 1 / 62) for _, score in result)


def test_youtube_url_normalizes_only_one_video():
    assert parse_youtube_url("https://youtu.be/AbCdEfGh123") == ("AbCdEfGh123", "https://www.youtube.com/watch?v=AbCdEfGh123")
    assert parse_youtube_url("https://www.youtube.com/watch?v=AbCdEfGh123&t=20") == ("AbCdEfGh123", "https://www.youtube.com/watch?v=AbCdEfGh123")


def test_youtube_url_rejects_playlist_and_unsafe_host():
    for url in ("https://youtube.com/watch?v=AbCdEfGh123&list=playlist", "https://youtube.com.evil.test/watch?v=AbCdEfGh123", "http://youtu.be/AbCdEfGh123", "https://youtube.com/playlist?list=abc"):
        try:
            parse_youtube_url(url)
        except MediaError:
            pass
        else:
            raise AssertionError(f"URL should be rejected: {url}")


def test_citation_allowlist_rejects_fabricated_or_missing_ids():
    allowed = {"e1", "e2"}
    valid, claims = validate_claims({"grounded": True, "claims": [{"text": "A claim", "evidence_ids": ["e1", "e2", "e1"]}]}, allowed)
    assert valid and claims == [{"text": "A claim", "evidence_ids": ["e1", "e2"]}]
    assert validate_claims({"grounded": True, "claims": [{"text": "No ID", "evidence_ids": []}]}, allowed) == (False, [])
    assert validate_claims({"grounded": True, "claims": [{"text": "Fake", "evidence_ids": ["outside"]}]}, allowed) == (False, [])
    assert validate_claims({"grounded": False, "claims": []}, allowed) == (False, [])


def test_job_transitions_and_retry_count_are_explicit():
    queued = JobSnapshot("queued", "queued")
    running = transition(queued, "transcribing")
    assert running.status == "processing"
    assert retry(running) == JobSnapshot("retrying", "retrying", 1)
    assert transition(running, "ready").status == "completed"


def test_range_header_supports_bounded_and_suffix_ranges():
    assert _range_header("bytes=10-19", 100) == (10, 19, True)
    assert _range_header("bytes=-10", 100) == (90, 99, True)
    assert _range_header(None, 100) == (0, 99, False)


def test_range_header_rejects_unsatisfiable_ranges():
    for value in ("bytes=100-", "items=0-4", "bytes=12-4"):
        try:
            _range_header(value, 100)
        except HTTPException as exc:
            assert exc.status_code == 416
        else:
            raise AssertionError(f"Invalid range should be rejected: {value}")


def test_api_health_and_contract_are_available_without_database_data():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok", "service": "api"}
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/videos/{video_id}/retry" in paths
    assert "/api/videos/{video_id}/stream" in paths
