"use client";

import { useState, type SubmitEvent } from "react";

import { Button } from "@/components/ui/Button";

type MessageInputProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
  /** Controlled draft so parents can preserve text after errors / retries. */
  value?: string;
  onChange?: (value: string) => void;
  /** Clear the field after a successful send when uncontrolled. */
  clearOnSend?: boolean;
};

export function MessageInput({
  onSend,
  disabled = false,
  value,
  onChange,
  clearOnSend = true,
}: MessageInputProps) {
  const [internalMessage, setInternalMessage] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const isControlled = value !== undefined;
  const message = isControlled ? value : internalMessage;

  function setMessage(next: string) {
    if (isControlled) {
      onChange?.(next);
    } else {
      setInternalMessage(next);
    }
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      setValidationError("Please enter a message before sending.");
      return;
    }
    if (disabled) {
      return;
    }
    setValidationError(null);
    onSend(trimmed);
    if (!isControlled && clearOnSend) {
      setInternalMessage("");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(event) => {
            setValidationError(null);
            setMessage(event.target.value);
          }}
          placeholder="Describe your support issue…"
          disabled={disabled}
          aria-invalid={validationError ? true : undefined}
          aria-describedby={validationError ? "message-input-error" : undefined}
          className="flex-1 rounded-button border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        />
        <Button type="submit" disabled={disabled}>
          Send
        </Button>
      </div>
      {validationError ? (
        <p id="message-input-error" className="text-xs text-danger" role="alert">
          {validationError}
        </p>
      ) : null}
    </form>
  );
}
