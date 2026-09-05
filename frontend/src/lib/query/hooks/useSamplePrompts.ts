"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";
import type { SamplePromptsResponse } from "@/lib/api/types";
import { queryDefaults, queryKeys } from "@/lib/query/keys";

function fetchSamplePrompts(): Promise<SamplePromptsResponse> {
  return apiFetch<SamplePromptsResponse>("/api/v1/sample-prompts");
}

export function useSamplePrompts() {
  return useQuery({
    queryKey: queryKeys.samplePrompts.all,
    queryFn: fetchSamplePrompts,
    staleTime: queryDefaults.staleTime,
  });
}
