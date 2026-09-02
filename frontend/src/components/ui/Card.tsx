import type { HTMLAttributes } from "react";

export type CardProps = HTMLAttributes<HTMLDivElement>;

export function Card({ className = "", ...props }: CardProps) {
  return (
    <div
      className={[
        "rounded-card border border-border bg-surface p-4 shadow-card",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
}
