"use client";

import { useCallback, useEffect, useState } from "react";
import { useGuard } from "@/context/AuthContext";
import { TaskAPI } from "@/lib/api";
import Shell from "@/components/Shell";
import Chat from "@/components/Chat";
import Stat from "@/components/Stat";
import OrdersTable from "@/components/OrdersTable";

export default function CustomerDashboard() {
  const { ready, user } = useGuard("customer");
  const [orders, setOrders] = useState([]);
  const [cancelId, setCancelId] = useState(null);

  const load = useCallback(
    () =>
      TaskAPI.list()
        .then((r) => setOrders(r.data))
        .catch(() => {}),
    []
  );

  const handleCancel = (id) => {
    setCancelId(id);
  };

  const confirmCancel = async () => {
    if (!cancelId) return;

    try {
      await TaskAPI.cancel(cancelId);
      setCancelId(null);
      await load();
    } catch (error) {
      console.error("Failed to cancel order:", error);
    }
  };

  const closeCancelModal = () => {
    setCancelId(null);
  };

  useEffect(() => {
    if (ready) load();
  }, [ready, load]);

  if (!ready) return null;

  const n = (statuses) =>
    orders.filter((o) => statuses.includes(o.status)).length;

  const firstName = user?.name
    ? user.name.split(" ")[0]
    : "Customer";

  const selectedOrder = orders.find((o) => o.id === cancelId);

  return (
    <Shell
      title={`Welcome back, ${firstName} 👋`}
      subtitle="Your intelligent spare-parts workspace — search inventory, track shipments, and request orders with El Doctor AI."
    >
      <section className="hero-center">
        <div className="hero-center-copy">
          <span className="agent-badge">
            <i /> El Doctor AI Engine is active
          </span>

          <h2>How can I assist your operations today?</h2>

          <p>
            Ask about spare parts availability, live inventory prices, or
            shipment tracking. The agent creates tasks and manages approvals
            seamlessly.
          </p>
        </div>

        <div className="quick-actions">
          <div className="quick-card">
            <span>⌕</span>
            <div>
              <b>Find Spare Parts</b>
              <small>Search by part code, car make or model</small>
            </div>
          </div>

          <div className="quick-card">
            <span>▣</span>
            <div>
              <b>Track Active Orders</b>
              <small>Real-time location & ETA updates</small>
            </div>
          </div>

          <div className="quick-card">
            <span>◈</span>
            <div>
              <b>Check Stock & Price</b>
              <small>Verify live warehouse inventory</small>
            </div>
          </div>

          <div className="quick-card">
            <span>✦</span>
            <div>
              <b>Automated Workflow</b>
              <small>Instant purchase request creation</small>
            </div>
          </div>
        </div>
      </section>

      <section className="agent-panel-wrap">
        <div className="section-title">
          <div>
            <h3>El Doctor Conversational Assistant</h3>
            <p>Smart RAG-powered spare-parts engine</p>
          </div>

          <span className="agent-flow">
            <i /> Ready for requests
          </span>
        </div>

        <Chat onReply={load} />
      </section>

      <div className="stats stats-lower">
        <Stat
          label="Total Orders"
          value={orders.length}
          icon="▣"
        />

        <Stat
          label="In Progress"
          value={n(["processing", "shipped"])}
          icon="↗"
          tone="blue"
        />

        <Stat
          label="Delivered"
          value={n(["delivered"])}
          icon="✓"
          tone="green"
        />

        <Stat
          label="Awaiting Approval"
          value={n(["pending_approval"])}
          icon="!"
          tone="amber"
        />
      </div>

      <section className="orders-section">
        <div className="section-title">
          <div>
            <h3>Recent Orders & Requests</h3>
            <p>Live order history and real-time execution status</p>
          </div>

          <span className="count-badge">
            {orders.length} Orders
          </span>
        </div>

        <div className="card">
          <OrdersTable
            orders={orders}
            onCancel={handleCancel}
          />
        </div>
      </section>

      {/* Cancel Confirmation Modal */}
      {cancelId && (
        <div className="cancel-modal-overlay">
          <div className="cancel-modal">
            <div className="cancel-modal-icon">!</div>

            <h3>Cancel Order?</h3>

            <p>
              Are you sure you want to cancel{" "}
              {selectedOrder ? `order #${selectedOrder.id}` : "this order"}?
            </p>

            <span className="cancel-modal-warning">
              This action cannot be undone.
            </span>

            <div className="cancel-modal-actions">
              <button
                className="cancel-modal-back"
                onClick={closeCancelModal}
              >
                Keep Order
              </button>

              <button
                className="cancel-modal-confirm"
                onClick={confirmCancel}
              >
                Yes, Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </Shell>
  );
}