"use client";

import { useCallback, useRef, useState } from "react";
import type { ChatMessage, ModelOption } from "../types/chat";
import ChatHeader from "./ChatHeader";
import MessageList from "./MessageList";
import Composer from "./Composer";
import { invokeAgent } from "../lib/api";
import { DEFAULT_MODELS, DEMO_MESSAGES } from "../lib/demoConversation";

export interface ChatUIProps {
  /** Conversation title shown in the header. */
  title?: string;
  /** Seed messages. Defaults to the built-in Lisbon demo. */
  initialMessages?: ChatMessage[];
  /** Selectable models for the picker. */
  models?: ModelOption[];
  /** Initially-selected model name. */
  defaultModel?: string;
  /** Fired whenever the user sends a message. */
  onSend?: (text: string) => void;
  /** Extra classes on the outer wrapper. */
  className?: string;
}

const EMPTY_REPLY_FALLBACK =
  "The agent didn't return a response yet — its answer nodes aren't implemented.";

let uid = 0;
const nextId = () => `m${Date.now()}_${uid++}`;

export default function ChatUI({
  title = "Weekend trip to Lisbon",
  initialMessages = DEMO_MESSAGES,
  models = DEFAULT_MODELS,
  defaultModel = "Haiku 4.5",
  onSend,
  className,
}: ChatUIProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [model, setModel] = useState(defaultModel);
  const [sending, setSending] = useState(false);
  // Persist across turns so the backend continues the same conversation
  // (and can resume a paused clarification with the user's answer).
  const threadIdRef = useRef<string | undefined>(undefined);

  const patchMessage = useCallback(
    (id: string, patch: Partial<ChatMessage>) => {
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...patch } : m))
      );
    },
    []
  );

  const handleSend = useCallback(
    async (text: string) => {
      onSend?.(text);
      const userMsg: ChatMessage = { id: nextId(), role: "user", content: text };
      const assistantId = nextId();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        pending: true,
      };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setSending(true);

      try {
        const res = await invokeAgent(text, threadIdRef.current);
        threadIdRef.current = res.thread_id;
        patchMessage(assistantId, {
          content: res.reply || EMPTY_REPLY_FALLBACK,
          pending: false,
          streaming: true,
        });
      } catch (err) {
        patchMessage(assistantId, {
          content:
            err instanceof Error
              ? `Sorry — I couldn't reach the agent. ${err.message}`
              : "Sorry — I couldn't reach the agent.",
          pending: false,
          streaming: false,
        });
      } finally {
        setSending(false);
      }
    },
    [onSend, patchMessage]
  );

  const handleStreamDone = useCallback((id: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, streaming: false } : m))
    );
  }, []);

  return (
    <div
      className={`cocoa-vignette flex h-screen flex-col font-sans font-normal text-cream ${
        className ?? ""
      }`}
    >
      <ChatHeader title={title} />
      <MessageList messages={messages} onStreamDone={handleStreamDone} />
      <Composer
        models={models}
        model={model}
        onModelChange={setModel}
        onSend={handleSend}
        disabled={sending}
      />
    </div>
  );
}
