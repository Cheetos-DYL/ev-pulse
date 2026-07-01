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

export interface RegionStat {
  region: string;
  count: number;
}

export interface CategoryStat {
  category: string;
  count: number;
}

export interface Stats {
  total_articles: number;
  by_region: RegionStat[];
  by_category: CategoryStat[];
  latest_report: Report | null;
}

export interface Trend {
  month: string;
  region: string;
  article_count: number;
  avg_relevance: number;
  top_category: string;
}

export interface ComparisonResult {
  month_a: string;
  month_b: string;
  a: { total: number; regions: Record<string, { count: number; avg_relevance: number; top_category: string }> };
  b: { total: number; regions: Record<string, { count: number; avg_relevance: number; top_category: string }> };
  change_percent: number;
}

export interface TimelineEntry {
  month: string;
  [region: string]: number | string;
}

const REGION_META: Record<string, { name: string; flag: string }> = {
  korea: { name: 'South Korea', flag: '🇰🇷' },
  uae: { name: 'UAE / Middle East', flag: '🇦🇪' },
  southeast_asia: { name: 'Southeast Asia', flag: '🌏' },
  japan: { name: 'Japan', flag: '🇯🇵' },
  australia: { name: 'Australia', flag: '🇦🇺' },
  taiwan: { name: 'Taiwan', flag: '🇹🇼' },
  africa: { name: 'Africa / South Africa', flag: '🌍' },
  brazil: { name: 'Brazil', flag: '🇧🇷' },
  mexico: { name: 'Mexico / Central America', flag: '🇲🇽' },
};

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

  search: (params: {
    q: string;
    region?: string;
    category?: string;
    min_relevance?: number;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set('q', params.q);
    if (params.region) qs.set('region', params.region);
    if (params.category) qs.set('category', params.category);
    if (params.min_relevance) qs.set('min_relevance', String(params.min_relevance));
    if (params.date_from) qs.set('date_from', params.date_from);
    if (params.date_to) qs.set('date_to', params.date_to);
    if (params.limit) qs.set('limit', String(params.limit));
    if (params.offset) qs.set('offset', String(params.offset));
    return fetchJSON<{ articles: Article[]; count: number; query: string }>(`/articles/search?${qs}`);
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

  trends: (limit?: number) =>
    fetchJSON<{ trends: Trend[] }>(`/trends${limit ? `?limit=${limit}` : ''}`),

  timeline: () =>
    fetchJSON<{ timeline: TimelineEntry[] }>('/trends/timeline'),

  compare: (month_a: string, month_b?: string) =>
    fetchJSON<ComparisonResult>(`/trends/compare?month_a=${month_a}${month_b ? `&month_b=${month_b}` : ''}`),
};

export { REGION_META };
