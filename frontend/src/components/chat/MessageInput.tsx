"use client";

import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type SubmitEvent,
} from "react";

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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isControlled = value !== undefined;
  const message = isControlled ? value : internalMessage;
  // Hide stale errors once the draft has content (e.g. after sample chip prefill).
  const visibleValidationError = message.trim() ? null : validationError;

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) {
      return;
    }
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [message]);

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

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <textarea
        ref={textareaRef}
        rows={1}
        value={message}
        onChange={(event) => {
          setValidationError(null);
          setMessage(event.target.value);
        }}
        onKeyDown={handleKeyDown}
        placeholder="Describe your support issue…"
        disabled={disabled}
        aria-invalid={visibleValidationError ? true : undefined}
        aria-describedby={
          visibleValidationError ? "message-input-error" : undefined
        }
        className="max-h-48 min-h-10 w-full resize-none overflow-y-auto rounded-button border border-border bg-surface px-3 py-2 text-sm leading-5 text-ink placeholder:text-ink-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      />
      {visibleValidationError ? (
        <p id="message-input-error" className="text-xs text-danger" role="alert">
          {visibleValidationError}
        </p>
      ) : null}
      <div className="flex justify-end">
        <Button type="submit" disabled={disabled}>
          Send
        </Button>
      </div>
    </form>
  );
}
