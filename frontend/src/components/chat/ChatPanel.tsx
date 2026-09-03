"use client";

import { useEffect, useState } from "react";

import { MessageInput } from "@/components/chat/MessageInput";
import type { ChatTurn } from "@/components/chat/MessageList";
import { MessageList } from "@/components/chat/MessageList";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { ApiError } from "@/lib/api/client";
import { useSendMessage } from "@/lib/query/hooks/useSendMessage";
import { useSession } from "@/lib/query/hooks/useSession";

type ChatPanelReadyProps = {
  sessionId: string;
  disabled?: boolean;
  onBusyChange?: (busy: boolean) => void;
};

function ChatPanelReady({
  sessionId,
  disabled = false,
  onBusyChange,
}: ChatPanelReadyProps) {
  const sendMessage = useSendMessage(sessionId);
  const [turns, setTurns] = useState<ChatTurn[]>([]);

  useEffect(() => {
    onBusyChange?.(sendMessage.isPending);
    return () => onBusyChange?.(false);
  }, [onBusyChange, sendMessage.isPending]);

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
        <MessageInput
          onSend={handleSend}
          disabled={disabled || sendMessage.isPending}
        />
      </section>
    </div>
  );
}

export function ChatPanel() {
  const {
    sessionId,
    isLoading,
    isError,
    isResetting,
    resetError,
    resetConversation,
  } = useSession();
  const [isSending, setIsSending] = useState(false);

  const resetErrorMessage =
    resetError instanceof ApiError
      ? resetError.body.message
      : resetError instanceof Error
        ? resetError.message
        : null;

  async function handleNewConversation() {
    await resetConversation();
  }

  return (
    <Card className="flex min-h-128 flex-col gap-4">
      <header className="flex shrink-0 items-start justify-between gap-4 border-b border-border pb-3">
        <div>
          <h1 className="text-lg font-semibold text-ink">Support chat</h1>
          <p className="text-sm text-ink-muted">
            Submit a message and receive a triaged, polished reply with topic,
            sentiment, urgency, and rationale.
          </p>
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="shrink-0"
          disabled={!sessionId || isLoading || isResetting || isSending}
          onClick={() => {
            void handleNewConversation();
          }}
        >
          {isResetting ? "Starting…" : "New conversation"}
        </Button>
      </header>

      {isLoading ? (
        <StatusMessage variant="info">Starting session…</StatusMessage>
      ) : null}

      {isError ? (
        <StatusMessage variant="error" title="Could not start session">
          Please refresh and try again.
        </StatusMessage>
      ) : null}

      {resetErrorMessage ? (
        <StatusMessage variant="error" title="Could not reset conversation">
          {resetErrorMessage}
        </StatusMessage>
      ) : null}

      {sessionId ? (
        <ChatPanelReady
          key={sessionId}
          sessionId={sessionId}
          disabled={isResetting}
          onBusyChange={setIsSending}
        />
      ) : null}
    </Card>
  );
}
