"use client";

import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";

type MessageInputProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
};

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [message, setMessage] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || disabled) {
      return;
    }
    onSend(trimmed);
    setMessage("");
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="Describe your support issue…"
        disabled={disabled}
        className="flex-1 rounded-button border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      />
      <Button type="submit" disabled={disabled || !message.trim()}>
        Send
      </Button>
    </form>
  );
}
