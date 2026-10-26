from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.inference import OpenRouterClient, ProviderError, validate_claims
from app.media import ALLOWED_VIDEO_EXTENSIONS, MediaError, parse_youtube_url, probe_media, sha256_file
from app.models import Answer, AnswerCitation, Chapter, Concept, ConceptLink, EvidenceChunk, ProcessingJob, SavedInsight, Takeaway, TranscriptSegment, Video
from app.schemas import ImportResponse, InsightCreate, InsightRead, KnowledgeMapRead, QuestionCreate, SearchResultRead, VideoListItem, VideoRead, YouTubeImportRequest
from app.settings import settings
from app.worker import process_video

app = FastAPI(title="RecallFrame API", version="0.1.0", description="Local-first, evidence-linked video knowledge API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["Content-Type", "Range"], expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"])


def _job(db: Session, video_id: str) -> ProcessingJob:
    row = ProcessingJob(id=str(uuid.uuid4()), video_id=video_id, status="queued", stage="queued", retry_count=0)
    db.add(row)
    db.commit()
    try:
        process_video.delay(video_id)
    except Exception:
        row.status, row.stage = "failed", "failed"
        row.error_message = "The background queue is unavailable. Start Redis and import this source again."
        video = db.get(Video, video_id)
        if video:
            video.status, video.error_message = "failed", row.error_message
        db.commit()
    return row


def _video_or_404(db: Session, video_id: str) -> Video:
    row = db.get(Video, video_id)
    if row is None:
        raise HTTPException(404, "Video not found.")
    return row


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}


@app.get("/api/settings")
def read_settings(db: Session = Depends(get_db)):
    database_status = "ok"
    try:
        db.execute(select(1))
    except Exception:
        database_status = "unavailable"
    queue_status = "unavailable"
    try:
        from redis import Redis
        queue_status = "ok" if Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1).ping() else "unavailable"
    except Exception:
        pass
    return {"api": "ok", "database": database_status, "queue": queue_status, "model": settings.openrouter_model, "openrouter_configured": bool(settings.openrouter_api_key), "whisper_model": settings.whisper_model, "embedding_model": settings.embedding_model, "storage_root": "private local storage", "max_upload_mb": settings.max_upload_mb, "max_video_duration_seconds": settings.max_video_duration_seconds}


@app.get("/api/videos", response_model=list[VideoListItem])
def list_videos(db: Session = Depends(get_db)):
    return list(db.scalars(select(Video).order_by(Video.created_at.desc())).all())


