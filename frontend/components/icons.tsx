import type { SVGProps } from "react";

/** Shared props so callers can size/style consistently. */
type IconProps = SVGProps<SVGSVGElement>;

const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function ChevronDown(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={2} {...stroke} {...props}>
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

export function Share(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.8} {...stroke} {...props}>
      <path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  );
}

export function Copy(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.7} {...stroke} {...props}>
      <rect x="9" y="9" width="11" height="11" rx="2" />
      <path d="M5 15V5a2 2 0 0 1 2-2h10" />
    </svg>
  );
}

export function Play(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.7} {...stroke} {...props}>
      <polygon points="6 4 20 12 6 20 6 4" />
    </svg>
  );
}

export function ThumbsUp(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.7} {...stroke} {...props}>
      <path d="M7 10v11" />
      <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
    </svg>
  );
}

export function ThumbsDown(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.7} {...stroke} {...props}>
      <path d="M17 14V3" />
      <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z" />
    </svg>
  );
}

export function Retry(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.7} {...stroke} {...props}>
      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </svg>
  );
}

export function Plus(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.8} {...stroke} {...props}>
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

export function Mic(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.7} {...stroke} {...props}>
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M19 10a7 7 0 0 1-14 0" />
      <line x1="12" y1="17" x2="12" y2="22" />
    </svg>
  );
}

export function Sparkle(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" strokeWidth={1.8} {...stroke} {...props}>
      <path d="M12 3v2M12 19v2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M3 12h2M19 12h2M5.6 18.4 7 17M17 7l1.4-1.4" />
      <circle cx="12" cy="12" r="3.5" />
    </svg>
  );
}

/** Solid "send" bars glyph (matches the composer send button). */
export function SendBars(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <rect x="4" y="6" width="2.4" height="12" rx="1.2" />
      <rect x="8.5" y="3" width="2.4" height="18" rx="1.2" />
      <rect x="13" y="8" width="2.4" height="8" rx="1.2" />
      <rect x="17.5" y="5" width="2.4" height="14" rx="1.2" />
    </svg>
  );
}
