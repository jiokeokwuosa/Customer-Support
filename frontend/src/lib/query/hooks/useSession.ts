"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";
import type { CreateSessionResponse } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

function createSession(): Promise<CreateSessionResponse> {
  return apiFetch<CreateSessionResponse>("/api/v1/sessions", { method: "POST" });
}

async function deleteSession(sessionId: string): Promise<void> {
  await apiFetch<undefined>(`/api/v1/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export function useSession() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.sessions.all,
    queryFn: createSession,
    staleTime: Infinity,
  });

  const resetMutation = useMutation({
    mutationFn: async () => {
      const current = queryClient.getQueryData<CreateSessionResponse>(
        queryKeys.sessions.all,
      );
      // Create first so a failed POST leaves the existing session usable.
      const next = await createSession();
      if (current?.session_id) {
        try {
          await deleteSession(current.session_id);
        } catch {
          // Best-effort cleanup; UI already rotates onto the new session.
        }
      }
      return next;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.sessions.all, data);
      queryClient.removeQueries({ queryKey: queryKeys.messages.all });
    },
  });

  return {
    sessionId: query.data?.session_id ?? null,
    createdAt: query.data?.created_at ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isResetting: resetMutation.isPending,
    resetError: resetMutation.error,
    resetConversation: () => resetMutation.mutateAsync(),
  };
}
