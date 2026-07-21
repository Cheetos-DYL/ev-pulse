"""EV Pulse — FastAPI backend for EV charging intelligence."""

import os
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager

import csv
import io
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from .db import (
    init_db, insert_article, get_articles, get_article_by_id,
    get_stats, get_reports, get_report_by_month,
    get_monthly_trends, get_month_comparison, get_all_region_timeline,
    record_monthly_metrics, seed_articles, seed_reports, seed_metrics,
    search_articles, get_connection, insert_report
)
from .scraper import collect_all_regions
from .analyzer import batch_analyze
from .reporter import generate_monthly_report
from .newsletter import generate_newsletter_html, get_newsletter_text
from .sources import SOURCES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("EV Pulse database initialized")

    # Auto-seed if database is empty (persists across Render deploys)
    stats = get_stats()
    if stats.get("total_articles", 0) == 0:
        seed_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
        if os.path.exists(seed_path):
            try:
                with open(seed_path) as f:
                    data = json.load(f)
                a = seed_articles(data.get("articles", []))
                r = seed_reports(data.get("reports", []))
                m = seed_metrics(data.get("metrics", []))
                logger.info(f"Auto-seeded: {a} articles, {r} reports, {m} metrics")
            except Exception as e:
                logger.error(f"Auto-seed failed: {e}")
        else:
            logger.info("No seed_data.json found, skipping auto-seed")
    else:
        logger.info(f"Database has {stats['total_articles']} articles, skipping auto-seed")

    yield


app = FastAPI(
    title="EV Pulse",
    description="EV Charging Intelligence for Emerging Markets",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ev-pulse", "time": datetime.now().isoformat()}


# ─── Articles ─────────────────────────────────────────────

@app.get("/api/articles")
def list_articles(
    region: str = None,
    category: str = None,
    min_relevance: float = 0,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    articles = get_articles(region=region, category=category,
                           min_relevance=min_relevance, limit=limit, offset=offset)
    return {"articles": articles, "count": len(articles)}


# ─── CSV Export ────────────────────────────────────────────

@app.get("/api/articles/csv")
def export_csv(
    region: str = None,
    category: str = None,
    min_relevance: float = Query(0, ge=0),
    limit: int = Query(10000, le=50000),
):
    """Export articles as CSV download."""
    articles = get_articles(region=region, category=category,
                           min_relevance=min_relevance, limit=limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "translated_title", "url", "source", "region",
        "category", "relevance_score", "summary", "why_it_matters",
        "keywords", "published_at", "collected_at"
    ])
    for a in articles:
        keywords = a.get("keywords", [])
        if isinstance(keywords, (list, tuple)):
            keywords_str = "; ".join(str(k) for k in keywords)
        else:
            keywords_str = str(keywords)
        writer.writerow([
            a["id"],
            a.get("translated_title") or a["title"],
            a.get("translated_title", ""),
            a["url"],
            a["source"],
            a["region"],
            a.get("category", "other"),
            a.get("relevance_score", 0),
            (a.get("summary") or "")[:500],
            a.get("why_it_matters", ""),
            keywords_str,
            a.get("published_at") or "",
            a.get("collected_at") or "",
        ])

    output.seek(0)
    filename = f"ev-pulse-export-{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/articles/{article_id}")
def get_article(article_id: int):
    article = get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


# ─── Search ────────────────────────────────────────────────

