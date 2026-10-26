"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bookmark, Trash2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api, formatTime } from "@/lib/api";
import type { SavedInsight } from "@/lib/types";

export default function SavedPage() {
  const [items, setItems] = useState<SavedInsight[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    void api<SavedInsight[]>("/insights")
      .then(setItems)
      .catch((cause: unknown) =>
        setError(
          cause instanceof Error
            ? cause.message
            : "Saved insights are unavailable.",
        ),
      );
  }, []);
  async function remove(id: string) {
    try {
      await api(`/insights/${id}`, { method: "DELETE" });
      setItems((current) => current.filter((item) => item.id !== id));
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not delete this insight.",
      );
    }
  }
  return (
    <AppShell>
      <div className="page-wrap">
        <div className="page-heading">
          <div>
            <div className="eyebrow">PERSONAL NOTES</div>
            <h1>Saved insights</h1>
            <p>
              Keep the ideas worth revisiting, always linked to their source
              moment.
            </p>
          </div>
        </div>
        {error && <div className="error-box">{error}</div>}
        <div className="subpage-panel">
          {items.map((item) => (
            <article className="subpage-row" key={item.id}>
              {item.start_ms != null ? (
                <Link
                  href={`/videos/${item.video_id}`}
                  className="timestamp-button"
                  onClick={() =>
                    sessionStorage.setItem(
                      "recallframe:seek-on-open",
                      JSON.stringify({
                        videoId: item.video_id,
                        milliseconds: item.start_ms,
                      }),
                    )
                  }
                >
                  {formatTime(item.start_ms)}
                </Link>
              ) : (
                <span className="timestamp-button">
                  <Bookmark size={12} />
                </span>
              )}
              <div>
                <p>{item.text}</p>
                <small>
                  <Link href={`/videos/${item.video_id}`}>
                    {item.video_title}
                  </Link>{" "}
                  · {new Date(item.created_at).toLocaleDateString()}
                </small>
              </div>
              <button
                className="icon-button"
                aria-label="Delete saved insight"
                onClick={() => void remove(item.id)}
              >
                <Trash2 size={14} />
              </button>
            </article>
          ))}
          {items.length === 0 && !error && (
            <div className="empty-library">
              <div className="empty-inner">
                <div className="empty-glyph">
                  <Bookmark size={22} />
                </div>
                <h2>Save a moment to keep it close</h2>
                <p>
                  Save a key takeaway or an answer from a video workspace. Its
                  timestamp stays attached.
                </p>
                <Link className="button" href="/">
                  Browse your library
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
