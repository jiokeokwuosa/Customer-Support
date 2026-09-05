"use client";

import { Button } from "@/components/ui/Button";
import type { SamplePrompt } from "@/lib/api/types";

type SamplePromptsProps = {
  prompts: SamplePrompt[];
  onSelect: (prompt: SamplePrompt) => void;
  disabled?: boolean;
};

export function SamplePrompts({
  prompts,
  onSelect,
  disabled = false,
}: SamplePromptsProps) {
  if (prompts.length === 0) {
    return null;
  }

  return (
    <section aria-label="Sample prompts" className="flex flex-col gap-2">
      <p className="text-xs font-medium text-ink-subtle">Try a sample</p>
      <ul className="flex flex-wrap gap-2">
        {prompts.map((prompt) => (
          <li key={prompt.id}>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              disabled={disabled}
              onClick={() => onSelect(prompt)}
            >
              {prompt.label}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
