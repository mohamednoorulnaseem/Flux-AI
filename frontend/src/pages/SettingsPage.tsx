/**
 * Flux Settings Page — User profile and account settings.
 */
import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Settings, User, Key, Bell, Shield, Check, Copy } from "lucide-react";
import "./SettingsPage.css";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [copied, setCopied] = useState(false);

  const copyApiKey = () => {
    navigator.clipboard.writeText(
      `ck_${user?.id ?? 0}_${Date.now().toString(36)}`,
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="settings-page">
      <header className="page-header">
        <h1>
          <Settings size={24} /> Settings
        </h1>
        <p>Manage your account, API keys, and preferences.</p>
      </header>

      <div className="settings-grid">
        {/* Profile */}
        <div className="settings-card">
          <div className="settings-card-header">
            <User size={18} />
            <h3>Profile</h3>
          </div>
          <div className="settings-card-body">
            <div className="profile-avatar">
              {user?.username?.charAt(0).toUpperCase() ?? "U"}
            </div>
            <div className="setting-row">
              <label>Username</label>
              <span className="setting-val">{user?.username ?? "—"}</span>
            </div>
            <div className="setting-row">
              <label>Email</label>
              <span className="setting-val">{user?.email ?? "—"}</span>
            </div>
            <div className="setting-row">
              <label>Full Name</label>
              <span className="setting-val">
                {user?.full_name || "Not set"}
              </span>
            </div>
            <div className="setting-row">
              <label>Member Since</label>
              <span className="setting-val">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : "—"}
              </span>
            </div>
          </div>
        </div>

        {/* Subscription */}
        <div className="settings-card">
          <div className="settings-card-header">
            <Shield size={18} />
            <h3>Subscription</h3>
          </div>
          <div className="settings-card-body">
            <div className="plan-display">
              <span className="current-plan">
                {user?.plan === "free" ? "Free" : "Pro"}
              </span>
              <span className="plan-desc">
                {user?.plan === "free"
                  ? "50 reviews/month • All 5 agents"
                  : "Unlimited reviews • Priority processing"}
              </span>
            </div>
            <div className="setting-row">
              <label>Reviews Used</label>
              <span className="setting-val">
                {user?.reviews_used ?? 0} / {user?.reviews_limit ?? 50}
              </span>
            </div>
            <button className="upgrade-btn">Upgrade to Pro</button>
          </div>
        </div>

        {/* API Key */}
        <div className="settings-card">
          <div className="settings-card-header">
            <Key size={18} />
            <h3>API Access</h3>
          </div>
          <div className="settings-card-body">
            <p className="api-desc">
              Use your API key to integrate Flux into your CI/CD pipeline.
            </p>
            <div className="api-key-box">
              <code>
                ck_***_{user?.id ?? 0}...{Date.now().toString(36).slice(0, 4)}
              </code>
              <button onClick={copyApiKey} className="copy-key-btn">
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
            <p className="api-hint">
              Keep this key secret. Regenerate if compromised.
            </p>
          </div>
        </div>

        {/* Notifications */}
        <div className="settings-card">
          <div className="settings-card-header">
            <Bell size={18} />
            <h3>Notifications</h3>
          </div>
          <div className="settings-card-body">
            <div className="toggle-row">
              <div>
                <span className="toggle-label">Email Notifications</span>
                <span className="toggle-desc">
                  Get notified about review results
                </span>
              </div>
              <div className="toggle-switch">
                <div className="toggle-thumb" />
              </div>
            </div>
            <div className="toggle-row">
              <div>
                <span className="toggle-label">Weekly Report</span>
                <span className="toggle-desc">
                  Receive weekly code quality summary
                </span>
              </div>
              <div className="toggle-switch active">
                <div className="toggle-thumb" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="danger-zone">
        <h3>Danger Zone</h3>
        <div className="danger-actions">
          <button className="danger-btn" onClick={logout}>
            Log Out
          </button>
          <button className="danger-btn destructive">Delete Account</button>
        </div>
      </div>
    </div>
  );
}
