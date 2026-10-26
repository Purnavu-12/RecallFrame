from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SegmentRead(ORMModel):
    id: str
    start_ms: int
    end_ms: int
    text: str


class ChapterRead(ORMModel):
    id: str
    title: str
    summary: str | None
    start_ms: int
    end_ms: int


class TakeawayRead(ORMModel):
    id: str
    text: str
    evidence_ids: list[str]


class CitationRead(BaseModel):
    id: str
    segment_id: str
    start_ms: int
    end_ms: int
    excerpt: str
    kind: Literal["transcript", "visual"]


class AnswerRead(BaseModel):
    id: str
    question: str
    answer: str
    grounded: bool
    citations: list[CitationRead]
    created_at: datetime


class VideoRead(ORMModel):
    id: str
    title: str
    source_type: Literal["upload", "youtube"]
    source_url: str | None
    youtube_id: str | None
    duration_ms: int | None
    thumbnail_url: str | None
    status: str
    error_message: str | None = None
    created_at: datetime
    chapters: list[ChapterRead] = Field(default_factory=list)
    segments: list[SegmentRead] = Field(default_factory=list)
    takeaways: list[TakeawayRead] = Field(default_factory=list)
    answers: list[AnswerRead] = Field(default_factory=list)


class VideoListItem(ORMModel):
    id: str
    title: str
    source_type: Literal["upload", "youtube"]
    source_url: str | None
    youtube_id: str | None
    duration_ms: int | None
    thumbnail_url: str | None
    status: str
    created_at: datetime


class ImportResponse(BaseModel):
    video_id: str
    job_id: str
    deduplicated: bool = False


class YouTubeImportRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    consent: bool


class QuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class InsightCreate(BaseModel):
    video_id: str
    text: str = Field(min_length=1, max_length=5000)
    segment_id: str | None = None
    start_ms: int | None = Field(default=None, ge=0)


class InsightRead(BaseModel):
    id: str
    video_id: str
    video_title: str
    text: str
    segment_id: str | None
    start_ms: int | None
    created_at: datetime


class SearchResultRead(BaseModel):
    video_id: str
    video_title: str
    segment_id: str
    start_ms: int
    end_ms: int
    excerpt: str
    score: float


class ConceptRead(BaseModel):
    id: str
    label: str
    video_id: str
    video_title: str
    segment_id: str
    start_ms: int
    end_ms: int
    description: str | None


class ConceptLinkRead(BaseModel):
    source_id: str
    target_id: str
    evidence_ids: list[str]
    score: float


class KnowledgeMapRead(BaseModel):
    nodes: list[ConceptRead]
    edges: list[ConceptLinkRead]
