import type { ChatMessage, ModelOption } from "../types/chat";

export const DEFAULT_MODELS: ModelOption[] = [
  { name: "Haiku 4.5", tag: "Fastest" },
  { name: "Sonnet 4.5", tag: "Balanced" },
  { name: "Opus 4.5", tag: "Most capable" },
];

/** Seeded conversation. The assistant message uses a rich `node`. */
export const DEMO_MESSAGES: ChatMessage[] = [
  {
    id: "u1",
    role: "user",
    content:
      "Hey Claude! I'm planning a long weekend in Lisbon next month and I'd love your help putting together a loose itinerary. Feel free to ask me anything you need to make it genuinely useful. If a little day-by-day plan or checklist would help, go right ahead and make one.",
  },
  {
    id: "a1",
    role: "assistant",
    content: "",
    summary: "Gathered key trip details to shape a Lisbon itinerary",
    node: (
      <>
        <p className="m-0 mb-[18px]">
          I'd be glad to help you plan Lisbon! It's a wonderful city for a long
          weekend. Let me ask a couple of quick questions so the plan actually
          fits your trip:
        </p>

        <ol className="m-0 mb-2 list-decimal pl-[26px]">
          <li className="mb-3.5">
            <span className="font-semibold text-cream">
              What&apos;s your travel style?
            </span>{" "}
            Are you leaning toward:
            <ul className="mt-2.5 list-disc pl-6">
              <li className="mb-2">
                <span className="font-medium text-gold">Relaxed</span> — a few
                highlights, long lunches, plenty of café time?
              </li>
              <li className="mb-2">
                <span className="font-medium text-gold">Packed</span> — see as
                much as possible across the three days?
              </li>
              <li className="mb-2">
                <span className="font-medium text-gold">Themed</span> — food,
                history, viewpoints, or day trips (Sintra, Cascais)?
              </li>
              <li>
                <span className="font-medium text-gold">A mix</span> — one big
                outing plus room to wander?
              </li>
            </ul>
          </li>
          <li>
            <span className="font-semibold text-cream">
              Who&apos;s coming, and what&apos;s the budget?
            </span>{" "}
            For example:
            <ul className="mt-2.5 list-disc pl-6">
              <li className="mb-2">Solo, couple, or a group of friends?</li>
              <li className="mb-2">Comfortable mid-range, or watching costs?</li>
              <li className="mb-2">Any must-dos already on your list?</li>
              <li>Anything you&apos;d rather skip?</li>
            </ul>
          </li>
        </ol>

        <p className="m-0 mb-[18px] mt-[22px]">
          Once I know where you&apos;re coming from, I can put together a
          day-by-day itinerary — maybe an Alfama-and-viewpoints day, a Belém
          pastries-and-history morning, and a Sintra day trip — with a packing
          checklist to match.
        </p>
        <p className="m-0">What sounds good?</p>
      </>
    ),
  },
];

/** Default canned reply used by the simulated streamer. */
export function defaultReply(_userText: string): string {
  return "Great — that gives me a clear picture. I'll sketch a relaxed three-day plan: an Alfama-and-viewpoints wander on day one, a Belém morning for pastéis de nata and the monastery on day two, and a Sintra day trip on day three. Want me to add rough timings and a short packing checklist alongside it?";
}
