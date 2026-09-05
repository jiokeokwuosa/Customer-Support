import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MessageList } from "@/components/chat/MessageList";
import type { LookupResult, TriageMetadata } from "@/lib/api/types";

const triage: TriageMetadata = {
  topic: "billing",
  sentiment: "frustrated",
  urgency: "high",
  rationale: "Duplicate charge complaint with urgent refund request",
};

const lookup: LookupResult = {
  lookup_type: "order",
  identifier: "ORD-12345",
  found: true,
  summary: "Order ORD-12345 is shipped via UPS.",
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

  it("shows citations under assistant turns when present", () => {
    render(
      <MessageList
        turns={[
          {
            id: "a1",
            role: "assistant",
            content: "Refunds are available within 14 days.",
            triage,
            citations: [
              {
                source_id: "faq-refunds",
                title: "Digital Product Refunds",
                excerpt: "Refunds for digital products are available within 14 days.",
              },
            ],
          },
        ]}
      />,
    );

    expect(screen.getByLabelText("Citations")).toBeInTheDocument();
    expect(screen.getByText("Digital Product Refunds")).toBeInTheDocument();
  });

  it("shows lookup badge under assistant turns when lookup is present", () => {
    render(
      <MessageList
        turns={[
          {
            id: "a1",
            role: "assistant",
            content: "Your order is on the way.",
            triage,
            lookup,
          },
        ]}
      />,
    );

    expect(screen.getByLabelText("Lookup context")).toBeInTheDocument();
    expect(screen.getByText("ORD-12345")).toBeInTheDocument();
    expect(screen.getByText("Matched")).toBeInTheDocument();
  });

  it("renders markdown formatting in assistant replies", () => {
    render(
      <MessageList
        turns={[
          {
            id: "a1",
            role: "assistant",
            content: "Refunds are available within **14 days**.",
            triage,
          },
        ]}
      />,
    );

    const bold = screen.getByText("14 days");
    expect(bold.tagName).toBe("STRONG");
  });

  it("keeps user messages as plain text", () => {
    render(
      <MessageList
        turns={[
          {
            id: "u1",
            role: "user",
            content: "Please refund **this** charge.",
          },
        ]}
      />,
    );

    expect(
      screen.getByText("Please refund **this** charge."),
    ).toBeInTheDocument();
    expect(screen.queryByText("this")).not.toBeInTheDocument();
  });
});
