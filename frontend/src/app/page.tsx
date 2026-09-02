import { ChatPanel } from "@/components/chat/ChatPanel";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-8">
      <ChatPanel />
    </main>
  );
}
