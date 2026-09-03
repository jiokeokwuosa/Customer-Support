import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MessageList } from "@/components/chat/MessageList";
import type { TriageMetadata } from "@/lib/api/types";

const triage: TriageMetadata = {
  topic: "billing",
  sentiment: "frustrated",
  urgency: "high",
  rationale: "Duplicate charge complaint with urgent refund request",
};

describe("MessageList", () => {
  it("shows TriageBadge under assistant turns with triage", () => {
    render(
      <MessageList
        turns={[
          { id: "u1", role: "user", content: "I was charged twice." },
          {
            id: "a1",
            role: "assistant",
            content: "I can help with that charge.",
            triage,
          },
        ]}
      />,
    );

    expect(screen.getByText("I can help with that charge.")).toBeInTheDocument();
    expect(screen.getByLabelText("Triage metadata")).toBeInTheDocument();
    expect(screen.getByText("billing")).toBeInTheDocument();
    expect(screen.getByText("frustrated")).toBeInTheDocument();
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(
      screen.getByText("Duplicate charge complaint with urgent refund request"),
    ).toBeInTheDocument();
  });

  it("does not show triage badges on user turns", () => {
    render(
      <MessageList
        turns={[{ id: "u1", role: "user", content: "Hello", triage }]}
      />,
    );

    expect(screen.queryByLabelText("Triage metadata")).not.toBeInTheDocument();
  });
});
