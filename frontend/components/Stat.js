"use client";

export default function Stat({ label, value, icon, tone = "violet" }) {
  return (
    <div className={`stat ${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-info">
        <span className="stat-label">{label}</span>
        <b className="stat-value">{value}</b>
      </div>
    </div>
  );
}
