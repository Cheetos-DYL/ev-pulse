import { useState, useEffect, useCallback } from 'react';
import { api } from './api';
import type { Article, Stats, Report } from './api';
import './index.css';

type Page = 'dashboard' | 'articles' | 'reports' | 'settings';

const REGIONS: Record<string, string> = {
  korea: '🇰🇷 Korea',
  uae: '🇦🇪 UAE / ME',
  southeast_asia: '🌏 SE Asia',
  japan: '🇯🇵 Japan',
  australia: '🇦🇺 Australia',
  taiwan: '🇹🇼 Taiwan',
  africa: '🌍 Africa',
  brazil: '🇧🇷 Brazil',
  mexico: '🇲🇽 Mexico',
};

const CATEGORIES: Record<string, string> = {
  service: '⚡ Service',
  trend: '📈 Trend',
  policy: '📋 Policy',
};

export default function App() {
  const [page, setPage] = useState<Page>('dashboard');

  return (
    <div className="app">
      <nav className="top-nav">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          EV Pulse
        </div>
        <div className="nav-links">
          {(['dashboard', 'articles', 'reports', 'settings'] as Page[]).map(p => (
            <button
              key={p}
              className={`nav-link ${page === p ? 'active' : ''}`}
              onClick={() => setPage(p)}
            >
              {p === 'dashboard' ? '📊 Dashboard' : p === 'articles' ? '📰 Articles' : p === 'reports' ? '📑 Reports' : '⚙️ Settings'}
            </button>
          ))}
        </div>
      </nav>
      <div className="container">
        {page === 'dashboard' && <Dashboard />}
        {page === 'articles' && <Articles />}
        {page === 'reports' && <Reports />}
        {page === 'settings' && <Settings />}
      </div>
    </div>
  );
}

/* ─── Dashboard ──────────────────────────────── */

