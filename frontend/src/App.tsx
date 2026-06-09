import { useState, useEffect, useCallback } from 'react';
import { api, REGION_META } from './api';
import type { Article, Stats, Report, Trend, ComparisonResult, TimelineEntry } from './api';
import './index.css';

type Page = 'home' | 'articles' | 'reports' | 'compare' | 'regions' | 'region-detail' | 'report-detail';

const CATEGORIES: Record<string, string> = {
  service: '⚡ Service',
  trend: '📈 Trend',
  policy: '📋 Policy',
};

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function fmtMonth(m: string) {
  const [y, mm] = m.split('-');
  return `${MONTHS[parseInt(mm) - 1]} ${y}`;
}

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [regionKey, setRegionKey] = useState<string>('');
  const [reportMonth, setReportMonth] = useState<string>('');

  const navigate = (p: Page, param?: string) => {
    setPage(p);
    if (p === 'region-detail' && param) setRegionKey(param);
    if (p === 'report-detail' && param) setReportMonth(param);
  };

  return (
    <div className="app">
      <nav className="top-nav">
        <div className="logo" onClick={() => navigate('home')} style={{ cursor: 'pointer' }}>
          <span className="logo-icon">⚡</span>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>EV Pulse</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>Charging Intelligence</div>
          </div>
        </div>
        <div className="nav-links">
          {(['home', 'articles', 'reports', 'compare', 'regions'] as Page[]).map(p => (
            <button
              key={p}
              className={`nav-link ${page === p ? 'active' : ''}`}
              onClick={() => navigate(p)}
            >
              {p === 'home' ? '🏠 Home' : p === 'articles' ? '📰 Articles' : p === 'reports' ? '📑 Reports' : p === 'compare' ? '📊 Compare' : '🌍 Regions'}
            </button>
          ))}
        </div>
      </nav>
      <div className="container">
        {page === 'home' && <HomePage onNavigate={navigate} />}
        {page === 'articles' && <ArticlesPage />}
        {page === 'reports' && <ReportsPage onNavigate={navigate} />}
        {page === 'report-detail' && <ReportDetailPage month={reportMonth} onBack={() => navigate('reports')} />}
        {page === 'compare' && <ComparePage />}
        {page === 'regions' && <RegionsPage onNavigate={navigate} />}
        {page === 'region-detail' && <RegionDetailPage regionKey={regionKey} />}
      </div>
      <footer className="footer">
        <p>⚡ EV Pulse — EV Charging Intelligence for Emerging Markets</p>
        <p className="footer-sub">Automatically collected & analyzed monthly • Data from public news sources</p>
      </footer>
    </div>
  );
}

/* ════════════════════════════════════════════════
   Home — Public-facing landing
   ════════════════════════════════════════════════ */

