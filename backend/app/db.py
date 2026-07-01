"""SQLite database for EV Pulse — article storage and reports."""

import sqlite3
import os
import json
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'ev_pulse.db')


def get_db_path():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                translated_title TEXT,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                region TEXT NOT NULL,
                country TEXT,
                language TEXT DEFAULT 'en',
                summary TEXT,
                content TEXT,
                relevance_score REAL DEFAULT 0,
                category TEXT CHECK(category IN ('government_policy', 'ma_partnership', 'charger_install', 'charging_standards', 'grid_pricing', 'ev_sales_stats', 'other')),
                tags TEXT DEFAULT '[]',
                published_at TEXT,
                collected_at TEXT DEFAULT (datetime('now')),
                analyzed INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                article_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region);
            CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
            CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_collected ON articles(collected_at DESC);
        """)

    # Migrate existing DBs: add columns that may not exist yet
    with get_connection() as conn:
        for col in [
            ("translated_title", "TEXT"),
            ("keywords", "TEXT DEFAULT '[]'"),
            ("why_it_matters", "TEXT DEFAULT ''"),
        ]:
            try:
                conn.execute(f"ALTER TABLE articles ADD COLUMN {col[0]} {col[1]}")
            except Exception:
                pass


@contextmanager
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_article(article: dict) -> int | None:
    """Insert article, return id or None if duplicate."""
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """INSERT INTO articles 
                   (title, translated_title, url, source, region, country, language, summary, content,
                    relevance_score, category, tags, keywords, why_it_matters, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    article['title'], article.get('translated_title'),
                    article['url'], article['source'],
                    article['region'], article.get('country'),
                    article.get('language', 'en'), article.get('summary'),
                    article.get('content'), article.get('relevance_score', 0),
                    article.get('category', 'other'),
                    str(article.get('tags', [])),
                    str(article.get('keywords', [])),
                    article.get('why_it_matters', ''),
                    article.get('published_at')
                )
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Duplicate URL


def get_articles(region=None, category=None, min_relevance=0, limit=50, offset=0):
    with get_connection() as conn:
        query = "SELECT * FROM articles WHERE relevance_score >= ?"
        params = [min_relevance]
        if region:
            query += " AND region = ?"
            params.append(region)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY collected_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        articles = []
        for row in conn.execute(query, params).fetchall():
            d = dict(row)
            # Parse JSON string fields
            for field in ['tags', 'keywords']:
                if isinstance(d.get(field), str):
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        d[field] = []
            articles.append(d)
        return articles


def search_articles(query: str, region: str = None, category: str = None,
                    min_relevance: float = 0, date_from: str = None, date_to: str = None,
                    limit: int = 50, offset: int = 0) -> list[dict]:
    """Full-text search across article title, summary, and source.
    Returns results sorted by relevance_score descending.
    """
    with get_connection() as conn:
        conditions = []
        params = []
        
        # Full-text search across title, summary, source
        if query:
            conditions.append("(title LIKE ? OR summary LIKE ? OR source LIKE ?)")
            like_q = f"%{query}%"
            params.extend([like_q, like_q, like_q])
        
        if region:
            conditions.append("region = ?")
            params.append(region)
        
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        if min_relevance > 0:
            conditions.append("relevance_score >= ?")
            params.append(min_relevance)
        
        if date_from:
            conditions.append("collected_at >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("collected_at <= ?")
            params.append(date_to)
        
        where = " AND ".join(conditions) if conditions else "1=1"
        query_sql = f"""SELECT * FROM articles WHERE {where}
                   ORDER BY relevance_score DESC, collected_at DESC
                   LIMIT ? OFFSET ?"""
        params.extend([limit, offset])
        
        articles = []
        for row in conn.execute(query_sql, params).fetchall():
            d = dict(row)
            for field in ['tags', 'keywords']:
                if isinstance(d.get(field), str):
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        d[field] = []
            articles.append(d)
        return articles

def get_article_by_id(article_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        return dict(row) if row else None


def init_trends_table():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS monthly_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                region TEXT NOT NULL,
                article_count INTEGER DEFAULT 0,
                avg_relevance REAL DEFAULT 0,
                top_category TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(month, region)
            );
            CREATE INDEX IF NOT EXISTS idx_metrics_month ON monthly_metrics(month);
            CREATE INDEX IF NOT EXISTS idx_metrics_region ON monthly_metrics(region);
        """)


def record_monthly_metrics(month: str, articles: list[dict]):
    """Record per-region metrics for trend tracking."""
    init_trends_table()
    regions = {}
    for a in articles:
        r = a['region']
        if r not in regions:
            regions[r] = {'count': 0, 'scores': [], 'categories': {}}
        regions[r]['count'] += 1
        regions[r]['scores'].append(a.get('relevance_score', 0))
        cat = a.get('category', 'other')
        regions[r]['categories'][cat] = regions[r]['categories'].get(cat, 0) + 1

    with get_connection() as conn:
        for region, data in regions.items():
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            top_cat = max(data['categories'], key=data['categories'].get) if data['categories'] else 'other'
            conn.execute(
                """INSERT OR REPLACE INTO monthly_metrics 
                   (month, region, article_count, avg_relevance, top_category)
                   VALUES (?, ?, ?, ?, ?)""",
                (month, region, data['count'], round(avg_score, 2), top_cat)
            )


def get_monthly_trends(limit: int = 12) -> list[dict]:
    """Get monthly aggregated metrics over time for trend visualization."""
    init_trends_table()
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT month, region, article_count, avg_relevance, top_category
               FROM monthly_metrics
               ORDER BY month DESC, region ASC
               LIMIT ?""",
            (limit * 20,)  # generous limit
        ).fetchall()
        return [dict(r) for r in rows]


