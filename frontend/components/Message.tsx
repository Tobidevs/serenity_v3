"use client";

import type { ChatMessage } from "../types/chat";
import StreamingText from "./StreamingText";
import { Copy, Play, Retry, Sparkle, ThumbsDown, ThumbsUp } from "./icons";

interface MessageProps {
  message: ChatMessage;
  /** Fired when a streaming assistant message finishes revealing. */
  onStreamDone?: (id: string) => void;
}

const actionButtons = [
  { key: "copy", label: "Copy", Icon: Copy },
  { key: "play", label: "Play", Icon: Play },
  { key: "up", label: "Good response", Icon: ThumbsUp },
  { key: "down", label: "Bad response", Icon: ThumbsDown },
  { key: "retry", label: "Retry", Icon: Retry },
] as const;

export default function Message({ message, onStreamDone }: MessageProps) {
  if (message.role === "user") {
    return (
      <div className="my-6 flex justify-end sm:my-10">
        <div className="max-w-[88%] whitespace-pre-wrap rounded-[18px] border border-cocoa-bubble-border bg-cocoa-bubble px-5 py-4 text-[16.5px] font-normal leading-[1.6] text-cream shadow-premium-sm">
          {message.content}
        </div>
      </div>
    );
  }

  // Assistant
  return (
    <div className="group/msg mb-2">
      {message.summary && (
        <div className="mb-4 inline-flex items-center gap-1.5 rounded-full bg-gold-deep/40 px-2.5 py-1 text-[12.5px] font-medium tracking-wide text-gold-bright">
          <Sparkle className="h-[13px] w-[13px]" />
          {message.summary}
        </div>
      )}

      <div className="font-serif text-[17px] font-normal leading-[1.68] tracking-[-0.003em] text-cream/95 sm:text-[18.5px]">
        {message.node ? (
          message.node
        ) : (
          <p className="m-0">
            <StreamingText
              text={message.content}
              animate={!!message.streaming}
              onDone={() => onStreamDone?.(message.id)}
            />
          </p>
        )}
      </div>

      {!message.streaming && (
        <div className="mt-4 flex items-center gap-0.5 text-muted opacity-70 transition-opacity duration-200 group-hover/msg:opacity-100">
          {actionButtons.map(({ key, label, Icon }, i) => (
            <button
              key={key}
              type="button"
              title={label}
              className={`flex h-[32px] w-[32px] items-center justify-center rounded-md text-inherit transition-colors hover:bg-cocoa-hover hover:text-gold-bright ${
                i === actionButtons.length - 1 ? "ml-1.5 border-l border-cocoa-border/70 pl-0" : ""
              }`}
            >
              <Icon className="h-[16px] w-[16px]" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
