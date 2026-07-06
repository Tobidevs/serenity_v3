"use client";

import { useCallback, useState } from "react";
import type { ChatMessage, ModelOption } from "../types/chat";
import ChatHeader from "./ChatHeader";
import MessageList from "./MessageList";
import Composer from "./Composer";
import {
  DEFAULT_MODELS,
  DEMO_MESSAGES,
  defaultReply,
} from "../lib/demoConversation";

export interface ChatUIProps {
  /** Conversation title shown in the header. */
  title?: string;
  /** Seed messages. Defaults to the built-in Lisbon demo. */
  initialMessages?: ChatMessage[];
  /** Selectable models for the picker. */
  models?: ModelOption[];
  /** Initially-selected model name. */
  defaultModel?: string;
  /**
   * Produces the assistant's reply text for a given user message.
   * Defaults to a canned response. Swap this for your own generator
   * (it can be sync — the streaming animation is handled here).
   */
  generateReply?: (userText: string) => string;
  /** Fired whenever the user sends a message. */
  onSend?: (text: string) => void;
  /** Extra classes on the outer wrapper. */
  className?: string;
}

let uid = 0;
const nextId = () => `m${Date.now()}_${uid++}`;

export default function ChatUI({
  title = "Weekend trip to Lisbon",
  initialMessages = DEMO_MESSAGES,
  models = DEFAULT_MODELS,
  defaultModel = "Haiku 4.5",
  generateReply = defaultReply,
  onSend,
  className,
}: ChatUIProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [model, setModel] = useState(defaultModel);

  const handleSend = useCallback(
    (text: string) => {
      onSend?.(text);
      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        content: text,
      };
      const assistantMsg: ChatMessage = {
        id: nextId(),
        role: "assistant",
        content: generateReply(text),
        streaming: true,
      };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
    },
    [generateReply, onSend]
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
      />
    </div>
  );
}
