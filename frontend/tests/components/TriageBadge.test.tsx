import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TriageBadge } from "@/components/chat/TriageBadge";
import type { TriageMetadata } from "@/lib/api/types";

const triage: TriageMetadata = {
  topic: "billing",
  sentiment: "frustrated",
  urgency: "high",
  rationale: "Duplicate charge complaint with urgent refund request",
};

describe("TriageBadge", () => {
  it("renders topic, sentiment, urgency, and rationale", () => {
    render(<TriageBadge triage={triage} />);

    expect(screen.getByText(/billing/i)).toBeInTheDocument();
    expect(screen.getByText(/frustrated/i)).toBeInTheDocument();
    expect(screen.getByText(/high/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Duplicate charge complaint with urgent refund request/),
    ).toBeInTheDocument();
  });
});
