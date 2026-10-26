"""Initial RecallFrame source, transcript, evidence, and insight schema."""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("videos",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False), sa.Column("source_url", sa.Text()),
        sa.Column("youtube_id", sa.String(20), unique=True), sa.Column("thumbnail_url", sa.Text()),
        sa.Column("storage_path", sa.Text()), sa.Column("sha256", sa.String(64), unique=True),
        sa.Column("duration_ms", sa.Integer()), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text()), sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("processing_jobs",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("stage", sa.String(80), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False), sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_processing_jobs_video_id", "processing_jobs", ["video_id"])
    op.create_table("transcript_segments",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False), sa.Column("text", sa.Text(), nullable=False),
        sa.UniqueConstraint("video_id", "ordinal", name="uq_segment_video_ordinal"))
    op.create_index("ix_transcript_segments_video_id", "transcript_segments", ["video_id"])
    op.create_table("evidence_chunks",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("segment_id", sa.String(36), sa.ForeignKey("transcript_segments.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(20), nullable=False), sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("embedding", Vector(384)))
    op.create_index("ix_evidence_chunks_video_id", "evidence_chunks", ["video_id"])
    op.create_index("ix_evidence_chunks_segment_id", "evidence_chunks", ["segment_id"])
    op.create_index("ix_evidence_video_kind", "evidence_chunks", ["video_id", "kind"])
    op.execute("CREATE INDEX ix_evidence_text_search ON evidence_chunks USING GIN (to_tsvector('simple', text))")
    op.create_table("chapters",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("title", sa.String(240), nullable=False), sa.Column("summary", sa.Text()),
        sa.Column("start_ms", sa.Integer(), nullable=False), sa.Column("end_ms", sa.Integer(), nullable=False))
    op.create_index("ix_chapters_video_id", "chapters", ["video_id"])
    op.create_table("takeaways",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False))
    op.create_index("ix_takeaways_video_id", "takeaways", ["video_id"])
    op.create_table("answers",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False), sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("grounded", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_answers_video_id", "answers", ["video_id"])
    op.create_table("answer_citations",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("answer_id", sa.String(36), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", sa.String(36), sa.ForeignKey("evidence_chunks.id", ondelete="CASCADE"), nullable=False))
    op.create_index("ix_answer_citations_answer_id", "answer_citations", ["answer_id"])
    op.create_index("ix_answer_citations_evidence_id", "answer_citations", ["evidence_id"])
    op.create_table("saved_insights",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False), sa.Column("segment_id", sa.String(36)), sa.Column("start_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_saved_insights_video_id", "saved_insights", ["video_id"])
    op.create_table("concepts",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(240), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("evidence_id", sa.String(36), sa.ForeignKey("evidence_chunks.id", ondelete="CASCADE"), nullable=False), sa.Column("embedding", Vector(384)))
    op.create_index("ix_concepts_video_id", "concepts", ["video_id"])
    op.create_index("ix_concepts_evidence_id", "concepts", ["evidence_id"])
    op.create_table("concept_links",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("source_id", sa.String(36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_id", sa.String(36), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False), sa.Column("score", sa.Float(), nullable=False))
    op.create_index("ix_concept_links_source_id", "concept_links", ["source_id"])
    op.create_index("ix_concept_links_target_id", "concept_links", ["target_id"])


def downgrade() -> None:
    op.drop_table("concept_links")
    op.drop_table("concepts")
    op.drop_table("saved_insights")
    op.drop_table("answer_citations")
    op.drop_table("answers")
    op.drop_table("takeaways")
    op.drop_table("chapters")
    op.drop_table("evidence_chunks")
    op.drop_table("transcript_segments")
    op.drop_table("processing_jobs")
    op.drop_table("videos")
