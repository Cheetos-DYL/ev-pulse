import { useState, useEffect, useCallback } from 'react';
import { api, REGION_META } from './api';
import type { Article, Stats, Report, Trend, ComparisonResult, TimelineEntry } from './api';
import './index.css';

type Page = 'home' | 'articles' | 'reports' | 'compare' | 'regions' | 'region-detail' | 'report-detail';

function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem('ev-pulse-theme');
    if (stored === 'dark' || stored === 'light') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ev-pulse-theme', theme);
  }, [theme]);

  const toggle = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');
  return { theme, toggle };
}

const CATEGORIES: Record<string, string> = {
  service: 'Service',
  trend: 'Trend',
  policy: 'Policy',
};

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function fmtMonth(m: string) {
  const [y, mm] = m.split('-');
  return `${MONTHS[parseInt(mm) - 1]} ${y}`;
}

function regionColor(key: string): string {
  const colors = [
    '#0075de', '#62aef0', '#2a9d99', '#1aae39',
    '#dd5b00', '#d6b6f6', '#ff64c8', '#523410', '#213183',
  ];
  const idx = Object.keys(REGION_META).indexOf(key);
  return colors[idx % colors.length];
}

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const [regionKey, setRegionKey] = useState<string>('');
  const [reportMonth, setReportMonth] = useState<string>('');
  const { theme, toggle } = useTheme();

  const navigate = (p: Page, param?: string) => {
    setPage(p);
    if (p === 'region-detail' && param) setRegionKey(param);
    if (p === 'report-detail' && param) setReportMonth(param);
  };

  return (
    <div className="app">
      <nav className="top-nav">
        <div className="nav-primary">
          <div className="logo" onClick={() => navigate('home')}>
            <span className="logo-icon">⚡</span>
            <span className="logo-text">EV Pulse</span>
          </div>
          <div className="nav-links">
            {(['home', 'articles', 'reports', 'compare', 'regions'] as Page[]).map(p => (
              <button
                key={p}
                className={`nav-link ${page === p ? 'active' : ''}`}
                onClick={() => navigate(p)}
              >
                {p === 'home' ? 'Home' : p === 'articles' ? 'Articles' : p === 'reports' ? 'Reports' : p === 'compare' ? 'Compare' : 'Regions'}
              </button>
            ))}
          </div>
          <div className="nav-right">
            <button
              className="theme-toggle"
              onClick={toggle}
              aria-label="Toggle dark mode"
            >
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <button className="nav-cta" onClick={() => navigate('home')}>
              Dashboard
            </button>
          </div>
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
        <p>EV Pulse — EV Charging Intelligence for Emerging Markets</p>
        <p className="footer-sub">Automatically collected & analyzed monthly • Data from public news sources</p>
      </footer>
    </div>
  );
}

/* ════════════════════════════════════════════════
   Home
   ════════════════════════════════════════════════ */

