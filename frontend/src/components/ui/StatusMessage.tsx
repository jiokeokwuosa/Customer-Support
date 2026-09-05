import type { HTMLAttributes, ReactNode } from "react";

import { Button } from "@/components/ui/Button";

export type StatusVariant = "info" | "success" | "warning" | "error";

export type StatusMessageProps = HTMLAttributes<HTMLDivElement> & {
  variant?: StatusVariant;
  title?: string;
  actionLabel?: string;
  onAction?: () => void;
  children?: ReactNode;
};

const variantClasses: Record<StatusVariant, string> = {
  info: "border-border bg-surface-elevated text-ink",
  success: "border-success/30 bg-success-subtle text-success",
  warning: "border-warning/30 bg-warning-subtle text-warning",
  error: "border-danger/30 bg-danger-subtle text-danger",
};

export function StatusMessage({
  variant = "info",
  title,
  actionLabel,
  onAction,
  className = "",
  children,
  ...props
}: StatusMessageProps) {
  return (
    <div
      role="status"
      className={[
        "rounded-card border px-4 py-3 text-sm",
        variantClasses[variant],
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {title ? <p className="mb-1 font-medium">{title}</p> : null}
          {children}
        </div>
        {actionLabel && onAction ? (
          <Button type="button" variant="secondary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
