"use client";

import { useEffect, useState } from "react";

import { MessageInput } from "@/components/chat/MessageInput";
import type { ChatTurn } from "@/components/chat/MessageList";
import { MessageList } from "@/components/chat/MessageList";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { useMessageStream } from "@/hooks/useMessageStream";
import { ApiError } from "@/lib/api/client";
import { useSendMessage } from "@/lib/query/hooks/useSendMessage";
import { useSession } from "@/lib/query/hooks/useSession";
import type { Citation, LookupResult, TriageMetadata } from "@/lib/api/types";

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
  const { streamMessage, isStreaming, error: streamError, resetError } =
    useMessageStream(sessionId);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  const isBusy = isStreaming || sendMessage.isPending;

  useEffect(() => {
    onBusyChange?.(isBusy);
    return () => onBusyChange?.(false);
  }, [isBusy, onBusyChange]);

  async function deliverMessage(
    message: string,
    options: { reuseUserBubble?: boolean } = {},
  ) {
    const assistantTurnId = crypto.randomUUID();
    setPendingMessage(message);
    setTurns((current) => {
      const next = [...current];
      if (!options.reuseUserBubble) {
        next.push({
          id: crypto.randomUUID(),
          role: "user",
          content: message,
        });
      }
      next.push({ id: assistantTurnId, role: "assistant", content: "" });
      return next;
    });

    const applyAssistant = (fields: {
      content?: string;
      triage?: TriageMetadata;
      citations?: Citation[];
      lookup?: LookupResult | null;
      id?: string;
    }) => {
      setTurns((current) =>
        current.map((turn) =>
          turn.id === assistantTurnId ? { ...turn, ...fields } : turn,
        ),
      );
    };

    let streamProgressed = false;

    try {
      const done = await streamMessage(message, {
        onTriage: (triage) => {
          streamProgressed = true;
          applyAssistant({ triage });
        },
        onToken: (text) => {
          streamProgressed = true;
          setTurns((current) =>
            current.map((turn) =>
              turn.id === assistantTurnId
                ? { ...turn, content: `${turn.content}${text}` }
                : turn,
            ),
          );
        },
        onCitations: (citations) => applyAssistant({ citations }),
        onLookup: (lookup) => applyAssistant({ lookup }),
        onDone: (response) =>
          applyAssistant({
            id: response.turn_id,
            content: response.message,
            triage: response.triage,
            citations: response.citations,
            lookup: response.lookup ?? null,
          }),
      });

      if (!done) {
        throw new Error("Stream ended without a done event");
      }
      setDraft("");
      setPendingMessage(null);
      resetError();
      sendMessage.reset();
    } catch {
      // Only fall back to sync when the stream never started delivering events
      // (avoids double-persisting a turn that may already be saved server-side).
      if (!streamProgressed) {
        try {
          const response = await sendMessage.mutateAsync(message);
          if (response.status === "error") {
            throw new Error(response.message);
          }
          applyAssistant({
            id: response.turn_id,
            content: response.message,
            triage: response.triage,
            citations: response.citations,
            lookup: response.lookup ?? null,
          });
          setDraft("");
          setPendingMessage(null);
          resetError();
          return;
        } catch {
          // Fall through to draft-preserving error path.
        }
      }
      setTurns((current) =>
        current.filter((turn) => turn.id !== assistantTurnId),
      );
      setDraft(message);
    }
  }

  function handleSend(message: string) {
    if (isBusy || disabled) {
      return;
    }
    void deliverMessage(message);
  }

  function handleRetry() {
    const message = pendingMessage ?? draft.trim();
    if (!message || isBusy || disabled) {
      return;
    }
    resetError();
    sendMessage.reset();
    void deliverMessage(message, { reuseUserBubble: true });
  }

  const errorMessage =
    streamError instanceof ApiError
      ? streamError.body.message
      : streamError instanceof Error
        ? streamError.message
        : sendMessage.error instanceof ApiError
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

      {isBusy ? (
        <StatusMessage variant="info">Generating reply…</StatusMessage>
      ) : null}

      {errorMessage && !isBusy ? (
        <StatusMessage
          variant="error"
          title="Message failed"
          actionLabel="Retry"
          onAction={handleRetry}
        >
          {errorMessage}
        </StatusMessage>
      ) : null}

      <section aria-label="Compose message" className="shrink-0">
        <MessageInput
          value={draft}
          onChange={setDraft}
          onSend={handleSend}
          disabled={disabled || isBusy}
          clearOnSend={false}
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
