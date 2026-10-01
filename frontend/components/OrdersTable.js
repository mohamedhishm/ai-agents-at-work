"use client";

const label = (s) => s.replaceAll("_", " ");

export default function OrdersTable({ orders, onApprove, showCustomer }) {
  if (!orders || !orders.length) {
    return (
      <div className="empty-table-state">
        <span className="empty-icon">📦</span>
        <b>No orders found</b>
        <p>Ask the El Doctor AI assistant to check stock or create a purchase request.</p>
      </div>
    );
  }

  return (
    <div className="scroll">
      <table className="orders-table">
        <thead>
          <tr>
            <th>ORDER ID</th>
            <th>ITEM & PART DETAILS</th>
            {showCustomer && <th>CUSTOMER</th>}
            <th>AMOUNT</th>
            <th>STATUS</th>
            {onApprove && <th className="text-right">ACTIONS</th>}
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td>
                <b className="order-id">#{o.id}</b>
              </td>
              <td>
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
                <span className="amount-tag">EGP {o.amount}</span>
              </td>
              <td>
                <span className={`tag ${o.status}`}>
                  <i />
                  {label(o.status)}
                </span>
              </td>
              {onApprove && (
                <td className="acts">
                  {o.status === "pending_approval" ? (
                    <>
                      <button className="approve-btn" onClick={() => onApprove(o.id, true)}>
                        Approve
                      </button>
                      <button className="reject-btn" onClick={() => onApprove(o.id, false)}>
                        Reject
                      </button>
                    </>
                  ) : (
                    <span className="processed-text">Completed</span>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
