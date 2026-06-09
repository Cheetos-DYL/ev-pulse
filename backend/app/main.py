"""EV Pulse — FastAPI backend for EV charging intelligence."""

import os
import json
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .db import (
    init_db, insert_article, get_articles, get_article_by_id,
    get_stats, get_reports, get_report_by_month,
    get_monthly_trends, get_month_comparison, get_all_region_timeline,
    record_monthly_metrics
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


@app.get("/api/articles/{article_id}")
def get_article(article_id: int):
    article = get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


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
