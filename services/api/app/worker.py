from __future__ import annotations

import logging
import subprocess
import tempfile
import uuid
from pathlib import Path

from celery import Celery
from sqlalchemy import select
import yt_dlp

from app.database import SessionLocal
from app.embeddings import embed_texts
from app.inference import OpenRouterClient, ProviderError
from app.job_state import JobSnapshot, retry as retry_job, transition
from app.media import extract_audio, make_video_chunk, probe_media
from app.models import Chapter, Concept, ConceptLink, EvidenceChunk, ProcessingJob, Takeaway, TranscriptSegment, Video
from app.segmentation import make_evidence_windows, normalize_chapters
from app.settings import settings
from app.transcribe import transcribe_audio

logger = logging.getLogger(__name__)
celery_app = Celery("recallframe", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"], task_acks_late=True, task_reject_on_worker_lost=True, worker_prefetch_multiplier=1, task_track_started=True)


def _stage(db, video: Video, job: ProcessingJob, name: str) -> None:
    snapshot = transition(JobSnapshot(job.status, job.stage, job.retry_count), name)
    video.status, job.status, job.stage = name, snapshot.status, snapshot.stage
    db.commit()


@celery_app.task(bind=True, max_retries=3, name="process_video")
def process_video(self, video_id: str) -> dict:
    with SessionLocal() as db:
        video = db.get(Video, video_id)
        if video is None:
            return {"status": "deleted"}
        if video.status == "ready":
            return {"status": "ready", "video_id": video_id}
        job = db.scalar(select(ProcessingJob).where(ProcessingJob.video_id == video_id).order_by(ProcessingJob.created_at.desc()))
        if job is None:
            return {"status": "missing_job"}
        Path(settings.media_root).mkdir(parents=True, exist_ok=True)
        source_path = Path(video.storage_path or "")
        is_youtube = video.source_type == "youtube"
        temp_root = Path(tempfile.mkdtemp(prefix=f"rf-{video_id}-", dir=settings.media_root))
        try:
            if is_youtube:
                _stage(db, video, job, "downloading")
                source_path = temp_root / "source.mp4"
                options = {"format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]", "outtmpl": str(temp_root / "source.%(ext)s"), "merge_output_format": "mp4", "noplaylist": True, "no_warnings": True, "quiet": True, "extractor_args": {"youtube": {"player_client": ["android"]}}}
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(video.source_url, download=False)
                    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming", "was_live"}:
                        raise RuntimeError("Live streams and recorded livestreams are not supported.")
                    if info.get("availability") not in (None, "public") or int(info.get("age_limit") or 0) > 0:
                        raise RuntimeError("Private, age-restricted, or members-only YouTube videos are not supported.")
                    duration_seconds = float(info.get("duration") or 0)
                    if not 0 < duration_seconds <= settings.max_video_duration_seconds:
                        raise RuntimeError("The YouTube video duration is unavailable or exceeds the two-hour limit.")
                    info = ydl.extract_info(video.source_url, download=True)
                    source_path = Path(ydl.prepare_filename(info))
                    if not source_path.exists():
                        merged_path = temp_root / "source.mp4"
                        if merged_path.exists():
                            source_path = merged_path
                video.title = str(info.get("title") or video.title)[:500]
                video.thumbnail_url = info.get("thumbnail")
            if not source_path.is_file():
                raise RuntimeError("The source media file is missing.")
            _stage(db, video, job, "validating")
            metadata = probe_media(source_path)
            video.duration_ms = metadata["duration_ms"]

            _stage(db, video, job, "extracting_audio")
            has_audio = any(stream.get("codec_type") == "audio" for stream in metadata["streams"])
            audio_path = temp_root / "audio.wav"
            if has_audio:
                extract_audio(source_path, audio_path)

            _stage(db, video, job, "transcribing")
            words = transcribe_audio(str(audio_path)) if has_audio else []
            db.query(TranscriptSegment).filter_by(video_id=video_id).delete()
            db.query(EvidenceChunk).filter_by(video_id=video_id).delete()
            db.query(Chapter).filter_by(video_id=video_id).delete()
            db.query(Takeaway).filter_by(video_id=video_id).delete()
            segments = []
            for ordinal, item in enumerate(words):
                segment = TranscriptSegment(id=str(uuid.uuid4()), video_id=video_id, ordinal=ordinal, start_ms=item["start_ms"], end_ms=item["end_ms"], text=item["text"])
                db.add(segment)
                segments.append(segment)
            db.flush()
            evidence_rows = []
            for window in make_evidence_windows([{"id": s.id, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text} for s in segments]):
                row = EvidenceChunk(id=str(uuid.uuid4()), video_id=video_id, segment_id=window["segment_id"], kind="transcript", start_ms=window["start_ms"], end_ms=window["end_ms"], text=window["text"])
                db.add(row)
                evidence_rows.append(row)
            db.flush()
            if evidence_rows:
                vectors = embed_texts([row.text for row in evidence_rows])
                for row, vector in zip(evidence_rows, vectors, strict=True):
                    row.embedding = vector
            db.commit()

            _stage(db, video, job, "visual_analysis")
            client = OpenRouterClient()
            all_chapters, all_takeaways, all_visuals, all_concepts = [], [], [], []
            # Chunk the video into bounded five-minute requests and pass only source-backed IDs.
            for start_ms in range(0, video.duration_ms, 300_000):
                chunk_duration = min(300_000, video.duration_ms - start_ms)
                chunk_segments = [{"id": s.id, "start_ms": s.start_ms - start_ms, "text": s.text} for s in segments if start_ms <= s.start_ms < start_ms + chunk_duration]
                clip = temp_root / f"chunk-{start_ms}.mp4"
                make_video_chunk(source_path, clip, start_ms, chunk_duration)
                frame_prefix = f"{video_id}:{start_ms}"
                result = client.analyze_video_chunk(str(clip), chunk_segments, chunk_duration, frame_prefix=frame_prefix)
                allowed_segment_ids = {item["id"] for item in chunk_segments}
                for chapter in result.get("chapters", []):
                    if chapter.get("evidence_ids") and set(chapter["evidence_ids"]) <= allowed_segment_ids:
                        try:
                            local_start, local_end = int(chapter["start_ms"]), int(chapter["end_ms"])
                        except (KeyError, TypeError, ValueError):
                            continue
                        if 0 <= local_start < local_end <= chunk_duration:
                            all_chapters.append({**chapter, "start_ms": start_ms + local_start, "end_ms": start_ms + local_end})
                for takeaway in result.get("takeaways", []):
                    if takeaway.get("evidence_ids") and set(takeaway["evidence_ids"]) <= allowed_segment_ids:
                        all_takeaways.append(takeaway)
                for concept in result.get("concepts", []):
                    if concept.get("label") and concept.get("evidence_ids") and set(concept["evidence_ids"]) <= allowed_segment_ids:
                        all_concepts.append(concept)
                for note in result.get("visual_notes", []):
                    index = note.get("frame_index")
                    expected_frame_id = f"{frame_prefix}:{index}" if isinstance(index, int) else ""
                    if note.get("frame_id") == expected_frame_id and isinstance(index, int) and 0 <= index < (chunk_duration + 9_999) // 10_000:
                        all_visuals.append({"label": str(note.get("concept", ""))[:240], "description": str(note.get("description", ""))[:1500], "start_ms": start_ms + index * 10_000})
            _stage(db, video, job, "indexing")
            normalized = normalize_chapters(all_chapters, video.duration_ms)
            for ordinal, item in enumerate(normalized):
                db.add(Chapter(id=str(uuid.uuid4()), video_id=video_id, ordinal=ordinal, **item))
            for ordinal, item in enumerate(all_takeaways):
                if item["evidence_ids"]:
                    db.add(Takeaway(
                        id=str(uuid.uuid4()), video_id=video_id, ordinal=ordinal,
                        text=str(item.get("text", ""))[:2000],
                        evidence_ids=list(dict.fromkeys(item["evidence_ids"])),
                    ))
            concepts = []
            by_segment: dict[str, EvidenceChunk] = {}
            for row in evidence_rows:
                if row.segment_id:
                    by_segment.setdefault(row.segment_id, row)
            for item in all_concepts:
                for segment_id in dict.fromkeys(item["evidence_ids"]):
                    source = by_segment.get(segment_id)
                    label = str(item["label"]).strip()[:240]
                    if not source or not label:
                        continue
                    concept = Concept(
                        id=str(uuid.uuid4()), video_id=video_id, label=label,
                        description=str(item.get("description", ""))[:1500],
                        evidence_id=source.id, embedding=embed_texts([label])[0],
                    )
                    db.add(concept)
                    concepts.append(concept)
            for visual in all_visuals:
                if not visual["label"] or not visual["description"]:
                    continue
                evidence = EvidenceChunk(id=str(uuid.uuid4()), video_id=video_id, segment_id=None, kind="visual", start_ms=visual["start_ms"], end_ms=min(video.duration_ms, visual["start_ms"] + 10_000), text=visual["description"])
                db.add(evidence)
                db.flush()
                concept = Concept(id=str(uuid.uuid4()), video_id=video_id, label=visual["label"], description=visual["description"], evidence_id=evidence.id, embedding=embed_texts([visual["label"]])[0])
                db.add(concept)
                concepts.append(concept)
            db.flush()
            # A relation is stored only when both labels are grounded in the same source evidence.
            for index, left in enumerate(concepts):
                for right in concepts[index + 1:]:
                    if left.evidence_id == right.evidence_id:
                        db.add(ConceptLink(id=str(uuid.uuid4()), source_id=left.id, target_id=right.id, evidence_ids=[left.evidence_id], score=1.0))
            snapshot = transition(JobSnapshot(job.status, job.stage, job.retry_count), "ready")
            video.status, video.error_message = snapshot.stage, None
            job.status, job.stage, job.error_message = snapshot.status, snapshot.stage, None
            db.commit()
            return {"status": "ready", "video_id": video_id}
        except Exception as exc:
            db.rollback()
            video = db.get(Video, video_id)
            job = db.get(ProcessingJob, job.id)
            if video is None or job is None:
                return {"status": "deleted", "video_id": video_id}
            retryable = (isinstance(exc, ProviderError) and exc.retryable) or isinstance(exc, (subprocess.TimeoutExpired, yt_dlp.utils.DownloadError))
            if retryable and self.request.retries < self.max_retries:
                snapshot = retry_job(JobSnapshot(job.status, job.stage, job.retry_count))
                job.status, job.stage, job.retry_count = snapshot.status, snapshot.stage, self.request.retries + 1
                job.error_message = "A temporary provider error occurred; retry scheduled."
                video.status = "retrying"
                db.commit()
                raise self.retry(exc=exc, countdown=min(60, 2 ** (self.request.retries + 1)))
            logger.exception("Video processing failed for %s", video_id)
            snapshot = transition(JobSnapshot(job.status, job.stage, job.retry_count), "failed")
            if isinstance(exc, ProviderError) and "not configured" in str(exc).lower():
                message = "OpenRouter is not configured. Add OPENROUTER_API_KEY to .env, restart the stack, then retry this source."
            elif isinstance(exc, ProviderError) and "(402)" in str(exc):
                message = "OpenRouter returned HTTP 402. Check the account balance and API key credit limit, then retry. The source and completed local transcript remain stored on this device."
            elif isinstance(exc, yt_dlp.utils.DownloadError):
                message = "The YouTube source could not be downloaded. It may be unavailable or restricted; verify it is public, then retry."
            else:
                message = "Processing failed. Check local settings or retry the job."
            video.status, video.error_message = snapshot.stage, message
            job.status, job.stage, job.error_message = snapshot.status, snapshot.stage, message
            db.commit()
            return {"status": "failed", "video_id": video_id}
        finally:
            import shutil
            shutil.rmtree(temp_root, ignore_errors=True)
