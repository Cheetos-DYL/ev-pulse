import { useState, useEffect, useCallback, useRef } from 'react';
import { api, REGION_META } from './api';
import type { Article, Stats, Report, Trend, ComparisonResult, TimelineEntry } from './api';
import * as d3 from 'd3';
import './index.css';

type Page = 'home' | 'articles' | 'reports' | 'compare' | 'regions' | 'graph' | 'region-detail' | 'report-detail';

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
  government_policy: 'Policy',
  ma_partnership: 'M&A',
  charger_install: 'Install',
  charging_standards: 'Standards',
  grid_pricing: 'Grid',
  ev_sales_stats: 'Stats',
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
            {(['home', 'articles', 'reports', 'compare', 'graph', 'regions'] as Page[]).map(p => (
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
        {page === 'graph' && <GraphPage onNavigate={navigate} />}
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
  const [searchQuery, setSearchQuery] = useState<string>('');
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback((search?: string) => {
    setLoading(true);
    const q = search ?? searchQuery;
    if (q.trim()) {
      api.search({
        q: q.trim(),
        region: regionFilter || undefined,
        category: categoryFilter || undefined,
        min_relevance: minScore,
        limit: 100,
      }).then(res => setArticles(res.articles)).finally(() => setLoading(false));
    } else {
      api.articles({
        region: regionFilter || undefined,
        category: categoryFilter || undefined,
        min_relevance: minScore,
        limit: 100,
      }).then(res => setArticles(res.articles)).finally(() => setLoading(false));
    }
  }, [regionFilter, categoryFilter, minScore, searchQuery]);

  useEffect(() => { load(); }, [load]);

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => load(value), 300);
  };

  const CATEGORY_KEYS = Object.keys(CATEGORIES);
  const CATEGORY_LABELS = CATEGORIES;

  return (
    <div>
      <h1 className="page-title">Article Archive</h1>
      <p className="page-subtitle">Browse EV charging news from all regions</p>

      <div className="search-bar" style={{ marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Search articles by keyword, company, country..."
          value={searchQuery}
          onChange={e => handleSearch(e.target.value)}
          className="search-input"
          style={{
            width: '100%', padding: '10px 16px', borderRadius: 8,
            border: '1px solid var(--color-border)', fontSize: 15,
            background: 'var(--color-bg)', color: 'var(--color-ink)',
          }}
        />
      </div>

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
        {CATEGORY_KEYS.map(k => (
          <button key={k} className={`filter-btn ${categoryFilter === k ? 'active' : ''}`} onClick={() => setCategoryFilter(k)}>
            {CATEGORY_LABELS[k]}
          </button>
        ))}
        <button className={`filter-btn ${minScore >= 30 ? 'active' : ''}`} onClick={() => setMinScore(minScore >= 30 ? 0 : 30)}>Score ≥ 30</button>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /> Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📰</div>
          <div className="empty-state-text">No articles found{searchQuery ? ' matching your search' : ''}. Check back after the next collection cycle.</div>
        </div>
      ) : (
        <>
          <p className="article-count">{searchQuery ? `Search results: ${articles.length} articles` : `Showing ${articles.length} articles`}</p>
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
   Knowledge Graph (Obsidian-style)
   ════════════════════════════════════════════════ */

function GraphPage({ onNavigate }: { onNavigate: (p: Page, param?: string) => void }) {
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[]; stats: any } | null>(null);
  const [loading, setLoading] = useState(true);
  const [hovered, setHovered] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/api/graph?limit=200').then(r => r.json()).then(data => {
      setGraphData(data);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!graphData || !svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = Math.max(500, window.innerHeight - 250);
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Color scales
    const colorMap: Record<string, string> = {
      article: '#60a5fa',
      keyword: '#34d399',
      region: '#fbbf24',
    };

    // Build simulation
    const nodes = graphData.nodes.map(n => ({ ...n }));
    const edges = graphData.edges.map(e => ({ ...e }));
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id((d: any) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(20));

    const link = svg.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#555')
      .attr('stroke-width', 0.8)
      .attr('stroke-opacity', 0.4);

    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .style('cursor', 'pointer')
      .on('mouseover', (_, d) => setHovered(d.id))
      .on('mouseout', () => setHovered(null))
      .on('click', (_, d) => {
        if (d.type === 'article') {
          setSelected(d.id === selected ? null : d.id);
        } else {
          // Toggle keyword/region selection to highlight connected articles
          setSelected(d.id === selected ? null : d.id);
        }
      })
      .call(d3.drag<any, any>()
        .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
      );

    // Circles
    node.append('circle')
      .attr('r', d => d.type === 'article' ? 6 : d.type === 'region' ? 10 : 5)
      .attr('fill', d => colorMap[d.type] || '#888')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    // Labels (show on hover or for selected nodes)
    node.append('text')
      .text(d => {
        const label = d.label || '';
        return label.length > 25 ? label.slice(0, 24) + '…' : label;
      })
      .attr('x', d => d.type === 'article' ? 10 : 12)
      .attr('y', 4)
      .attr('font-size', '11px')
      .attr('fill', '#ccc')
      .attr('opacity', d => (d.id === hovered || d.id === selected) ? 1 : 0)
      .style('pointer-events', 'none');

    // Highlight connected nodes when something is selected
    const tick = () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);

      // Opacity based on selection
      if (selected) {
        const connectedIds = new Set<string>();
        connectedIds.add(selected);
        edges.forEach(e => {
          const sid = typeof e.source === 'object' ? e.source.id : e.source;
          const tid = typeof e.target === 'object' ? e.target.id : e.target;
          if (sid === selected) connectedIds.add(tid);
          if (tid === selected) connectedIds.add(sid);
        });

        link.attr('stroke-opacity', (e: any) => {
          const sid = typeof e.source === 'object' ? e.source.id : e.source;
          const tid = typeof e.target === 'object' ? e.target.id : e.target;
          return (sid === selected || tid === selected) ? 0.8 : 0.05;
        });

        node.select('circle').attr('opacity', (d: any) => connectedIds.has(d.id) ? 1 : 0.15);
        node.select('text').attr('opacity', (d: any) => connectedIds.has(d.id) ? 1 : 0);
      } else {
        link.attr('stroke-opacity', hovered ? (e: any) => {
          const sid = typeof e.source === 'object' ? e.source.id : e.source;
          const tid = typeof e.target === 'object' ? e.target.id : e.target;
          return (sid === hovered || tid === hovered) ? 0.8 : 0.1;
        } : 0.3);
        node.select('circle').attr('opacity', hovered ? (d: any) => d.id === hovered ? 1 : 0.3 : 1);
      }
    };

    simulation.on('tick', tick);

    // Zoom
    svg.call(d3.zoom<any, any>()
      .extent([[0, 0], [width, height]])
      .scaleExtent([0.3, 4])
      .on('zoom', (e) => svg.selectAll('g').attr('transform', e.transform))
    );

    // Cleanup
    return () => { simulation.stop(); };
  }, [graphData, hovered, selected]);

  // Legend info
  const stats = graphData?.stats;

  return (
    <div className="page">
      <div className="graph-header">
        <h2 className="page-title">Knowledge Graph</h2>
        <div className="graph-legend">
          <span><span className="dot" style={{ background: '#60a5fa' }} /> Article</span>
          <span><span className="dot" style={{ background: '#34d399' }} /> Keyword</span>
          <span><span className="dot" style={{ background: '#fbbf24' }} /> Region</span>
          {stats && <span className="stats">{stats.articles} articles · {stats.keywords} keywords · {stats.regions} regions</span>}
        </div>
      </div>
      {loading ? (
        <div className="loading">Loading graph...</div>
      ) : (
        <div className="graph-container" ref={containerRef}>
          <svg ref={svgRef} width="100%" height={Math.max(500, typeof window !== 'undefined' ? window.innerHeight - 250 : 500)} />
          {selected && (
            <div className="graph-detail">
              <button className="close-btn" onClick={() => setSelected(null)}>✕</button>
              {graphData?.nodes.find(n => n.id === selected)?.type === 'article' ? (
                <ArticleNodeDetail nodeId={selected} graphData={graphData!} onNavigate={onNavigate} />
              ) : (
                <KeywordNodeDetail nodeId={selected} graphData={graphData!} />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ArticleNodeDetail({ nodeId, graphData, onNavigate }: { nodeId: string; graphData: any; onNavigate: any }) {
  const node = graphData.nodes.find((n: any) => n.id === nodeId);
  if (!node) return null;
  const regionMeta = REGION_META[node.region] || {};
  return (
    <div className="node-detail">
      <h3>{node.label}</h3>
      {node.title_original && node.title_original !== node.label && (
        <p className="original-title">{node.title_original}</p>
      )}
      <p className="meta">{regionMeta.flag} {regionMeta.name || node.region} · Score {node.relevance}</p>
      <a href={node.url} target="_blank" rel="noopener noreferrer" className="btn-link">Read Article →</a>
    </div>
  );
}

function KeywordNodeDetail({ nodeId, graphData }: { nodeId: string; graphData: any }) {
  const node = graphData.nodes.find((n: any) => n.id === nodeId);
  if (!node) return null;

  // Find connected articles
  const connArticles = graphData.edges
    .filter((e: any) => e.source === nodeId || e.target === nodeId)
    .map((e: any) => {
      const otherId = e.source === nodeId ? e.target : e.source;
      return graphData.nodes.find((n: any) => n.id === otherId);
    })
    .filter((n: any) => n && n.type === 'article');

  return (
    <div className="node-detail">
      <h3>{node.label}</h3>
      <p className="type-badge">{node.type === 'region' ? '🌍 Region' : '🔑 Keyword'}</p>
      <p className="count">{connArticles.length} related articles</p>
      <div className="related-list">
        {connArticles.slice(0, 10).map((a: any) => (
          <div key={a.id} className="related-item">
            <span className="related-title">{(a.label || '').slice(0, 50)}</span>
            <span className="related-region">{REGION_META[a.region]?.flag} {a.region}</span>
          </div>
        ))}
      </div>
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
