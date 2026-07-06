"use client";

import { useEffect, useMemo, useState } from "react";

interface StreamingTextProps {
  /** Full text to reveal. */
  text: string;
  /** When true, reveal token-by-token; when false, render immediately. */
  animate: boolean;
  /** Milliseconds between tokens. Default 24ms. */
  speed?: number;
  /** Fired once every token has been revealed. */
  onDone?: () => void;
  className?: string;
}

/**
 * Reveals `text` one token (word) at a time. Each newly-mounted token span
 * plays the `token-in` fade/blur animation exactly once, producing a smooth
 * streaming effect.
 */
export default function StreamingText({
  text,
  animate,
  speed = 24,
  onDone,
  className,
}: StreamingTextProps) {
  // Split into whitespace-preserving tokens so spacing survives.
  const tokens = useMemo(() => text.match(/\S+\s*/g) ?? [], [text]);
  const [count, setCount] = useState(animate ? 0 : tokens.length);

  useEffect(() => {
    if (!animate) {
      setCount(tokens.length);
      return;
    }
    setCount(0);
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setCount(i);
      if (i >= tokens.length) {
        clearInterval(id);
        onDone?.();
      }
    }, speed);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, animate, speed]);

  return (
    <span className={className}>
      {tokens.slice(0, count).map((tok, i) => (
        <span
          key={i}
          className={animate ? "inline animate-token-in" : "inline"}
        >
          {tok}
        </span>
      ))}
    </span>
  );
}
