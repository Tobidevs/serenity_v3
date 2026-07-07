// Client for the Serenity backend agent API.
//
// Base URL is configurable via NEXT_PUBLIC_API_BASE_URL (see .env.local.example)
// and defaults to the local FastAPI dev server.
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface AgentMessage {
  role: string;
  content: string;
}

export interface InvokeResponse {
  thread_id: string;
  /** Text to show the user: the agent's answer or a clarification question. */
  reply: string;
  /** When true, `reply` is a clarification question; send the answer back with the same thread_id. */
  awaiting_clarification: boolean;
  messages: AgentMessage[];
}

/**
 * Send a user message to the agent's /agent/invoke route.
 *
 * Pass the `thread_id` returned by a previous call to continue the same
 * conversation (required to answer a clarification question).
 */
export async function invokeAgent(
  message: string,
  threadId?: string
): Promise<InvokeResponse> {
  const res = await fetch(`${API_BASE_URL}/agent/invoke`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, thread_id: threadId ?? null }),
  });

  if (!res.ok) {
    throw new Error(`Agent request failed (${res.status} ${res.statusText})`);
  }

  return res.json() as Promise<InvokeResponse>;
}
