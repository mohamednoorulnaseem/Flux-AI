/**
 * Flux API Service — Centralized API client for the SaaS platform.
 * Includes standard REST + SSE streaming for real-time review progress.
 */
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("Flux_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("Flux_token");
      localStorage.removeItem("Flux_user");
    }
    return Promise.reject(err);
  },
);

// ─── Auth ────────────────────────────────────────────────

export const authAPI = {
  signup: (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => api.post("/api/auth/signup", data),

  login: (data: { email: string; password: string }) =>
    api.post("/api/auth/login", data),

  getMe: () => api.get("/api/auth/me"),
};

// ─── Types ───────────────────────────────────────────────

export type ReviewRequest = {
  filename?: string;
  language: string;
  code: string;
  project_id?: number;
};

export type Issue = {
  line: number;
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  type: string;
  description: string;
  suggestion: string;
  impact?: string;
};

export type AgentResult = {
  score: number;
  summary: string;
  duration_ms: number;
  [key: string]: any;
};

export type ReviewMetrics = {
  security: number;
  performance: number;
  maintainability: number;
  readability: number;
};

export type ReviewResult = {
  id?: number;
  issues: Issue[];
  summary: string;
  score: number;
  grade: string;
  fixed_code: string;
  changes_made: { line: number; type: string; description: string }[];
  agent_results: {
    security: AgentResult;
    performance: AgentResult;
    style: AgentResult;
    bugs: AgentResult;
    autofix: AgentResult;
  };
  metrics: ReviewMetrics;
  quick_wins: string[];
  metadata: {
    total_issues: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    processing_time_ms: number;
    agents_used: number;
  };
};

// ─── SSE Agent Events ────────────────────────────────────

export type AgentEvent = {
  agent: string;
  status: "started" | "running" | "completed" | "failed" | "merging";
  data: {
    label?: string;
    phase?: string;
    total_agents?: number;
    duration_ms?: number;
    error?: string;
    total_time_ms?: number;
    [key: string]: any;
  };
  timestamp: number;
};

export type SSECallbacks = {
  onAgentEvent: (event: AgentEvent) => void;
  onResult: (result: ReviewResult) => void;
  onError: (message: string) => void;
};

// ─── Reviews ─────────────────────────────────────────────

export const reviewAPI = {
  /** Standard JSON review (blocks until complete) */
  runReview: (data: ReviewRequest) =>
    api.post<ReviewResult>("/api/review", data),

  /**
   * Stream review via SSE — real-time agent progress.
   * Returns an AbortController so the caller can cancel.
   */
  runReviewStream: (
    data: ReviewRequest,
    callbacks: SSECallbacks,
  ): AbortController => {
    const controller = new AbortController();
    const token = localStorage.getItem("Flux_token");

    fetch(`${API_BASE}/api/review/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.text();
          throw new Error(body || `HTTP ${response.status}`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEventType = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const dataStr = line.slice(6);
              try {
                const payload = JSON.parse(dataStr);

                if (currentEventType === "result") {
                  callbacks.onResult(payload as ReviewResult);
                } else if (currentEventType === "error") {
                  callbacks.onError(payload.message || "Unknown error");
                } else if (currentEventType === "timeout") {
                  callbacks.onError("Review timed out. Please try again.");
                } else {
                  // Agent progress events
                  callbacks.onAgentEvent(payload as AgentEvent);
                }
              } catch {
                // Skip malformed JSON
              }
              currentEventType = "";
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          callbacks.onError(err.message || "Connection failed");
        }
      });

    return controller;
  },

  getReviews: (limit = 20, offset = 0) =>
    api.get(`/api/reviews?limit=${limit}&offset=${offset}`),

  getReview: (id: number) => api.get(`/api/reviews/${id}`),

  deleteReview: (id: number) => api.delete(`/api/reviews/${id}`),
};

// ─── Dashboard ───────────────────────────────────────────

export const dashboardAPI = {
  getStats: () => api.get("/api/dashboard"),
};

// ─── Health ──────────────────────────────────────────────

export const healthAPI = {
  check: () => api.get("/health"),
};

export default api;
