import type { HTMLAttributes } from "react";

export type StatusVariant = "info" | "success" | "warning" | "error";

export type StatusMessageProps = HTMLAttributes<HTMLDivElement> & {
  variant?: StatusVariant;
  title?: string;
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
      {title ? <p className="mb-1 font-medium">{title}</p> : null}
      {children}
    </div>
  );
}
