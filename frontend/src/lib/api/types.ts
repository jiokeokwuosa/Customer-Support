/** API types mirrored from backend OpenAPI schemas. */

export type TopicCategory = "technical" | "billing" | "general";

export type SentimentLabel = "positive" | "neutral" | "negative" | "frustrated";

export type UrgencyLevel = "low" | "medium" | "high" | "critical";

export interface TriageMetadata {
  topic: TopicCategory;
  sentiment: SentimentLabel;
  urgency: UrgencyLevel;
  rationale: string;
}

export interface Citation {
  source_id: string;
  title: string;
  excerpt: string;
}

export type LookupType = "order" | "account";

export interface LookupResult {
  lookup_type: LookupType;
  identifier: string;
  found: boolean;
  summary: string;
  details?: Record<string, unknown>;
}

export interface TurnResponse {
  turn_id: string;
  session_id: string;
  status: "success" | "error";
  message: string;
  triage: TriageMetadata;
  citations: Citation[];
  lookup?: LookupResult | null;
  error_code: string | null;
  next_actions: string[];
}

export interface SamplePrompt {
  id: string;
  label: string;
  message: string;
  expected_topic?: TopicCategory;
}

export type ErrorCode =
  | "VALIDATION_ERROR"
  | "SESSION_NOT_FOUND"
  | "LLM_ERROR"
  | "LLM_TIMEOUT"
  | "SERVICE_UNAVAILABLE"
  | "RATE_LIMITED";

export interface ErrorResponse {
  status: "error";
  message: string;
  error_code: ErrorCode;
  next_actions: string[];
}

export interface CreateSessionResponse {
  session_id: string;
  created_at: string;
}

export interface HealthResponse {
  status: "ok";
}

export interface ReadyResponse {
  status: "ready";
  knowledge_loaded: boolean;
}

export interface SendMessageRequest {
  message: string;
}

export interface SamplePromptsResponse {
  prompts: SamplePrompt[];
}