function HomePage({ onNavigate }: { onNavigate: (p: Page, param?: string) => void }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [latestArticles, setLatestArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats().then(s => {
      setStats(s);
    });
    api.articles({ limit: 8, min_relevance: 5 }).then(a => {
      setLatestArticles(a.articles);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /> Loading intelligence...</div>;

  return (
    <div>
      {/* Hero */}
      <div className="hero">
        <h1 className="hero-title">EV Charging Intelligence</h1>
        <p className="hero-subtitle">Monitoring EV charging services, market trends, and policy across 9 emerging markets</p>
        {stats && (
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">{stats.total_articles}</span>
              <span className="hero-stat-label">Articles Tracked</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">{stats.by_region.length}</span>
              <span className="hero-stat-label">Active Regions</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">{stats.latest_report?.month ? fmtMonth(stats.latest_report.month) : '—'}</span>
              <span className="hero-stat-label">Latest Report</span>
            </div>
          </div>
        )}
      </div>

      {/* Latest Report */}
      {stats?.latest_report && (
        <div className="card card-accent" style={{ cursor: 'pointer' }} onClick={() => onNavigate('report-detail', stats.latest_report!.month)}>
          <div className="card-header">
            <h2>📑 Latest Report — {fmtMonth(stats.latest_report.month)}</h2>
            <span className="badge badge-region">{stats.latest_report.article_count} articles</span>
          </div>
          <div className="report-excerpt">
            {stats.latest_report.content.slice(0, 600)}
            {stats.latest_report.content.length > 600 ? '...' : ''}
          </div>
          <div className="card-footer-link">Read full report →</div>
        </div>
      )}

      {/* Region Overview */}
      <h2 style={{ margin: '32px 0 16px' }}>🌍 Regions</h2>
      <div className="region-grid">
        {Object.entries(REGION_META).map(([key, meta]) => {
          const regionStat = stats?.by_region.find(r => r.region === key);
          return (
            <div key={key} className="region-card" onClick={() => onNavigate('region-detail', key)}>
              <div className="region-card-flag">{meta.flag}</div>
              <div className="region-card-name">{meta.name}</div>
              <div className="region-card-count">{regionStat?.count || 0} articles</div>
            </div>
          );
        })}
      </div>

      {/* Latest Articles */}
      <h2 style={{ margin: '32px 0 16px' }}>📰 Latest Intelligence</h2>
      {latestArticles.map(a => (
        <div key={a.id} className="card">
          <div className="card-header">
            <a href={a.url} target="_blank" rel="noopener noreferrer" className="card-title">
              {a.title}
            </a>
            <span className={`badge-score badge ${a.relevance_score >= 7 ? 'high' : 'medium'}`}>
              {a.relevance_score.toFixed(1)}
            </span>
          </div>
          {a.summary && <div className="card-summary">{a.summary}</div>}
          <div className="card-meta">
            <span className="badge badge-region">{REGION_META[a.region]?.flag} {REGION_META[a.region]?.name || a.region}</span>
            <span className={`badge badge-category ${a.category}`}>{CATEGORIES[a.category] || a.category}</span>
            <span className="card-source">{a.source}</span>
            <span className="card-date">{a.collected_at?.slice(0, 10)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Articles
   ════════════════════════════════════════════════ */

function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [minScore, setMinScore] = useState<number>(0);

  const load = useCallback(() => {
    setLoading(true);
    api.articles({
      region: regionFilter || undefined,
      category: categoryFilter || undefined,
      min_relevance: minScore,
      limit: 100,
    }).then(res => setArticles(res.articles)).finally(() => setLoading(false));
  }, [regionFilter, categoryFilter, minScore]);

  useEffect(() => { load(); }, [load]);

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>📰 Article Archive</h1>

      <div className="filters">
        <button className={`filter-btn ${!regionFilter ? 'active' : ''}`} onClick={() => setRegionFilter('')}>All Regions</button>
        {Object.entries(REGION_META).map(([k, v]) => (
          <button key={k} className={`filter-btn ${regionFilter === k ? 'active' : ''}`} onClick={() => setRegionFilter(k)}>{v.flag} {v.name}</button>
        ))}
      </div>
      <div className="filters">
        <button className={`filter-btn ${!categoryFilter ? 'active' : ''}`} onClick={() => setCategoryFilter('')}>All Categories</button>
        {Object.entries(CATEGORIES).map(([k, v]) => (
          <button key={k} className={`filter-btn ${categoryFilter === k ? 'active' : ''}`} onClick={() => setCategoryFilter(k)}>{v}</button>
        ))}
        <button className={`filter-btn ${minScore >= 5 ? 'active' : ''}`} onClick={() => setMinScore(minScore >= 5 ? 0 : 5)}>⭐ Relevance ≥ 5</button>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📰</div>
          <div className="empty-state-text">No articles found. Check back after the next collection cycle.</div>
        </div>
      ) : (
        <div className="article-count">Showing {articles.length} articles</div>
      )}
      {articles.map(a => (
        <div key={a.id} className="card">
          <div className="card-header">
            <a href={a.url} target="_blank" rel="noopener noreferrer" className="card-title">
              {a.title}
            </a>
            <span className={`badge-score badge ${a.relevance_score >= 7 ? 'high' : a.relevance_score >= 4 ? 'medium' : 'low'}`}>
              {a.relevance_score.toFixed(1)}
            </span>
          </div>
          {a.summary && <div className="card-summary">{a.summary}</div>}
          <div className="card-meta">
            <span className="badge badge-region">{REGION_META[a.region]?.flag} {REGION_META[a.region]?.name || a.region}</span>
            <span className={`badge badge-category ${a.category}`}>{CATEGORIES[a.category] || a.category}</span>
            <span className="card-source">{a.source}</span>
            <span className="card-date">{a.collected_at?.slice(0, 10)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Reports
   ════════════════════════════════════════════════ */

function ReportsPage({ onNavigate }: { onNavigate: (p: Page, param?: string) => void }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.reports().then(res => setReports(res.reports)).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>📑 Monthly Reports</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
        Monthly digests of EV charging market intelligence across all regions
      </p>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : reports.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📑</div>
          <div className="empty-state-text">No reports generated yet. Reports are created monthly.</div>
        </div>
      ) : (
        <div className="report-list">
          {reports.map((report, i) => {
            const prev = i < reports.length - 1 ? reports[i + 1] : null;
            return (
              <div key={report.month} className="card" style={{ cursor: 'pointer' }} onClick={() => onNavigate('report-detail', report.month)}>
                <div className="report-list-header">
                  <h2 className="report-list-month">{fmtMonth(report.month)}</h2>
                  <div className="report-list-meta">
                    <span className="badge badge-region">{report.article_count} articles</span>
                    {prev && (
                      <span className="badge badge-category trend">
                        {report.article_count > prev.article_count ? '📈 +' : report.article_count < prev.article_count ? '📉 ' : '➡️ '}
                        {Math.abs(report.article_count - prev.article_count)} vs {fmtMonth(prev.month)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="report-excerpt">
                  {report.content.slice(0, 300)}
                  {report.content.length > 300 ? '...' : ''}
                </div>
                <div className="card-footer-link">Read full report →</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Report Detail
   ════════════════════════════════════════════════ */

function ReportDetailPage({ month, onBack }: { month: string; onBack: () => void }) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.report(month).then(setReport).finally(() => setLoading(false));
  }, [month]);

  return (
    <div>
      <button className="btn btn-secondary" onClick={onBack} style={{ marginBottom: 24 }}>
        ← Back to Reports
      </button>
      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : !report ? (
        <div className="empty-state">
          <div className="empty-state-icon">📑</div>
          <div className="empty-state-text">Report not found for {month}</div>
        </div>
      ) : (
        <div className="card">
          <h1 style={{ marginBottom: 8, color: 'var(--accent-light)' }}>EV Pulse — {fmtMonth(month)}</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: 24, fontSize: 14 }}>
            {report.article_count} articles • Generated {report.created_at?.slice(0, 10)}
          </p>
          <div className="report-content" dangerouslySetInnerHTML={{ __html: renderMarkdown(report.content) }} />
        </div>
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Compare — Month-over-Month
   ════════════════════════════════════════════════ */

function ComparePage() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [monthA, setMonthA] = useState('');
  const [monthB, setMonthB] = useState('');
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.trends(24).then(res => {
      setTrends(res.trends);
      const months = [...new Set(res.trends.map(t => t.month))].sort().reverse();
      setAvailableMonths(months);
      if (months.length >= 2) {
        setMonthA(months[1]);
        setMonthB(months[0]);
      }
    });
    api.timeline().then(res => setTimeline(res.timeline));
    setLoading(false);
  }, []);

  useEffect(() => {
    if (monthA && monthB) {
      api.compare(monthA, monthB).then(setComparison);
    }
  }, [monthA, monthB]);

  if (loading) return <div className="loading"><div className="spinner" /> Loading...</div>;

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>📊 Month-over-Month Comparison</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
        Track how EV charging news volume and focus shift across regions over time
      </p>

      {/* Month selector */}
      {availableMonths.length >= 2 && (
        <div className="compare-selectors">
          <div className="compare-selector">
            <label>Earlier Month</label>
            <select value={monthA} onChange={e => setMonthA(e.target.value)} className="select-styled">
              {availableMonths.map(m => <option key={m} value={m}>{fmtMonth(m)}</option>)}
            </select>
          </div>
          <div className="compare-arrow">→</div>
          <div className="compare-selector">
            <label>Later Month</label>
            <select value={monthB} onChange={e => setMonthB(e.target.value)} className="select-styled">
              {availableMonths.map(m => <option key={m} value={m}>{fmtMonth(m)}</option>)}
            </select>
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <>
          <div className="compare-header">
            <div className={`compare-change ${comparison.change_percent >= 0 ? 'up' : 'down'}`}>
              {comparison.change_percent >= 0 ? '📈' : '📉'} {Math.abs(comparison.change_percent)}% change
            </div>
            <div className="compare-totals">
              <span>{fmtMonth(comparison.month_a)}: <strong>{comparison.a.total}</strong> articles</span>
              <span style={{ margin: '0 16px', color: 'var(--text-muted)' }}>→</span>
              <span>{fmtMonth(comparison.month_b)}: <strong>{comparison.b.total}</strong> articles</span>
            </div>
          </div>

          <h3 style={{ margin: '24px 0 12px' }}>By Region</h3>
          <div className="compare-grid">
            {Object.keys(REGION_META).map(region => {
              const aData = comparison.a.regions[region];
              const bData = comparison.b.regions[region];
              const aCount = aData?.count || 0;
              const bCount = bData?.count || 0;
              const diff = bCount - aCount;
              const meta = REGION_META[region];
              return (
                <div key={region} className="compare-region-card">
                  <div className="compare-region-header">
                    <span>{meta.flag} {meta.name}</span>
                    <span className={`badge ${diff > 0 ? 'badge-category trend' : diff < 0 ? 'badge-category policy' : ''}`}>
                      {diff > 0 ? `+${diff}` : diff < 0 ? diff : '—'}
                    </span>
                  </div>
                  <div className="compare-bars">
                    <div className="compare-bar-group">
                      <div className="compare-bar-label">{fmtMonth(comparison.month_a)}</div>
                      <div className="compare-bar-track">
                        <div className="compare-bar compare-bar-a" style={{ width: `${Math.min(100, (aCount / Math.max(bCount, 1)) * 100)}%` }} />
                      </div>
                      <div className="compare-bar-value">{aCount}</div>
                    </div>
                    <div className="compare-bar-group">
                      <div className="compare-bar-label">{fmtMonth(comparison.month_b)}</div>
                      <div className="compare-bar-track">
                        <div className="compare-bar compare-bar-b" style={{ width: `${Math.min(100, (bCount / Math.max(aCount, 1)) * 100)}%` }} />
                      </div>
                      <div className="compare-bar-value">{bCount}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Timeline */}
      {timeline.length > 0 && (
        <div className="card" style={{ marginTop: 32 }}>
          <h3 style={{ marginBottom: 16 }}>Historical Timeline</h3>
          <div className="timeline">
            {timeline.map(entry => (
              <div key={entry.month} className="timeline-item">
                <div className="timeline-month">{fmtMonth(entry.month as string)}</div>
                <div className="timeline-bars">
                  {Object.keys(REGION_META).map(region => {
                    const count = (entry[region] as number) || 0;
                    if (count === 0) return null;
                    return (
                      <div key={region} className="timeline-bar-item" title={`${REGION_META[region].name}: ${count}`}>
                        <div className="timeline-bar-fill" style={{ height: `${Math.min(100, count * 10)}px`, background: regionColors(region) }} />
                        <div className="timeline-bar-label">{count}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const REGION_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#a855f7', '#84cc16', '#14b8a6'];
function regionColors(region: string) {
  const idx = Object.keys(REGION_META).indexOf(region);
  return REGION_COLORS[idx % REGION_COLORS.length];
}

/* ════════════════════════════════════════════════
   Regions
   ════════════════════════════════════════════════ */

function RegionsPage({ onNavigate }: { onNavigate: (p: Page, param?: string) => void }) {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => { api.stats().then(setStats); }, []);

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>🌍 Regions</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
        Country-specific EV charging market intelligence
      </p>
      <div className="region-grid-full">
        {Object.entries(REGION_META).map(([key, meta]) => {
          const regionStat = stats?.by_region.find(r => r.region === key);
          return (
            <div key={key} className="region-card-full" onClick={() => onNavigate('region-detail', key)}>
              <div className="region-card-flag-full">{meta.flag}</div>
              <div className="region-card-info">
                <div className="region-card-name-full">{meta.name}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                  {regionStat?.count || 0} articles tracked
                </div>
              </div>
              <span className="region-card-arrow">→</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════
   Region Detail
   ════════════════════════════════════════════════ */

function RegionDetailPage({ regionKey }: { regionKey: string }) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [loading, setLoading] = useState(true);
  const meta = REGION_META[regionKey];

  useEffect(() => {
    Promise.all([
      api.articles({ region: regionKey, limit: 50 }),
      api.trends(12),
    ]).then(([a, t]) => {
      setArticles(a.articles);
      setTrends(t.trends.filter(tr => tr.region === regionKey));
    }).finally(() => setLoading(false));
  }, [regionKey]);

  if (loading) return <div className="loading"><div className="spinner" /> Loading...</div>;

  return (
    <div>
      <div className="region-detail-header">
        <span style={{ fontSize: 48 }}>{meta?.flag}</span>
        <div>
          <h1 style={{ margin: 0 }}>{meta?.name}</h1>
          <p style={{ color: 'var(--text-secondary)', margin: '4px 0 0' }}>
            {articles.length} articles • {trends.length} months tracked
          </p>
        </div>
      </div>

      {/* Trend Chart */}
      {trends.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: 16 }}>📈 Monthly Article Count</h3>
          <div className="timeline">
            {trends.sort((a, b) => a.month.localeCompare(b.month)).map(t => (
              <div key={t.month} className="timeline-item">
                <div className="timeline-month">{fmtMonth(t.month)}</div>
                <div className="timeline-bars">
                  <div className="timeline-bar-item">
                    <div className="timeline-bar-fill" style={{ height: `${Math.min(100, t.article_count * 15)}px`, background: regionColors(regionKey) }} />
                    <div className="timeline-bar-label">{t.article_count}</div>
                  </div>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                  Avg relevance: {t.avg_relevance.toFixed(1)} • {t.top_category}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <h3 style={{ margin: '24px 0 12px' }}>📰 Articles</h3>
      {articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📰</div>
          <div className="empty-state-text">No articles tracked for this region yet.</div>
        </div>
      ) : (
        articles.map(a => (
          <div key={a.id} className="card">
            <div className="card-header">
              <a href={a.url} target="_blank" rel="noopener noreferrer" className="card-title">{a.title}</a>
              <span className={`badge-score badge ${a.relevance_score >= 7 ? 'high' : a.relevance_score >= 4 ? 'medium' : 'low'}`}>
                {a.relevance_score.toFixed(1)}
              </span>
            </div>
            {a.summary && <div className="card-summary">{a.summary}</div>}
            <div className="card-meta">
              <span className={`badge badge-category ${a.category}`}>{CATEGORIES[a.category] || a.category}</span>
              <span className="card-source">{a.source}</span>
              <span className="card-date">{a.collected_at?.slice(0, 10)}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Markdown Renderer
   ════════════════════════════════════════════════ */

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
