/**
 * ReviewPage — Advanced AI Code Review Workbench
 * Redesigned for premium 'Flux' aesthetic inspired by Qodo & CodeRabbit.
 */
import { useState, useRef, useCallback, useEffect } from "react";
import Editor, { type OnMount, DiffEditor } from "@monaco-editor/react";
import { motion } from "framer-motion";
import {
  Play,
  Loader2,
  Shield,
  Bug,
  Zap,
  Paintbrush,
  Wrench,
  Check,
  FileCode,
  Sparkles,
  Terminal,
  MessageSquare,
  Send,
  HelpCircle,
  FileText,
  BarChart3,
} from "lucide-react";
import { reviewAPI, type ReviewResult, type AgentEvent } from "../services/api";
import "./ReviewPage.css";

// ─── Constants ─────────────────────────────────────────

const LANGUAGE_OPTIONS = [
  { value: "python", label: "Python", ext: "py" },
  { value: "javascript", label: "JS", ext: "js" },
  { value: "typescript", label: "TS", ext: "ts" },
  { value: "java", label: "Java", ext: "java" },
  { value: "go", label: "Go", ext: "go" },
];

const TEMPLATES: Record<string, string> = {
  python: `def calculate_score(user_id, raw_data):
    # Potential SQL Injection
    db.execute("SELECT * FROM users WHERE id = " + user_id)
    
    # Performance: O(n^2) loop
    results = []
    for item in raw_data:
        for other in raw_data:
            if item == other: results.append(item)
            
    # Hardcoded Secret
    API_KEY = "sk-1234567890abcdef"
    return results`,
  javascript: `async function fetchData(url) {
    const res = await fetch(url);
    const data = res.json(); // Missing await
    
    // Dangerous eval
    eval(data.input);
    
    if (data == null) { // Weak comparison
      return "none";
    }
  }`,
};

const AGENT_CONFIG = [
  { key: "security", icon: Shield, color: "#ef4444", label: "Security" },
  { key: "performance", icon: Zap, color: "#f59e0b", label: "Performance" },
  { key: "style", icon: Paintbrush, color: "#8b5cf6", label: "Style" },
  { key: "bugs", icon: Bug, color: "#06b6d4", label: "Bugs" },
  { key: "autofix", icon: Wrench, color: "#22c55e", label: "Fixer" },
];

// ─── Sub-Components ───────────────────────────────────

function GaugeScore({ score, grade }: { score: number; grade: string }) {
  const [displayScore, setDisplayScore] = useState(0);
  const circumference = 2 * Math.PI * 46;
  const offset = circumference - (displayScore / 100) * circumference;

  useEffect(() => {
    const timer = setTimeout(() => setDisplayScore(score), 500);
    return () => clearTimeout(timer);
  }, [score]);

  return (
    <div className="shield-gauge">
      <svg width="120" height="120" viewBox="0 0 120 120" className="gauge-svg">
        <circle cx="60" cy="60" r="46" className="gauge-bg" />
        <circle
          cx="60"
          cy="60"
          r="46"
          className="gauge-fill"
          stroke="url(#gauge-gradient)"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
        <defs>
          <linearGradient
            id="gauge-gradient"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="100%"
          >
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>
      </svg>
      <div className="gauge-center">
        <motion.span
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="grade-symbol"
        >
          {grade}
        </motion.span>
        <span className="score-value">{displayScore}/100</span>
      </div>
    </div>
  );
}

// ─── Main ReviewPage Component ─────────────────────────

