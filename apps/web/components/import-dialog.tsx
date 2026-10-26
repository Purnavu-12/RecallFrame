"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileVideo2, Link2, LoaderCircle, Upload, X } from "lucide-react";
import { api } from "@/lib/api";

type ImportResponse = {
  video_id: string;
  job_id: string;
  deduplicated?: boolean;
};

export function ImportDialog({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<"upload" | "youtube">("upload");
  const [url, setUrl] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState("");

  function openVideo(result: ImportResponse) {
    router.push(`/videos/${result.video_id}`);
  }

  function uploadFile(file: File) {
    setError("");
    if (!consent) {
      setError("Confirm the AI data handling notice before analysis.");
      return;
    }
    setBusy(true);
    setProgress(0);
    const form = new FormData();
    form.set("file", file);
    form.set("consent", "true");
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/videos/upload");
    xhr.responseType = "json";
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable)
        setProgress(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onload = () => {
      setBusy(false);
      if (xhr.status >= 200 && xhr.status < 300 && xhr.response?.video_id)
        openVideo(xhr.response as ImportResponse);
      else setError(xhr.response?.detail ?? `Upload failed (${xhr.status}).`);
    };
    xhr.onerror = () => {
      setBusy(false);
      setError("Upload could not reach the local RecallFrame API.");
    };
    xhr.send(form);
  }

  async function importUrl() {
    setError("");
    if (!consent) {
      setError("Confirm the AI data handling notice before analysis.");
      return;
    }
    if (!url.trim()) {
      setError("Paste a public YouTube video URL to continue.");
      return;
    }
    setBusy(true);
    try {
      const response = await api<ImportResponse>("/videos/import", {
        method: "POST",
        body: JSON.stringify({ url: url.trim(), consent }),
      });
      openVideo(response);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The video could not be imported.",
      );
      setBusy(false);
    }
  }

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-title"
      >
        <div className="modal-head">
          <div>
            <h2 id="import-title">Add a source video</h2>
            <p>RecallFrame will build a searchable, timestamped workspace.</p>
          </div>
          <button
            className="icon-button"
            aria-label="Close import dialog"
            onClick={onClose}
            disabled={busy}
          >
            <X size={16} />
          </button>
        </div>
        <div className="modal-body">
          <div
            className="import-tabs"
            role="tablist"
            aria-label="Import source"
          >
            <button
              className={`import-tab${mode === "upload" ? " active" : ""}`}
              role="tab"
              aria-selected={mode === "upload"}
              onClick={() => setMode("upload")}
            >
              <Upload size={13} /> &nbsp;Upload
            </button>
            <button
              className={`import-tab${mode === "youtube" ? " active" : ""}`}
              role="tab"
              aria-selected={mode === "youtube"}
              onClick={() => setMode("youtube")}
            >
              <Link2 size={13} /> &nbsp;YouTube URL
            </button>
          </div>
          {mode === "upload" ? (
            <>
              <label className="field-label" htmlFor="video-file">
                Video file
              </label>
              <input
                ref={fileRef}
                id="video-file"
                type="file"
                accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
                hidden
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) uploadFile(file);
                }}
              />
              <button
                className="dropzone"
                type="button"
                onClick={() => fileRef.current?.click()}
                disabled={busy}
              >
                {busy ? (
                  <LoaderCircle size={20} className="spin-icon" />
                ) : (
                  <FileVideo2 size={22} />
                )}
                <span>
                  <strong>
                    {busy
                      ? "Uploading source video"
                      : "Choose a video from this device"}
                  </strong>
                  <small>MP4, MOV, or WebM · up to 1 GB and 2 hours</small>
                </span>
              </button>
            </>
          ) : (
            <>
              <label className="field-label" htmlFor="youtube-url">
                Public YouTube video
              </label>
              <input
                id="youtube-url"
                className="text-input"
                inputMode="url"
                placeholder="https://www.youtube.com/watch?v=…"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                disabled={busy}
              />
              <p className="footer-note">
                Single public videos only. Playlists, live streams, and
                restricted videos are not supported.
              </p>
            </>
          )}
          <label className="consent-box">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
              disabled={busy}
            />
            <p>
              <b>External AI processing — please read.</b> Timestamped
              transcript excerpts and compressed video chunks will be sent to
              NVIDIA through OpenRouter’s free Nemotron endpoint. The endpoint
              warns against confidential or personal data, including people’s
              voices and faces, and says submissions may be logged to improve
              its services. Do not import sensitive media. I understand and
              consent for this video.
            </p>
          </label>
          {progress !== null && (
            <p className="upload-progress" aria-live="polite">
              {progress < 100
                ? `Uploading ${progress}%`
                : "Upload received · starting processing"}
            </p>
          )}
          {error && (
            <p className="error-box" role="alert">
              {error}
            </p>
          )}
          <div className="modal-actions">
            <button
              className="button button-quiet"
              onClick={onClose}
              disabled={busy}
            >
              Cancel
            </button>
            {mode === "youtube" && (
              <button
                className="button button-primary"
                onClick={importUrl}
                disabled={busy || !consent}
              >
                {busy ? (
                  <>
                    <LoaderCircle size={14} className="spin-icon" /> Checking
                    source…
                  </>
                ) : (
                  <>
                    Import video <Link2 size={14} />
                  </>
                )}
              </button>
            )}
          </div>
          {mode === "upload" && busy && (
            <span className="sr-only" aria-live="polite">
              Upload in progress
            </span>
          )}
        </div>
      </section>
    </div>
  );
}
