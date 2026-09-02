import { describe, expect, it } from "vitest";

import { queryDefaults, queryKeys } from "@/lib/query/keys";

describe("queryKeys", () => {
  it("builds stable session detail keys", () => {
    expect(queryKeys.sessions.detail("abc")).toEqual(["sessions", "abc"]);
  });

  it("builds health check keys", () => {
    expect(queryKeys.health.check()).toEqual(["health", "check"]);
    expect(queryKeys.health.ready()).toEqual(["health", "ready"]);
  });

  it("builds message keys scoped to session", () => {
    expect(queryKeys.messages.bySession("s1")).toEqual(["messages", "s1"]);
  });
});

describe("queryDefaults", () => {
  it("exposes shared staleTime and retry settings", () => {
    expect(queryDefaults.staleTime).toBe(60_000);
    expect(queryDefaults.retry).toBe(1);
    expect(queryDefaults.refetchOnWindowFocus).toBe(false);
  });
});
