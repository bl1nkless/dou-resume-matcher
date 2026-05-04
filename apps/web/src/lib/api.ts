export type HealthResponse = {
  service: string;
  status: string;
  environment: string;
  database: string;
  llm_provider: string;
  llm_model: string;
  embedding_model: string;
  mlflow_tracking_uri: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type DocumentResponse = {
  id: string;
  document_type: string;
  source_url: string | null;
  language: string | null;
  object_storage_uri: string | null;
  created_at: string;
};

export type CandidateProfileResponse = {
  id: string;
  target_role: string | null;
  estimated_seniority: string | null;
  positioning: string | null;
  profile_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type JobResponse = {
  id: string;
  title: string;
  source: string;
  source_url: string | null;
  seniority: string | null;
  domain: string | null;
  work_format: string | null;
  raw_document_id: string | null;
  extracted_json: Record<string, unknown>;
  first_seen_at: string;
};

export type AnalysisReportResponse = {
  id: string;
  candidate_profile_id: string;
  job_id: string;
  status: string;
  model_version: string | null;
  feature_json: Record<string, number | string | null> | null;
  score_json: Record<string, number> | null;
  verdict: string | null;
  created_at: string;
  completed_at: string | null;
  evidence: Array<{
    id: string;
    requirement_text: string;
    evidence_level: string;
    confidence: number;
    requirement_priority: string | null;
  }>;
  gaps: Array<{
    id: string;
    gap_text: string;
    gap_type: string;
    severity: number;
    reason: string;
    recommended_action: string | null;
  }>;
  recommendations: Array<{
    id: string;
    recommendation_type: string;
    content_json: Record<string, unknown>;
  }>;
};

export type FeedbackEventResponse = {
  id: string;
  analysis_run_id: string | null;
  event_type: string;
  event_value: Record<string, unknown>;
  created_at: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}/health`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Health check failed with ${response.status}`);
  }

  return response.json();
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {})
    }
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? `Request failed with ${response.status}`);
  }
  return payload as T;
}

export function register(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function createResume(token: string, text: string): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>("/documents/resume", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ text })
  });
}

export function createCandidateProfile(
  token: string,
  resumeDocumentId: string,
  targetRole?: string
): Promise<CandidateProfileResponse> {
  return apiFetch<CandidateProfileResponse>("/candidate-profiles", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ resume_document_id: resumeDocumentId, target_role: targetRole || null })
  });
}

export function createJobFromText(token: string, text: string): Promise<JobResponse> {
  return apiFetch<JobResponse>("/jobs/from-text", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ text })
  });
}

export async function createAnalysis(
  token: string,
  candidateProfileId: string,
  jobId: string
): Promise<AnalysisReportResponse> {
  const run = await apiFetch<{ id: string }>("/analyses", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ candidate_profile_id: candidateProfileId, job_id: jobId })
  });
  return apiFetch<AnalysisReportResponse>(`/analyses/${run.id}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
}

export function submitAnalysisFeedback(
  token: string,
  analysisId: string,
  eventType: "verdict_rating" | "recommendation_rating" | "gap_quality" | "free_text",
  eventValue: Record<string, unknown>
): Promise<FeedbackEventResponse> {
  return apiFetch<FeedbackEventResponse>(`/analyses/${analysisId}/feedback`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ event_type: eventType, event_value: eventValue })
  });
}