function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /> Loading...</div>;
  if (!stats) return <div className="empty-state"><div className="empty-state-icon">📊</div><div className="empty-state-text">No data yet</div></div>;

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Dashboard</h1>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.total_articles}</div>
          <div className="stat-label">Total Articles</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.by_region.length}</div>
          <div className="stat-label">Active Regions</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.by_category.length}</div>
          <div className="stat-label">Categories</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>By Region</h3>
          {stats.by_region.map(r => (
            <div key={r.region} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span>{REGIONS[r.region] || r.region}</span>
              <span style={{ color: 'var(--accent-light)', fontWeight: 600 }}>{r.count}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>By Category</h3>
          {stats.by_category.map(c => (
            <div key={c.category} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span>{CATEGORIES[c.category] || c.category}</span>
              <span style={{ color: 'var(--accent-light)', fontWeight: 600 }}>{c.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Articles ───────────────────────────────── */

function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [minScore, setMinScore] = useState<number>(0);

  const loadArticles = useCallback(() => {
    setLoading(true);
    api.articles({
      region: regionFilter || undefined,
      category: categoryFilter || undefined,
      min_relevance: minScore,
      limit: 100,
    }).then(res => setArticles(res.articles)).finally(() => setLoading(false));
  }, [regionFilter, categoryFilter, minScore]);

  useEffect(() => { loadArticles(); }, [loadArticles]);

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Articles</h1>

      <div className="filters">
        <button className={`filter-btn ${!regionFilter ? 'active' : ''}`} onClick={() => setRegionFilter('')}>All Regions</button>
        {Object.entries(REGIONS).map(([k, v]) => (
          <button key={k} className={`filter-btn ${regionFilter === k ? 'active' : ''}`} onClick={() => setRegionFilter(k)}>{v}</button>
        ))}
      </div>
      <div className="filters">
        <button className={`filter-btn ${!categoryFilter ? 'active' : ''}`} onClick={() => setCategoryFilter('')}>All Categories</button>
        {Object.entries(CATEGORIES).map(([k, v]) => (
          <button key={k} className={`filter-btn ${categoryFilter === k ? 'active' : ''}`} onClick={() => setCategoryFilter(k)}>{v}</button>
        ))}
        <button className={`filter-btn ${minScore >= 5 ? 'active' : ''}`} onClick={() => setMinScore(minScore >= 5 ? 0 : 5)}>Score ≥ 5</button>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📰</div>
          <div className="empty-state-text">No articles yet. Run collection first!</div>
        </div>
      ) : (
        articles.map(article => (
          <ArticleCard key={article.id} article={article} />
        ))
      )}
    </div>
  );
}

function ArticleCard({ article }: { article: Article }) {
  const scoreClass = article.relevance_score >= 7 ? 'high' : article.relevance_score >= 4 ? 'medium' : 'low';
  const catClass = article.category || 'other';

  return (
    <div className="card">
      <div className="card-header">
        <a href={article.url} target="_blank" rel="noopener noreferrer" className="card-title" style={{ textDecoration: 'none', color: 'inherit' }}>
          {article.title}
        </a>
        <span className={`badge-score badge ${scoreClass}`}>
          {article.relevance_score.toFixed(1)}
        </span>
      </div>
      {article.summary && <div className="card-summary">{article.summary}</div>}
      <div className="card-meta">
        <span className="badge badge-region">{REGIONS[article.region] || article.region}</span>
        <span className={`badge badge-category ${catClass}`}>{CATEGORIES[article.category] || article.category}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{article.source}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{article.collected_at?.slice(0, 10)}</span>
      </div>
    </div>
  );
}

/* ─── Reports ────────────────────────────────── */

function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.reports().then(res => setReports(res.reports)).finally(() => setLoading(false));
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await api.generateReport();
      const newReport: Report = {
        id: 0,
        month: res.month,
        content: res.content,
        article_count: 0,
        created_at: new Date().toISOString(),
      };
      setSelectedReport(newReport);
      api.reports().then(r => setReports(r.reports));
    } catch (e) {
      alert('Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /> Loading...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1>Reports</h1>
        <button className="btn btn-primary" onClick={handleGenerate} disabled={generating}>
          {generating ? '⏳ Generating...' : '✨ Generate Monthly Report'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedReport ? '300px 1fr' : '1fr', gap: 16 }}>
        <div>
          {reports.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📑</div>
              <div className="empty-state-text">No reports yet. Generate one!</div>
            </div>
          ) : (
            reports.map(report => (
              <div
                key={report.month}
                className={`card ${selectedReport?.month === report.month ? 'selected' : ''}`}
                style={{ cursor: 'pointer', borderColor: selectedReport?.month === report.month ? 'var(--accent)' : undefined }}
                onClick={() => setSelectedReport(report)}
              >
                <div style={{ fontWeight: 600 }}>{report.month}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{report.article_count} articles</div>
              </div>
            ))
          )}
        </div>

        {selectedReport && (
          <div className="card">
            <div className="report-content" dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedReport.content) }} />
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Settings ───────────────────────────────── */

function Settings() {
  const [collecting, setCollecting] = useState(false);
  const [lastResult, setLastResult] = useState<string>('');

  const handleCollect = async (region?: string) => {
    setCollecting(true);
    setLastResult('');
    try {
      const res = await api.collect(region);
      setLastResult(`✅ Collected: ${res.stored} new articles from ${region || 'all regions'}`);
    } catch (e: any) {
      setLastResult(`❌ Error: ${e.message}`);
    } finally {
      setCollecting(false);
    }
  };

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Settings</h1>

      <div className="card">
        <h3 style={{ marginBottom: 16 }}>📰 Collect Articles</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>
          Fetch new articles from RSS feeds and web sources.
        </p>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
          <button className="btn btn-primary" onClick={() => handleCollect()} disabled={collecting}>
            {collecting ? '⏳ Collecting...' : '🔄 Collect All Regions'}
          </button>
          {Object.entries(REGIONS).map(([k, v]) => (
            <button key={k} className="btn btn-secondary" onClick={() => handleCollect(k)} disabled={collecting}>
              {v}
            </button>
          ))}
        </div>
        {lastResult && (
          <div style={{ padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 14 }}>
            {lastResult}
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginBottom: 16 }}>ℹ️ About</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.8 }}>
          <strong>EV Pulse</strong> monitors EV charging services, market trends, and policy changes across 13 emerging markets.
          Articles are collected from RSS feeds, filtered by relevance using AI, and archived for analysis.
          Monthly reports summarize the most important developments.
        </p>
      </div>
    </div>
  );
}

/* ─── Markdown renderer (basic) ──────────────── */

function renderMarkdown(md: string): string {
  return md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.*$)/gm, '<li>$2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}
