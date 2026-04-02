/**
 * AutoTriage API client — mapped to the FastAPI backend at /api/v1/*
 * All requests carry X-Tenant-Id header (from VITE_TENANT_ID env var).
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TENANT_ID = import.meta.env.VITE_TENANT_ID || 'patil_group';

const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'X-Tenant-Id': TENANT_ID,
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...DEFAULT_HEADERS, ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types — mirror backend Pydantic schemas
// ---------------------------------------------------------------------------

export interface TicketCreate {
  source: string;
  raw_text: string;
  reporter?: string;
}

export interface TriageResponse {
  decision_id: string;
  ticket_id: string;
  module: string;
  priority: string;
  issue_type: string;
  root_cause_hypothesis: string;
  recommended_solution: string;
  assign_to: string;
  confidence: number;           // 0.0 – 1.0
  confidence_calibrated: number | null;
  classification_source: string;
  model_version: string;
  rules_applied: string[];
  similar_ticket_ids: string[];
  similar_ticket_scores: number[];
  kb_article_ids: string[];
  manual_review_required: boolean;
  review_reason: string | null;
  latency_ms: number;
}

export interface TicketResponse {
  id: string;
  tenant_id: string;
  source: string;
  description: string;
  tcode: string | null;
  error_code: string | null;
  environment: string | null;
  reporter: string | null;
  status: string;
  created_at: string;
  triage: TriageResponse | null;
}

export interface TicketListResponse {
  tickets: TicketResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface FeedbackCreate {
  action: 'accepted' | 'overridden';
  overrides?: Record<string, string>;
  override_category?: string;
  comment?: string;
  consultant_id: string;
}

export interface FeedbackResponse {
  id: string;
  ticket_id: string;
  action: string;
  overrides: Record<string, string> | null;
  override_category: string | null;
  comment: string | null;
  consultant_id: string;
  decided_at: string;
  final_module: string;
  final_priority: string;
  is_correct_module: boolean;
  is_correct_priority: boolean;
}

export interface KBArticleCreate {
  title: string;
  content: string;
  module: string;
  error_codes?: string[];
  tcodes?: string[];
  tags?: string[];
}

export interface KBArticle {
  id: string;
  title: string;
  content: string;
  module: string;
  error_codes: string[];
  tcodes: string[];
  tags: string[];
  created_at: string;
}

export interface KBSearchResponse {
  results: KBArticle[];
  query: string;
}

export interface DashboardKPIs {
  total_tickets: number;
  triaged_tickets: number;
  accuracy_rate: number;
  override_rate: number;
  avg_confidence: number;
  avg_latency_ms: number;
  manual_review_count: number;
  mttr_hours: number | null;
}

export interface ModuleAccuracy {
  module: string;
  total: number;
  correct: number;
  accuracy: number;
  override_count: number;
  most_common_override_category: string | null;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: Record<string, string>;
}

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------

export const api = {
  // Health
  async getHealth(): Promise<HealthStatus> {
    return request('/api/v1/health');
  },

  // Tickets
  async createTicket(body: TicketCreate): Promise<TicketResponse> {
    return request('/api/v1/tickets', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  async listTickets(params?: {
    status?: string;
    module?: string;
    priority?: string;
    page?: number;
    page_size?: number;
  }): Promise<TicketListResponse> {
    const qs = new URLSearchParams();
    if (params?.status)    qs.set('status', params.status);
    if (params?.module)    qs.set('module', params.module);
    if (params?.priority)  qs.set('priority', params.priority);
    if (params?.page)      qs.set('page', String(params.page));
    if (params?.page_size) qs.set('page_size', String(params.page_size));
    const q = qs.toString() ? `?${qs}` : '';
    return request(`/api/v1/tickets${q}`);
  },

  async getTicket(ticketId: string): Promise<TicketResponse> {
    return request(`/api/v1/tickets/${ticketId}`);
  },

  async retriageTicket(ticketId: string): Promise<TriageResponse> {
    return request(`/api/v1/tickets/${ticketId}/triage`, { method: 'POST' });
  },

  // Feedback
  async submitFeedback(
    decisionId: string,
    body: FeedbackCreate
  ): Promise<FeedbackResponse> {
    return request(`/api/v1/triage/${decisionId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  // Knowledge Base
  async listKBArticles(module?: string): Promise<KBArticle[]> {
    const q = module ? `?module=${encodeURIComponent(module)}` : '';
    return request(`/api/v1/kb/articles${q}`);
  },

  async createKBArticle(body: KBArticleCreate): Promise<KBArticle> {
    return request('/api/v1/kb/articles', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  async updateKBArticle(id: string, body: KBArticleCreate): Promise<KBArticle> {
    return request(`/api/v1/kb/articles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  async getKBArticle(id: string): Promise<KBArticle> {
    return request(`/api/v1/kb/articles/${id}`);
  },

  async searchKB(query: string, limit = 5): Promise<KBSearchResponse> {
    return request(
      `/api/v1/kb/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  },

  // Dashboard
  async getDashboardKPIs(): Promise<DashboardKPIs> {
    return request('/api/v1/dashboard/kpis');
  },

  async getModuleAccuracy(): Promise<ModuleAccuracy[]> {
    return request('/api/v1/dashboard/module-accuracy');
  },

  async getConfidenceDistribution() {
    return request('/api/v1/dashboard/confidence-distribution');
  },
};

// ---------------------------------------------------------------------------
// SSE stream URL (used by useSSE hook)
// ---------------------------------------------------------------------------

export function getSSEUrl(): string {
  return `${API_BASE}/api/v1/tickets/stream`;
}

export { TENANT_ID };
