"""SQLite database for EV Pulse — article storage and reports."""

import sqlite3
import os
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
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                region TEXT NOT NULL,
                country TEXT,
                language TEXT DEFAULT 'en',
                summary TEXT,
                content TEXT,
                relevance_score REAL DEFAULT 0,
                category TEXT CHECK(category IN ('service', 'trend', 'policy', 'other')),
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
                   (title, url, source, region, country, language, summary, content,
                    relevance_score, category, tags, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    article['title'], article['url'], article['source'],
                    article['region'], article.get('country'),
                    article.get('language', 'en'), article.get('summary'),
                    article.get('content'), article.get('relevance_score', 0),
                    article.get('category', 'other'),
                    str(article.get('tags', [])), article.get('published_at')
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
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_article_by_id(article_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        return dict(row) if row else None


def get_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        by_region = [dict(r) for r in conn.execute(
            "SELECT region, COUNT(*) as count FROM articles GROUP BY region ORDER BY count DESC"
        ).fetchall()]
        by_category = [dict(r) for r in conn.execute(
            "SELECT category, COUNT(*) as count FROM articles GROUP BY category ORDER BY count DESC"
        ).fetchall()]
        return {
            "total_articles": total,
            "by_region": by_region,
            "by_category": by_category
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
