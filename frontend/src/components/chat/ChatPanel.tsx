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

export function ChatPanel() {
  const { sessionId, isLoading: sessionLoading, isError: sessionError } =
    useSession();
  const sendMessage = useSendMessage(sessionId);
  const [turns, setTurns] = useState<ChatTurn[]>([]);

  function handleSend(message: string) {
    if (!sessionId) {
      return;
    }

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
    <Card className="flex flex-col gap-4">
      <header>
        <h1 className="text-lg font-semibold text-ink">Support chat</h1>
        <p className="text-sm text-ink-muted">
          Submit a message and receive a triaged, polished reply.
        </p>
      </header>

      {sessionLoading ? (
        <StatusMessage variant="info">Starting session…</StatusMessage>
      ) : null}

      {sessionError ? (
        <StatusMessage variant="error" title="Could not start session">
          Please refresh and try again.
        </StatusMessage>
      ) : null}

      <div className="min-h-[240px] flex-1 overflow-y-auto">
        <MessageList turns={turns} />
      </div>

      {errorMessage ? (
        <StatusMessage variant="error" title="Message failed">
          {errorMessage}
        </StatusMessage>
      ) : null}

      <MessageInput
        onSend={handleSend}
        disabled={!sessionId || sessionLoading || sendMessage.isPending}
      />
    </Card>
  );
}
