import type { LookupResult } from "@/lib/api/types";

type LookupBadgeProps = {
  lookup: LookupResult;
};

const badgeClass =
  "inline-flex items-center gap-1 rounded-button border border-border bg-surface px-2 py-1";

export function LookupBadge({ lookup }: LookupBadgeProps) {
  const statusLabel = lookup.found ? "Matched" : "Not found";

  return (
    <dl
      className="mt-3 flex flex-col gap-2 border-t border-border pt-3 text-xs"
      aria-label="Lookup context"
    >
      <div className="flex flex-wrap gap-2">
        <div className={badgeClass}>
          <dt className="font-medium text-ink-subtle">Lookup</dt>
          <dd className="capitalize text-ink">{lookup.lookup_type}</dd>
        </div>
        <div className={badgeClass}>
          <dt className="font-medium text-ink-subtle">ID</dt>
          <dd className="font-mono text-ink">{lookup.identifier}</dd>
        </div>
        <div className={badgeClass}>
          <dt className="font-medium text-ink-subtle">Status</dt>
          <dd className="text-ink">{statusLabel}</dd>
        </div>
      </div>
      <div className={`${badgeClass} w-full`}>
        <dt className="shrink-0 font-medium text-ink-subtle">Context</dt>
        <dd className="text-ink-muted">{lookup.summary}</dd>
      </div>
    </dl>
  );
}
