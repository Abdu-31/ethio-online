import { useState, useEffect } from "react";
import { API_BASE, getInitData } from "../App";

const STEPS = ["pending", "processing", "booked", "completed"];
const STEP_LABELS = { pending:"Pending", processing:"Processing", booked:"Booked", completed:"Done" };

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

function Timeline({ status }) {
  if (status === "cancelled") {
    return <div style={{marginTop:8}}><span className="badge badge-cancelled">❌ Cancelled</span></div>;
  }
  const current = STEPS.indexOf(status);
  return (
    <div className="timeline">
      {STEPS.map((step, i) => (
        <>
          <div className="timeline-step" key={step}>
            <div className={`timeline-dot ${i < current ? "done" : i === current ? "active" : ""}`} />
            <div className={`timeline-label ${i <= current ? "done" : ""}`}>{STEP_LABELS[step]}</div>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`timeline-line ${i < current ? "done" : ""}`} key={`line-${i}`} />
          )}
        </>
      ))}
    </div>
  );
}

export default function MyOrders({ tgUser }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/orders/my`, {
      headers: { "x-init-data": getInitData() || "dev_mode" }
    })
      .then(r => r.json())
      .then(data => { setOrders(data); setLoading(false); })
      .catch(() => { setError("Could not load orders."); setLoading(false); });
  }, []);

  if (loading) return <div className="loading">Loading your orders...</div>;
  if (error)   return <div className="error-msg">{error}</div>;

  if (orders.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📭</div>
        <div className="empty-text">No orders yet.<br />Place your first order from the New Order tab.</div>
      </div>
    );
  }

  return (
    <div>
      <div className="section-title">My Orders</div>
      {orders.map(order => (
        <div className="order-row" key={order.id}>
          <div className="order-row-top">
            <div>
              <div className="order-id">Order #{order.id}</div>
              <div className="order-meta">
                {order.passport_type} · {order.urgency}<br />
                {order.created_at?.slice(0,10)}
              </div>
            </div>
            <StatusBadge status={order.status} />
          </div>
          <Timeline status={order.status} />
        </div>
      ))}
    </div>
  );
}
