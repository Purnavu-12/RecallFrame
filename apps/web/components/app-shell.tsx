"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bookmark,
  CircleHelp,
  Clapperboard,
  Library,
  Network,
  Search,
  Settings2,
} from "lucide-react";
import type { ReactNode } from "react";

const links = [
  { href: "/", label: "Library", icon: Library },
  { href: "/search", label: "Search", icon: Search },
  { href: "/saved", label: "Saved insights", icon: Bookmark },
  { href: "/map", label: "Knowledge map", icon: Network },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const current =
    pathname === "/"
      ? "Library"
      : pathname.startsWith("/videos/")
        ? "Video workspace"
        : (links.find((link) => link.href === pathname)?.label ?? "Settings");

  return (
    <div className="app-frame">
      <header className="topbar">
        <div className="topbar-left">
          <Link className="brand" href="/" aria-label="RecallFrame home">
            <span className="brand-mark">
              <Clapperboard size={14} strokeWidth={2.1} />
            </span>
            <span>RecallFrame</span>
          </Link>
          <div className="crumbs">
            <span>
              {current === "Library" ? "Knowledge workspace" : "Library"}
            </span>
            <span className="slash">/</span>
            <span className="current">{current}</span>
          </div>
        </div>
        <div className="topbar-right">
          <span className="local-pill">
            <i className="status-dot" /> LOCAL · PRIVATE
          </span>
          <Link
            href="/settings"
            className="icon-button"
            aria-label="Open settings"
          >
            <Settings2 size={17} />
          </Link>
          <span className="avatar" aria-label="Local workspace">
            RF
          </span>
        </div>
      </header>
      <aside className="app-sidebar" aria-label="Main navigation">
        <nav className="nav-section">
          {links.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/"
                ? pathname === "/" || pathname.startsWith("/videos/")
                : pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`nav-link${active ? " active" : ""}`}
                aria-current={active ? "page" : undefined}
              >
                <Icon size={16} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebar-divider" />
        <div className="nav-section">
          <div className="nav-label">Workspace</div>
          <Link
            href="/settings"
            className={`nav-link${pathname === "/settings" ? " active" : ""}`}
          >
            <Settings2 size={16} />
            <span>Settings</span>
          </Link>
          <a
            className="nav-link"
            href="https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free"
            target="_blank"
            rel="noreferrer"
          >
            <CircleHelp size={16} />
            <span>AI data handling</span>
          </a>
        </div>
        <div className="sidebar-bottom">
          <span>
            <Activity size={12} /> &nbsp;On this device
          </span>
          <code>v0.1</code>
        </div>
      </aside>
      <main className="main-area">{children}</main>
    </div>
  );
}
