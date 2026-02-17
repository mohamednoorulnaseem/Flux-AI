/**
 * Flux Analytics Page — Dashboard with stats and charts.
 */
import React, { useState, useEffect } from "react";
import { dashboardAPI } from "../services/api";
import {
  BarChart3,
  TrendingUp,
  Shield,
  Bug,
  Paintbrush,
  Zap,
  Loader2,
  AlertTriangle,
  Target,
} from "lucide-react";
import "./AnalyticsPage.css";

type Stats = {
  total_reviews: number;
  avg_score: number;
  total_issues_found: number;
  severity_breakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  score_trend: { score: number; date: string }[];
  languages: Record<string, number>;
};

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await dashboardAPI.getStats();
      setStats(res.data.stats);
      setUser(res.data.user);
    } catch {}
    setLoading(false);
  };

  const getScoreColor = (s: number) => {
    if (s >= 80) return "var(--success)";
    if (s >= 60) return "var(--warning)";
    return "var(--error)";
  };

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="loading-state">
          <Loader2 size={28} className="animate-spin" />
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  const sev = stats?.severity_breakdown || {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  const totalSev = sev.critical + sev.high + sev.medium + sev.low || 1;

  return (
    <div className="analytics-page">
      <header className="page-header">
        <h1>
          <BarChart3 size={24} /> Analytics Dashboard
        </h1>
        <p>Track your code quality trends and improvement over time.</p>
      </header>

      {/* ── KPI Cards ────────────────────────── */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div
            className="kpi-icon"
            style={{
              background: "rgba(139, 92, 246, 0.1)",
              color: "var(--accent-violet)",
            }}
          >
            <BarChart3 size={20} />
          </div>
          <div className="kpi-info">
            <span className="kpi-value">{stats?.total_reviews ?? 0}</span>
            <span className="kpi-label">Total Reviews</span>
          </div>
        </div>

        <div className="kpi-card">
          <div
            className="kpi-icon"
            style={{
              background: "rgba(34, 197, 94, 0.1)",
              color: "var(--success)",
            }}
          >
            <Target size={20} />
          </div>
          <div className="kpi-info">
            <span
              className="kpi-value"
              style={{ color: getScoreColor(stats?.avg_score ?? 0) }}
            >
              {stats?.avg_score ?? 0}
            </span>
            <span className="kpi-label">Avg. Score</span>
          </div>
        </div>

        <div className="kpi-card">
          <div
            className="kpi-icon"
            style={{
              background: "rgba(239, 68, 68, 0.1)",
              color: "var(--error)",
            }}
          >
            <AlertTriangle size={20} />
          </div>
          <div className="kpi-info">
            <span className="kpi-value">{stats?.total_issues_found ?? 0}</span>
            <span className="kpi-label">Issues Found</span>
          </div>
        </div>

        <div className="kpi-card">
          <div
            className="kpi-icon"
            style={{
              background: "rgba(6, 182, 212, 0.1)",
              color: "var(--accent-cyan)",
            }}
          >
            <TrendingUp size={20} />
          </div>
          <div className="kpi-info">
            <span className="kpi-value">
              {Object.keys(stats?.languages ?? {}).length}
            </span>
            <span className="kpi-label">Languages</span>
          </div>
        </div>
      </div>

      <div className="analytics-grid">
        {/* ── Severity Distribution ─────────── */}
        <div className="analytics-card">
          <h3>Issue Severity Distribution</h3>
          <div className="severity-bars">
            {[
              {
                label: "Critical",
                count: sev.critical,
                color: "var(--severity-critical)",
              },
              { label: "High", count: sev.high, color: "var(--severity-high)" },
              {
                label: "Medium",
                count: sev.medium,
                color: "var(--severity-medium)",
              },
              { label: "Low", count: sev.low, color: "var(--severity-low)" },
            ].map((item) => (
              <div key={item.label} className="severity-bar-row">
                <div className="sev-bar-label">
                  <span
                    className="sev-dot"
                    style={{ background: item.color }}
                  />
                  <span>{item.label}</span>
                </div>
                <div className="sev-bar-track">
                  <div
                    className="sev-bar-fill"
                    style={{
                      width: `${(item.count / totalSev) * 100}%`,
                      background: item.color,
                    }}
                  />
                </div>
                <span className="sev-bar-count">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Score Trend ──────────────────────── */}
        <div className="analytics-card">
          <h3>Recent Score Trend</h3>
          {(stats?.score_trend?.length ?? 0) > 0 ? (
            <div className="score-trend">
              {stats!.score_trend.map((item, i) => (
                <div key={i} className="trend-bar-col">
                  <div
                    className="trend-bar"
                    style={{
                      height: `${item.score}%`,
                      background: getScoreColor(item.score),
                    }}
                    title={`Score: ${item.score}`}
                  />
                  <span className="trend-label">{item.score}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-data">No data yet. Run some reviews!</div>
          )}
        </div>

        {/* ── Language Distribution ────────────── */}
        <div className="analytics-card">
          <h3>Languages Reviewed</h3>
          {Object.keys(stats?.languages ?? {}).length > 0 ? (
            <div className="lang-list">
              {Object.entries(stats!.languages)
                .sort((a, b) => b[1] - a[1])
                .map(([lang, count]) => (
                  <div key={lang} className="lang-row">
                    <span className="lang-name">{lang}</span>
                    <div className="lang-bar-track">
                      <div
                        className="lang-bar-fill"
                        style={{
                          width: `${(count / Math.max(...Object.values(stats!.languages))) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="lang-count">{count}</span>
                  </div>
                ))}
            </div>
          ) : (
            <div className="no-data">No data yet.</div>
          )}
        </div>

        {/* ── Account Info ─────────────────────── */}
        <div className="analytics-card">
          <h3>Account</h3>
          <div className="account-info">
            <div className="account-row">
              <span className="account-key">Username</span>
              <span className="account-val">{user?.username ?? "—"}</span>
            </div>
            <div className="account-row">
              <span className="account-key">Plan</span>
              <span className="account-val plan-badge-info">
                {user?.plan ?? "free"}
              </span>
            </div>
            <div className="account-row">
              <span className="account-key">Reviews Used</span>
              <span className="account-val">
                {user?.reviews_used ?? 0}/{user?.reviews_limit ?? 50}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
