"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, ArrowRight, Play, Sparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { demoChapters, demoSegments } from "@/lib/demo";
import { formatTime } from "@/lib/api";

export default function DemoPage() {
  const [activeSegment, setActiveSegment] = useState(demoSegments[0].id);
  const active = demoSegments.find((segment) => segment.id === activeSegment)!;
  const seek = (segmentId: string) => setActiveSegment(segmentId);

  return (
    <AppShell>
      <div className="demo-workspace">
        <section className="workspace-main">
          <div className="workspace-content">
            <Link className="eyebrow demo-back" href="/">
              <ArrowLeft size={12} /> BACK TO YOUR LIBRARY
            </Link>
            <div className="video-heading demo-heading">
              <div>
                <div className="eyebrow">PREPROCESSED DEMO · ILLUSTRATIVE</div>
                <h1>How a load balancer routes requests</h1>
                <p>
                  <span className="source-chip">SAMPLE SOURCE</span>
                  <span>·</span>
                  <span>2:20</span>
                  <span>·</span>
                  <span>Not in your library</span>
                </p>
              </div>
              <Link className="button button-primary" href="/">
                Add your own video <ArrowRight size={14} />
              </Link>
            </div>

            <div className="demo-notice" role="note">
              <Sparkles size={15} />
              <p>
                <b>Demo data, not a real source.</b> This prewritten transcript,
                diagram, timestamps, and answer are illustrative. No video was
                processed and no AI inference ran for this page.
              </p>
            </div>

            <div
              className="player-shell demo-player"
              aria-label="Illustrative diagram preview"
            >
              <svg
                viewBox="0 0 960 480"
                role="img"
                aria-labelledby="diagram-title diagram-description"
              >
                <title id="diagram-title">Load balancer request flow</title>
                <desc id="diagram-description">
                  A browser sends traffic through a load balancer to three
                  application servers, which read from a database.
                </desc>
                <defs>
                  <linearGradient id="demo-bg" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#171b24" />
                    <stop offset="100%" stopColor="#0d1118" />
                  </linearGradient>
                  <marker
                    id="demo-arrow"
                    markerWidth="10"
                    markerHeight="10"
                    refX="8"
                    refY="5"
                    orient="auto"
                  >
                    <path
                      d="M0 0L10 5L0 10"
                      fill="none"
                      stroke="#8b8c9d"
                      strokeWidth="1.5"
                    />
                  </marker>
                </defs>
                <rect width="960" height="480" rx="18" fill="url(#demo-bg)" />
                <text
                  x="48"
                  y="47"
                  fill="#8e91a3"
                  fontSize="12"
                  fontFamily="monospace"
                  letterSpacing="2"
                >
                  SAMPLE ARCHITECTURE · PREPROCESSED
                </text>
                <g
                  fill="none"
                  stroke="#8b8c9d"
                  strokeWidth="2"
                  markerEnd="url(#demo-arrow)"
                >
                  <path d="M226 236H335" />
                  <path d="M525 236H640" />
                  <path d="M777 236H835" />
                </g>
                <g>
                  <rect
                    x="62"
                    y="168"
                    width="164"
                    height="136"
                    rx="14"
                    fill="#172235"
                    stroke="#6397cb"
                    strokeWidth="2"
                  />
                  <rect
                    x="108"
                    y="202"
                    width="72"
                    height="48"
                    rx="4"
                    fill="none"
                    stroke="#83b5ed"
                    strokeWidth="3"
                  />
                  <path
                    d="M98 262H190"
                    stroke="#83b5ed"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                  <text
                    x="144"
                    y="342"
                    textAnchor="middle"
                    fill="#e4e8f2"
                    fontSize="16"
                    fontWeight="600"
                  >
                    Browser
                  </text>
                </g>
                <g>
                  <rect
                    x="335"
                    y="150"
                    width="190"
                    height="172"
                    rx="16"
                    fill="#28213e"
                    stroke="#a78bfa"
                    strokeWidth="2"
                  />
                  <circle
                    cx="430"
                    cy="207"
                    r="10"
                    fill="none"
                    stroke="#c4b5fd"
                    strokeWidth="3"
                  />
                  <circle
                    cx="401"
                    cy="251"
                    r="8"
                    fill="none"
                    stroke="#c4b5fd"
                    strokeWidth="3"
                  />
                  <circle
                    cx="459"
                    cy="251"
                    r="8"
                    fill="none"
                    stroke="#c4b5fd"
                    strokeWidth="3"
                  />
                  <path
                    d="M425 216L405 244M435 216L455 244M409 251H451"
                    stroke="#c4b5fd"
                    strokeWidth="2.5"
                  />
                  <text
                    x="430"
                    y="289"
                    textAnchor="middle"
                    fill="#e7ddff"
                    fontSize="14"
                    fontWeight="600"
                  >
                    Load balancer
                  </text>
                  <text
                    x="430"
                    y="342"
                    textAnchor="middle"
                    fill="#a78bfa"
                    fontSize="12"
                    fontFamily="monospace"
                  >
                    ROUTE · CHECK · DISTRIBUTE
                  </text>
                </g>
                <g>
                  <rect
                    x="640"
                    y="148"
                    width="137"
                    height="176"
                    rx="13"
                    fill="#121b28"
                    stroke="#5e86bc"
                    strokeWidth="2"
                    strokeDasharray="6 5"
                  />
                  {[0, 1, 2].map((item) => (
                    <g
                      key={item}
                      transform={`translate(662 ${166 + item * 49})`}
                    >
                      <rect
                        width="93"
                        height="37"
                        rx="6"
                        fill="#1c2d43"
                        stroke="#7da5d7"
                        strokeWidth="1.5"
                      />
                      <path
                        d="M12 12H67M12 24H54"
                        stroke="#8fb5e4"
                        strokeWidth="2"
                        strokeLinecap="round"
                      />
                      <circle cx="80" cy="12" r="2.5" fill="#68d5b2" />
                    </g>
                  ))}
                  <text
                    x="708"
                    y="354"
                    textAnchor="middle"
                    fill="#e4e8f2"
                    fontSize="14"
                    fontWeight="600"
                  >
                    App servers
                  </text>
                </g>
                <g>
                  <rect
                    x="835"
                    y="177"
                    width="83"
                    height="119"
                    rx="13"
                    fill="#142922"
                    stroke="#68d5b2"
                    strokeWidth="2"
                  />
                  <ellipse
                    cx="876"
                    cy="218"
                    rx="20"
                    ry="8"
                    fill="none"
                    stroke="#80e7c5"
                    strokeWidth="2.5"
                  />
                  <path
                    d="M856 218V254C856 265 896 265 896 254V218M856 230C856 241 896 241 896 230M856 242C856 253 896 253 896 242"
                    fill="none"
                    stroke="#80e7c5"
                    strokeWidth="2"
                  />
                  <text
                    x="876"
                    y="334"
                    textAnchor="middle"
                    fill="#e4e8f2"
                    fontSize="14"
                    fontWeight="600"
                  >
                    Database
                  </text>
                </g>
                <g transform="translate(48 411)">
                  <circle cx="7" cy="7" r="6" fill="#a78bfa" />
                  <text x="25" y="11" fill="#b9bbca" fontSize="12">
                    Selected demo passage · {formatTime(active.start_ms)}
                  </text>
                </g>
              </svg>
              <div className="demo-player-controls">
                <span className="demo-play-icon">
                  <Play size={14} fill="currentColor" />
                </span>
                <span>Illustrative diagram · no source video</span>
                <span className="timecode">
                  {formatTime(active.start_ms)} / 2:20
                </span>
              </div>
            </div>

            <div className="chapter-strip" aria-label="Sample chapters">
              {demoChapters.map((chapter, index) => (
                <button
                  className="chapter-segment"
                  key={chapter.title}
                  onClick={() => seek(demoSegments[index].id)}
                >
                  <b>{chapter.title}</b>
                  <span>
                    {formatTime(chapter.start_ms)} –{" "}
                    {formatTime(chapter.end_ms)}
                  </span>
                </button>
              ))}
            </div>

            <div className="tabs" aria-label="Demo transcript">
              <span className="tab active">Transcript</span>
              <span className="source-chip">ILLUSTRATIVE SAMPLE</span>
            </div>
            <div className="transcript-list">
              {demoSegments.map((segment) => (
                <article
                  className={`transcript-row${activeSegment === segment.id ? " current" : ""}`}
                  key={segment.id}
                >
                  <button
                    className="timestamp-button"
                    onClick={() => seek(segment.id)}
                  >
                    {formatTime(segment.start_ms)}
                  </button>
                  <p>{segment.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <aside className="answer-panel" aria-label="Sample grounded answer">
          <div className="answer-header">
            <h2>
              <Sparkles size={16} /> Ask this video
            </h2>
            <span className="source-chip">DEMO</span>
          </div>
          <p className="answer-intro">
            This prewritten response demonstrates source navigation. It was not
            generated by an AI model.
          </p>
          <div className="question-form">
            <div className="demo-question">Why use a load balancer?</div>
          </div>
          <article className="answer-card">
            <p className="answer-text">
              It provides one entry point for incoming requests, then
              distributes traffic across healthy application servers. In this
              sample, the transcript also describes how health checks can keep
              requests away from an unresponsive instance.
            </p>
            <div className="evidence-label">DEMO SOURCE PASSAGES</div>
            {demoSegments.slice(1).map((segment) => (
              <div className="evidence-card" key={segment.id}>
                <p className="evidence-quote">“{segment.text}”</p>
                <button
                  className="evidence-chip"
                  onClick={() => seek(segment.id)}
                >
                  {formatTime(segment.start_ms)} · sample timestamp
                </button>
              </div>
            ))}
            <div className="demo-verified">
              Illustrative references · not verified against a real recording
            </div>
          </article>
          <div className="side-section-title">
            <Sparkles size={14} /> Sample takeaways
          </div>
          <div className="takeaway-list">
            {demoSegments.slice(1).map((segment) => (
              <button
                className="takeaway-row demo-takeaway"
                key={segment.id}
                onClick={() => seek(segment.id)}
              >
                <span className="timestamp-button">
                  {formatTime(segment.start_ms)}
                </span>
                <span>{segment.text.split(".")[0]}.</span>
              </button>
            ))}
          </div>
          <div className="demo-notice demo-notice-small">
            <p>
              Prewritten demonstration only. Real answers require an indexed
              source and are built from retrieved evidence.
            </p>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
