import { ChevronDown, Share } from "./icons";

interface ChatHeaderProps {
  title: string;
  onShare?: () => void;
  onTitleClick?: () => void;
}

export default function ChatHeader({
  title,
  onShare,
  onTitleClick,
}: ChatHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex shrink-0 items-center justify-between border-b border-cocoa-border/60 bg-cocoa/80 px-4 py-3.5 backdrop-blur-md sm:px-6">
      <button
        type="button"
        onClick={onTitleClick}
        className="group flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[15px] font-medium tracking-[-0.01em] text-cream/95 transition-colors hover:bg-cocoa-hover"
      >
        <span className="max-w-[60vw] truncate">{title}</span>
        <ChevronDown className="h-4 w-4 text-gold/80 transition-colors group-hover:text-gold" />
      </button>

      <button
        type="button"
        title="Share"
        onClick={onShare}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-muted transition-colors hover:bg-cocoa-hover hover:text-cream"
      >
        <Share className="h-[18px] w-[18px]" />
      </button>
    </header>
  );
}
