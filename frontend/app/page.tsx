import ChatUI from "../components/ChatUI";

export default function Page() {
  // Fully self-contained: renders the built-in demo conversation.
  // Pass props (title, initialMessages, models, generateReply, onSend) to
  // customize. See components/ChatUI.tsx for the full prop list.
  return <ChatUI />;
}
