from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), default="Untitled video")
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    youtube_id: Mapped[str | None] = mapped_column(String(20), unique=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    storage_path: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64), unique=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    takeaways: Mapped[list["Takeaway"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    evidence: Mapped[list["EvidenceChunk"]] = relationship(back_populates="video", cascade="all, delete-orphan")
    answers: Mapped[list["Answer"]] = relationship(back_populates="video", cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False)
    stage: Mapped[str] = mapped_column(String(80), default="queued", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)
    video: Mapped[Video] = relationship(back_populates="jobs")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    video: Mapped[Video] = relationship(back_populates="segments")
    __table_args__ = (UniqueConstraint("video_id", "ordinal", name="uq_segment_video_ordinal"),)


class EvidenceChunk(Base):
    __tablename__ = "evidence_chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    segment_id: Mapped[str | None] = mapped_column(ForeignKey("transcript_segments.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20), default="transcript", nullable=False)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    video: Mapped[Video] = relationship(back_populates="evidence")
    __table_args__ = (Index("ix_evidence_video_kind", "video_id", "kind"),)


class Chapter(Base):
    __tablename__ = "chapters"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    start_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    end_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    video: Mapped[Video] = relationship(back_populates="chapters")


class Takeaway(Base):
    __tablename__ = "takeaways"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    video: Mapped[Video] = relationship(back_populates="takeaways")


class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    grounded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    video: Mapped[Video] = relationship(back_populates="answers")
    citations: Mapped[list["AnswerCitation"]] = relationship(back_populates="answer", cascade="all, delete-orphan")


class AnswerCitation(Base):
    __tablename__ = "answer_citations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    answer_id: Mapped[str] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_chunks.id", ondelete="CASCADE"), index=True)
    answer: Mapped[Answer] = relationship(back_populates="citations")


class SavedInsight(Base):
    __tablename__ = "saved_insights"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    segment_id: Mapped[str | None] = mapped_column(String(36))
    start_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)


class Concept(Base):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_chunks.id", ondelete="CASCADE"), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))


class ConceptLink(Base):
    __tablename__ = "concept_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