function HomePage({ onNavigate }: { onNavigate: (p: Page, param?: string) => void }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [latestArticles, setLatestArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats().then(s => setStats(s));
    api.articles({ limit: 6, min_relevance: 5 }).then(a => setLatestArticles(a.articles))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /> Loading intelligence...</div>;

  return (
    <div>
      {/* Hero — Editorial feature */}
      <div className="hero-feature">
        <div className="hero-eyebrow">Market Intelligence</div>
        <h1 className="hero-title">EV Charging Intelligence</h1>
        <p className="hero-subtitle">
          Monitoring EV charging services, market trends, and policy across 9 emerging markets
        </p>
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

      {/* Latest Report — Featured card */}
      {stats?.latest_report && (
        <div
          className="card card-accent"
          onClick={() => onNavigate('report-detail', stats.latest_report!.month)}
        >
          <div className="card-header">
            <span className="card-title">
              {fmtMonth(stats.latest_report.month)} Report
            </span>
            <span className="badge badge-region">{stats.latest_report.article_count} articles</span>
          </div>
          <div className="card-summary">
            {stats.latest_report.content.slice(0, 500)}
            {stats.latest_report.content.length > 500 ? '...' : ''}
          </div>
          <span className="card-footer-link">Read full report →</span>
        </div>
      )}

      {/* Regions */}
      <h2 className="section-heading">Regions</h2>
      <p style={{ color: 'var(--color-ink-muted)', fontSize: 14, marginBottom: 16, marginTop: -8 }}>
        Click any region to explore in-depth intelligence
      </p>
      <div className="region-grid">
        {Object.entries(REGION_META).map(([key, meta]) => {
          const regionStat = stats?.by_region.find(r => r.region === key);
          return (
            <div key={key} className="region-card" onClick={() => onNavigate('region-detail', key)}>
              <span className="region-card-flag">{meta.flag}</span>
              <div className="region-card-name">{meta.name}</div>
              <div className="region-card-count">{regionStat?.count || 0} articles</div>
            </div>
          );
        })}
      </div>

      {/* Latest Articles */}
      <h2 className="section-heading">Latest Intelligence</h2>
      {latestArticles.map(a => (
        <ArticleCard key={a.id} article={a} />
      ))}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Article Card
   ════════════════════════════════════════════════ */

function ArticleCard({ article }: { article: Article }) {
  const scoreClass = article.relevance_score >= 7 ? 'high' : article.relevance_score >= 4 ? 'medium' : 'low';

  return (
    <div className="card">
      <div className="card-header">
        <a href={article.url} target="_blank" rel="noopener noreferrer" className="card-title">
          {article.title}
        </a>
        <span className={`badge-score badge ${scoreClass}`}>
          {article.relevance_score.toFixed(1)}
        </span>
      </div>
      {article.summary && <div className="card-summary">{article.summary}</div>}
      <div className="card-meta">
        <span className="badge badge-region">
          {REGION_META[article.region]?.flag} {REGION_META[article.region]?.name || article.region}
        </span>
        <span className="card-meta-sep" />
        <span className={`badge badge-${article.category}`}>
          {CATEGORIES[article.category] || article.category}
        </span>
        <span className="card-meta-sep" />
        <span className="card-source">{article.source}</span>
        <span className="card-meta-sep" />
        <span className="card-date">{article.collected_at?.slice(0, 10)}</span>
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════════
   Articles Page
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
      <h1 className="page-title">Article Archive</h1>
      <p className="page-subtitle">Browse EV charging news from all regions</p>

      <div className="filters">
        <button className={`filter-btn ${!regionFilter ? 'active' : ''}`} onClick={() => setRegionFilter('')}>All</button>
        {Object.entries(REGION_META).map(([k, v]) => (
          <button key={k} className={`filter-btn ${regionFilter === k ? 'active' : ''}`} onClick={() => setRegionFilter(k)}>
            {v.flag} {v.name.split(' ')[0]}
          </button>
        ))}
      </div>
      <div className="filters" style={{ marginBottom: 24 }}>
        <button className={`filter-btn ${!categoryFilter ? 'active' : ''}`} onClick={() => setCategoryFilter('')}>All Categories</button>
        <button className={`filter-btn ${categoryFilter === 'service' ? 'active' : ''}`} onClick={() => setCategoryFilter('service')}>Service</button>
        <button className={`filter-btn ${categoryFilter === 'trend' ? 'active' : ''}`} onClick={() => setCategoryFilter('trend')}>Trend</button>
        <button className={`filter-btn ${categoryFilter === 'policy' ? 'active' : ''}`} onClick={() => setCategoryFilter('policy')}>Policy</button>
        <button className={`filter-btn ${minScore >= 5 ? 'active' : ''}`} onClick={() => setMinScore(minScore >= 5 ? 0 : 5)}>Score ≥ 5</button>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📰</div>
          <div className="empty-state-text">No articles found. Check back after the next collection cycle.</div>
        </div>
      ) : (
        <>
          <p className="article-count">Showing {articles.length} articles</p>
          {articles.map(a => <ArticleCard key={a.id} article={a} />)}
        </>
      )}
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
      <h1 className="page-title">Monthly Reports</h1>
      <p className="page-subtitle">
        Monthly digests of EV charging market intelligence across all regions
      </p>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : reports.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📑</div>
          <div className="empty-state-text">No reports generated yet. Reports are created on the 1st of each month.</div>
        </div>
      ) : (
        reports.map((report, i) => {
          const prev = i < reports.length - 1 ? reports[i + 1] : null;
          return (
            <div key={report.month} className="card card-accent" onClick={() => onNavigate('report-detail', report.month)}>
              <div className="report-list-header">
                <h2 className="report-list-month">{fmtMonth(report.month)}</h2>
                <div className="report-list-meta">
                  <span className="badge badge-region">{report.article_count} articles</span>
                  {prev && (
                    <span className="badge" style={{
                      background: report.article_count > prev.article_count
                        ? 'rgba(26, 174, 57, 0.08)'
                        : 'rgba(221, 91, 0, 0.08)',
                      color: report.article_count > prev.article_count
                        ? 'var(--color-accent-green)'
                        : 'var(--color-accent-orange)',
                      border: '1px solid transparent',
                    }}>
                      {report.article_count > prev.article_count ? '↑' : '↓'} {Math.abs(report.article_count - prev.article_count)}
                    </span>
                  )}
                </div>
              </div>
              <div className="card-summary">
                {report.content.slice(0, 280)}
                {report.content.length > 280 ? '...' : ''}
              </div>
              <span className="card-footer-link">Read full report →</span>
            </div>
          );
        })
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
      <button className="btn btn-utility" onClick={onBack} style={{ marginBottom: 24 }}>← Back</button>
      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : !report ? (
        <div className="empty-state">
          <div className="empty-state-icon">📑</div>
          <div className="empty-state-text">Report not found for {month}</div>
        </div>
      ) : (
        <div className="card" style={{ padding: 32 }}>
          <h1 style={{ marginBottom: 8, fontSize: 26, fontWeight: 700, letterSpacing: '-0.625px', color: 'var(--color-ink)' }}>
            EV Pulse — {fmtMonth(month)}
          </h1>
          <p style={{ color: 'var(--color-ink-faint)', marginBottom: 28, fontSize: 14 }}>
            {report.article_count} articles • Generated {report.created_at?.slice(0, 10)}
          </p>
          <div className="report-content" dangerouslySetInnerHTML={{ __html: renderMarkdown(report.content) }} />
        </div>
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Compare
   ════════════════════════════════════════════════ */

function ComparePage() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [monthA, setMonthA] = useState('');
  const [monthB, setMonthB] = useState('');
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);

  useEffect(() => {
    api.trends(24).then(res => {
      setTrends(res.trends);
      const months = [...new Set(res.trends.map(t => t.month))].sort().reverse();
      setAvailableMonths(months);
      if (months.length >= 2) { setMonthA(months[1]); setMonthB(months[0]); }
    });
    api.timeline().then(res => setTimeline(res.timeline));
  }, []);

  useEffect(() => {
    if (monthA && monthB) api.compare(monthA, monthB).then(setComparison);
  }, [monthA, monthB]);

  const allRegions = Object.keys(REGION_META);

  return (
    <div>
      <h1 className="page-title">Month Comparison</h1>
      <p className="page-subtitle">
        Track EV charging news volume and focus shifts across regions over time
      </p>

      {availableMonths.length >= 2 && (
        <div className="compare-selectors">
          <div className="compare-selector">
            <label>Earlier</label>
            <select value={monthA} onChange={e => setMonthA(e.target.value)} className="select-styled">
              {availableMonths.map(m => <option key={m} value={m}>{fmtMonth(m)}</option>)}
            </select>
          </div>
          <div className="compare-arrow">→</div>
          <div className="compare-selector">
            <label>Later</label>
            <select value={monthB} onChange={e => setMonthB(e.target.value)} className="select-styled">
              {availableMonths.map(m => <option key={m} value={m}>{fmtMonth(m)}</option>)}
            </select>
          </div>
        </div>
      )}

      {comparison && (
        <>
          <div className="compare-header">
            <div className={`compare-change ${comparison.change_percent >= 0 ? 'up' : 'down'}`}>
              {comparison.change_percent >= 0 ? '↑' : '↓'} {Math.abs(comparison.change_percent)}% overall change
            </div>
            <div className="compare-totals">
              {fmtMonth(comparison.month_a)}: <strong>{comparison.a.total}</strong> articles
              <span style={{ margin: '0 12px', opacity: 0.4 }}>→</span>
              {fmtMonth(comparison.month_b)}: <strong>{comparison.b.total}</strong> articles
            </div>
          </div>

          <h2 className="section-heading-sm">By Region</h2>
          <div className="compare-grid">
            {allRegions.map(region => {
              const aData = comparison.a.regions[region];
              const bData = comparison.b.regions[region];
              const aCount = aData?.count || 0;
              const bCount = bData?.count || 0;
              const diff = bCount - aCount;
              const meta = REGION_META[region];
              const maxCount = Math.max(aCount, bCount, 1);
              return (
                <div key={region} className="compare-region-card">
                  <div className="compare-region-header">
                    <span>{meta.flag} {meta.name}</span>
                    <span className="badge" style={
                      diff > 0
                        ? { background: 'rgba(26, 174, 57, 0.08)', color: 'var(--color-accent-green)', border: '1px solid rgba(26, 174, 57, 0.16)' }
                        : diff < 0
                        ? { background: 'rgba(221, 91, 0, 0.08)', color: 'var(--color-accent-orange)', border: '1px solid rgba(221, 91, 0, 0.16)' }
                        : { color: 'var(--color-ink-faint)', border: '1px solid var(--color-hairline)', background: 'transparent' }
                    }>
                      {diff > 0 ? `+${diff}` : diff < 0 ? String(diff) : '—'}
                    </span>
                  </div>
                  <div className="compare-bars">
                    <div className="compare-bar-group">
                      <span className="compare-bar-label">{fmtMonth(comparison.month_a)}</span>
                      <div className="compare-bar-track">
                        <div className="compare-bar compare-bar-a" style={{ width: `${(aCount / maxCount) * 100}%` }} />
                      </div>
                      <span className="compare-bar-value">{aCount}</span>
                    </div>
                    <div className="compare-bar-group">
                      <span className="compare-bar-label">{fmtMonth(comparison.month_b)}</span>
                      <div className="compare-bar-track">
                        <div className="compare-bar compare-bar-b" style={{ width: `${(bCount / maxCount) * 100}%` }} />
                      </div>
                      <span className="compare-bar-value">{bCount}</span>
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
        <div className="timeline-section">
          <h2 className="section-heading-sm">Historical Timeline</h2>
          <div className="timeline">
            {timeline.map(entry => (
              <div key={entry.month} className="timeline-item">
                <span className="timeline-month">{fmtMonth(entry.month as string)}</span>
                <div className="timeline-bars">
                  {allRegions.map(region => {
                    const count = (entry[region] as number) || 0;
                    if (count === 0) return null;
                    const maxForMonth = Math.max(...allRegions.map(r => (entry[r] as number) || 0), 1);
                    return (
                      <div key={region} className="timeline-bar-item" title={`${REGION_META[region].name}: ${count}`}>
                        <div className="timeline-bar-fill" style={{
                          height: `${Math.max(3, (count / maxForMonth) * 80)}px`,
                          background: regionColor(region),
                        }} />
                        {count >= 3 && <span className="timeline-bar-label">{count}</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key insights */}
      {trends.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-header" style={{ marginBottom: 8 }}>
            <span style={{ fontSize: 20, fontWeight: 600, letterSpacing: '-0.125px', color: 'var(--color-ink)' }}>
              Key Observations
            </span>
          </div>
          <div className="card-summary">
            {(() => {
              const topRegions = [...allRegions]
                .map(r => ({ region: r, count: trends.filter(t => t.region === r).reduce((s, t) => s + t.article_count, 0) }))
                .sort((a, b) => b.count - a.count);
              return (
                <ul style={{ paddingLeft: 20, listStyle: 'none' }}>
                  <li style={{ marginBottom: 6 }}>• <strong>{REGION_META[topRegions[0]?.region]?.name}</strong> has the most coverage ({topRegions[0]?.count} articles tracked)</li>
                  {comparison && (
                    <li style={{ marginBottom: 6 }}>• {comparison.change_percent >= 0 ? '↑ Article volume increased by' : '↓ Article volume decreased by'} <strong>{Math.abs(comparison.change_percent)}%</strong> month over month</li>
                  )}
                  <li>• {trends.length} monthly data points recorded across {allRegions.length} regions</li>
                </ul>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Regions
   ════════════════════════════════════════════════ */

function RegionsPage({ onNavigate }: { onNavigate: (p: Page, param?: string) => void }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.stats().then(s => setStats(s)).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-title">Regions</h1>
      <p className="page-subtitle">
        Explore EV charging market intelligence by region — each tracked separately with its own sources
      </p>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : (
        <div className="region-list">
          {Object.entries(REGION_META).map(([key, meta]) => {
            const regionStat = stats?.by_region.find(r => r.region === key);
            return (
              <div key={key} className="region-list-item" onClick={() => onNavigate('region-detail', key)}>
                <span className="region-list-flag">{meta.flag}</span>
                <div className="region-list-info">
                  <div className="region-list-name">{meta.name}</div>
                  <div style={{ color: 'var(--color-ink-faint)', fontSize: 14, marginTop: 2 }}>
                    {regionStat?.count || 0} articles tracked
                  </div>
                </div>
                <span className="region-list-arrow">→</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Region Detail
   ════════════════════════════════════════════════ */

function RegionDetailPage({ regionKey }: { regionKey: string }) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const meta = REGION_META[regionKey];

  useEffect(() => {
    api.articles({ region: regionKey, limit: 100 }).then(res => setArticles(res.articles))
      .finally(() => setLoading(false));
  }, [regionKey]);

  return (
    <div>
      <div className="region-detail-header">
        <span style={{ fontSize: 48 }}>{meta?.flag}</span>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.625px', color: 'var(--color-ink)' }}>
            {meta?.name || regionKey}
          </h1>
          <p style={{ color: 'var(--color-ink-faint)', fontSize: 14, marginTop: 4 }}>
            {articles.length} articles tracked
          </p>
        </div>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📰</div>
          <div className="empty-state-text">No articles yet for this region.</div>
        </div>
      ) : (
        articles.map(a => <ArticleCard key={a.id} article={a} />)
      )}
    </div>
  );
}

/* ════════════════════════════════════════════════
   Markdown → HTML renderer
   ════════════════════════════════════════════════ */

function renderMarkdown(text: string): string {
  if (!text) return '';

  let html = text
    // Headers
    .replace(/^###### (.*)$/gm, '<h6>$1</h6>')
    .replace(/^##### (.*)$/gm, '<h5>$1</h5>')
    .replace(/^#### (.*)$/gm, '<h4>$1</h4>')
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    // Bold & italic
    .replace(/\*\*\*(.+?)\*\*\*/g, '<em><strong>$1</strong></em>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    // Horizontal rules
    .replace(/^---$/gm, '<hr>')
    // Line breaks for paragraphs
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  return `<p>${html}</p>`;
}
