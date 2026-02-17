import React from "react";

interface LogoProps {
  size?: number;
  className?: string;
  showText?: boolean;
}

const Logo: React.FC<LogoProps> = ({
  size = 32,
  className = "",
  showText = false,
}) => {
  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ borderRadius: "8px", overflow: "hidden" }}
      >
        <defs>
          <linearGradient
            id="flux-grad-comp"
            x1="0%"
            y1="0%"
            x2="100%"
            y2="100%"
          >
            <stop offset="0%" stopColor="#8B5CF6" />
            <stop offset="50%" stopColor="#6366F1" />
            <stop offset="100%" stopColor="#06B6D4" />
          </linearGradient>
          <linearGradient
            id="flux-bolt-comp"
            x1="20%"
            y1="0%"
            x2="80%"
            y2="100%"
          >
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#E0E7FF" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="48" height="48" fill="url(#flux-grad-comp)" />
        <path
          d="M28.5 8L16 25.5H23L19.5 40L32 22.5H25L28.5 8Z"
          fill="url(#flux-bolt-comp)"
        />
      </svg>
      {showText && (
        <span
          className="font-bold tracking-tight"
          style={{
            fontWeight: 800,
            fontSize: "1.25rem",
            color: "var(--text-primary)",
          }}
        >
          Flux
        </span>
      )}
    </div>
  );
};

export default Logo;
