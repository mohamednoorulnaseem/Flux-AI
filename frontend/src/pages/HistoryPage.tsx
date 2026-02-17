/**
 * Flux History Page — View past reviews with search and details.
 */
import React, { useState, useEffect } from "react";
import { reviewAPI } from "../services/api";
import {
  History,
  Clock,
  ChevronRight,
  Trash2,
  AlertTriangle,
  Search,
  Filter,
  Loader2,
  FileCode,
} from "lucide-react";
import "./HistoryPage.css";

type ReviewEntry = {
  id: number;
  filename: string;
  language: string;
  score: number;
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  processing_time_ms: number;
  created_at: string;
  summary: string;
};

export default function HistoryPage() {
  const [reviews, setReviews] = useState<ReviewEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<ReviewEntry | null>(null);

  useEffect(() => {
    loadReviews();
  }, []);

  const loadReviews = async () => {
    setLoading(true);
    try {
      const res = await reviewAPI.getReviews(50, 0);
      setReviews(res.data.reviews || []);
    } catch {
      // User might not be authenticated
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await reviewAPI.deleteReview(id);
      setReviews((prev) => prev.filter((r) => r.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch {}
  };

  const filtered = reviews.filter(
    (r) =>
      r.filename.toLowerCase().includes(search.toLowerCase()) ||
      r.language.toLowerCase().includes(search.toLowerCase()),
  );

  const getScoreColor = (s: number) => {
    if (s >= 80) return "var(--success)";
    if (s >= 60) return "var(--warning)";
    return "var(--error)";
  };

  const formatDate = (d: string) => {
    try {
      const date = new Date(d);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return d;
    }
  };

  return (
    <div className="history-page">
      <header className="page-header">
        <div>
          <h1>
            <History size={24} /> Review History
          </h1>
          <p>Browse and search your past code reviews.</p>
        </div>
      </header>

      <div className="history-toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            placeholder="Search by filename or language..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            id="history-search"
          />
        </div>
        <span className="result-count">{filtered.length} reviews</span>
      </div>

      {loading ? (
        <div className="loading-state">
          <Loader2 size={28} className="animate-spin" />
          <p>Loading reviews...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty-history">
          <FileCode size={48} />
          <h3>No reviews yet</h3>
          <p>Run your first code review to see it here.</p>
        </div>
      ) : (
        <div className="history-list">
          {filtered.map((review) => (
            <div
              key={review.id}
              className={`history-item ${selected?.id === review.id ? "selected" : ""}`}
              onClick={() => setSelected(review)}
            >
              <div className="history-left">
                <div
                  className="history-score"
                  style={{ color: getScoreColor(review.score) }}
                >
                  {review.score}
                </div>
                <div className="history-info">
                  <span className="history-filename">{review.filename}</span>
                  <div className="history-meta">
                    <span className="lang-tag">{review.language}</span>
                    <span className="meta-sep">•</span>
                    <span>{review.total_issues} issues</span>
                    <span className="meta-sep">•</span>
                    <Clock size={11} />
                    <span>{formatDate(review.created_at)}</span>
                  </div>
                </div>
              </div>
              <div className="history-right">
                {review.critical_count > 0 && (
                  <span className="sev-pill critical">
                    {review.critical_count} critical
                  </span>
                )}
                {review.high_count > 0 && (
                  <span className="sev-pill high">
                    {review.high_count} high
                  </span>
                )}
                <button
                  className="delete-btn"
                  onClick={(e) => handleDelete(review.id, e)}
                  title="Delete"
                >
                  <Trash2 size={14} />
                </button>
                <ChevronRight size={14} className="chevron-icon" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Panel */}
      {selected && (
        <div className="detail-panel">
          <div className="detail-header">
            <h3>{selected.filename}</h3>
            <button className="close-detail" onClick={() => setSelected(null)}>
              ×
            </button>
          </div>
          <div className="detail-body">
            <div
              className="detail-score"
              style={{ color: getScoreColor(selected.score) }}
            >
              Score: {selected.score}/100
            </div>
            <p className="detail-summary">{selected.summary}</p>
            <div className="detail-stats">
              <span>Language: {selected.language}</span>
              <span>Issues: {selected.total_issues}</span>
              <span>
                Time: {(selected.processing_time_ms / 1000).toFixed(1)}s
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