@app.get("/api/articles/search")
def search(
    q: str = Query("", description="Search keyword"),
    region: str = None,
    category: str = None,
    min_relevance: float = Query(0, ge=0),
    date_from: str = None,
    date_to: str = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    """Full-text search across articles."""
    if not q and not region and not category:
        return {"articles": [], "count": 0, "query": q}
    articles = search_articles(
        query=q, region=region, category=category,
        min_relevance=min_relevance,
        date_from=date_from, date_to=date_to,
        limit=limit, offset=offset
    )
    return {"articles": articles, "count": len(articles), "query": q}



# ─── Collection ───────────────────────────────────────────

@app.post("/api/collect")
def run_collection(use_llm: bool = True):
    """Collect articles from all RSS feeds and analyze them."""
    logger.info("Starting collection from all regions...")
    results = collect_all_regions()

    total_collected = 0
    total_stored = 0
    total_analyzed = 0

    for region, articles in results.items():
        total_collected += len(articles)

        # Analyze
        analyzed = batch_analyze(articles, use_llm=use_llm)
        total_analyzed += len(analyzed)

        # Store
        for article in analyzed:
            result = insert_article(article)
            if result:
                total_stored += 1

    return {
        "status": "completed",
        "collected": total_collected,
        "analyzed": total_analyzed,
        "stored": total_stored,
        "duplicates_skipped": total_analyzed - total_stored,
        "regions": {r: len(a) for r, a in results.items()}
    }


@app.post("/api/collect/{region}")
def run_collection_region(region: str, use_llm: bool = True):
    """Collect from a single region."""
    if region not in SOURCES:
        raise HTTPException(status_code=400, detail=f"Unknown region: {region}")

    articles = collect_all_regions().get(region, [])
    analyzed = batch_analyze(articles, use_llm=use_llm)
    stored = 0
    for article in analyzed:
        if insert_article(article):
            stored += 1

    return {
        "status": "completed",
        "region": region,
        "collected": len(articles),
        "analyzed": len(analyzed),
        "stored": stored
    }


# ─── Reports ──────────────────────────────────────────────

@app.get("/api/reports")
def list_reports(limit: int = 12):
    return {"reports": get_reports(limit)}


@app.get("/api/reports/{month}")
def get_report(month: str):
    report = get_report_by_month(month)
    if not report:
        raise HTTPException(status_code=404, detail=f"No report for {month}")
    return report


@app.post("/api/reports/generate")
def generate_report(month: str = None):
    """Generate a monthly report for the given month."""
    if not month:
        month = datetime.now().strftime("%Y-%m")
    report_content = generate_monthly_report(month)
    return {"month": month, "content": report_content}


# ─── Stats ────────────────────────────────────────────────

@app.get("/api/stats")
def stats():
    return get_stats()


# ─── Article Update ────────────────────────────────────────

class ArticleUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    translated_title: str | None = None

@app.patch("/api/articles/{article_id}")
def update_article(article_id: int, update: ArticleUpdate):
    """Update an article's title and/or summary."""
    existing = get_article_by_id(article_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Article not found")
    with get_connection() as conn:
        fields = []
        params = []
        if update.title is not None:
            fields.append("title = ?")
            params.append(update.title)
        if update.summary is not None:
            fields.append("summary = ?")
            params.append(update.summary)
        if update.translated_title is not None:
            fields.append("translated_title = ?")
            params.append(update.translated_title)
        if not fields:
            return {"status": "no_changes"}
        params.append(article_id)
        conn.execute(f"UPDATE articles SET {', '.join(fields)} WHERE id = ?", params)
    return {"status": "updated", "id": article_id, "title": update.title, "summary": update.summary}


# ─── Trends & Comparison ─────────────────────────

@app.get("/api/trends")
def trends(limit: int = 12):
    """Monthly aggregated metrics over time."""
    return {"trends": get_monthly_trends(limit=limit)}


@app.get("/api/trends/timeline")
def region_timeline():
    """Article count per region over time (for line charts)."""
    return {"timeline": get_all_region_timeline()}


@app.get("/api/trends/compare")
def compare(month_a: str, month_b: str = None):
    """Compare two months."""
    if not month_b:
        from datetime import datetime
        month_b = datetime.now().strftime("%Y-%m")
    return get_month_comparison(month_a, month_b)


@app.get("/api/regions")
def regions():
    return {"regions": {k: v["name"] for k, v in SOURCES.items()}}


@app.get("/api/weekly")
def weekly_summary():
    """Articles from last 7 days, grouped by region."""
    from datetime import datetime, timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    articles = get_articles(limit=500, min_relevance=0)
    recent = [a for a in articles if a.get("collected_at", "")[:10] >= week_ago]
    by_region = {}
    for a in recent:
        r = a["region"]
        if r not in by_region:
            by_region[r] = {"count": 0, "articles": []}
        by_region[r]["count"] += 1
        by_region[r]["articles"].append(a)
    # Sort each region by score, keep top 5
    for r in by_region:
        by_region[r]["articles"].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        by_region[r]["articles"] = by_region[r]["articles"][:5]
    return {"week_start": week_ago, "total": len(recent), "regions": by_region}


@app.get("/api/weekly/report")
def weekly_report():
    """Markdown report: weekly stats + top articles per region."""
    from datetime import datetime, timedelta
    from app.sources import CATEGORY_NAMES
    REGION_ORDER = ["korea","uae","southeast_asia","japan","australia","taiwan","africa","brazil","mexico"]
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    articles = get_articles(limit=500, min_relevance=0)
    recent = [a for a in articles if a.get("collected_at", "")[:10] >= week_ago]
    if not recent:
        return {"report": "No articles collected this week.", "total": 0}

    by_region = {}
    for a in recent:
        r = a["region"]
        if r not in by_region:
            by_region[r] = {"count": 0, "articles": [], "cats": {}}
        by_region[r]["count"] += 1
        by_region[r]["articles"].append(a)
        cat = a.get("category", "other")
        by_region[r]["cats"][cat] = by_region[r]["cats"].get(cat, 0) + 1
    for r in by_region:
        by_region[r]["articles"].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    lines = [f"# 📰 EV Pulse — Weekly Briefing", f"**Week of {week_ago}** — {len(recent)} articles across {len(by_region)} regions", ""]
    lines.append("## 🔥 Market Activity")
    for region in [r for r in REGION_ORDER if r in by_region]:
        rd = by_region[region]
        flag = {"korea":"🇰🇷","uae":"🇦🇪","southeast_asia":"🌏","japan":"🇯🇵","australia":"🇦🇺","taiwan":"🇹🇼","africa":"🌍","brazil":"🇧🇷","mexico":"🇲🇽"}.get(region,"")
        lines.append(f"- {flag} **{region.replace('_',' ').title()}**: {rd['count']} articles")
    lines.append("")
    lines.append("## 📊 Category Breakdown")
    all_cats = {}
    for rd in by_region.values():
        for cat, n in rd["cats"].items():
            all_cats[cat] = all_cats.get(cat, 0) + n
    for cat in sorted(all_cats, key=all_cats.get, reverse=True):
        name = CATEGORY_NAMES.get(cat, cat)
        lines.append(f"- {name}: {all_cats[cat]}")
    lines.append("")
    for region in [r for r in REGION_ORDER if r in by_region]:
        rd = by_region[region]
        flag = {"korea":"🇰🇷","uae":"🇦🇪","southeast_asia":"🌏","japan":"🇯🇵","australia":"🇦🇺","taiwan":"🇹🇼","africa":"🌍","brazil":"🇧🇷","mexico":"🇲🇽"}.get(region,"")
        name = {"korea":"South Korea","uae":"UAE / Middle East","southeast_asia":"SE Asia","japan":"Japan","australia":"Australia","taiwan":"Taiwan","africa":"Africa","brazil":"Brazil","mexico":"Mexico"}.get(region, region)
        lines.append(f"## {flag} {name} ({rd['count']})")
        for a in rd["articles"][:3]:
            title = a.get("translated_title") or a["title"]
            score = a.get("relevance_score", 0)
            lines.append(f"- **{title[:100]}** [{score:.0f}]")
            lines.append(f"  [{a['source']}]({a['url']})")
        lines.append("")

    return {"report": "\n".join(lines), "total": len(recent)}


# ─── Wiki Graph (Obsidian-style) ───────────────────────

@app.get("/api/graph")
def get_graph(limit: int = 200, min_relevance: float = Query(3, ge=0)):
    """Build a graph of articles connected by shared keywords, categories, and regions."""
    articles = get_articles(limit=limit, min_relevance=min_relevance)
    nodes = {}
    edges = set()

    CATEGORY_LABELS = {
        "government_policy": "Policy", "ma_partnership": "M&A",
        "charger_install": "Install", "charging_standards": "Standards",
        "grid_pricing": "Grid", "ev_sales_stats": "Stats",
    }

    # Track keyword→articles for backlinks
    kw_to_articles = {}

    for a in articles:
        art_id = f"article:{a['id']}"
        category = a.get("category", "other")
        nodes[art_id] = {
            "id": art_id, "type": "article",
            "label": a.get("translated_title") or a["title"],
            "title_original": a["title"],
            "region": a.get("region", "?"),
            "category": category,
            "url": a.get("url", ""),
            "relevance": a.get("relevance_score", 0),
        }

        # Region node
        region_id = f"region:{a['region']}"
        if region_id not in nodes:
            nodes[region_id] = {
                "id": region_id, "type": "region",
                "label": SOURCES.get(a["region"], {}).get("name", a["region"]),
            }
        edges.add((art_id, region_id))

        # Category node
        cat_label = CATEGORY_LABELS.get(category, category)
        cat_id = f"category:{category}"
        if cat_id not in nodes:
            nodes[cat_id] = {
                "id": cat_id, "type": "category",
                "label": cat_label,
            }
        edges.add((art_id, cat_id))

        # Keyword nodes + backlink tracking
        keywords = a.get("keywords", [])
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords)
            except Exception:
                keywords = []
        article_kws = []
        for kw in keywords[:6]:
            if not kw or len(str(kw).strip()) < 2:
                continue
            kw_str = str(kw).strip()
            kw_id = f"kw:{kw_str.lower()}"
            if kw_id not in nodes:
                nodes[kw_id] = {
                    "id": kw_id, "type": "keyword",
                    "label": kw_str,
                }
            edges.add((art_id, kw_id))
            article_kws.append(kw_id)
            if kw_id not in kw_to_articles:
                kw_to_articles[kw_id] = []
            kw_to_articles[kw_id].append(art_id)

        # Article→article backlinks via shared keywords (only 2+ shared)
        art_kw_set = set(article_kws)
        if len(art_kw_set) > 1:
            for kw_id in art_kw_set:
                for linked_art in kw_to_articles.get(kw_id, []):
                    if linked_art != art_id and (art_id, linked_art) not in edges and (linked_art, art_id) not in edges:
                        # Check if they share at least 2 keywords
                        linked_kws = set()
                        for a2 in articles:
                            if f"article:{a2['id']}" == linked_art:
                                kws2 = a2.get("keywords", [])
                                if isinstance(kws2, str):
                                    try:
                                        kws2 = json.loads(kws2)
                                    except Exception:
                                        kws2 = []
                                linked_kws = {f"kw:{str(k).strip().lower()}" for k in kws2[:6] if k and len(str(k).strip()) >= 2}
                                break
                        shared = art_kw_set & linked_kws
                        if len(shared) >= 2:
                            edges.add((art_id, linked_art))

    return {
        "nodes": list(nodes.values()),
        "edges": [{"source": s, "target": t} for s, t in edges],
        "stats": {
            "articles": sum(1 for n in nodes.values() if n["type"] == "article"),
            "keywords": sum(1 for n in nodes.values() if n["type"] == "keyword"),
            "regions": sum(1 for n in nodes.values() if n["type"] == "region"),
            "categories": sum(1 for n in nodes.values() if n["type"] == "category"),
            "backlinks": sum(1 for e in edges if e[0].startswith("article:") and e[1].startswith("article:")),
        }
    }


# ─── Newsletter ─────────────────────────────────────────

@app.get("/api/newsletter/{month}")
def newsletter_html(month: str):
    """Get HTML newsletter for a month."""
    html = generate_newsletter_html(month)
    return {"month": month, "html": html}


@app.get("/api/newsletter/{month}/text")
def newsletter_text(month: str):
    """Get plain text newsletter for a month."""
    text = get_newsletter_text(month)
    return {"month": month, "text": text}


# ─── Seed (import local data) ──────────────────────────

class SeedData(BaseModel):
    articles: list[dict] = []
    reports: list[dict] = []
    metrics: list[dict] = []

@app.post("/api/seed")
def seed_database(data: SeedData):
    """Seed the database with exported articles, reports, and metrics."""
    article_count = seed_articles(data.articles)
    report_count = seed_reports(data.reports)
    metric_count = seed_metrics(data.metrics)
    return {
        "status": "seeded",
        "articles_inserted": article_count,
        "reports_inserted": report_count,
        "metrics_inserted": metric_count,
        "total_articles": len(data.articles),
        "total_reports": len(data.reports),
        "total_metrics": len(data.metrics),
    }


@app.post("/api/maintenance/rebuild")
def maintenance_rebuild():
    """Delete all data and run fresh collection + analysis."""
    logger.warning("MAINTENANCE: Rebuilding entire database from scratch")
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM articles")
            conn.execute("DELETE FROM reports")
            conn.execute("DELETE FROM monthly_metrics")
        logger.info("Database cleared, starting fresh collection...")
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")

    # Run fresh collection with LLM
    results = collect_all_regions()
    total_stored = 0
    total_collected = sum(len(a) for a in results.values())

    for region, articles in results.items():
        analyzed = batch_analyze(articles, use_llm=True)
        for article in analyzed:
            result = insert_article(article)
            if result:
                total_stored += 1

    # Generate report for current month
    month = datetime.now().strftime("%Y-%m")
    report_content = generate_monthly_report(month)
    insert_report(month, report_content, total_stored)

    return {
        "status": "completed",
        "collected": total_collected,
        "stored": total_stored,
        "message": f"Rebuilt database: {total_stored} articles from {total_collected} collected"
    }
@app.post("/api/reanalyze")
def reanalyze_all(limit: int = 100, offset: int = 0):
    """Re-analyze existing articles with LLM to translate titles to English."""
    from .analyzer import llm_analyze_article, get_client, llm_call, get_last_llm_error
    # Debug: check if client/key is available
    c = get_client()
    llm_status = "client_ready" if c else "no_client"

    # Test the LLM directly
    test_result = llm_call(
        messages=[{"role": "user", "content": "Say 'TEST_OK' and nothing else."}],
        temperature=0,
        max_tokens=20
    )
    llm_test = test_result if test_result else get_last_llm_error()

    try:
        articles = get_articles(limit=limit, offset=offset)
        translated = 0
        errors = []
        for article in articles:
            old_title = article.get("title", "")
            old_summary = article.get("summary", "")
            if not old_title or article.get("translated_title"):
                continue
            # Skip articles already in English (no non-Latin chars)
            has_non_latin = any(ord(c) > 0x2E80 for c in old_title)
            if not has_non_latin and article.get("keywords"):
                continue  # Already has keywords, skip
            if not has_non_latin:
                # English article missing keywords — extract only
                try:
                    result = llm_analyze_article(article)
                    if result.get("keywords"):
                        with get_connection() as conn:
                            conn.execute(
                                "UPDATE articles SET keywords = ? WHERE id = ?",
                                (json.dumps(result["keywords"]), article["id"])
                            )
                    # Still count as processed
                except Exception:
                    pass
                continue
            try:
                result = llm_analyze_article(article)
                if result.get("translated_title") and result["translated_title"] != old_title:
                    with get_connection() as conn:
                        conn.execute(
                            "UPDATE articles SET translated_title = ?, summary = ?, keywords = ?, analyzed = ? WHERE id = ?",
                            (result["translated_title"], result.get("summary", old_summary),
                             json.dumps(result.get("keywords", [])), 1, article["id"])
                        )
                    translated += 1
            except Exception as e:
                err_msg = f"Article {article.get('id')}: {type(e).__name__}: {e}"
                logger.warning(f"Failed to re-analyze article {article.get('id')}: {e}")
                errors.append(err_msg)
        return {"status": "completed", "translated": translated, "errors": errors, "total": len(articles), "llm_status": llm_status, "llm_test": llm_test}
    except Exception as e:
        logger.error(f"Reanalyze endpoint failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Serve Frontend ───────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
