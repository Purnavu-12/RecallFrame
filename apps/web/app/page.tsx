"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  FileVideo2,
  FolderOpen,
  Plus,
  Search,
} from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { ImportDialog } from "@/components/import-dialog";
import { api, formatTime } from "@/lib/api";
import type { Video } from "@/lib/types";

export default function LibraryPage() {
  const router = useRouter();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiUnavailable, setApiUnavailable] = useState(false);
  const [search, setSearch] = useState("");
  const [importOpen, setImportOpen] = useState(false);

  useEffect(() => {
    let active = true;
    api<Video[]>("/videos")
      .then((data) => {
        if (active) {
          setVideos(data);
          setApiUnavailable(false);
        }
      })
      .catch(() => {
        if (active) setApiUnavailable(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const filtered = videos.filter((video) =>
    video.title.toLowerCase().includes(search.toLowerCase()),
  );
  const ready = videos.filter((video) => video.status === "ready").length;

  return (
    <AppShell>
      <div className="page-wrap">
        <div className="page-heading">
          <div>
            <div className="eyebrow">PERSONAL VIDEO INDEX</div>
            <h1>Your library</h1>
            <p>
              Find the exact idea, then return to the moment it was explained.
            </p>
          </div>
          <button
            className="button button-primary"
            onClick={() => setImportOpen(true)}
          >
            <Plus size={15} /> Add a video
          </button>
        </div>

        {apiUnavailable && (
          <div className="error-box" role="status">
            The local API is not responding. Start the stack with{" "}
            <code>docker compose up --build</code> and refresh this page.
          </div>
        )}

        <div className="library-controls" style={{ marginTop: 22 }}>
          <label className="search-field">
            <Search size={15} />
            <input
              aria-label="Search your videos"
              placeholder="Search titles in your library…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <Link className="button" href="/search">
            <Search size={14} /> Search knowledge
          </Link>
          <Link className="button demo-link" href="/demo">
            <FileVideo2 size={14} /> Try preprocessed demo
          </Link>
        </div>
        <div className="library-statline" aria-label="Library status">
          <span>
            <FolderOpen size={13} /> <b>{videos.length}</b> sources
          </span>
          <span>
            <CheckCircle2 size={13} className="status-ready" /> <b>{ready}</b>{" "}
            indexed
          </span>
          <span>
            <Activity size={13} /> private on this device
          </span>
        </div>

        {loading ? (
          <div className="video-list" aria-label="Loading library">
            {[0, 1, 2].map((key) => (
              <div className="video-row" key={key}>
                <div className="video-thumb skeleton" />
                <div>
                  <div
                    className="skeleton"
                    style={{ width: "45%", height: 14, marginBottom: 10 }}
                  />
                  <div
                    className="skeleton"
                    style={{ width: "30%", height: 10 }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <div className="video-list">
            {filtered.map((video) => (
              <Link
                className="video-row"
                href={`/videos/${video.id}`}
                key={video.id}
              >
                <div className="video-thumb">
                  {video.thumbnail_url ? (
                    <Image
                      src={video.thumbnail_url}
                      alt=""
                      width={200}
                      height={112}
                      unoptimized
                    />
                  ) : (
                    <FileVideo2 size={25} color="#a78bfa" />
                  )}
                  <span className="thumb-play">
                    <ArrowUpRight size={14} />
                  </span>
                  {video.duration_ms ? (
                    <span className="duration">
                      {formatTime(video.duration_ms)}
                    </span>
                  ) : null}
                </div>
                <div className="video-meta">
                  <h3>{video.title}</h3>
                  <p>
                    <span>
                      {video.source_type === "youtube"
                        ? "YouTube"
                        : "Local upload"}
                    </span>
                    <span className="meta-dot">·</span>
                    <span>
                      {new Date(video.created_at).toLocaleDateString()}
                    </span>
                    <span className="meta-dot">·</span>
                    <span
                      className={
                        video.status === "ready"
                          ? "status-ready"
                          : video.status === "failed"
                            ? "status-error"
                            : "status-running"
                      }
                    >
                      {video.status === "ready"
                        ? "Indexed"
                        : video.status === "failed"
                          ? "Needs attention"
                          : "Processing"}
                    </span>
                  </p>
                </div>
                <div className="video-actions">
                  <span className="icon-button video-open" aria-hidden="true">
                    <ArrowUpRight size={16} />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : search ? (
          <div className="empty-library">
            <div className="empty-inner">
              <div className="empty-glyph">
                <Search size={24} />
              </div>
              <h2>No titles match “{search}”</h2>
              <p>
                Try another title, or search the transcript index to find an
                idea inside a video.
              </p>
              <Link
                className="button"
                href={`/search?q=${encodeURIComponent(search)}`}
              >
                Search transcripts <ArrowUpRight size={14} />
              </Link>
            </div>
          </div>
        ) : (
          <div className="empty-library">
            <div className="empty-inner">
              <div className="empty-glyph">
                <ClapperboardIcon />
              </div>
              <h2>Your first source starts here</h2>
              <p>
                Add a local video or a public YouTube lesson. RecallFrame will
                transcribe it locally, index its moments, and make each answer
                traceable to the source.
              </p>
              <button
                className="button button-primary"
                onClick={() => setImportOpen(true)}
              >
                <Plus size={14} /> Add your first video
              </button>
              <Link className="demo-empty-link" href="/demo">
                Explore a clearly labeled preprocessed demo
              </Link>
            </div>
          </div>
        )}

        {!loading && videos.length > 0 && (
          <p className="footer-note">
            Search uses your local transcript and semantic index. AI answers are
            generated only from retrieved source evidence.
          </p>
        )}
        {importOpen && (
          <ImportDialog
            onClose={() => {
              setImportOpen(false);
              router.refresh();
            }}
          />
        )}
      </div>
    </AppShell>
  );
}

function ClapperboardIcon() {
  return <FileVideo2 size={25} />;
}
