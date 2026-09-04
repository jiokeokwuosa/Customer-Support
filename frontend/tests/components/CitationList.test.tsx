import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CitationList } from "@/components/chat/CitationList";
import type { Citation } from "@/lib/api/types";

const citations: Citation[] = [
  {
    source_id: "faq-refunds",
    title: "Digital Product Refunds",
    excerpt: "Refunds are available within 14 days of purchase.",
  },
];

describe("CitationList", () => {
  it("renders citation titles and excerpts", () => {
    render(<CitationList citations={citations} />);

    expect(screen.getByLabelText("Citations")).toBeInTheDocument();
    expect(screen.getByText("Digital Product Refunds")).toBeInTheDocument();
    expect(
      screen.getByText("Refunds are available within 14 days of purchase."),
    ).toBeInTheDocument();
  });

  it("renders nothing when citations are empty", () => {
    const { container } = render(<CitationList citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