export default function ReviewPage() {
  const [code, setCode] = useState(TEMPLATES.python);
  const [language, setLanguage] = useState("python");
  const [filename, setFilename] = useState("analysis.py");
  const [reviewing, setReviewing] = useState(false);
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [agentStates, setAgentStates] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState("walkthrough");
  const [showDiff, setShowDiff] = useState(false);
  const [chatMessage, setChatMessage] = useState("");

  const editorRef = useRef<any>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleEditorMount: OnMount = (editor, monaco) => {
    editorRef.current = { editor, monaco };
    monaco.editor.setTheme("flux-dark");
  };

  const handleReview = useCallback(() => {
    if (!code.trim() || reviewing) return;
    setReviewing(true);
    setResult(null);
    setAgentStates({});
    setShowDiff(false);

    abortRef.current = reviewAPI.runReviewStream(
      { filename, language, code },
      {
        onAgentEvent: (event: AgentEvent) => {
          setAgentStates((prev) => ({ ...prev, [event.agent]: event.status }));
        },
        onResult: (data: ReviewResult) => {
          setResult(data);
          setReviewing(false);
        },
        onError: (msg) => {
          console.error(msg);
          setReviewing(false);
        },
      },
    );
  }, [code, language, filename, reviewing]);

  return (
    <div className="review-page">
      {/* ━━ Workbench Toolbar ━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <header className="review-toolbar">
        <div className="toolbar-left">
          <div className="filename-pill">
            <FileCode size={14} />
            <input
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              spellCheck={false}
            />
          </div>
          <div className="lang-selector">
            {LANGUAGE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className={`lang-btn ${language === opt.value ? "active" : ""}`}
                onClick={() => {
                  setLanguage(opt.value);
                  setFilename(`analysis.${opt.ext}`);
                  setCode(TEMPLATES[opt.value] || "");
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <div className="toolbar-right">
          <button
            className={`review-btn ${reviewing ? "loading" : ""}`}
            onClick={handleReview}
            disabled={reviewing}
          >
            {reviewing ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Play size={16} />
            )}
            <span>{reviewing ? "Analyzing..." : "Run Review"}</span>
          </button>
        </div>
      </header>

      {/* ━━ Workbench Main Area ━━━━━━━━━━━━━━━━━━━━━━ */}
      <div className="review-grid">
        {/* Left: Code Editor Container */}
        <section className="editor-canvas">
          <div className="editor-header">
            <Terminal size={12} style={{ marginRight: "8px" }} />
            SOURCE_CODE.RAW
            {reviewing && <motion.div className="scan-line" layoutId="scan" />}
          </div>
          <div className="editor-main">
            {showDiff && result?.fixed_code ? (
              <DiffEditor
                height="100%"
                original={code}
                modified={result.fixed_code}
                language={language}
                theme="flux-dark"
                options={{ fontSize: 13, minimap: { enabled: false } }}
              />
            ) : (
              <Editor
                height="100%"
                language={language}
                value={code}
                theme="flux-dark"
                onMount={handleEditorMount}
                onChange={(val) => setCode(val || "")}
                options={{
                  fontSize: 14,
                  fontFamily: "'JetBrains Mono', monospace",
                  lineHeight: 1.6,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  cursorBlinking: "smooth",
                  cursorSmoothCaretAnimation: "on",
                  padding: { top: 20 },
                  readOnly: reviewing,
                }}
              />
            )}
          </div>
        </section>

        {/* Right: Insights Sidecar */}
        <aside className="insights-sidecar">
          <div className="insights-content">
            {/* Pipeline Stream */}
            <div className="agent-stream">
              <div className="agent-stream-header">
                <div
                  className="neural-pulse-loader"
                  style={{ width: 12, height: 12 }}
                />
                <span className="agent-stream-title">Pipeline Monitor</span>
              </div>
              <div className="agent-pipeline-horizontal">
                {AGENT_CONFIG.map((agent) => (
                  <div
                    key={agent.key}
                    className={`agent-mini-card ${agentStates[agent.key] || "idle"}`}
                    title={agent.label}
                  >
                    <agent.icon
                      size={16}
                      color={
                        agentStates[agent.key] === "completed"
                          ? "#22c55e"
                          : "#64748b"
                      }
                    />
                  </div>
                ))}
              </div>
            </div>

            {result ? (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="insights-stack"
              >
                <div className="analysis-shield">
                  <GaugeScore score={result.score} grade={result.grade} />
                  <p
                    className="summary-text"
                    style={{
                      marginTop: "16px",
                      fontSize: "12px",
                      textAlign: "center",
                    }}
                  >
                    {result.summary}
                  </p>
                </div>

                <div className="insights-tabs">
                  <button
                    className={activeTab === "walkthrough" ? "active" : ""}
                    onClick={() => setActiveTab("walkthrough")}
                  >
                    <FileText size={14} /> Walkthrough
                  </button>
                  <button
                    className={activeTab === "insights" ? "active" : ""}
                    onClick={() => setActiveTab("insights")}
                  >
                    <BarChart3 size={14} /> Issues ({result.issues.length})
                  </button>
                  <button
                    className={activeTab === "diff" ? "active" : ""}
                    onClick={() => {
                      setShowDiff(true);
                      setActiveTab("diff");
                    }}
                  >
                    <Wrench size={14} /> Auto-Fix
                  </button>
                </div>

                <div className="insights-scroll-area">
                  {activeTab === "walkthrough" && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="walkthrough-view"
                    >
                      <div className="walkthrough-header">
                        <Sparkles size={16} className="text-accent" />
                        <h4>Strategic Summary</h4>
                      </div>
                      <p className="summary-p">{result.summary}</p>

                      <div className="walkthrough-categories">
                        {["security", "performance", "style"].map((cat) => {
                          const count = result.issues.filter(
                            (i) => i.category === cat,
                          ).length;
                          if (count === 0) return null;
                          return (
                            <div key={cat} className="walkthrough-cat-item">
                              <div className="cat-bullet" />
                              <span className="cat-name">{cat}</span>
                              <span className="cat-count">
                                {count} findings
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}

                  {activeTab === "insights" && (
                    <div className="insights-scroll">
                      {result.issues.map((issue, idx) => (
                        <motion.div
                          key={idx}
                          className={`insight-card severity-${issue.severity}`}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                        >
                          <div
                            className="discovery-avatar"
                            style={{
                              background:
                                AGENT_CONFIG.find(
                                  (a) => a.key === issue.category,
                                )?.color ?? "var(--accent-violet)",
                            }}
                          >
                            {(() => {
                              const Icon = AGENT_CONFIG.find(
                                (a) => a.key === issue.category,
                              )?.icon;
                              return Icon ? (
                                <Icon size={10} color="white" />
                              ) : null;
                            })()}
                          </div>
                          <div className="insight-header">
                            <span
                              className={`insight-severity sev-${issue.severity}`}
                            >
                              {issue.severity}
                            </span>
                            <span className="line-tag">Line {issue.line}</span>
                          </div>
                          <p className="insight-description">
                            {issue.description}
                          </p>
                        </motion.div>
                      ))}
                    </div>
                  )}

                  {activeTab === "diff" && (
                    <div className="diff-view-controls">
                      <div className="diff-card">
                        <p>
                          We've generated an optimized version of your code.
                          Review the changes and click apply to update your
                          editor.
                        </p>
                      </div>
                      <button
                        className="apply-btn"
                        onClick={() => {
                          setCode(result.fixed_code);
                          setShowDiff(false);
                          setActiveTab("walkthrough");
                        }}
                      >
                        <Check size={16} /> Apply All Fixes
                      </button>
                    </div>
                  )}
                </div>

                {/* AI Assistant Chat Box (Qodo/CodeRabbit Pattern) */}
                <div className="insight-chat-box">
                  <div className="chat-header">
                    <MessageSquare size={14} />
                    <span>Ask Flux Assistant</span>
                    <HelpCircle size={12} className="ml-auto opacity-50" />
                  </div>
                  <div className="chat-input-wrapper">
                    <input
                      placeholder="Ask about these changes..."
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && setChatMessage("")}
                    />
                    <button className="chat-send-btn">
                      <Send size={14} />
                    </button>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="workbench-empty">
                {reviewing ? (
                  <div className="analyzing-state">
                    <div className="neural-pulse-loader" />
                    <p style={{ marginTop: "20px" }}>Agents are thinking...</p>
                  </div>
                ) : (
                  <>
                    <Sparkles size={48} />
                    <p>Paste code and run review to get insights</p>
                  </>
                )}
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
