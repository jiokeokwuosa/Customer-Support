"use client";

import { useState } from "react";

import { MessageInput } from "@/components/chat/MessageInput";
import type { ChatTurn } from "@/components/chat/MessageList";
import { MessageList } from "@/components/chat/MessageList";
import { Card } from "@/components/ui/Card";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { ApiError } from "@/lib/api/client";
import { useSendMessage } from "@/lib/query/hooks/useSendMessage";
import { useSession } from "@/lib/query/hooks/useSession";

type ChatPanelReadyProps = {
  sessionId: string;
};

function ChatPanelReady({ sessionId }: ChatPanelReadyProps) {
  const sendMessage = useSendMessage(sessionId);
  const [turns, setTurns] = useState<ChatTurn[]>([]);

  function handleSend(message: string) {
    const userTurnId = crypto.randomUUID();
    setTurns((current) => [
      ...current,
      { id: userTurnId, role: "user", content: message },
    ]);

    sendMessage.mutate(message, {
      onSuccess: (response) => {
        setTurns((current) => [
          ...current,
          {
            id: response.turn_id,
            role: "assistant",
            content: response.message,
            triage: response.triage,
          },
        ]);
      },
    });
  }

  const errorMessage =
    sendMessage.error instanceof ApiError
      ? sendMessage.error.body.message
      : sendMessage.error instanceof Error
        ? sendMessage.error.message
        : null;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <section
        aria-label="Conversation"
        className="min-h-60 flex-1 overflow-y-auto rounded-card border border-border bg-surface-muted p-4"
      >
        <MessageList turns={turns} />
      </section>

      {errorMessage ? (
        <StatusMessage variant="error" title="Message failed">
          {errorMessage}
        </StatusMessage>
      ) : null}

      <section aria-label="Compose message" className="shrink-0">
        <MessageInput onSend={handleSend} disabled={sendMessage.isPending} />
      </section>
    </div>
  );
}

export function ChatPanel() {
  const { sessionId, isLoading, isError } = useSession();

  return (
    <Card className="flex min-h-128 flex-col gap-4">
      <header className="shrink-0 border-b border-border pb-3">
        <h1 className="text-lg font-semibold text-ink">Support chat</h1>
        <p className="text-sm text-ink-muted">
          Submit a message and receive a triaged, polished reply with topic,
          sentiment, urgency, and rationale.
        </p>
      </header>

      {isLoading ? (
        <StatusMessage variant="info">Starting session…</StatusMessage>
      ) : null}

      {isError ? (
        <StatusMessage variant="error" title="Could not start session">
          Please refresh and try again.
        </StatusMessage>
      ) : null}

      {sessionId ? <ChatPanelReady sessionId={sessionId} /> : null}
    </Card>
  );
}