def get_month_comparison(month_a: str, month_b: str) -> dict:
    """Compare two months: article counts, top regions, category shifts."""
    trends = get_monthly_trends(limit=24)
    months_data = {}
    for t in trends:
        m = t['month']
        if m not in months_data:
            months_data[m] = {'total': 0, 'regions': {}}
        months_data[m]['total'] += t['article_count']
        months_data[m]['regions'][t['region']] = {
            'count': t['article_count'],
            'avg_relevance': t['avg_relevance'],
            'top_category': t['top_category'],
        }

    def _safe(month):
        return months_data.get(month, {'total': 0, 'regions': {}})

    return {
        "month_a": month_a,
        "month_b": month_b,
        "a": _safe(month_a),
        "b": _safe(month_b),
        "change_percent": (
            round((_safe(month_b)['total'] - _safe(month_a)['total']) / max(_safe(month_a)['total'], 1) * 100, 1)
            if _safe(month_a)['total'] > 0 else 0
        )
    }


def get_all_region_timeline() -> list[dict]:
    """Get article counts per region over time for line charts."""
    trends = get_monthly_trends(limit=60)  # 5 years worth
    timeline = {}
    for t in trends:
        m = t['month']
        if m not in timeline:
            timeline[m] = {}
        timeline[m][t['region']] = t['article_count']
    result = []
    for month in sorted(timeline.keys()):
        entry = {"month": month}
        entry.update(timeline[month])
        result.append(entry)
    return result


def get_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        by_region = [dict(r) for r in conn.execute(
            "SELECT region, COUNT(*) as count FROM articles GROUP BY region ORDER BY count DESC"
        ).fetchall()]
        by_category = [dict(r) for r in conn.execute(
            "SELECT category, COUNT(*) as count FROM articles GROUP BY category ORDER BY count DESC"
        ).fetchall()]
        # Latest report
        latest = conn.execute("SELECT * FROM reports ORDER BY month DESC LIMIT 1").fetchone()
        return {
            "total_articles": total,
            "by_region": by_region,
            "by_category": by_category,
            "latest_report": dict(latest) if latest else None
        }


def insert_report(month: str, content: str, article_count: int):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO reports (month, content, article_count) VALUES (?, ?, ?)",
            (month, content, article_count)
        )


def get_reports(limit=12):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM reports ORDER BY month DESC LIMIT ?", (limit,)
        ).fetchall()]


def get_report_by_month(month: str):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM reports WHERE month = ?", (month,)).fetchone()
        return dict(row) if row else None


def seed_articles(articles: list[dict]):
    """Bulk insert articles, skipping duplicates."""
    count = 0
    for a in articles:
        # Convert string timestamps from JSON export
        if isinstance(a.get('tags'), str):
            import json as _json
            try:
                a['tags'] = _json.loads(a['tags'])
            except Exception:
                a['tags'] = []
        result = insert_article(a)
        if result:
            count += 1
    return count


def seed_reports(reports: list[dict]):
    """Bulk insert reports."""
    count = 0
    for r in reports:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO reports (month, content, article_count, created_at) VALUES (?, ?, ?, ?)",
                    (r['month'], r['content'], r.get('article_count', 0), r.get('created_at'))
                )
            count += 1
        except Exception:
            pass
    return count


def seed_metrics(metrics: list[dict]):
    """Bulk insert monthly metrics."""
    init_trends_table()
    count = 0
    for m in metrics:
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO monthly_metrics (month, region, article_count, avg_relevance, top_category) VALUES (?, ?, ?, ?, ?)",
                    (m['month'], m['region'], m.get('article_count', 0), m.get('avg_relevance', 0), m.get('top_category', 'other'))
                )
            count += 1
        except Exception:
            pass
    return count
