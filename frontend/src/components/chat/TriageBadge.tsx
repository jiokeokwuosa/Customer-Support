import type { TriageMetadata } from "@/lib/api/types";

type TriageBadgeProps = {
  triage: TriageMetadata;
};

export function TriageBadge({ triage }: TriageBadgeProps) {
  return (
    <dl className="mt-2 flex flex-wrap gap-2 text-xs text-ink-muted">
      <div className="rounded-button border border-border bg-surface-elevated px-2 py-1">
        <dt className="sr-only">Topic</dt>
        <dd>{triage.topic}</dd>
      </div>
      <div className="rounded-button border border-border bg-surface-elevated px-2 py-1">
        <dt className="sr-only">Sentiment</dt>
        <dd>{triage.sentiment}</dd>
      </div>
      <div className="rounded-button border border-border bg-surface-elevated px-2 py-1">
        <dt className="sr-only">Urgency</dt>
        <dd>{triage.urgency}</dd>
      </div>
      <div className="w-full rounded-button border border-border bg-surface-elevated px-2 py-1">
        <dt className="sr-only">Rationale</dt>
        <dd>{triage.rationale}</dd>
      </div>
    </dl>
  );
}
