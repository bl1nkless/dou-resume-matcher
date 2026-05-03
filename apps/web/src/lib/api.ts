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
  language: string | null;
  created_at: string;
};

export type JobResponse = {
  id: string;
  title: string;
  source: string;
  raw_document_id: string | null;
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

export function createJobFromText(token: string, text: string): Promise<JobResponse> {
  return apiFetch<JobResponse>("/jobs/from-text", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ text })
  });
}
