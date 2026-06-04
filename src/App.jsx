import { useState, useEffect } from "react";
import OrderForm from "./components/OrderForm";
import MyOrders from "./components/MyOrders";
import AdminDashboard from "./components/AdminDashboard";
import "./App.css";

const ADMIN_ID = parseInt(process.env.REACT_APP_ADMIN_ID || "0");
const API_BASE = process.env.REACT_APP_API_URL || "https://your-api.onrender.com";

export { API_BASE };

export function getInitData() {
  return window.Telegram?.WebApp?.initData || "";
}

export function getTelegramUser() {
  return window.Telegram?.WebApp?.initDataUnsafe?.user || null;
}

export default function App() {
  const [tab, setTab] = useState("order");
  const [tgUser, setTgUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      tg.setHeaderColor("#0F1923");
      tg.setBackgroundColor("#0F1923");
    }
    const user = getTelegramUser();
    setTgUser(user);
    setReady(true);
  }, []);

  const isAdmin = tgUser?.id === ADMIN_ID;

  if (!ready) {
    return (
      <div className="splash">
        <div className="splash-icon">🛂</div>
        <div className="splash-text">Loading...</div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-flag">🇪🇹</div>
        <div className="header-text">
          <span className="header-title">Passport Service</span>
          {tgUser && (
            <span className="header-user">
              {tgUser.first_name}
            </span>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="app-main">
        {tab === "order" && <OrderForm tgUser={tgUser} />}
        {tab === "orders" && <MyOrders tgUser={tgUser} />}
        {tab === "admin" && isAdmin && <AdminDashboard />}
        {tab === "admin" && !isAdmin && (
          <div className="unauthorized">
            <div className="unauth-icon">🔒</div>
            <p>Admin access only</p>
          </div>
        )}
      </main>

      {/* Bottom Nav */}
      <nav className="bottom-nav">
        <button
          className={`nav-btn ${tab === "order" ? "active" : ""}`}
          onClick={() => setTab("order")}
        >
          <span className="nav-icon">📝</span>
          <span className="nav-label">New Order</span>
        </button>
        <button
          className={`nav-btn ${tab === "orders" ? "active" : ""}`}
          onClick={() => setTab("orders")}
        >
          <span className="nav-icon">📋</span>
          <span className="nav-label">My Orders</span>
        </button>
        {isAdmin && (
          <button
            className={`nav-btn ${tab === "admin" ? "active" : ""}`}
            onClick={() => setTab("admin")}
          >
            <span className="nav-icon">⚙️</span>
            <span className="nav-label">Admin</span>
          </button>
        )}
      </nav>
    </div>
  );
}
