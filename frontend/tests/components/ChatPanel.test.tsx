import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "@/components/chat/ChatPanel";

const sessionId = "11111111-1111-1111-1111-111111111111";

function renderChatPanel() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <ChatPanel />
    </QueryClientProvider>,
  );
}

function mockSessionCreate() {
  return {
    ok: true,
    status: 200,
    json: async () => ({
      session_id: sessionId,
      created_at: "2026-09-05T00:00:00Z",
    }),
  };
}

function sseBody(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);

        if (url.endsWith("/api/v1/sessions") && init?.method === "POST") {
          return mockSessionCreate();
        }

        if (url.includes("/messages/stream") && init?.method === "POST") {
          return {
            ok: true,
            status: 200,
            body: sseBody([
              'event: triage\ndata: {"topic":"billing","sentiment":"frustrated","urgency":"high","rationale":"Duplicate charge"}\n\n',
              'event: token\ndata: {"text":"Hello "}\n\n',
              'event: token\ndata: {"text":"world"}\n\n',
              `event: done\ndata: {"turn_id":"22222222-2222-2222-2222-222222222222","session_id":"${sessionId}","status":"success","message":"Hello world","triage":{"topic":"billing","sentiment":"frustrated","urgency":"high","rationale":"Duplicate charge"},"citations":[],"lookup":null,"error_code":null,"next_actions":[]}\n\n`,
            ]),
          };
        }

        throw new Error(`Unhandled fetch: ${url}`);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows a loading indicator while streaming a reply", async () => {
    const user = userEvent.setup();
    let releaseStream: (() => void) | undefined;
    const gate = new Promise<void>((resolve) => {
      releaseStream = resolve;
    });

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/api/v1/sessions") && init?.method === "POST") {
          return mockSessionCreate();
        }
        if (url.includes("/messages/stream")) {
          await gate;
          return {
            ok: true,
            status: 200,
            body: sseBody([
              'event: triage\ndata: {"topic":"billing","sentiment":"neutral","urgency":"low","rationale":"ok"}\n\n',
              'event: token\ndata: {"text":"Done"}\n\n',
              `event: done\ndata: {"turn_id":"22222222-2222-2222-2222-222222222222","session_id":"${sessionId}","status":"success","message":"Done","triage":{"topic":"billing","sentiment":"neutral","urgency":"low","rationale":"ok"},"citations":[],"lookup":null,"error_code":null,"next_actions":[]}\n\n`,
            ]),
          };
        }
        throw new Error(`Unhandled fetch: ${url}`);
      }),
    );

    renderChatPanel();
    await screen.findByPlaceholderText("Describe your support issue…");

    await user.type(
      screen.getByPlaceholderText("Describe your support issue…"),
      "Need help",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Generating reply…")).toBeInTheDocument();
    releaseStream?.();
    await waitFor(() => {
      expect(screen.queryByText("Generating reply…")).not.toBeInTheDocument();
    });
    expect(await screen.findByText("Done")).toBeInTheDocument();
  });

  it("preserves the draft and offers retry after a stream failure", async () => {
    const user = userEvent.setup();
    let attempt = 0;

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/api/v1/sessions") && init?.method === "POST") {
          return mockSessionCreate();
        }
        if (url.includes("/messages/stream")) {
          attempt += 1;
          if (attempt === 1) {
            return {
              ok: false,
              status: 503,
              json: async () => ({
                status: "error",
                message: "Service unavailable",
                error_code: "SERVICE_UNAVAILABLE",
                next_actions: ["retry"],
              }),
            };
          }
          return {
            ok: true,
            status: 200,
            body: sseBody([
              'event: triage\ndata: {"topic":"general","sentiment":"neutral","urgency":"low","rationale":"ok"}\n\n',
              'event: token\ndata: {"text":"Recovered"}\n\n',
              `event: done\ndata: {"turn_id":"33333333-3333-3333-3333-333333333333","session_id":"${sessionId}","status":"success","message":"Recovered","triage":{"topic":"general","sentiment":"neutral","urgency":"low","rationale":"ok"},"citations":[],"lookup":null,"error_code":null,"next_actions":[]}\n\n`,
            ]),
          };
        }
        if (url.includes("/messages") && init?.method === "POST") {
          // Sync fallback also fails on first attempt so retry UX stays visible.
          return {
            ok: false,
            status: 503,
            json: async () => ({
              status: "error",
              message: "Service unavailable",
              error_code: "SERVICE_UNAVAILABLE",
              next_actions: ["retry"],
            }),
          };
        }
        throw new Error(`Unhandled fetch: ${url}`);
      }),
    );

    renderChatPanel();
    const input = await screen.findByPlaceholderText(
      "Describe your support issue…",
    );
    await user.type(input, "Please retry me");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Service unavailable")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Please retry me")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Recovered")).toBeInTheDocument();
    expect(screen.getAllByText("Please retry me")).toHaveLength(1);
  });

  it("shows inline validation and does not call the API for empty messages", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/sessions") && init?.method === "POST") {
        return mockSessionCreate();
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderChatPanel();
    await screen.findByPlaceholderText("Describe your support issue…");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(
      await screen.findByText("Please enter a message before sending."),
    ).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes("/messages")),
    ).toBe(false);
  });

  it("uses the sync messages endpoint when Full reply is selected", async () => {
    const user = userEvent.setup();
    let releaseSync: (() => void) | undefined;
    const gate = new Promise<void>((resolve) => {
      releaseSync = resolve;
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/sessions") && init?.method === "POST") {
        return mockSessionCreate();
      }
      if (
        url.includes(`/api/v1/sessions/${sessionId}/messages`) &&
        !url.includes("/stream") &&
        init?.method === "POST"
      ) {
        await gate;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            turn_id: "44444444-4444-4444-4444-444444444444",
            session_id: sessionId,
            status: "success",
            message: "Full reply text",
            triage: {
              topic: "general",
              sentiment: "neutral",
              urgency: "low",
              rationale: "ok",
            },
            citations: [],
            lookup: null,
            error_code: null,
            next_actions: [],
          }),
        };
      }
      throw new Error(`Unhandled fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderChatPanel();
    await screen.findByPlaceholderText("Describe your support issue…");
    await user.click(screen.getByRole("button", { name: "Full reply" }));
    await user.type(
      screen.getByPlaceholderText("Describe your support issue…"),
      "Need a full reply",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("Waiting for full reply…")).toBeInTheDocument();
    releaseSync?.();
    expect(await screen.findByText("Full reply text")).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes("/messages/stream")),
    ).toBe(false);
    expect(
      fetchMock.mock.calls.some(
        ([url]) =>
          String(url).includes("/messages") && !String(url).includes("/stream"),
      ),
    ).toBe(true);
  });
});
