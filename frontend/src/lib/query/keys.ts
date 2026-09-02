/** TanStack Query key factory — keeps cache keys consistent across hooks. */

export const queryKeys = {
  health: {
    all: ["health"] as const,
    check: () => [...queryKeys.health.all, "check"] as const,
    ready: () => [...queryKeys.health.all, "ready"] as const,
  },
  sessions: {
    all: ["sessions"] as const,
    detail: (sessionId: string) =>
      [...queryKeys.sessions.all, sessionId] as const,
  },
  messages: {
    all: ["messages"] as const,
    bySession: (sessionId: string) =>
      [...queryKeys.messages.all, sessionId] as const,
  },
  samplePrompts: {
    all: ["sample-prompts"] as const,
  },
} as const;

/** Shared query defaults — referenced from Providers and hooks. */
export const queryDefaults = {
  staleTime: 60_000,
  retry: 1,
  refetchOnWindowFocus: false,
} as const;
