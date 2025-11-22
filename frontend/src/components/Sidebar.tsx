// frontend/src/components/Sidebar.tsx
import React from "react";
import CodexaLogo from "../assets/codexa-logo.svg";

type SidebarProps = {
  activeTab: "review" | "history" | "settings";
  onChangeTab: (tab: "review" | "history" | "settings") => void;
};

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onChangeTab }) => {
  return (
    <aside className="sidebar">
      {/* Logo block */}
      <div className="sidebar-logo">
        <div className="logo-icon">
          <img src={CodexaLogo} alt="Codexa logo" className="logo-img" />
        </div>
        <div className="logo-text">
          <span>Codexa</span>
          <small>AI Code Reviewer</small>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <button
          className={`nav-item ${activeTab === "review" ? "active" : ""}`}
          onClick={() => onChangeTab("review")}
        >
          ⚡ Review
        </button>

        <button
          className={`nav-item ${activeTab === "history" ? "active" : ""}`}
          onClick={() => onChangeTab("history")}
        >
          📜 History
        </button>

        <button
          className={`nav-item ${activeTab === "settings" ? "active" : ""}`}
          onClick={() => onChangeTab("settings")}
        >
          ⚙️ Settings
        </button>
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <span className="status-dot" />
        <span className="status-text">
          Backend: <span>local</span>
        </span>
      </div>
    </aside>
  );
};

export default Sidebar;
