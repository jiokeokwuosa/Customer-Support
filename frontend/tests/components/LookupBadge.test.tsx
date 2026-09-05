import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LookupBadge } from "@/components/chat/LookupBadge";
import type { LookupResult } from "@/lib/api/types";

const foundLookup: LookupResult = {
  lookup_type: "order",
  identifier: "ORD-12345",
  found: true,
  summary: "Order ORD-12345 is shipped via UPS.",
  details: { carrier: "UPS", status: "shipped" },
};

const missingLookup: LookupResult = {
  lookup_type: "order",
  identifier: "ORD-99999",
  found: false,
  summary: "No order found for ORD-99999.",
};

describe("LookupBadge", () => {
  it("shows matched lookup type, id, status, and summary", () => {
    render(<LookupBadge lookup={foundLookup} />);

    expect(screen.getByLabelText("Lookup context")).toBeInTheDocument();
    expect(screen.getByText("order")).toBeInTheDocument();
    expect(screen.getByText("ORD-12345")).toBeInTheDocument();
    expect(screen.getByText("Matched")).toBeInTheDocument();
    expect(
      screen.getByText("Order ORD-12345 is shipped via UPS."),
    ).toBeInTheDocument();
  });

  it("shows not-found status when the identifier is unmatched", () => {
    render(<LookupBadge lookup={missingLookup} />);

    expect(screen.getByText("Not found")).toBeInTheDocument();
    expect(
      screen.getByText("No order found for ORD-99999."),
    ).toBeInTheDocument();
  });
});
