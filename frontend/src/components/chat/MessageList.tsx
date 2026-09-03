"use client";

import { TriageBadge } from "@/components/chat/TriageBadge";
import type { TurnResponse } from "@/lib/api/types";

export type ChatTurn = {
  id: string;
  role: "user" | "assistant";
  content: string;
  triage?: TurnResponse["triage"];
};

type MessageListProps = {
  turns: ChatTurn[];
};

export function MessageList({ turns }: MessageListProps) {
  if (turns.length === 0) {
    return (
      <p className="text-sm text-ink-muted">
        Send a message to start the conversation.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {turns.map((turn) => (
        <li
          key={turn.id}
          className={[
            "rounded-card px-4 py-3 text-sm",
            turn.role === "user"
              ? "ml-auto max-w-[85%] bg-primary text-white"
              : "mr-auto w-full max-w-[92%] border border-border bg-surface-elevated text-ink",
          ].join(" ")}
        >
          <p>{turn.content}</p>
          {turn.role === "assistant" && turn.triage ? (
            <TriageBadge triage={turn.triage} />
          ) : null}
        </li>
      ))}
    </ul>
  );
}
