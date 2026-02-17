/**
 * Flux Landing Page — Qodo-inspired premium SaaS marketing page.
 *
 * Design language inspired by qodo.ai:
 *  • Bold confidence-driven headline
 *  • Dot-grid background with gradient glows
 *  • Section-per-feature with sub-label + headline + description
 *  • "How It Works" 3-step flow
 *  • Value pillars (Cleaner / Smarter / Consistent)
 *  • Enterprise trust signals
 *  • Pricing grid with highlighted Pro tier
 */
import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Shield,
  Zap,
  Bug,
  Paintbrush,
  Wrench,
  ArrowRight,
  ChevronRight,
  Code2,
  Layers,
  BarChart3,
  Lock,
  Cpu,
  Eye,
  Sparkles,
  Check,
  GitPullRequest,
  Terminal,
  FileSearch,
  Target,
  Award,
  CheckCircle2,
} from "lucide-react";
import Logo from "../components/Logo";
import "./Landing.css";

// ─── Data ──────────────────────────────────────────────

const AGENTS = [
  {
    icon: <Shield size={26} />,
    name: "Security Scan",
    desc: "Detects SQL injection, XSS, hardcoded secrets, SSRF, and 50+ vulnerability patterns with CWE references.",
    color: "#ef4444",
    tag: "SECURITY",
  },
  {
    icon: <Zap size={26} />,
    name: "Performance Analysis",
    desc: "Identifies O(n²) algorithms, memory leaks, N+1 queries, blocking ops, and missing caching.",
    color: "#f59e0b",
    tag: "PERFORMANCE",
  },
  {
    icon: <Paintbrush size={26} />,
    name: "Style & Readability",
    desc: "Enforces naming conventions, DRY principles, type safety, and language-specific best practices.",
    color: "#8b5cf6",
    tag: "QUALITY",
  },
  {
    icon: <Bug size={26} />,
    name: "Bug Detection",
    desc: "Hunts logic errors, off-by-one bugs, null references, race conditions — generates test cases.",
    color: "#06b6d4",
    tag: "RELIABILITY",
  },
  {
    icon: <Wrench size={26} />,
    name: "Auto-Fix Generation",
    desc: "Generates production-ready corrected code with all fixes applied. One-click to apply changes.",
    color: "#22c55e",
    tag: "AUTO-FIX",
  },
  {
    icon: <Layers size={26} />,
    name: "Orchestrator",
    desc: "Master agent coordinating the pipeline — parallel execution, weighted scoring, unified report.",
    color: "#ec4899",
    tag: "ENGINE",
  },
];

const VALUE_PILLARS = [
  {
    icon: <Target size={24} />,
    title: "High-Signal Issue Finding",
    desc: "Context-aware analysis that detects real issues, logic gaps, and security flaws — not noise.",
    color: "#8b5cf6",
  },
  {
    icon: <Zap size={24} />,
    title: "Instant Code Reviews",
    desc: "5 agents run in parallel. Get comprehensive results in under 10 seconds, not hours.",
    color: "#f59e0b",
  },
  {
    icon: <CheckCircle2 size={24} />,
    title: "Production-Ready Fixes",
    desc: "Auto-generated fixes with line-by-line diffs. Review, apply, and ship with confidence.",
    color: "#22c55e",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    icon: <Terminal size={28} />,
    title: "Paste Your Code",
    desc: "Drop code into the Monaco editor or connect your GitHub repo. Select your language.",
    color: "#8b5cf6",
  },
  {
    step: "02",
    icon: <FileSearch size={28} />,
    title: "AI Agents Analyze",
    desc: "5 specialized agents scan your code simultaneously — security, performance, style, bugs, and fixes.",
    color: "#06b6d4",
  },
  {
    step: "03",
    icon: <Award size={28} />,
    title: "Review & Ship",
    desc: "Get a scored report with letter grades, inline annotations, quick wins, and one-click auto-fix.",
    color: "#22c55e",
  },
];

const FEATURES = [
  {
    icon: <Code2 size={20} />,
    title: "Multi-Language",
    desc: "Python, JS, TS, Java, C++, Go, Rust",
  },
  {
    icon: <BarChart3 size={20} />,
    title: "Analytics Dashboard",
    desc: "Track quality trends and patterns",
  },
  {
    icon: <Lock size={20} />,
    title: "Secure by Design",
    desc: "JWT auth, encrypted, no code stored",
  },
  {
    icon: <GitPullRequest size={20} />,
    title: "GitHub Ready",
    desc: "PR webhooks (coming soon)",
  },
  {
    icon: <Cpu size={20} />,
    title: "Parallel Pipeline",
    desc: "4 agents run simultaneously",
  },
  {
    icon: <Eye size={20} />,
    title: "Line-by-Line",
    desc: "Monaco editor with inline markers",
  },
];

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: [
      "50 reviews/month",
      "All 5 agents",
      "Auto-fix generation",
      "Review history",
      "Community support",
    ],
    cta: "Get Started Free",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$19",
    period: "/month",
    features: [
      "Unlimited reviews",
      "Priority processing",
      "GitHub PR integration",
      "Export reports",
      "API access",
      "Email support",
    ],
    cta: "Start Pro Trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    features: [
      "Everything in Pro",
      "SSO & team management",
      "Self-hosted option",
      "Custom agents",
      "SLA guarantee",
      "Dedicated support",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

