"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  CircleAlert,
  Database,
  HardDrive,
  LockKeyhole,
  Radio,
  Server,
  ShieldCheck,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";

type SettingsStatus = {
  api: string;
  database: string;
  queue: string;
  model: string;
  openrouter_configured: boolean;
  whisper_model: string;
  embedding_model: string;
  max_upload_mb: number;
  max_video_duration_seconds: number;
};

export default function SettingsPage() {
  const [status, setStatus] = useState<SettingsStatus | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    void api<SettingsStatus>("/settings")
      .then(setStatus)
      .catch((cause: unknown) =>
        setError(
          cause instanceof Error ? cause.message : "Settings could not load.",
        ),
      );
  }, []);
  const item = (
    label: string,
    detail: string,
    value: string,
    Icon = Server,
  ) => (
    <div className="setting-row">
      <div>
        <strong>{label}</strong>
        <small>{detail}</small>
      </div>
      <span className="setting-value">
        <Icon size={12} /> &nbsp;{value}
      </span>
    </div>
  );
  return (
    <AppShell>
      <div className="page-wrap">
        <div className="page-heading">
          <div>
            <div className="eyebrow">LOCAL INSTANCE</div>
            <h1>Settings</h1>
            <p>
              Processing configuration and system health for this private
              workspace.
            </p>
          </div>
        </div>
        <div className="settings-grid">
          <nav className="settings-nav" aria-label="Settings sections">
            <a className="nav-link active" href="#system">
              <Server size={15} />
              <span>System status</span>
            </a>
            <a className="nav-link" href="#privacy">
              <LockKeyhole size={15} />
              <span>Privacy & data</span>
            </a>
            <a className="nav-link" href="#models">
              <Radio size={15} />
              <span>Processing models</span>
            </a>
          </nav>
          <div className="settings-section" id="system">
            <h2>System status</h2>
            <p>
              Services are private to this device. No analytics or external
              media hosting is enabled.
            </p>
            {error && <div className="error-box">{error}</div>}
            {status && (
              <>
                {item(
                  "API service",
                  "Receives local requests and stores source metadata",
                  status.api,
                  status.api === "ok" ? CheckCircle2 : CircleAlert,
                )}
                {item(
                  "Database",
                  "Transcript, evidence, and saved insight records",
                  status.database,
                  Database,
                )}
                {item(
                  "Job queue",
                  "Background processing state",
                  status.queue,
                  status.queue === "ok" ? CheckCircle2 : CircleAlert,
                )}
                {item(
                  "Media storage",
                  `${status.max_upload_mb} MB max · ${Math.round(status.max_video_duration_seconds / 60)} minute duration limit`,
                  "LOCAL VOLUME",
                  HardDrive,
                )}
              </>
            )}
            <h2 id="privacy" style={{ marginTop: 24 }}>
              Privacy & data
            </h2>
            <p>
              Uploaded media and derived data stay in the local Docker volume
              until you delete a video. YouTube working copies and temporary
              processing files are removed after analysis.
            </p>
            <div className="error-box" style={{ marginBottom: 12 }}>
              <b>
                External AI processing is enabled only after per-video consent.
              </b>{" "}
              Consented transcript context and compressed video chunks are sent
              to NVIDIA via OpenRouter. The configured free endpoint warns
              against personal/confidential media and says submissions may be
              logged to improve its services. Do not use it with sensitive
              recordings.
            </div>
            {item(
              "Network access",
              "App port binds to loopback only",
              "127.0.0.1",
              ShieldCheck,
            )}
            <h2 id="models" style={{ marginTop: 24 }}>
              Processing models
            </h2>
            <p>
              Local speech recognition and semantic indexing do not send your
              audio or transcript to a third-party service.
            </p>
            {status && (
              <>
                {item(
                  "Video understanding",
                  "OpenRouter model",
                  status.model,
                  Radio,
                )}
                {item(
                  "API key",
                  "Secret remains server-side; value is never returned",
                  status.openrouter_configured
                    ? "CONFIGURED"
                    : "NOT CONFIGURED",
                  status.openrouter_configured ? CheckCircle2 : CircleAlert,
                )}
                {item(
                  "Speech recognition",
                  "faster-whisper · local inference",
                  status.whisper_model,
                  Radio,
                )}
                {item(
                  "Semantic search",
                  "Sentence Transformers · local inference",
                  status.embedding_model,
                  Database,
                )}
              </>
            )}
            <p className="footer-note">
              To configure models, edit the local <code>.env</code> file and
              restart the stack. Never paste API keys into browser code.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
