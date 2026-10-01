"use client";

import { useState } from "react";

const label = (s) => s.replaceAll("_", " ");

const getTimeline = (status) => {
  const steps = [
    { key: "created", label: "Order Created" },
    { key: "approved", label: "Approved" },
    { key: "processing", label: "Processing" },
    { key: "shipped", label: "Shipped" },
    { key: "delivered", label: "Delivered" },
  ];

  const progress = {
    pending_approval: 1,
    processing: 2,
    shipped: 3,
    delivered: 4,
    rejected: 1,
    cancelled: 1,
  };

  const current = progress[status] ?? 0;

  return steps.map((step, index) => ({
    ...step,
    completed: index < current,
    active:
      (status === "pending_approval" && step.key === "approved") ||
      (status === "processing" && step.key === "processing") ||
      (status === "shipped" && step.key === "shipped") ||
      (status === "delivered" && step.key === "delivered"),
  }));
};

export default function OrdersTable({
  orders,
  onApprove,
  onCancel,
  showCustomer,
}) {
  const [selectedOrder, setSelectedOrder] = useState(null);

  if (!orders || !orders.length) {
    return (
      <div className="empty-table-state">
        <span className="empty-icon">📦</span>
        <b>No orders found</b>
        <p>
          Ask the El Doctor AI assistant to check stock or create a purchase
          request.
        </p>
      </div>
    );
  }

  const timeline = selectedOrder
    ? getTimeline(selectedOrder.status)
    : [];

  return (
    <>
      <div className="scroll">
        <table className="orders-table">
          <thead>
            <tr>
              <th>ORDER ID</th>
              <th>ITEM & PART DETAILS</th>
              {showCustomer && <th>CUSTOMER</th>}
              <th>AMOUNT</th>
              <th>STATUS</th>
              {(onApprove || onCancel) && (
                <th className="text-right">ACTIONS</th>
              )}
            </tr>
          </thead>

          <tbody>
            {orders.map((o) => (
             <tr
                  key={o.id}
                  className="order-row-clickable"
                  onClick={() => setSelectedOrder(o)}
                >
                <td
                  className="order-clickable"
                  onClick={() => setSelectedOrder(o)}
                >
                  <b className="order-id">#{o.id}</b>
                </td>

                <td
                  className="order-clickable"
                  onClick={() => setSelectedOrder(o)}
                >
                  <div className="item-cell">
                    <span className="item-icon">⚙</span>

                    <div className="item-details">
                      <span className="item-name">{o.title}</span>
                    </div>
                  </div>
                </td>

                {showCustomer && (
                  <td>
                    <span className="customer-name">{o.customer}</span>
                  </td>
                )}

                <td>
                  <span className="amount-tag">
                    EGP {o.amount}
                  </span>
                </td>

                <td>
                  <span className={`tag ${o.status}`}>
                    <i />
                    {label(o.status)}
                  </span>
                </td>

                {(onApprove || onCancel) && (
                  <td className="acts"
                  onClick={(e) => e.stopPropagation()}>
                    {onApprove &&
                    o.status === "pending_approval" ? (
                      <>
                        <button
                          className="approve-btn"
                          onClick={() => onApprove(o.id, true)}
                        >
                          Approve
                        </button>

                        <button
                          className="reject-btn"
                          onClick={() => onApprove(o.id, false)}
                        >
                          Reject
                        </button>
                      </>
                    ) : onCancel &&
                      ["pending_approval", "processing"].includes(
                        o.status
                      ) ? (
                      <button
                        className="reject-btn"
                        onClick={() => onCancel(o.id)}
                      >
                        Cancel
                      </button>
                    ) : (
                      <span className="processed-text">—</span>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedOrder && (
        <div
          className="order-details-overlay"
          onClick={() => setSelectedOrder(null)}
        >
          <div
            className="order-details-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="order-details-header">
              <div>
                <span className="order-details-label">
                  ORDER DETAILS
                </span>

                <h2>Order #{selectedOrder.id}</h2>
              </div>

              <button
                className="order-details-close"
                onClick={() => setSelectedOrder(null)}
              >
                ✕
              </button>
            </div>

            <div className="order-details-item">
              <div className="order-details-item-icon">⚙</div>

              <div>
                <span>Item & Part</span>
                <strong>{selectedOrder.title}</strong>
              </div>
            </div>

            <div className="order-details-info">
              <div className="order-info-box">
                <span>Customer</span>
                <strong>
                  {selectedOrder.customer || "—"}
                </strong>
              </div>

              <div className="order-info-box">
                <span>Amount</span>
                <strong>
                  EGP {selectedOrder.amount}
                </strong>
              </div>

              <div className="order-info-box">
                <span>Status</span>
                <strong>
                  <span
                    className={`tag ${selectedOrder.status}`}
                  >
                    <i />
                    {label(selectedOrder.status)}
                  </span>
                </strong>
              </div>

              <div className="order-info-box">
                <span>ETA</span>
                <strong>
                  {selectedOrder.eta || "—"}
                </strong>
              </div>

              <div className="order-info-box full">
                <span>Current Location</span>
                <strong>
                  {selectedOrder.location || "—"}
                </strong>
              </div>
            </div>
            <div className="order-info-box full">
              <span>Delivery Address</span>
              <strong>{selectedOrder.delivery_address || "—"}</strong>
            </div>

            <div className="order-timeline-section">
              <h3>Order Timeline</h3>

              <div className="order-timeline">
                {timeline.map((step, index) => (
                  <div
                    key={step.key}
                    className={`timeline-step ${
                      step.completed ? "completed" : ""
                    } ${step.active ? "active" : ""}`}
                  >
                    <div className="timeline-marker">
                      {step.completed ? "✓" : ""}
                    </div>

                    <div className="timeline-content">
                      <strong>{step.label}</strong>

                      {step.active && (
                        <span>Current status</span>
                      )}
                    </div>

                    {index < timeline.length - 1 && (
                      <div className="timeline-line" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            <button
              className="order-details-done"
              onClick={() => setSelectedOrder(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}