"use client";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

export default function Shell({ title, subtitle, children }) {
  const { user, logout } = useAuth();
  const initials = (user?.name || "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const admin = user?.role === "admin";

  return (
    <div className="app-layout">
      <header className="appbar">
        <div className="appbar-inner">
          <div className="brand brand-dark">
            <span className="brand-icon">✦</span>
            <span>
              El Doctor <em>AI</em>
            </span>
          </div>

          <div className="workspace-badge">
            <span className={`status-indicator ${admin ? "admin-mode" : ""}`} />
            <span>{admin ? "Admin Operations Control" : "Customer Workspace"}</span>
          </div>

          <div className="appbar-links">
            <span className="secure-badge">
              <i className="pulse-dot" /> Secure Workspace
            </span>
          </div>

          <div className="user-menu">
            <div className="header-avatar">{initials}</div>
            <div className="user-info">
              <b>{user?.name}</b>
              <small>{admin ? "Administrator" : "Verified Customer"}</small>
            </div>
            <button className="signout-btn" onClick={logout} title="Sign out">
              <span>Sign out</span>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main className="content">
        <div className="page-heading">
          <div>
            <div className="eyebrow">{admin ? "SYSTEM CONTROL & APPROVALS" : "INTELLIGENT ASSISTANT WORKSPACE"}</div>
            <h1>{title}</h1>
            <p className="muted">{subtitle}</p>
          </div>
        </div>

        {children}
      </main>
    </div>
  );
}
