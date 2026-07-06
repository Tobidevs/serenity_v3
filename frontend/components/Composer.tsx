"use client";

import {
  useRef,
  useState,
  type KeyboardEvent,
  type ChangeEvent,
} from "react";
import type { ModelOption } from "../types/chat";
import ModelPicker from "./ModelPicker";
import { Mic, Plus, SendBars } from "./icons";

interface ComposerProps {
  models: ModelOption[];
  model: string;
  onModelChange: (name: string) => void;
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function Composer({
  models,
  model,
  onModelChange,
  onSend,
  disabled = false,
  placeholder = "Write a message…",
}: ComposerProps) {
  const [draft, setDraft] = useState("");
  const taRef = useRef<HTMLTextAreaElement>(null);

  const autosize = () => {
    const el = taRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  };

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(e.target.value);
    autosize();
  };

  const submit = () => {
    const text = draft.trim();
    if (!text || disabled) return;
    onSend(text);
    setDraft("");
    if (taRef.current) taRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <footer className="shrink-0 px-4 pb-4 sm:px-6">
      <div className="mx-auto max-w-[780px]">
        <div className="rounded-3xl border border-cocoa-border bg-cocoa-elevated p-4 shadow-premium-md shadow-inner-top transition-shadow duration-200 focus-within:border-gold-dim/70 focus-within:shadow-premium-lg">
          <textarea
            ref={taRef}
            rows={1}
            value={draft}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="max-h-[180px] w-full resize-none bg-transparent text-[15.5px] font-normal leading-relaxed text-cream outline-none placeholder:text-faint"
          />

          <div className="mt-3 flex items-center justify-between">
            <button
              type="button"
              title="Add"
              className="flex h-[34px] w-[34px] items-center justify-center rounded-full border border-cocoa-border text-gold transition-colors hover:border-gold-dim hover:bg-cocoa-hover hover:text-gold-bright"
            >
              <Plus className="h-[18px] w-[18px]" />
            </button>

            <div className="flex items-center gap-2">
              <ModelPicker
                models={models}
                value={model}
                onChange={onModelChange}
              />

              <button
                type="button"
                title="Dictate"
                className="flex h-9 w-9 items-center justify-center rounded-lg text-gold transition-colors hover:bg-cocoa-hover hover:text-gold-bright"
              >
                <Mic className="h-[19px] w-[19px]" />
              </button>

              <button
                type="button"
                title="Send"
                onClick={submit}
                disabled={disabled}
                className="flex h-[38px] w-[38px] items-center justify-center rounded-[10px] bg-gold text-cocoa shadow-premium-sm transition-all duration-150 hover:bg-gold-bright hover:shadow-premium-md active:scale-95 disabled:opacity-40 disabled:shadow-none"
              >
                <SendBars className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        <p className="mt-3 text-center text-[12px] tracking-wide text-faint">
          Claude is AI and can make mistakes. Please double-check responses.
        </p>
      </div>
    </footer>
  );
}
