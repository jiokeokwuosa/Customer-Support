"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";
import type { SendMessageRequest, TurnResponse } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

function sendMessage(
  sessionId: string,
  body: SendMessageRequest,
): Promise<TurnResponse> {
  return apiFetch<TurnResponse>(`/api/v1/sessions/${sessionId}/messages`, {
    method: "POST",
    body,
  });
}

export function useSendMessage(sessionId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (message: string) => {
      if (!sessionId) {
        return Promise.reject(new Error("Session not ready"));
      }
      return sendMessage(sessionId, { message });
    },
    onSuccess: () => {
      if (sessionId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.messages.bySession(sessionId),
        });
      }
    },
  });
}
