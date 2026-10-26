"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  BookmarkPlus,
  Check,
  ChevronDown,
  CircleAlert,
  Clock3,
  FileVideo2,
  Lightbulb,
  LoaderCircle,
  MoreHorizontal,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api, formatTime, seekVideo } from "@/lib/api";
import type { Answer, SavedInsight, Video } from "@/lib/types";

const stageCopy: Record<string, string> = {
  queued: "Waiting for a worker",
  validating: "Checking the media file",
  downloading: "Preparing the public source",
  extracting_audio: "Preparing audio locally",
  transcribing: "Transcribing speech locally",
  visual_analysis: "Analyzing video evidence with Nemotron",
  indexing: "Building chapters and search index",
  retrying: "Retrying a temporary processing step",
};

export default function VideoWorkspacePage() {
  const params = useParams<{ id: string }>();
  const videoId = params.id;
  const router = useRouter();
  const [video, setVideo] = useState<Video | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState("");
  const [tab, setTab] = useState<"overview" | "transcript" | "chapters">(
    "transcript",
  );
  const [transcriptQuery, setTranscriptQuery] = useState("");
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");
  const [activeSegment, setActiveSegment] = useState<string | null>(null);
  const [saved, setSaved] = useState<string[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);
  const youtubeRef = useRef<HTMLIFrameElement>(null);

  const loadVideo = useCallback(async () => {
    try {
      const data = await api<Video>(`/videos/${videoId}`);
      setVideo(data);
      setApiError("");
      return data.status;
    } catch (cause) {
      setApiError(
        cause instanceof Error ? cause.message : "Could not load this video.",
      );
      return null;
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    let active = true;
    const poll = async () => {
      const status = await loadVideo();
      if (active && status && status !== "ready" && status !== "failed")
        timer = setTimeout(poll, 2500);
    };
    void poll();
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [loadVideo]);

  useEffect(() => {
    function onSeek(event: Event) {
      const detail = (
        event as CustomEvent<{ videoId: string; milliseconds: number }>
      ).detail;
      if (detail.videoId !== videoId) return;
      setActiveSegment(
        video?.segments.find(
          (segment) =>
            detail.milliseconds >= segment.start_ms &&
            detail.milliseconds <= segment.end_ms,
        )?.id ?? null,
      );
      if (
        video?.source_type === "youtube" &&
        youtubeRef.current?.contentWindow
      ) {
        youtubeRef.current.contentWindow.postMessage(
          JSON.stringify({
            event: "command",
            func: "seekTo",
            args: [detail.milliseconds / 1000, true],
          }),
          "https://www.youtube.com",
        );
      } else if (videoRef.current) {
        videoRef.current.currentTime = detail.milliseconds / 1000;
        void videoRef.current.play().catch(() => undefined);
      }
    }
    window.addEventListener("recallframe:seek", onSeek);
    return () => window.removeEventListener("recallframe:seek", onSeek);
  }, [video, videoId]);

  useEffect(() => {
    if (!video) return;
    const savedTarget = sessionStorage.getItem("recallframe:seek-on-open");
    if (!savedTarget) return;
    sessionStorage.removeItem("recallframe:seek-on-open");
    try {
      const target = JSON.parse(savedTarget) as {
        videoId: string;
        milliseconds: number;
      };
      if (
        target.videoId === videoId &&
        Number.isFinite(target.milliseconds) &&
        target.milliseconds >= 0
      ) {
        window.setTimeout(() => seekVideo(videoId, target.milliseconds), 0);
      }
    } catch {
      // Ignore malformed in-browser navigation state.
    }
  }, [video, videoId]);

  const segments = useMemo(() => video?.segments ?? [], [video?.segments]);
  const chapters = video?.chapters ?? [];
  const filteredSegments = useMemo(
    () =>
      segments.filter((segment) =>
        segment.text.toLowerCase().includes(transcriptQuery.toLowerCase()),
      ),
    [segments, transcriptQuery],
  );

  async function submitQuestion(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = question.trim();
    if (!value || asking) return;
    setAsking(true);
    setAskError("");
    try {
      const answer = await api<Answer>(`/videos/${videoId}/questions`, {
        method: "POST",
        body: JSON.stringify({ question: value }),
      });
      setVideo((current) =>
        current
          ? { ...current, answers: [answer, ...current.answers] }
          : current,
      );
      setQuestion("");
    } catch (cause) {
      setAskError(
        cause instanceof Error
          ? cause.message
          : "The question could not be answered.",
      );
    } finally {
      setAsking(false);
    }
  }

  async function saveInsight(
    text: string,
    segmentId?: string,
    startMs?: number,
    savedKey?: string,
  ) {
    try {
      const insight = await api<SavedInsight>("/insights", {
        method: "POST",
        body: JSON.stringify({
          video_id: videoId,
          text,
          segment_id: segmentId || undefined,
          start_ms: startMs,
        }),
      });
      setSaved((current) => [...current, savedKey ?? insight.id]);
    } catch (cause) {
      setAskError(
        cause instanceof Error ? cause.message : "Could not save this insight.",
      );
    }
  }

  async function deleteVideo() {
    if (
      !window.confirm(
        "Delete this video and all of its transcripts, answers, indexes, and derived evidence? This cannot be undone.",
      )
    )
      return;
    try {
      await api(`/videos/${videoId}`, { method: "DELETE" });
      router.push("/");
    } catch (cause) {
      setApiError(
        cause instanceof Error ? cause.message : "Could not delete the video.",
      );
    }
  }

  async function retryVideo() {
    try {
      await api(`/videos/${videoId}/retry`, { method: "POST" });
      setApiError("");
      await loadVideo();
    } catch (cause) {
      setApiError(
        cause instanceof Error
          ? cause.message
          : "The source could not be retried.",
      );
    }
  }

  function jumpTo(milliseconds: number, segmentId?: string) {
    setActiveSegment(segmentId ?? null);
    seekVideo(videoId, milliseconds);
  }

  const isProcessing =
    video && video.status !== "ready" && video.status !== "failed";
  return (
    <AppShell>
      {loading ? (
        <div className="page-wrap">
          <div
            className="skeleton"
            style={{ width: 270, height: 24, marginBottom: 20 }}
          />
          <div
            className="skeleton"
            style={{ width: "100%", aspectRatio: "16 / 9" }}
          />
        </div>
      ) : apiError && !video ? (
        <div className="page-wrap">
          <Link href="/" className="eyebrow">
            ← BACK TO LIBRARY
          </Link>
          <h1>Video unavailable</h1>
          <div className="error-box">{apiError}</div>
        </div>
      ) : video ? (
        <div className="workspace-grid">
          <section className="workspace-main">
            <div className="workspace-content">
              <div className="video-heading">
                <div>
                  <div className="eyebrow">SOURCE WORKSPACE</div>
                  <h1>{video.title}</h1>
                  <p>
                    <span className="source-chip">
                      {video.source_type === "youtube"
                        ? "YOUTUBE"
                        : "LOCAL VIDEO"}
                    </span>
                    {video.duration_ms ? (
                      <>
                        <span>·</span>
                        <Clock3 size={12} /> {formatTime(video.duration_ms)}
                      </>
                    ) : null}
                    <span>·</span>
                    {video.status === "ready" ? (
                      <span className="status-ready">Indexed</span>
                    ) : video.status === "failed" ? (
                      <span className="status-error">Needs attention</span>
                    ) : (
                      <span className="status-running">Processing</span>
                    )}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 4 }}>
                  <button
                    className="icon-button"
                    aria-label="Delete video"
                    onClick={deleteVideo}
                  >
                    <Trash2 size={16} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label="More video actions"
                    title="More actions"
                  >
                    <MoreHorizontal size={17} />
                  </button>
                </div>
              </div>

              <div className="player-shell">
                {video.source_type === "youtube" && video.youtube_id ? (
                  <iframe
                    ref={youtubeRef}
                    title={`YouTube video: ${video.title}`}
                    src={`https://www.youtube.com/embed/${encodeURIComponent(video.youtube_id)}?enablejsapi=1&origin=${encodeURIComponent(typeof window !== "undefined" ? window.location.origin : "http://localhost:3000")}`}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowFullScreen
                  />
                ) : video.status === "ready" ? (
                  <video
                    ref={videoRef}
                    controls
                    preload="metadata"
                    src={`/api/videos/${video.id}/stream`}
                    aria-label={`Video player for ${video.title}`}
                  />
                ) : (
                  <div className="player-placeholder">
                    <div className="player-placeholder-inner">
                      <FileVideo2 size={32} />
                      <span>
                        Video preview becomes available when processing is ready
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {chapters.length > 0 && (
                <div className="chapter-strip" aria-label="Video chapters">
                  {chapters.map((chapter, index) => (
                    <button
                      key={chapter.id}
                      className="chapter-segment"
                      style={
                        {
                          "--segment-color": [
                            "#a78bfa",
                            "#7ba8ff",
                            "#68d5b2",
                            "#e9b86a",
                          ][index % 4],
                        } as React.CSSProperties
                      }
                      onClick={() => jumpTo(chapter.start_ms)}
                      title={`${chapter.title} · ${formatTime(chapter.start_ms)}`}
                    >
                      <b>{chapter.title}</b>
                      <span>
                        {formatTime(chapter.start_ms)} –{" "}
                        {formatTime(chapter.end_ms)}
                      </span>
                    </button>
                  ))}
                </div>
              )}

              <div className="tabs" role="tablist" aria-label="Video content">
                {(["overview", "transcript", "chapters"] as const).map(
                  (name) => (
                    <button
                      key={name}
                      className={`tab${tab === name ? " active" : ""}`}
                      role="tab"
                      aria-selected={tab === name}
                      onClick={() => setTab(name)}
                    >
                      {name[0].toUpperCase() + name.slice(1)}
                    </button>
                  ),
                )}
                {tab === "transcript" && (
                  <label
                    className="search-field"
                    style={{ height: 29, marginLeft: "auto", maxWidth: 210 }}
                  >
                    <SearchIcon />
                    <input
                      aria-label="Search transcript"
                      placeholder="Find in transcript…"
                      value={transcriptQuery}
                      onChange={(event) =>
                        setTranscriptQuery(event.target.value)
                      }
                    />
                  </label>
                )}
              </div>

              {tab === "transcript" && (
                <div className="transcript-list">
                  {filteredSegments.length ? (
                    filteredSegments.map((segment) => (
                      <article
                        id={`segment-${segment.id}`}
                        className={`transcript-row${activeSegment === segment.id ? " current" : ""}`}
                        key={segment.id}
                      >
                        <button
                          className="timestamp-button"
                          onClick={() => jumpTo(segment.start_ms, segment.id)}
                        >
                          {formatTime(segment.start_ms)}
                        </button>
                        <p>{segment.text}</p>
                      </article>
                    ))
                  ) : (
                    <div className="answer-empty">
                      {segments.length
                        ? "No transcript lines match that search."
                        : isProcessing
                          ? "Transcript segments will appear here after local transcription."
                          : "No transcript was produced for this source."}
                    </div>
                  )}
                </div>
              )}
              {tab === "chapters" && (
                <div className="transcript-list">
                  {chapters.length ? (
                    chapters.map((chapter) => (
                      <article className="transcript-row" key={chapter.id}>
                        <button
                          className="timestamp-button"
                          onClick={() => jumpTo(chapter.start_ms)}
                        >
                          {formatTime(chapter.start_ms)}
                        </button>
                        <div>
                          <p style={{ color: "var(--text)", marginBottom: 4 }}>
                            {chapter.title}
                          </p>
                          <p>
                            {chapter.summary ||
                              "Chapter from the source video."}
                          </p>
                        </div>
                      </article>
                    ))
                  ) : (
                    <div className="answer-empty">
                      Chapters will be generated from this video’s transcript
                      and visual evidence.
                    </div>
                  )}
                </div>
              )}
              {tab === "overview" && (
                <div className="takeaway-list">
                  {video.takeaways.length ? (
                    video.takeaways.map((takeaway) => (
                      <article className="takeaway-row" key={takeaway.id}>
                        <span className="source-chip">IDEA</span>
                        <div>
                          <p>{takeaway.text}</p>
                          <button
                            className="insight-save"
                            onClick={() => void saveInsight(takeaway.text)}
                          >
                            <BookmarkPlus size={12} /> Save insight
                          </button>
                        </div>
                      </article>
                    ))
                  ) : (
                    <div className="answer-empty">
                      Key takeaways will appear here after this source is
                      indexed.
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          <aside className="answer-panel" aria-label="Ask this video">
            <div className="answer-header">
              <h2>
                <Sparkles size={16} /> Ask this video
              </h2>
              <span className="source-chip">
                {video.status === "ready" ? "EVIDENCE ONLY" : "INDEXING"}
              </span>
            </div>
            <p className="answer-intro">
              Answers cite passages from this video. If the source does not
              contain the answer, RecallFrame will say so.
            </p>
            {askError && (
              <div
                role="alert"
                className="error-box"
                style={{ marginBottom: 10 }}
              >
                {askError}
              </div>
            )}
            <form className="question-form" onSubmit={submitQuestion}>
              <textarea
                aria-label="Ask a question about this video"
                placeholder="Ask about an idea, explanation, or demonstration…"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                disabled={video.status !== "ready" || asking}
              />
              <button
                className="send-button"
                aria-label="Ask question"
                disabled={
                  !question.trim() || asking || video.status !== "ready"
                }
              >
                {asking ? (
                  <LoaderCircle size={15} className="spin-icon" />
                ) : (
                  <ArrowIcon />
                )}
              </button>
            </form>
            <div className="answer-scroll">
              {isProcessing && (
                <div className="processing-card">
                  <h2>Building your source index</h2>
                  <p>
                    Progress updates reflect the worker’s current task; no
                    percentage is estimated.
                  </p>
                  <div className="processing-stage">
                    <span className="spinner" />
                    {stageCopy[video.status] ?? "Processing the source"}
                  </div>
                  <div className="progress-track">
                    <i />
                  </div>
                </div>
              )}
              {video.status === "failed" && (
                <div className="error-box">
                  {video.error_message ||
                    (video.answers.length
                      ? "The processing job failed. Existing indexed evidence remains available."
                      : "This source could not be indexed.")}{" "}
                  <button
                    className="button button-quiet"
                    style={{ marginTop: 8 }}
                    onClick={() => void retryVideo()}
                  >
                    Retry processing
                  </button>
                </div>
              )}
              {!isProcessing &&
                video.answers.length === 0 &&
                video.status === "ready" && (
                  <div className="answer-empty">
                    Try a question that points to a specific explanation. Each
                    answer includes the transcript passage and exact time it
                    came from.
                  </div>
                )}
              {[...video.answers].reverse().map((answer) => (
                <article className="answer-card" key={answer.id}>
                  <p className="answer-question">{answer.question}</p>
                  <p className="answer-text">{answer.answer}</p>
                  {answer.citations.length > 0 && (
                    <>
                      <div className="evidence-label">Source evidence</div>
                      {answer.citations.map((citation) => (
                        <div className="evidence-card" key={citation.id}>
                          <p className="evidence-quote">“{citation.excerpt}”</p>
                          <div className="evidence-actions">
                            <button
                              className="evidence-chip"
                              onClick={() =>
                                jumpTo(citation.start_ms, citation.segment_id)
                              }
                            >
                              {formatTime(citation.start_ms)}
                            </button>
                            {citation.end_ms !== citation.start_ms && (
                              <button
                                className="evidence-chip"
                                onClick={() =>
                                  jumpTo(citation.end_ms, citation.segment_id)
                                }
                              >
                                {formatTime(citation.end_ms)}
                              </button>
                            )}
                            <button
                              className="insight-save"
                              onClick={() =>
                                void saveInsight(
                                  answer.answer,
                                  citation.segment_id,
                                  citation.start_ms,
                                  citation.id,
                                )
                              }
                            >
                              {saved.includes(citation.id) ? (
                                <Check size={12} />
                              ) : (
                                <BookmarkPlus size={12} />
                              )}{" "}
                              {saved.includes(citation.id)
                                ? "Saved"
                                : "Save insight"}
                            </button>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                  <div className="verified">
                    {answer.grounded ? (
                      <>
                        <ShieldCheck size={13} /> Evidence references verified
                      </>
                    ) : (
                      <>
                        <CircleAlert size={13} /> Insufficient source evidence
                      </>
                    )}
                  </div>
                </article>
              ))}
            </div>
            <div className="side-section-title">
              <Lightbulb size={14} /> Key takeaways{" "}
              <span className="source-chip" style={{ marginLeft: "auto" }}>
                {video.takeaways.length}
              </span>
            </div>
            <div className="takeaway-list">
              {video.takeaways.slice(0, 3).map((takeaway, index) => {
                const segment = segments.find((item) =>
                  takeaway.evidence_ids.includes(item.id),
                );
                return (
                  <article className="takeaway-row" key={takeaway.id}>
                    <button
                      className="timestamp-button"
                      onClick={() =>
                        segment && jumpTo(segment.start_ms, segment.id)
                      }
                    >
                      {segment
                        ? formatTime(segment.start_ms)
                        : String(index + 1).padStart(2, "0")}
                    </button>
                    <p>{takeaway.text}</p>
                  </article>
                );
              })}
              {video.takeaways.length === 0 && (
                <p className="footer-note">
                  Takeaways appear once the video is indexed.
                </p>
              )}
            </div>
          </aside>
        </div>
      ) : null}
    </AppShell>
  );
}

function SearchIcon() {
  return <Search size={13} />;
}
function ArrowIcon() {
  return <ChevronDown size={15} style={{ transform: "rotate(-90deg)" }} />;
}
