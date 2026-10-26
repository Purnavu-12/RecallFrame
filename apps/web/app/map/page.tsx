"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, GitBranch, Network } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { api, formatTime } from "@/lib/api";
import type { KnowledgeConcept } from "@/lib/types";

type Graph = {
  nodes: KnowledgeConcept[];
  edges: {
    source_id: string;
    target_id: string;
    evidence_ids: string[];
    score: number;
  }[];
};

export default function MapPage() {
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] });
  const [error, setError] = useState("");
  useEffect(() => {
    void api<Graph>("/knowledge-map")
      .then(setGraph)
      .catch((cause: unknown) =>
        setError(
          cause instanceof Error
            ? cause.message
            : "Knowledge map is unavailable.",
        ),
      );
  }, []);
  return (
    <AppShell>
      <div className="page-wrap">
        <div className="page-heading">
          <div>
            <div className="eyebrow">EVIDENCE-LINKED CONCEPTS</div>
            <h1>Knowledge map</h1>
            <p>
              Related ideas connect only when their source moments support the
              relationship.
            </p>
          </div>
          <span className="source-chip">
            <GitBranch size={12} /> {graph.edges.length} VERIFIED LINKS
          </span>
        </div>
        {error && <div className="error-box">{error}</div>}
        {graph.nodes.length === 0 ? (
          <div className="map-canvas">
            <div className="map-empty">
              <Network size={23} color="#a78bfa" />
              <h2>The map grows from your sources</h2>
              <p>
                Once videos are indexed, related concepts will appear here with
                paths back to their original segments.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="concept-list">
              {graph.nodes.map((node) => (
                <article className="subpage-row" key={node.id}>
                  <Link
                    href={`/videos/${node.video_id}`}
                    className="timestamp-button"
                    onClick={() =>
                      sessionStorage.setItem(
                        "recallframe:seek-on-open",
                        JSON.stringify({
                          videoId: node.video_id,
                          milliseconds: node.start_ms,
                        }),
                      )
                    }
                  >
                    {formatTime(node.start_ms)}
                  </Link>
                  <div>
                    <p>{node.label}</p>
                    <small>
                      {node.description ?? "Evidence-linked concept"} ·{" "}
                      <Link href={`/videos/${node.video_id}`}>
                        {node.video_title}
                      </Link>
                    </small>
                  </div>
                  <span className="source-chip">SOURCE LINKED</span>
                </article>
              ))}
            </div>
            {graph.edges.length > 0 && (
              <section className="subpage-panel" style={{ marginTop: 20 }}>
                <div className="side-section-title">
                  <GitBranch size={14} /> Source-backed associations
                </div>
                {graph.edges.map((edge) => {
                  const source = graph.nodes.find(
                    (node) => node.id === edge.source_id,
                  );
                  const target = graph.nodes.find(
                    (node) => node.id === edge.target_id,
                  );
                  if (!source || !target) return null;
                  return (
                    <article
                      className="subpage-row"
                      key={`${edge.source_id}-${edge.target_id}`}
                    >
                      <Link
                        href={`/videos/${source.video_id}`}
                        className="timestamp-button"
                        onClick={() =>
                          sessionStorage.setItem(
                            "recallframe:seek-on-open",
                            JSON.stringify({
                              videoId: source.video_id,
                              milliseconds: source.start_ms,
                            }),
                          )
                        }
                      >
                        {formatTime(source.start_ms)}
                      </Link>
                      <div>
                        <p>
                          {source.label} <ArrowRight size={13} /> {target.label}
                        </p>
                        <small>
                          Both concepts point to the same cited source moment ·{" "}
                          {source.video_title}
                        </small>
                      </div>
                      <span className="source-chip">SHARED EVIDENCE</span>
                    </article>
                  );
                })}
              </section>
            )}
          </>
        )}
        <p className="footer-note">
          A visible connection is not proof that two ideas are equivalent. Each
          concept links to the segment that supports it.
        </p>
      </div>
    </AppShell>
  );
}
