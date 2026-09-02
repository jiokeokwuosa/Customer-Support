/**
 * Typed HTTP client for the backend API.
 *
 * Reads `NEXT_PUBLIC_API_BASE_URL` (defaults to http://localhost:8000).
 * Non-2xx responses are parsed into `ApiError` with the unified error contract.
 */

import type { ErrorResponse } from "./types";

const DEFAULT_BASE_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return DEFAULT_BASE_URL;
}

export class ApiError extends Error {
  readonly status: number;
  readonly body: ErrorResponse;

  constructor(status: number, body: ErrorResponse) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

function isErrorResponse(value: unknown): value is ErrorResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    record.status === "error" &&
    typeof record.message === "string" &&
    typeof record.error_code === "string" &&
    Array.isArray(record.next_actions)
  );
}

async function parseErrorBody(response: Response): Promise<ErrorResponse> {
  try {
    const data: unknown = await response.json();
    if (isErrorResponse(data)) {
      return data;
    }
  } catch {
    // Response body was not JSON — fall through to generic error.
  }

  return {
    status: "error",
    message: response.statusText || "Request failed",
    error_code: "SERVICE_UNAVAILABLE",
    next_actions: [],
  };
}

function buildUrl(path: string): string {
  const base = getApiBaseUrl().replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

export interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

/** Low-level fetch wrapper — throws `ApiError` on non-2xx responses. */
export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(buildUrl(path), {
    ...rest,
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorBody(response));
  }

  return response.json() as Promise<T>;
}
