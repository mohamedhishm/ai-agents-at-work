"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { IS_MOCK } from "@/lib/api";

const demo = {
  admin: { email: "nour@eldoctor.com", password: "demo1234", name: "Nour Hussien" },
  customer: { email: "salma@eldoctor.com", password: "demo1234", name: "Salma Mohamed" },
};

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [role, setRole] = useState("customer");
  const [name, setName] = useState("");
  const [email, setEmail] = useState(IS_MOCK ? demo.customer.email : "");
  const [password, setPassword] = useState(IS_MOCK ? demo.customer.password : "");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const pickRole = (r) => {
    setRole(r);
    if (IS_MOCK && mode === "login") {
      setEmail(demo[r].email);
      setPassword(demo[r].password);
    }
  };

  const switchMode = (next) => {
    setMode(next);
    setErr("");
    if (next === "login" && IS_MOCK) {
      setEmail(demo[role].email);
      setPassword(demo[role].password);
    } else {
      setName("");
      setEmail("");
      setPassword("");
    }
  };

  const submit = async (e) => {
    e?.preventDefault();
    setBusy(true);
    setErr("");
    try {
      if (mode === "register") {
        if (!name.trim() || !email.trim() || password.length < 6) {
          throw new Error("Please enter your name, valid email, and password (min 6 characters).");
        }
        await register(name, email, password);
      } else {
        await login(email, password, role);
      }
    } catch (e) {
      setErr(e.response?.data?.detail || e.message || "Something went wrong.");
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg-glow glow-1" />
      <div className="login-bg-glow glow-2" />
      <div className="login-bg-glow glow-3" />
      <div className="login-grid-pattern" />

      <div className="login-container">
        {/* Left Side: Brand & Hero Showcase */}
        <div className="login-hero">
          <div className="brand light">
            <span className="brand-icon">✦</span>
            <span>El Doctor <span>AI</span></span>
          </div>

          <div className="login-hero-content">
            <div className="hero-badge">
              <span className="badge-dot" />
              INTELLIGENT SPARE-PARTS OPERATING SYSTEM
            </div>
            <h1>Automate & elevate your <span>spare-parts</span> operations</h1>
            <p>
              An integrated AI workspace for stock lookup, real-time tracking, purchase requests, and instant task approval workflows.
            </p>

            <div className="hero-feature-list">
              <div className="feature-item">
                <div className="feature-icon">✦</div>
                <div>
                  <b>Conversational AI Assistant</b>
                  <span>Natural language part search, pricing & stock checks</span>
                </div>
              </div>

              <div className="feature-item">
                <div className="feature-icon">⚡</div>
                <div>
                  <b>Instant Order Approvals</b>
                  <span>Smart task creation and real-time administrator reviews</span>
                </div>
              </div>

              <div className="feature-item">
                <div className="feature-icon">▣</div>
                <div>
                  <b>Live Order Tracking</b>
                  <span>End-to-end shipment status and estimated delivery times</span>
                </div>
              </div>
            </div>
          </div>

          <div className="hero-footer">
            <span>Powered by El Doctor AI Engine v2.4</span>
            <span className="status-live"><i /> System Operational</span>
          </div>
        </div>

        {/* Right Side: Integrated Auth Card */}
        <div className="login-form-wrapper">
          <div className="login-card">
            <div className="card-header">
              <h2>{mode === "login" ? "Welcome back" : "Create account"}</h2>
              <p>{mode === "login" ? "Sign in to access your El Doctor workspace" : "Get started with your smart operations account"}</p>
            </div>

            {/* Mode Switcher */}
            <div className="seg mode-switch">
              <button
                type="button"
                className={mode === "login" ? "on" : ""}
                onClick={() => switchMode("login")}
              >
                Sign in
              </button>
              <button
                type="button"
                className={mode === "register" ? "on" : ""}
                onClick={() => switchMode("register")}
              >
                Create account
              </button>
            </div>

            {/* Role Switcher (Login mode) */}
            {mode === "login" && (
              <div className="role-selector">
                <span className="role-label">ACCOUNT TYPE:</span>
                <div className="seg role-switch">
                  <button
                    type="button"
                    className={role === "customer" ? "on" : ""}
                    onClick={() => pickRole("customer")}
                  >
                    Customer Workspace
                  </button>
                  <button
                    type="button"
                    className={role === "admin" ? "on" : ""}
                    onClick={() => pickRole("admin")}
                  >
                    Admin Control
                  </button>
                </div>
              </div>
            )}

            {/* Form Fields */}
            <form onSubmit={submit} className="form-fields">
              {mode === "register" && (
                <div className="input-field">
                  <label htmlFor="full-name">Full name</label>
                  <div className="input-wrap">
                    <span className="field-icon">👤</span>
                    <input
                      id="full-name"
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Salma Mohamed"
                      required
                    />
                  </div>
                </div>
              )}

              <div className="input-field">
                <label htmlFor="email">Work Email</label>
                <div className="input-wrap">
                  <span className="field-icon">✉</span>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    required
                  />
                </div>
              </div>

              <div className="input-field">
                <label htmlFor="password">Password</label>
                <div className="input-wrap">
                  <span className="field-icon">🔒</span>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              {err && <div className="error-alert"><span>⚠️</span> {err}</div>}

              <button type="submit" className="submit-btn" disabled={busy}>
                {busy ? (
                  <span>{mode === "login" ? "Signing in..." : "Creating account..."}</span>
                ) : (
                  <>
                    <span>{mode === "login" ? "Sign In to Workspace" : "Create Account"}</span>
                    <span className="arrow-icon">→</span>
                  </>
                )}
              </button>
            </form>

            {/* Demo Quick Select */}
            {IS_MOCK && (
              <div className="demo-accounts-box">
                <div className="demo-title">
                  <span>⚡ Quick Demo Login</span>
                  <small>Click to auto-fill</small>
                </div>
                <div className="demo-buttons">
                  <button
                    type="button"
                    className={`demo-btn ${role === "customer" && mode === "login" ? "active" : ""}`}
                    onClick={() => {
                      switchMode("login");
                      pickRole("customer");
                    }}
                  >
                    <span className="role-chip customer">Customer</span>
                    <span className="demo-email">salma@eldoctor.com</span>
                  </button>
                  <button
                    type="button"
                    className={`demo-btn ${role === "admin" && mode === "login" ? "active" : ""}`}
                    onClick={() => {
                      switchMode("login");
                      pickRole("admin");
                    }}
                  >
                    <span className="role-chip admin">Admin</span>
                    <span className="demo-email">nour@eldoctor.com</span>
                  </button>
                </div>
              </div>
            )}

            <div className="card-footer">
              <span className="lock-icon">🔒</span>
              <span>Encrypted & secure enterprise session</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
