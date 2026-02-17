/**
 * Flux Dashboard Layout — SaaS app shell with sidebar navigation.
 */
import React, { useState } from "react";
import { Outlet, useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Zap,
  History,
  BarChart3,
  Settings,
  LogOut,
  User,
  ChevronDown,
  Menu,
  X,
  Search,
  FolderDot,
} from "lucide-react";
import Logo from "../components/Logo";
import "./Dashboard.css";

type NavItem = {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "review", label: "Review", icon: <Zap size={18} />, path: "/app" },
  {
    id: "history",
    label: "History",
    icon: <History size={18} />,
    path: "/app/history",
  },
  {
    id: "analytics",
    label: "Analytics",
    icon: <BarChart3 size={18} />,
    path: "/app/analytics",
  },
  {
    id: "settings",
    label: "Settings",
    icon: <Settings size={18} />,
    path: "/app/settings",
  },
];

export default function DashboardLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const activeId =
    NAV_ITEMS.find((n) => location.pathname === n.path)?.id ??
    NAV_ITEMS.find(
      (n) => location.pathname.startsWith(n.path) && n.path !== "/app",
    )?.id ??
    "review";

  return (
    <div className="dashboard-shell">
      {/* ── Sidebar ─────────────────────────── */}
      <aside className={`dash-sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-top">
          <Link to="/" className="sidebar-brand">
            <div className="brand-logo-hex">
              <Logo size={22} />
              <div className="neural-ping" />
            </div>
            <div className="brand-info">
              <span className="brand-text">Flux</span>
              <span className="brand-tagline">Intelligence Hub</span>
            </div>
          </Link>

          <div className="project-selector-mock">
            <div className="selector-inner">
              <FolderDot size={14} className="folder-icon" />
              <span>core-engine-v2</span>
              <ChevronDown size={12} className="chevron" />
            </div>
          </div>

          <div className="sidebar-search">
            <Search size={14} className="search-icon" />
            <input placeholder="Command / Search" />
            <span className="search-kbd">⌘K</span>
          </div>

          <nav className="sidebar-nav">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                className={`nav-btn ${activeId === item.id ? "active" : ""}`}
                onClick={() => {
                  navigate(item.path);
                  setMobileOpen(false);
                }}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="sidebar-bottom">
          <div className="usage-card">
            <div className="usage-header">
              <span className="usage-label">Reviews Used</span>
              <span className="usage-count">
                {user?.reviews_used ?? 0}/{user?.reviews_limit ?? 50}
              </span>
            </div>
            <div className="usage-bar">
              <div
                className="usage-fill"
                style={{
                  width: `${Math.min(100, ((user?.reviews_used ?? 0) / (user?.reviews_limit ?? 50)) * 100)}%`,
                }}
              />
            </div>
            <span className="usage-plan">
              {user?.plan === "free" ? "Free Plan" : "Pro Plan"}
            </span>
          </div>

          <div className="user-section">
            <button
              className="user-btn"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
            >
              <div className="user-avatar">
                {user?.username?.charAt(0).toUpperCase() ?? "U"}
              </div>
              <div className="user-info">
                <span className="user-name">{user?.username ?? "User"}</span>
                <span className="user-email">{user?.email ?? ""}</span>
              </div>
              <ChevronDown
                size={14}
                className={`chevron ${userMenuOpen ? "open" : ""}`}
              />
            </button>

            {userMenuOpen && (
              <div className="user-menu">
                <button
                  onClick={() => {
                    navigate("/app/settings");
                    setUserMenuOpen(false);
                  }}
                >
                  <User size={14} /> Profile
                </button>
                <button onClick={handleLogout} className="logout-btn">
                  <LogOut size={14} /> Log Out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* ── Mobile Header ──────────────────── */}
      <div className="mobile-header">
        <button
          className="mobile-toggle"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
        <Link to="/" className="mobile-brand">
          <Logo size={18} />
          <span>Flux</span>
        </Link>
      </div>

      {/* ── Main Content ───────────────────── */}
      <main className="dash-main">
        <Outlet />
      </main>

      {/* ── Mobile Overlay ─────────────────── */}
      {mobileOpen && (
        <div className="mobile-overlay" onClick={() => setMobileOpen(false)} />
      )}
    </div>
  );
}
