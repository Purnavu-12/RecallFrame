export type JobStage =
  | "queued"
  | "validating"
  | "downloading"
  | "extracting_audio"
  | "transcribing"
  | "visual_analysis"
  | "indexing"
  | "retrying"
  | "ready"
  | "failed";

export type TranscriptSegment = {
  id: string;
  start_ms: number;
  end_ms: number;
  text: string;
};

export type Chapter = {
  id: string;
  title: string;
  start_ms: number;
  end_ms: number;
  summary?: string | null;
};

export type Takeaway = {
  id: string;
  text: string;
  evidence_ids: string[];
};

export type EvidenceCitation = {
  id: string;
  segment_id: string;
  start_ms: number;
  end_ms: number;
  excerpt: string;
  kind: "transcript" | "visual";
};

export type Answer = {
  id: string;
  question: string;
  answer: string;
  grounded: boolean;
  citations: EvidenceCitation[];
  created_at: string;
};

export type ProcessingJob = {
  id: string;
  status: "queued" | "processing" | "retrying" | "completed" | "failed";
  stage: string;
  error_message?: string | null;
  retry_count: number;
};

export type Video = {
  id: string;
  title: string;
  source_type: "upload" | "youtube";
  source_url?: string | null;
  youtube_id?: string | null;
  duration_ms?: number | null;
  thumbnail_url?: string | null;
  status: JobStage;
  error_message?: string | null;
  created_at: string;
  chapters: Chapter[];
  segments: TranscriptSegment[];
  takeaways: Takeaway[];
  answers: Answer[];
};

export type SearchResult = {
  video_id: string;
  video_title: string;
  segment_id: string;
  start_ms: number;
  end_ms: number;
  excerpt: string;
  score: number;
};

export type SavedInsight = {
  id: string;
  video_id: string;
  video_title: string;
  text: string;
  segment_id?: string | null;
  start_ms?: number | null;
  created_at: string;
};

export type KnowledgeConcept = {
  id: string;
  label: string;
  video_id: string;
  video_title: string;
  segment_id: string;
  start_ms: number;
  end_ms: number;
  description?: string | null;
};

export type ApiError = { detail?: string; message?: string };
