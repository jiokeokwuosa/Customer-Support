import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch, getApiBaseUrl } from "@/lib/api/client";

describe("getApiBaseUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("defaults to localhost when env is unset", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("reads NEXT_PUBLIC_API_BASE_URL", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://api.example.com");
    expect(getApiBaseUrl()).toBe("http://api.example.com");
  });
});

describe("apiFetch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("returns parsed JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: "ok" }),
      }),
    );

    const data = await apiFetch<{ status: string }>("/health");

    expect(data).toEqual({ status: "ok" });
    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({ body: undefined }),
    );
  });

  it("throws ApiError with parsed error body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => ({
          status: "error",
          message: "Session not found",
          error_code: "SESSION_NOT_FOUND",
          next_actions: ["new_conversation"],
        }),
      }),
    );

    await expect(apiFetch("/api/v1/sessions/missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "Session not found",
      body: {
        status: "error",
        error_code: "SESSION_NOT_FOUND",
        next_actions: ["new_conversation"],
      },
    });
  });

  it("builds generic ApiError when response is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        statusText: "Bad Gateway",
        json: async () => {
          throw new Error("not json");
        },
      }),
    );

    try {
      await apiFetch("/health");
      expect.fail("expected ApiError");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      const apiError = error as ApiError;
      expect(apiError.status).toBe(502);
      expect(apiError.body.error_code).toBe("SERVICE_UNAVAILABLE");
    }
  });

  it("returns undefined for 204 No Content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
      }),
    );

    const data = await apiFetch<void>("/api/v1/sessions/abc");

    expect(data).toBeUndefined();
  });

  it("JSON-encodes request bodies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ turn_id: "t1" }),
      }),
    );

    await apiFetch("/api/v1/sessions/s1/messages", {
      method: "POST",
      body: { message: "hello" },
    });

    expect(fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/sessions/s1/messages",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ message: "hello" }),
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
  });
});