@app.post("/api/videos/upload", response_model=ImportResponse, status_code=202)
async def upload_video(file: UploadFile = File(...), consent: bool = Form(False), db: Session = Depends(get_db)):
    if not consent:
        raise HTTPException(400, "Confirm the OpenRouter/NVIDIA analysis data notice before processing.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(415, "Upload an MP4, MOV, or WebM video.")
    root = Path(settings.media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    video_id = str(uuid.uuid4())
    destination = root / f"{video_id}{suffix}"
    temp_path = root / f".{video_id}.upload"
    size = 0
    try:
        with temp_path.open("wb") as output:
            while block := await file.read(1024 * 1024):
                size += len(block)
                if size > settings.max_upload_mb * 1024 * 1024:
                    raise HTTPException(413, f"Upload exceeds {settings.max_upload_mb} MB.")
                output.write(block)
        metadata = probe_media(temp_path)
        digest = sha256_file(temp_path)
        existing = db.scalar(select(Video).where(Video.sha256 == digest))
        if existing:
            temp_path.unlink(missing_ok=True)
            job = db.scalar(select(ProcessingJob).where(ProcessingJob.video_id == existing.id).order_by(ProcessingJob.created_at.desc()))
            return ImportResponse(video_id=existing.id, job_id=job.id if job else "", deduplicated=True)
        os.replace(temp_path, destination)
        video = Video(id=video_id, title=Path(file.filename or "Untitled video").stem[:500], source_type="upload", storage_path=str(destination), sha256=digest, duration_ms=metadata["duration_ms"], status="queued", consent_at=datetime.now(timezone.utc))
        db.add(video)
        db.commit()
        job = _job(db, video_id)
        return ImportResponse(video_id=video_id, job_id=job.id)
    except HTTPException:
        temp_path.unlink(missing_ok=True)
        raise
    except MediaError as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        temp_path.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        db.rollback()
        raise HTTPException(500, "The upload could not be stored.")
    finally:
        await file.close()


@app.post("/api/videos/import", response_model=ImportResponse, status_code=202)
def import_youtube(body: YouTubeImportRequest, db: Session = Depends(get_db)):
    if body.consent is not True:
        raise HTTPException(400, "Confirm the OpenRouter/NVIDIA analysis data notice before processing.")
    try:
        youtube_id, canonical = parse_youtube_url(body.url)
    except MediaError as exc:
        raise HTTPException(422, str(exc)) from exc
    existing = db.scalar(select(Video).where(Video.youtube_id == youtube_id))
    if existing:
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.video_id == existing.id).order_by(ProcessingJob.created_at.desc()))
        if existing.status not in {"ready", "processing", "queued", "downloading", "transcribing", "visual_analysis", "indexing"}:
            existing.status, existing.error_message = "queued", None
            db.commit()
            job = _job(db, existing.id)
        return ImportResponse(video_id=existing.id, job_id=job.id if job else "", deduplicated=True)
    video_id = str(uuid.uuid4())
    video = Video(id=video_id, title="YouTube video", source_type="youtube", source_url=canonical, youtube_id=youtube_id, thumbnail_url=f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg", status="queued", consent_at=datetime.now(timezone.utc))
    db.add(video)
    db.commit()
    job = _job(db, video_id)
    return ImportResponse(video_id=video_id, job_id=job.id)


@app.get("/api/videos/{video_id}", response_model=VideoRead)
def get_video(video_id: str, db: Session = Depends(get_db)):
    video = db.scalar(select(Video).where(Video.id == video_id).options(selectinload(Video.segments), selectinload(Video.chapters), selectinload(Video.takeaways), selectinload(Video.answers).selectinload(Answer.citations), selectinload(Video.jobs)))
    if video is None:
        raise HTTPException(404, "Video not found.")
    citation_rows = db.execute(select(AnswerCitation, EvidenceChunk).join(EvidenceChunk, AnswerCitation.evidence_id == EvidenceChunk.id).join(Answer, Answer.id == AnswerCitation.answer_id).where(Answer.video_id == video_id)).all()
    sources = {citation.evidence_id: (citation, evidence) for citation, evidence in citation_rows}
    answers = []
    for answer in video.answers:
        citations = []
        for link in answer.citations:
            if link.evidence_id in sources:
                _, evidence = sources[link.evidence_id]
                citations.append({"id": evidence.id, "segment_id": evidence.segment_id or "", "start_ms": evidence.start_ms, "end_ms": evidence.end_ms, "excerpt": evidence.text, "kind": evidence.kind})
        answers.append({"id": answer.id, "question": answer.question, "answer": answer.answer, "grounded": answer.grounded, "created_at": answer.created_at, "citations": citations})
    return VideoRead(
        id=video.id, title=video.title, source_type=video.source_type, source_url=video.source_url,
        youtube_id=video.youtube_id, duration_ms=video.duration_ms, thumbnail_url=video.thumbnail_url,
        status=video.status, error_message=video.error_message, created_at=video.created_at, chapters=video.chapters, segments=video.segments,
        takeaways=video.takeaways, answers=answers,
    )


@app.get("/api/videos/{video_id}/job")
def job_status(video_id: str, db: Session = Depends(get_db)):
    _video_or_404(db, video_id)
    job = db.scalar(select(ProcessingJob).where(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc()))
    if job is None:
        raise HTTPException(404, "Processing job not found.")
    return {"id": job.id, "video_id": job.video_id, "status": job.status, "stage": job.stage, "retry_count": job.retry_count, "error_message": job.error_message, "updated_at": job.updated_at}


@app.post("/api/videos/{video_id}/retry", response_model=ImportResponse, status_code=202)
def retry_video(video_id: str, db: Session = Depends(get_db)):
    video = _video_or_404(db, video_id)
    if video.status != "failed":
        raise HTTPException(409, "Only failed sources can be retried.")
    video.status, video.error_message = "queued", None
    db.commit()
    job = _job(db, video.id)
    return ImportResponse(video_id=video.id, job_id=job.id)


@app.get("/api/videos/{video_id}/transcript")
def transcript(video_id: str, db: Session = Depends(get_db)):
    _video_or_404(db, video_id)
    return list(db.scalars(select(TranscriptSegment).where(TranscriptSegment.video_id == video_id).order_by(TranscriptSegment.ordinal)).all())


@app.get("/api/videos/{video_id}/chapters")
def chapters(video_id: str, db: Session = Depends(get_db)):
    _video_or_404(db, video_id)
    return list(db.scalars(select(Chapter).where(Chapter.video_id == video_id).order_by(Chapter.ordinal)).all())


@app.get("/api/videos/{video_id}/takeaways")
def takeaways(video_id: str, db: Session = Depends(get_db)):
    _video_or_404(db, video_id)
    return list(db.scalars(select(Takeaway).where(Takeaway.video_id == video_id).order_by(Takeaway.ordinal)).all())


def _range_header(raw: str | None, size: int) -> tuple[int, int, bool]:
    if not raw:
        return 0, size - 1, False
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", raw.strip())
    if not match:
        raise HTTPException(416, "Invalid byte range.", headers={"Content-Range": f"bytes */{size}"})
    first, last = match.groups()
    if not first and not last:
        raise HTTPException(416, "Invalid byte range.")
    if not first:
        length = min(int(last), size)
        start, end = size - length, size - 1
    else:
        start, end = int(first), min(int(last) if last else size - 1, size - 1)
    if start >= size or end < start:
        raise HTTPException(416, "Byte range is not satisfiable.", headers={"Content-Range": f"bytes */{size}"})
    return start, end, True


@app.get("/api/videos/{video_id}/stream")
def stream_video(video_id: str, range_header: str | None = Header(default=None, alias="Range"), db: Session = Depends(get_db)):
    video = _video_or_404(db, video_id)
    if video.source_type == "youtube" and video.youtube_id:
        raise HTTPException(400, "YouTube video is played using the embedded player.")
    path = Path(video.storage_path or "").resolve()
    root = Path(settings.media_root).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(404, "Local media file not found.")
    size = path.stat().st_size
    start, end, partial = _range_header(range_header, size)
    def chunks():
        with path.open("rb") as media:
            media.seek(start)
            remaining = end - start + 1
            while remaining:
                data = media.read(min(1024 * 1024, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data
    mime = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}.get(path.suffix.lower(), "application/octet-stream")
    headers = {"Accept-Ranges": "bytes", "Content-Length": str(end - start + 1)}
    if partial:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return StreamingResponse(chunks(), status_code=206 if partial else 200, media_type=mime, headers=headers)


@app.get("/api/search", response_model=list[SearchResultRead])
def search(q: str = Query(min_length=1, max_length=500), video_id: str | None = None, db: Session = Depends(get_db)):
    from app.retrieval import retrieve_evidence
    rows = retrieve_evidence(db, q, video_id, limit=20)
    video_map = {v.id: v.title for v in db.scalars(select(Video).where(Video.id.in_({row.video_id for row in rows}))).all()} if rows else {}
    return [{"video_id": row.video_id, "video_title": video_map.get(row.video_id, "Video"), "segment_id": row.segment_id or "", "start_ms": row.start_ms, "end_ms": row.end_ms, "excerpt": row.text[:600], "score": 1.0 / (index + 1)} for index, row in enumerate(rows)]


@app.post("/api/videos/{video_id}/questions")
def ask_question(video_id: str, body: QuestionCreate, db: Session = Depends(get_db)):
    video = _video_or_404(db, video_id)
    if video.status != "ready":
        raise HTTPException(409, "This video is not ready for questions yet.")
    from app.retrieval import retrieve_evidence
    rows = retrieve_evidence(db, body.question, video_id, limit=8)
    claims: list[dict] = []
    grounded = False
    if rows:
        try:
            result = OpenRouterClient().answer_from_evidence(body.question, [{"id": row.id, "start_ms": row.start_ms, "end_ms": row.end_ms, "kind": row.kind, "text": row.text} for row in rows])
            grounded, claims = validate_claims(result, {row.id for row in rows})
        except ProviderError as exc:
            if exc.retryable:
                raise HTTPException(503, str(exc)) from exc
            raise HTTPException(503, str(exc)) from exc
    answer_text = " ".join(claim["text"] for claim in claims) if grounded else "I couldn’t find enough evidence in this video to answer that question."
    answer = Answer(id=str(uuid.uuid4()), video_id=video_id, question=body.question.strip(), answer=answer_text, grounded=grounded)
    db.add(answer)
    evidence_by_id = {row.id: row for row in rows}
    for evidence_id in dict.fromkeys(eid for claim in claims for eid in claim["evidence_ids"]):
        db.add(AnswerCitation(id=str(uuid.uuid4()), answer_id=answer.id, evidence_id=evidence_id))
    db.commit()
    citations = [{"id": evidence_id, "segment_id": evidence_by_id[evidence_id].segment_id or "", "start_ms": evidence_by_id[evidence_id].start_ms, "end_ms": evidence_by_id[evidence_id].end_ms, "excerpt": evidence_by_id[evidence_id].text, "kind": evidence_by_id[evidence_id].kind} for evidence_id in dict.fromkeys(eid for claim in claims for eid in claim["evidence_ids"])]
    return {"id": answer.id, "question": answer.question, "answer": answer.answer, "grounded": answer.grounded, "citations": citations, "created_at": answer.created_at}


@app.get("/api/insights", response_model=list[InsightRead])
def list_insights(video_id: str | None = None, db: Session = Depends(get_db)):
    query = select(SavedInsight).order_by(SavedInsight.created_at.desc())
    if video_id:
        query = query.where(SavedInsight.video_id == video_id)
    rows = list(db.scalars(query).all())
    titles = {v.id: v.title for v in db.scalars(select(Video).where(Video.id.in_({r.video_id for r in rows}))).all()} if rows else {}
    return [{"id": r.id, "video_id": r.video_id, "video_title": titles.get(r.video_id, "Video"), "text": r.text, "segment_id": r.segment_id, "start_ms": r.start_ms, "created_at": r.created_at} for r in rows]


@app.post("/api/insights", response_model=InsightRead, status_code=201)
def save_insight(body: InsightCreate, db: Session = Depends(get_db)):
    video = _video_or_404(db, body.video_id)
    if body.segment_id:
        segment = db.scalar(select(TranscriptSegment).where(TranscriptSegment.id == body.segment_id, TranscriptSegment.video_id == video.id))
        if segment is None:
            raise HTTPException(422, "The selected transcript segment does not belong to this video.")
        start_ms = segment.start_ms
    else:
        start_ms = body.start_ms
        if start_ms is not None and video.duration_ms is not None and start_ms > video.duration_ms:
            raise HTTPException(422, "The saved timestamp is outside the source video.")
    row = SavedInsight(id=str(uuid.uuid4()), video_id=video.id, text=body.text.strip(), segment_id=body.segment_id, start_ms=start_ms)
    db.add(row)
    db.commit()
    return {"id": row.id, "video_id": row.video_id, "video_title": video.title, "text": row.text, "segment_id": row.segment_id, "start_ms": row.start_ms, "created_at": row.created_at}


@app.delete("/api/insights/{insight_id}", status_code=204)
def delete_insight(insight_id: str, db: Session = Depends(get_db)):
    row = db.get(SavedInsight, insight_id)
    if row is None:
        raise HTTPException(404, "Saved insight not found.")
    db.delete(row)
    db.commit()


@app.get("/api/knowledge-map", response_model=KnowledgeMapRead)
def knowledge_map(db: Session = Depends(get_db)):
    concepts = list(db.scalars(select(Concept)).all())
    video_ids = {row.video_id for row in concepts}
    videos = {v.id: v.title for v in db.scalars(select(Video).where(Video.id.in_(video_ids))).all()} if video_ids else {}
    evidence_ids = {row.evidence_id for row in concepts}
    evidence = {e.id: e for e in db.scalars(select(EvidenceChunk).where(EvidenceChunk.id.in_(evidence_ids))).all()} if evidence_ids else {}
    nodes = []
    for item in concepts:
        source = evidence.get(item.evidence_id)
        if source:
            nodes.append({"id": item.id, "label": item.label, "video_id": item.video_id, "video_title": videos.get(item.video_id, "Video"), "segment_id": source.segment_id or "", "start_ms": source.start_ms, "end_ms": source.end_ms, "description": item.description})
    edges = list(db.scalars(select(ConceptLink)).all())
    return {"nodes": nodes, "edges": [{"source_id": e.source_id, "target_id": e.target_id, "evidence_ids": e.evidence_ids, "score": e.score} for e in edges]}


@app.delete("/api/videos/{video_id}", status_code=204)
def delete_video(video_id: str, db: Session = Depends(get_db)):
    video = _video_or_404(db, video_id)
    storage_path = Path(video.storage_path).resolve() if video.storage_path else None
    root = Path(settings.media_root).resolve()
    if storage_path and root in storage_path.parents:
        try:
            storage_path.unlink(missing_ok=True)
        except OSError as exc:
            raise HTTPException(409, "The video file is in use. Wait for processing to stop, then try deleting it again.") from exc
    db.delete(video)
    db.commit()
