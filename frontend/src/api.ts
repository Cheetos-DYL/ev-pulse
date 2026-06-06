const API_BASE = '/api';

export interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  region: string;
  country: string | null;
  language: string;
  summary: string;
  content: string | null;
  relevance_score: number;
  category: string;
  tags: string;
  published_at: string | null;
  collected_at: string;
  analyzed: number;
}

export interface Report {
  id: number;
  month: string;
  content: string;
  article_count: number;
  created_at: string;
}

export interface Stats {
  total_articles: number;
  by_region: { region: string; count: number }[];
  by_category: { category: string; count: number }[];
}

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchJSON<{ status: string }>('/health'),

  articles: (params?: {
    region?: string;
    category?: string;
    min_relevance?: number;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.region) qs.set('region', params.region);
    if (params?.category) qs.set('category', params.category);
    if (params?.min_relevance) qs.set('min_relevance', String(params.min_relevance));
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    return fetchJSON<{ articles: Article[]; count: number }>(`/articles?${qs}`);
  },

  collect: (region?: string) =>
    fetchJSON<{ status: string; stored: number }>(
      region ? `/collect/${region}` : '/collect',
      { method: 'POST' }
    ),

  stats: () => fetchJSON<Stats>('/stats'),

  regions: () => fetchJSON<{ regions: Record<string, string> }>('/regions'),

  reports: () => fetchJSON<{ reports: Report[] }>('/reports'),

  report: (month: string) => fetchJSON<Report>(`/reports/${month}`),

  generateReport: (month?: string) =>
    fetchJSON<{ month: string; content: string }>(
      '/reports/generate',
      {
        method: 'POST',
        body: JSON.stringify({ month }),
        headers: { 'Content-Type': 'application/json' },
      }
    ),
};
