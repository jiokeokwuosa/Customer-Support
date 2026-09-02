"use client";

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
            "max-w-[85%] rounded-card px-4 py-3 text-sm",
            turn.role === "user"
              ? "ml-auto bg-primary text-white"
              : "bg-surface-elevated text-ink border border-border",
          ].join(" ")}
        >
          {turn.content}
        </li>
      ))}
    </ul>
  );
}
