"use client";
import { useCallback, useEffect, useState } from "react";
import { useGuard } from "@/context/AuthContext";
import { TaskAPI, AgentAPI } from "@/lib/api";
import Shell from "@/components/Shell";
import Stat from "@/components/Stat";
import OrdersTable from "@/components/OrdersTable";

export default function AdminDashboard() {
  const { ready } = useGuard("admin");
  const [orders, setOrders] = useState([]);
  const [activity, setActivity] = useState([]);

  const load = useCallback(() => {
    TaskAPI.list()
      .then((r) => setOrders(r.data))
      .catch(() => {});
    AgentAPI.activity()
      .then((r) => setActivity(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!ready) return;
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [ready, load]);

  const decide = async (id, ok) => {
    await TaskAPI.approve(id, ok);
    load();
  };

  if (!ready) return null;

  const revenue = orders
    .filter((o) => o.status !== "rejected")
    .reduce((s, o) => s + o.amount, 0);

  return (
    <Shell
      title="Administrator Operations Center 👋"
      subtitle="Monitor AI task creation, review pending order approvals, and supervise operational execution in real time."
    >
      <section className="admin-hero">
        <div>
          <span className="agent-badge">
            <i /> El Doctor AI Operational Supervisor
          </span>
          <h2>Live Agent Operations & Control</h2>
          <p>
            Review automated part lookup queries, tool activations, and human-in-the-loop task authorizations.
          </p>
        </div>
        <div className="runtime-card">
          <span>AGENT RUNTIME</span>
          <b>Active</b>
          <small>RAG · Tools · Approvals</small>
        </div>
      </section>

      <div className="stats">
        <Stat label="Total Order Value" value={`EGP ${revenue.toLocaleString()}`} icon="₤" tone="green" />
        <Stat label="Total Orders" value={orders.length} icon="▣" />
        <Stat
          label="Needs Approval"
          value={orders.filter((o) => o.status === "pending_approval").length}
          icon="!"
          tone="amber"
        />
        <Stat label="Agent Actions" value={activity.length} icon="✦" tone="pink" />
      </div>

      <div className="admin-grid">
        <section className="admin-orders-col">
          <div className="section-title">
            <div>
              <h3>Order Approval Queue</h3>
              <p>Authorize or reject customer purchase tasks</p>
            </div>
          </div>
          <div className="card">
            <OrdersTable orders={orders} onApprove={decide} showCustomer />
          </div>
        </section>

        <section className="admin-activity-col">
          <div className="section-title">
            <div>
              <h3>Live Agent Activity</h3>
              <p>Real-time log of tool calls and RAG searches</p>
            </div>
            <span className="agent-flow">
              <i /> Live Feed
            </span>
          </div>
          <div className="card feed">
            {activity.length ? (
              activity.map((a) => (
                <div key={a.id} className="act">
                  <span className={`pip ${a.status}`} />
                  <div>
                    <b>{a.type}</b>
                    <small>{a.detail}</small>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted pad">No agent activity logged yet.</p>
            )}
          </div>
        </section>
      </div>
    </Shell>
  );
}
