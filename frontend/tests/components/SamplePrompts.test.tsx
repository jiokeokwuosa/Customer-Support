import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SamplePrompts } from "@/components/chat/SamplePrompts";
import type { SamplePrompt } from "@/lib/api/types";

const prompts: SamplePrompt[] = [
  {
    id: "billing-duplicate-charge",
    label: "Duplicate charge",
    message: "I was charged twice for my last invoice.",
    expected_topic: "billing",
  },
  {
    id: "technical-login-error",
    label: "Login error",
    message: "I keep getting an error when I try to sign in.",
    expected_topic: "technical",
  },
];

describe("SamplePrompts", () => {
  it("renders chips and pre-fills via onSelect when clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(<SamplePrompts prompts={prompts} onSelect={onSelect} />);

    expect(screen.getByLabelText("Sample prompts")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Duplicate charge" }));

    expect(onSelect).toHaveBeenCalledWith(prompts[0]);
  });

  it("renders nothing when there are no prompts", () => {
    const { container } = render(
      <SamplePrompts prompts={[]} onSelect={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
