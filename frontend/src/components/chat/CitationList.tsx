import type { Citation } from "@/lib/api/types";

type CitationListProps = {
  citations: Citation[];
};

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) {
    return null;
  }

  return (
    <section
      className="mt-3 border-t border-border pt-3"
      aria-label="Citations"
    >
      <h2 className="mb-2 text-xs font-medium text-ink-subtle">Sources</h2>
      <ul className="flex flex-col gap-2">
        {citations.map((citation) => (
          <li
            key={`${citation.source_id}-${citation.title}`}
            className="rounded-button border border-border bg-surface px-3 py-2 text-xs"
          >
            <p className="font-medium text-ink">{citation.title}</p>
            <p className="mt-1 text-ink-muted">{citation.excerpt}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
