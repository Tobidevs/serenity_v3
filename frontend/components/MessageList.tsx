"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types/chat";
import Message from "./Message";

interface MessageListProps {
  messages: ChatMessage[];
  onStreamDone?: (id: string) => void;
}

export default function MessageList({
  messages,
  onStreamDone,
}: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Keep the newest content in view as messages arrive / stream.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <main
      ref={scrollRef}
      className="beige-scroll flex-1 overflow-y-auto px-4 pb-10 pt-2 sm:px-6"
    >
      <div className="mx-auto max-w-[780px]">
        {messages.map((m) => (
          <Message key={m.id} message={m} onStreamDone={onStreamDone} />
        ))}
        <div ref={endRef} />
      </div>
    </main>
  );
}
