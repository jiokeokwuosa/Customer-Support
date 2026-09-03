import type { TriageMetadata } from "@/lib/api/types";

type TriageBadgeProps = {
  triage: TriageMetadata;
};

const badgeClass =
  "inline-flex items-center gap-1 rounded-button border border-border bg-surface px-2 py-1";

export function TriageBadge({ triage }: TriageBadgeProps) {
  return (
    <dl
      className="mt-3 flex flex-col gap-2 border-t border-border pt-3 text-xs"
      aria-label="Triage metadata"
    >
      <div className="flex flex-wrap gap-2">
        <div className={badgeClass}>
          <dt className="font-medium text-ink-subtle">Topic</dt>
          <dd className="capitalize text-ink">{triage.topic}</dd>
        </div>
        <div className={badgeClass}>
          <dt className="font-medium text-ink-subtle">Sentiment</dt>
          <dd className="capitalize text-ink">{triage.sentiment}</dd>
        </div>
        <div className={badgeClass}>
          <dt className="font-medium text-ink-subtle">Urgency</dt>
          <dd className="capitalize text-ink">{triage.urgency}</dd>
        </div>
      </div>
      <div className={`${badgeClass} w-full`}>
        <dt className="shrink-0 font-medium text-ink-subtle">Rationale</dt>
        <dd className="text-ink-muted">{triage.rationale}</dd>
      </div>
    </dl>
  );
}
