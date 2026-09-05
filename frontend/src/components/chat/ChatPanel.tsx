"use client";

import { useEffect, useState } from "react";

import { MessageInput } from "@/components/chat/MessageInput";
import type { ChatTurn } from "@/components/chat/MessageList";
import { MessageList } from "@/components/chat/MessageList";
import { SamplePrompts } from "@/components/chat/SamplePrompts";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { useMessageStream } from "@/hooks/useMessageStream";
import { ApiError } from "@/lib/api/client";
import type {
  Citation,
  LookupResult,
  SamplePrompt,
  TriageMetadata,
} from "@/lib/api/types";
import { useSamplePrompts } from "@/lib/query/hooks/useSamplePrompts";
import { useSendMessage } from "@/lib/query/hooks/useSendMessage";
import { useSession } from "@/lib/query/hooks/useSession";

export type ResponseMode = "stream" | "full";

type ChatPanelReadyProps = {
  sessionId: string;
  disabled?: boolean;
  responseMode: ResponseMode;
  onBusyChange?: (busy: boolean) => void;
};

function ChatPanelReady({
  sessionId,
  disabled = false,
  responseMode,
  onBusyChange,
}: ChatPanelReadyProps) {
  const sendMessage = useSendMessage(sessionId);
  const { streamMessage, isStreaming, error: streamError, resetError } =
    useMessageStream(sessionId);
  const samplePrompts = useSamplePrompts();
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  const isBusy = isStreaming || sendMessage.isPending;

  useEffect(() => {
    onBusyChange?.(isBusy);
    return () => onBusyChange?.(false);
  }, [isBusy, onBusyChange]);

  async function deliverFullMessage(
    message: string,
    assistantTurnId: string,
    applyAssistant: (fields: {
      content?: string;
      triage?: TriageMetadata;
      citations?: Citation[];
      lookup?: LookupResult | null;
      id?: string;
    }) => void,
  ) {
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
    } catch {
      setTurns((current) =>
        current.filter((turn) => turn.id !== assistantTurnId),
      );
      setDraft(message);
    }
  }

  async function deliverStreamMessage(
    message: string,
    assistantTurnId: string,
    applyAssistant: (fields: {
      content?: string;
      triage?: TriageMetadata;
      citations?: Citation[];
      lookup?: LookupResult | null;
      id?: string;
    }) => void,
  ) {
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
        await deliverFullMessage(message, assistantTurnId, applyAssistant);
        return;
      }
      setTurns((current) =>
        current.filter((turn) => turn.id !== assistantTurnId),
      );
      setDraft(message);
    }
  }

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

    if (responseMode === "full") {
      await deliverFullMessage(message, assistantTurnId, applyAssistant);
      return;
    }

    await deliverStreamMessage(message, assistantTurnId, applyAssistant);
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

  function handleSampleSelect(prompt: SamplePrompt) {
    if (isBusy || disabled) {
      return;
    }
    setDraft(prompt.message);
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
        <StatusMessage variant="info">
          {responseMode === "stream"
            ? "Generating reply…"
            : "Waiting for full reply…"}
        </StatusMessage>
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

      <section aria-label="Compose message" className="shrink-0 space-y-3">
        {samplePrompts.data?.prompts?.length ? (
          <SamplePrompts
            prompts={samplePrompts.data.prompts}
            onSelect={handleSampleSelect}
            disabled={disabled || isBusy}
          />
        ) : null}
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

function ResponseModeToggle({
  value,
  onChange,
  disabled = false,
}: {
  value: ResponseMode;
  onChange: (mode: ResponseMode) => void;
  disabled?: boolean;
}) {
  return (
    <div
      className="inline-flex rounded-button border border-border p-0.5"
      role="group"
      aria-label="Reply mode"
    >
      <Button
        type="button"
        size="sm"
        variant={value === "stream" ? "primary" : "ghost"}
        disabled={disabled}
        aria-pressed={value === "stream"}
        onClick={() => onChange("stream")}
      >
        Stream
      </Button>
      <Button
        type="button"
        size="sm"
        variant={value === "full" ? "primary" : "ghost"}
        disabled={disabled}
        aria-pressed={value === "full"}
        onClick={() => onChange("full")}
      >
        Full reply
      </Button>
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
  const [responseMode, setResponseMode] = useState<ResponseMode>("stream");

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
        <div className="flex shrink-0 flex-col items-end gap-2 sm:flex-row sm:items-center">
          <ResponseModeToggle
            value={responseMode}
            onChange={setResponseMode}
            disabled={isSending || isResetting}
          />
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={!sessionId || isLoading || isResetting || isSending}
            onClick={() => {
              void handleNewConversation();
            }}
          >
            {isResetting ? "Starting…" : "New conversation"}
          </Button>
        </div>
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
          responseMode={responseMode}
          disabled={isResetting}
          onBusyChange={setIsSending}
        />
      ) : null}
    </Card>
  );
}
