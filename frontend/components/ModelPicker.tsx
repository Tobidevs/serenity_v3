"use client";

import { useEffect, useRef, useState } from "react";
import type { ModelOption } from "../types/chat";
import { ChevronDown } from "./icons";

interface ModelPickerProps {
  models: ModelOption[];
  value: string;
  onChange: (name: string) => void;
  /** Suffix label after the model name, e.g. "Extended". */
  mode?: string;
}

export default function ModelPicker({
  models,
  value,
  onChange,
  mode = "Extended",
}: ModelPickerProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className={`flex items-center gap-2 rounded-xl border px-3 py-1.5 text-sm transition-colors ${
          open
            ? "border-gold-dim bg-cocoa-hover text-cream"
            : "border-cocoa-border bg-cocoa-panel text-cream hover:border-gold-dim/70 hover:bg-cocoa-hover"
        }`}
      >
        <span className="font-medium">{value}</span>
        <span className="hidden text-[12.5px] font-medium tracking-wide text-gold sm:inline">
          {mode}
        </span>
        <ChevronDown
          className={`h-3.5 w-3.5 text-gold transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute bottom-[46px] right-0 min-w-[220px] rounded-2xl border border-cocoa-border bg-cocoa-panel p-1.5 shadow-premium-lg"
        >
          {models.map((m) => (
            <button
              key={m.name}
              role="option"
              aria-selected={m.name === value}
              type="button"
              onClick={() => {
                onChange(m.name);
                setOpen(false);
              }}
              className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-cocoa-hover ${
                m.name === value ? "text-cream" : "text-cream/85"
              }`}
            >
              <span className="font-medium">{m.name}</span>
              <span className="text-[12px] font-medium tracking-wide text-gold">
                {m.tag}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
