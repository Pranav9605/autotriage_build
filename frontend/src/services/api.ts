const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface TicketInput {
  ticket_id: string;
  source: string;
  subject: string;
  description: string;
  product?: string;
}

export interface TriageResult {
  category: string;
  priority: string;
  confidence: number;
  diagnosis: string;
  solution: string;
  suggested_team: string;
  source: 'ml' | 'kb' | 'cache' | 'llm';
  model_used: string;
}

export interface KBArticle {
  article_id?: string;
  title: string;
  problem: string;
  solution: string;
  category: string;
  priority: string;
}

export interface PipelineStats {
  ml_classifier: { available: boolean; both_models: boolean };
  knowledge_base: { total_articles: number; total_hits: number };
  response_cache: { total_entries: number; total_hits: number };
  gemini: { available: boolean; model: string };
}

export const api = {
  // Triage
  async triageTicket(ticket: TicketInput): Promise<TriageResult> {
    const res = await fetch(`${API_BASE}/triage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ticket)
    });
    if (!res.ok) throw new Error(`Triage failed: ${res.statusText}`);
    return res.json();
  },

  // Knowledge Base
  async addKBArticle(article: KBArticle) {
    const res = await fetch(`${API_BASE}/kb/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(article)
    });
    if (!res.ok) throw new Error(`Add KB article failed: ${res.statusText}`);
    return res.json();
  },

  async searchKB(query: string) {
    const res = await fetch(`${API_BASE}/kb/search?query=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error(`Search KB failed: ${res.statusText}`);
    return res.json();
  },

  async listKBArticles(): Promise<KBArticle[]> {
    const res = await fetch(`${API_BASE}/kb/articles`);
    if (!res.ok) throw new Error(`List KB articles failed: ${res.statusText}`);
    return res.json();
  },

  async deleteKBArticle(articleId: string) {
    const res = await fetch(`${API_BASE}/kb/${articleId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Delete KB article failed: ${res.statusText}`);
    return res.json();
  },

  // Stats
  async getPipelineStats(): Promise<PipelineStats> {
    const res = await fetch(`${API_BASE}/pipeline/stats`);
    if (!res.ok) throw new Error(`Get pipeline stats failed: ${res.statusText}`);
    return res.json();
  },

  async getCacheStats() {
    const res = await fetch(`${API_BASE}/cache/stats`);
    if (!res.ok) throw new Error(`Get cache stats failed: ${res.statusText}`);
    return res.json();
  },

  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  }
};
