"use client";

import { useCallback, useRef, useState } from "react";

import { ApiError, getApiBaseUrl } from "@/lib/api/client";
import type {
  Citation,
  ErrorResponse,
  LookupResult,
  TriageMetadata,
  TurnResponse,
} from "@/lib/api/types";

export type StreamHandlers = {
  onTriage?: (triage: TriageMetadata) => void;
  onToken?: (text: string) => void;
  onCitations?: (citations: Citation[]) => void;
  onLookup?: (lookup: LookupResult | null) => void;
  onDone?: (turn: TurnResponse) => void;
  onError?: (error: Error) => void;
};

type StreamState = {
  isStreaming: boolean;
  error: Error | null;
};

function parseErrorBody(raw: unknown): ErrorResponse {
  if (
    typeof raw === "object" &&
    raw !== null &&
    "status" in raw &&
    (raw as ErrorResponse).status === "error"
  ) {
    return raw as ErrorResponse;
  }
  return {
    status: "error",
    message: "Streaming request failed",
    error_code: "SERVICE_UNAVAILABLE",
    next_actions: ["retry"],
  };
}

async function readSseStream(
  response: Response,
  handlers: StreamHandlers,
): Promise<TurnResponse | null> {
  if (!response.body) {
    throw new Error("No response body for SSE stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let doneTurn: TurnResponse | null = null;
  let eventName = "message";
  let dataLines: string[] = [];

  const flush = () => {
    if (dataLines.length === 0) {
      eventName = "message";
      return;
    }
    const data = dataLines.join("\n");
    dataLines = [];
    const name = eventName;
    eventName = "message";

    if (name === "triage") {
      handlers.onTriage?.(JSON.parse(data) as TriageMetadata);
      return;
    }
    if (name === "token") {
      const payload = JSON.parse(data) as { text?: string };
      if (payload.text) {
        handlers.onToken?.(payload.text);
      }
      return;
    }
    if (name === "citations") {
      handlers.onCitations?.(JSON.parse(data) as Citation[]);
      return;
    }
    if (name === "lookup") {
      handlers.onLookup?.(JSON.parse(data) as LookupResult);
      return;
    }
    if (name === "done") {
      doneTurn = JSON.parse(data) as TurnResponse;
      handlers.onDone?.(doneTurn);
      return;
    }
    if (name === "error") {
      const body = parseErrorBody(JSON.parse(data));
      throw new ApiError(500, body);
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      } else if (line === "") {
        flush();
      }
    }
  }
  flush();
  return doneTurn;
}

export function useMessageStream(sessionId: string) {
  const [state, setState] = useState<StreamState>({
    isStreaming: false,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);

  const resetError = useCallback(() => {
    setState((current) => ({ ...current, error: null }));
  }, []);

  const streamMessage = useCallback(
    async (message: string, handlers: StreamHandlers = {}) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState({ isStreaming: true, error: null });

      try {
        const response = await fetch(
          `${getApiBaseUrl()}/api/v1/sessions/${sessionId}/messages/stream`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          let body: ErrorResponse;
          try {
            body = parseErrorBody(await response.json());
          } catch {
            body = parseErrorBody(null);
          }
          throw new ApiError(response.status, body);
        }

        const done = await readSseStream(response, handlers);
        setState({ isStreaming: false, error: null });
        return done;
      } catch (error) {
        const normalized =
          error instanceof Error ? error : new Error("Streaming failed");
        setState({ isStreaming: false, error: normalized });
        handlers.onError?.(normalized);
        throw normalized;
      }
    },
    [sessionId],
  );

  return {
    streamMessage,
    isStreaming: state.isStreaming,
    error: state.error,
    resetError,
  };
}