// ─── Component ─────────────────────────────────────────

export default function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handler = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const goApp = () => navigate(isAuthenticated ? "/app" : "/signup");

  return (
    <div className="landing">
      {/* ━━ Navbar ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <nav className={`landing-nav ${scrollY > 50 ? "scrolled" : ""}`}>
        <div className="nav-inner">
          <Link to="/" className="nav-brand">
            <Logo size={24} />
            <span className="brand-text">Flux</span>
          </Link>
          <div className="nav-links">
            <a href="#agents">Agents</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
          </div>
          <div className="nav-actions">
            {isAuthenticated ? (
              <button className="btn-primary" onClick={() => navigate("/app")}>
                Open Dashboard <ArrowRight size={16} />
              </button>
            ) : (
              <>
                <Link to="/login" className="btn-ghost">
                  Log In
                </Link>
                <Link to="/signup" className="btn-primary">
                  Get Started <ArrowRight size={16} />
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ━━ Hero ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="hero">
        <div className="hero-dot-grid" />
        <div className="hero-gradient-orb hero-orb-1" />
        <div className="hero-gradient-orb hero-orb-2" />

        <div className="hero-content">
          <div className="hero-badge">
            <Sparkles size={14} />
            <span>Powered by 5 Specialized AI Agents</span>
          </div>

          <h1 className="hero-title">
            AI Code Review.
            <br />
            <span className="gradient-text">Ship with Confidence.</span>
          </h1>

          <p className="hero-subtitle">
            Flux delivers context-aware AI code review for complex codebases.
            Detect real issues, generate fixes, and standardize quality — in
            seconds.
          </p>

          <div className="hero-actions">
            <button className="btn-primary btn-lg" onClick={goApp}>
              <Sparkles size={18} />
              Start Free Review
            </button>
            <button
              className="btn-outline btn-lg"
              onClick={() => navigate(isAuthenticated ? "/app" : "/login")}
            >
              <Eye size={18} />
              See It In Action
            </button>
          </div>

          <div className="hero-stats">
            <div className="hero-stat">
              <span className="stat-value">5</span>
              <span className="stat-label">AI Agents</span>
            </div>
            <div className="stat-divider" />
            <div className="hero-stat">
              <span className="stat-value">&lt;10s</span>
              <span className="stat-label">Avg Review</span>
            </div>
            <div className="stat-divider" />
            <div className="hero-stat">
              <span className="stat-value">50+</span>
              <span className="stat-label">Issue Patterns</span>
            </div>
            <div className="stat-divider" />
            <div className="hero-stat">
              <span className="stat-value">A+</span>
              <span className="stat-label">Grade System</span>
            </div>
          </div>
        </div>

        {/* Pipeline Visual */}
        <div className="hero-visual">
          <div className="pipeline-demo">
            <div className="pipeline-node pipeline-input">
              <Code2 size={20} />
              <span>Your Code</span>
            </div>
            <div className="pipeline-connector">
              <ChevronRight size={16} />
            </div>
            <div className="pipeline-agents-row">
              {["🔐", "⚡", "🎨", "🐛"].map((emoji, i) => (
                <div
                  key={i}
                  className="pipeline-agent-node"
                  style={{ animationDelay: `${i * 0.15}s` }}
                >
                  {emoji}
                </div>
              ))}
            </div>
            <div className="pipeline-connector">
              <ChevronRight size={16} />
            </div>
            <div className="pipeline-node pipeline-output">
              <span>🔧</span>
              <span>Fixed Code + Report</span>
            </div>
          </div>
        </div>
      </section>

      {/* ━━ Tagline Banner ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="tagline-section">
        <div className="tagline-inner">
          <p className="tagline-text">
            Between <span className="tagline-em">"AI wrote it"</span> and{" "}
            <span className="tagline-em">"production-ready"</span>, there's{" "}
            <span className="tagline-brand gradient-text">Flux</span>.
          </p>
        </div>
      </section>

      {/* ━━ Value Pillars ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="section">
        <div className="section-inner">
          <div className="pillars-grid">
            {VALUE_PILLARS.map((pillar, i) => (
              <div className="pillar-card" key={i}>
                <div
                  className="pillar-icon"
                  style={{
                    background: `${pillar.color}15`,
                    color: pillar.color,
                  }}
                >
                  {pillar.icon}
                </div>
                <h3>{pillar.title}</h3>
                <p>{pillar.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Agents ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="section section-alt" id="agents">
        <div className="section-inner">
          <div className="section-header">
            <span className="section-tag">MULTI-AGENT PIPELINE</span>
            <h2>
              The Most Advanced Code Review
              <br />
              for{" "}
              <span className="gradient-text">High-Signal Issue Finding</span>
            </h2>
            <p>
              Each agent is an expert in its domain. They run in parallel and
              produce a unified, scored report.
            </p>
          </div>
          <div className="agents-grid">
            {AGENTS.map((agent, i) => (
              <div
                className="agent-card"
                key={i}
                style={{ "--agent-color": agent.color } as React.CSSProperties}
              >
                <div className="agent-card-top">
                  <span
                    className="agent-tag"
                    style={{
                      color: agent.color,
                      borderColor: `${agent.color}40`,
                    }}
                  >
                    {agent.tag}
                  </span>
                </div>
                <div className="agent-icon-wrap">{agent.icon}</div>
                <h3>{agent.name}</h3>
                <p>{agent.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ How It Works ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="section" id="how-it-works">
        <div className="section-inner">
          <div className="section-header">
            <span className="section-tag">HOW IT WORKS</span>
            <h2>
              Review as you write. Fix as you go.
              <br />
              <span className="gradient-text">Ship with confidence.</span>
            </h2>
          </div>
          <div className="steps-grid">
            {HOW_IT_WORKS.map((step, i) => (
              <div className="step-card" key={i}>
                <div className="step-number" style={{ color: step.color }}>
                  {step.step}
                </div>
                <div
                  className="step-icon-wrap"
                  style={{ background: `${step.color}12`, color: step.color }}
                >
                  {step.icon}
                </div>
                <h3>{step.title}</h3>
                <p>{step.desc}</p>
                {i < HOW_IT_WORKS.length - 1 && (
                  <div className="step-connector">
                    <ArrowRight size={18} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Features ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="section section-alt" id="features">
        <div className="section-inner">
          <div className="section-header">
            <span className="section-tag">PLATFORM CAPABILITIES</span>
            <h2>
              Built for{" "}
              <span className="gradient-text">Modern Engineering Teams</span>
            </h2>
            <p>
              Everything you need for production-grade code quality, all in one
              platform.
            </p>
          </div>
          <div className="features-grid">
            {FEATURES.map((feat, i) => (
              <div className="feature-card" key={i}>
                <div className="feature-icon">{feat.icon}</div>
                <div className="feature-info">
                  <h4>{feat.title}</h4>
                  <p>{feat.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Pricing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="section" id="pricing">
        <div className="section-inner">
          <div className="section-header">
            <span className="section-tag">PRICING</span>
            <h2>
              Simple, <span className="gradient-text">Transparent Pricing</span>
            </h2>
            <p>Start free. Upgrade when you need more power.</p>
          </div>
          <div className="pricing-grid">
            {PLANS.map((plan, i) => (
              <div
                className={`plan-card ${plan.highlighted ? "highlighted" : ""}`}
                key={i}
              >
                {plan.highlighted && (
                  <div className="plan-badge">Most Popular</div>
                )}
                <h3>{plan.name}</h3>
                <div className="plan-price">
                  <span className="price">{plan.price}</span>
                  <span className="period">{plan.period}</span>
                </div>
                <ul className="plan-features">
                  {plan.features.map((f, j) => (
                    <li key={j}>
                      <Check size={16} /> {f}
                    </li>
                  ))}
                </ul>
                <button
                  className={
                    plan.highlighted
                      ? "btn-primary btn-full"
                      : "btn-outline btn-full"
                  }
                  onClick={() => navigate("/signup")}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ━━ Final CTA ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <section className="cta-section">
        <div className="cta-glow" />
        <div className="cta-inner">
          <h2>
            Ready to ship <span className="gradient-text">better code</span>?
          </h2>
          <p>
            Join developers who use Flux to catch bugs, fix vulnerabilities, and
            improve code quality — automatically.
          </p>
          <button
            className="btn-primary btn-lg"
            onClick={() => navigate("/signup")}
          >
            <Sparkles size={18} /> Get Started Free
          </button>
        </div>
      </section>

      {/* ━━ Footer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Logo size={20} />
            <span>Flux</span>
          </div>
          <p className="footer-copy">
            Built by <strong>Mohamed Noorul Naseem</strong> • AI & Backend
            Engineering Enthusiast
          </p>
          <p className="footer-copy">© 2026 Flux. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
