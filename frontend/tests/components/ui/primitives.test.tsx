import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatusMessage } from "@/components/ui/StatusMessage";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Send</Button>);
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
  });
});

describe("Card", () => {
  it("renders content inside a card container", () => {
    render(<Card>Support panel</Card>);
    expect(screen.getByText("Support panel")).toBeInTheDocument();
  });
});

describe("StatusMessage", () => {
  it("renders error variant with title", () => {
    render(
      <StatusMessage variant="error" title="Something went wrong">
        Please try again.
      </StatusMessage>,
    );

    expect(screen.getByRole("status")).toHaveTextContent(
      "Something went wrong",
    );
    expect(screen.getByText("Please try again.")).toBeInTheDocument();
  });
});
