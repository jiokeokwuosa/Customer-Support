"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";
import type { CreateSessionResponse } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

function createSession(): Promise<CreateSessionResponse> {
  return apiFetch<CreateSessionResponse>("/api/v1/sessions", { method: "POST" });
}

export function useSession() {
  const query = useQuery({
    queryKey: queryKeys.sessions.all,
    queryFn: createSession,
    staleTime: Infinity,
  });

  return {
    sessionId: query.data?.session_id ?? null,
    createdAt: query.data?.created_at ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}
