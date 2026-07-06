# Beige Claude UI — Next.js component

A production-ready, TypeScript + Tailwind recreation of the beige/cocoa Claude
chat interface, with token-by-token streaming (fade + de-blur) for assistant
replies.

## Files

```
app/
  layout.tsx          Root layout — loads Source Serif 4 via next/font
  page.tsx            Demo usage (<ChatUI />)
  fonts.ts            next/font setup (--font-serif variable)
  globals.css         Tailwind directives + custom scrollbar
components/
  ChatUI.tsx          Main orchestrator (state, send, streaming lifecycle)
  ChatHeader.tsx      Title + share
  MessageList.tsx     Scroll container + autoscroll
  Message.tsx         User bubble / assistant prose + action row
  Composer.tsx        Textarea, autosize, model picker, send
  ModelPicker.tsx     Model dropdown (outside-click / Esc close)
  StreamingText.tsx   Token-by-token fade-in reveal
  icons.tsx           Inline SVG icon set (no dependencies)
lib/
  demoConversation.tsx  Seed messages + default reply generator
types/
  chat.ts             ChatMessage, ModelOption, Role
tailwind.config.ts    Color tokens + token-in keyframe
```

## Install

1. Copy the folders into your Next.js 13+ (App Router) project root.
2. Merge `tailwind.config.ts` `theme.extend` into your existing config
   (or use it directly). It adds the color tokens and the `token-in` animation.
3. Ensure `globals.css` is imported (already imported in `app/layout.tsx`).
4. `next/font` handles the serif — no extra font setup needed.

No third-party dependencies (icons are inline SVG).

## Palette (Tailwind tokens)

| Token                  | Hex       | Use                          |
| ---------------------- | --------- | ---------------------------- |
| `cocoa`                | `#1E1712` | page background              |
| `cocoa-panel`          | `#2A2118` | composer / dropdown surface  |
| `cocoa-bubble`         | `#2C231A` | user message bubble          |
| `cocoa-bubble-border`  | `#3A3025` | bubble border                |
| `cocoa-border`         | `#392F24` | surface borders              |
| `cocoa-hover`          | `#2E251B` | hover wash                   |
| `cream`                | `#F4F1EC` | primary text                 |
| `muted`                | `#A99A82` | secondary text / idle icons  |
| `faint`                | `#7E7159` | disclaimer text              |
| `gold`                 | `#E6CE8A` | accent                       |
| `gold-bright`          | `#F0DA9E` | accent hover                 |

## Usage

```tsx
import ChatUI from "@/components/ChatUI";

export default function Page() {
  return (
    <ChatUI
      title="Weekend trip to Lisbon"
      // initialMessages={...}
      // models={[{ name: "Sonnet 4.5", tag: "Balanced" }]}
      // defaultModel="Sonnet 4.5"
      // generateReply={(userText) => myModel(userText)}
      // onSend={(text) => console.log(text)}
    />
  );
}
```

### Streaming

`StreamingText` reveals text one token at a time; each token span mounts with
the `token-in` animation (opacity 0→1 + blur 4px→0). To wire a real backend,
replace `generateReply` — the fade animation is applied client-side regardless
of where the text comes from. For a true incremental stream you can append to a
message's `content` as chunks arrive; set `streaming: true` while in flight and
`false` (via `onStreamDone`) when complete.

## Responsiveness

- Fluid `max-w-[780px]` message column, centered.
- Reduced padding and slightly smaller serif size on small screens.
- `mode` label ("Extended") hides on narrow viewports.
- Bubble capped at `max-w-[88%]`.
