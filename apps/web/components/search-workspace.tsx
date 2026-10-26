"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Search, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api, formatTime } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

export function SearchWorkspace({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(Boolean(initialQuery));
  const [error, setError] = useState("");

  const runSearch = useCallback(async (value: string) => {
    if (!value.trim()) return;
    setLoading(true);
    setError("");
    setActiveQuery(value);
    try {
      setResults(
        await api<SearchResult[]>(
          `/search?q=${encodeURIComponent(value.trim())}`,
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Search is unavailable.",
      );
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!initialQuery) return;
    let active = true;
    api<SearchResult[]>(`/search?q=${encodeURIComponent(initialQuery.trim())}`)
      .then((data) => {
        if (active) setResults(data);
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error ? cause.message : "Search is unavailable.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [initialQuery]);

  function prepareSeek(result: SearchResult) {
    sessionStorage.setItem(
      "recallframe:seek-on-open",
      JSON.stringify({
        videoId: result.video_id,
        milliseconds: result.start_ms,
      }),
    );
  }

  return (
    <AppShell>
      <div className="page-wrap">
        <div className="page-heading">
          <div>
            <div className="eyebrow">CROSS-LIBRARY RETRIEVAL</div>
            <h1>Search knowledge</h1>
            <p>
              Search transcripts and indexed visual notes across your sources.
            </p>
          </div>
        </div>
        <form
          className="library-controls"
          onSubmit={(event) => {
            event.preventDefault();
            void runSearch(query);
          }}
        >
          <label className="search-field">
            <Search size={15} />
            <input
              autoFocus
              aria-label="Search all source videos"
              placeholder="Try a term, concept, or question…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <button
            className="button button-primary"
            disabled={loading || !query.trim()}
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </form>
        {error && (
          <p className="error-box" role="alert">
            {error}
          </p>
        )}
        {activeQuery && !loading && !error && (
          <div className="library-statline">
            <span>
              <Sparkles size={13} /> {results.length} evidence matches for{" "}
              <b>“{activeQuery}”</b>
            </span>
            <span>Keyword + semantic ranking</span>
          </div>
        )}
        <div className="subpage-panel" style={{ marginTop: 12 }}>
          {results.map((result) => (
            <div
              className="subpage-row"
              key={`${result.video_id}-${result.segment_id}-${result.start_ms}`}
            >
              <Link
                className="timestamp-button"
                href={`/videos/${result.video_id}`}
                onClick={() => prepareSeek(result)}
              >
                {formatTime(result.start_ms)}
              </Link>
              <Link
                href={`/videos/${result.video_id}`}
                onClick={() => prepareSeek(result)}
              >
                <p>{result.excerpt}</p>
                <small>{result.video_title}</small>
              </Link>
              <Link
                className="button button-quiet"
                href={`/videos/${result.video_id}`}
                onClick={() => prepareSeek(result)}
              >
                Open source <ArrowUpRight size={13} />
              </Link>
            </div>
          ))}
          {activeQuery && !loading && results.length === 0 && !error && (
            <div className="empty-library">
              <div className="empty-inner">
                <h2>No supporting passages found</h2>
                <p>
                  Try different wording, or ask a narrower question about one
                  indexed video. RecallFrame does not invent search results when
                  evidence is missing.
                </p>
              </div>
            </div>
          )}
          {!activeQuery && (
            <div className="empty-library">
              <div className="empty-inner">
                <div className="empty-glyph">
                  <Search size={23} />
                </div>
                <h2>Search what your videos explain</h2>
                <p>
                  Search works across transcript segments and timestamped video
                  evidence after a source is indexed.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
