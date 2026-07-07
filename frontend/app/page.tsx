import ChatUI from "../components/ChatUI";

export default function Page() {
  // Start with an empty conversation; messages come from the backend agent as
  // the user chats. Pass props (title, initialMessages, models, onSend) to
  // customize. See components/ChatUI.tsx for the full prop list.
  return <ChatUI title="Serenity" initialMessages={[]} />;
}
