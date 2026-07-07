import type { ReactNode } from "react";

export type Role = "user" | "assistant";

export interface ModelOption {
  /** Display name, e.g. "Haiku 4.5" */
  name: string;
  /** Short qualifier shown to the right, e.g. "Fastest" */
  tag: string;
}

export interface ChatMessage {
  id: string;
  role: Role;
  /** Plain-text content. Used for streaming and for user bubbles. */
  content: string;
  /** When true, the assistant text reveals token-by-token with a fade. */
  streaming?: boolean;
  /** When true, the assistant reply is still being fetched — show a typing indicator. */
  pending?: boolean;
  /**
   * Optional pre-rendered rich content (lists, headings, emphasis).
   * When present it is rendered as-is instead of `content` and is NOT
   * streamed — use it for seeded/example assistant messages.
   */
  node?: ReactNode;
  /** Optional label above an assistant reply, e.g. a tool/thinking summary. */
  summary?: string;
}
