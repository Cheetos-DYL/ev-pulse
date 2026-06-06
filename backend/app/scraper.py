"""RSS feed scraper using Google News RSS for reliable collection.

Google News RSS is the most reliable source for regional EV news.
Each region gets targeted queries that filter by geography.
"""

import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

from .sources import SOURCES, CATEGORIES

logger = logging.getLogger(__name__)


def _is_ev_related(title: str, summary: str) -> bool:
    """Check if article is about EV/charging."""
    text = f"{title} {summary}".lower()
    ev_keywords = [
        "ev charging", "electric vehicle", "charging station",
        "charging point", "ev policy", "ev incentive",
        "ev market", "ev adoption", "ev sales", "ev infrastructure",
        "charging network", "ev investment", "charging tariff",
        "v2g", "ultra-fast charging", "fast charging",
        "electric mobility", "ev rollout", "ev deployment",
    ]
    return any(kw in text for kw in ev_keywords)


def _get_google_news_rss(query: str) -> list[dict]:
    """Fetch articles from Google News RSS."""
    articles = []
    encoded_query = query.replace(' ', '+')
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            
            if not title or not link:
                continue
            
            # Get summary
            summary = ''
            if hasattr(entry, 'summary'):
                summary = BeautifulSoup(entry.summary, 'html.parser').get_text()[:500]
            
            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            
            articles.append({
                'title': title,
                'url': link,
                'source': 'Google News',
                'summary': summary,
                'published_at': published,
            })
    except Exception as e:
        logger.warning(f"Failed to fetch Google News: {e}")
    
    return articles


def collect_from_rss(region: str) -> list[dict]:
    """Collect EV-related articles from a region using Google News RSS."""
    articles = []
    source_config = SOURCES.get(region, {})
    feeds = source_config.get("feeds", [])
    
    # First try region-specific RSS feeds
    for feed_info in feeds:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:30]:
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                
                if not title or not link:
                    continue
                
                summary = ''
                if hasattr(entry, 'summary'):
                    summary = BeautifulSoup(entry.summary, 'html.parser').get_text()[:500]
                
                if _is_ev_related(title, summary):
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6]).isoformat()
                    
                    articles.append({
                        'title': title,
                        'url': link,
                        'source': feed_info["name"],
                        'region': region,
                        'language': feed_info.get('language', 'en'),
                        'summary': summary,
                        'published_at': published,
                    })
        except Exception as e:
            logger.warning(f"Failed to parse feed {feed_info['url']}: {e}")
            continue
    
    # Also use Google News RSS with region-specific queries
    region_queries = {
        'korea': 'Korea EV charging electric vehicle',
        'uae': 'UAE Dubai EV charging electric vehicle',
        'southeast_asia': 'Singapore Thailand Indonesia EV charging',
        'japan': 'Japan EV charging CHAdeMO electric vehicle',
        'australia': 'Australia EV charging electric vehicle',
        'taiwan': 'Taiwan EV charging electric vehicle',
        'africa': 'South Africa EV charging electric vehicle',
        'brazil': 'Brazil EV charging electric vehicle',
        'mexico': 'Mexico EV charging electric vehicle',
    }
    
    if region in region_queries:
        google_articles = _get_google_news_rss(region_queries[region])
        for article in google_articles:
            if _is_ev_related(article['title'], article['summary']):
                article['region'] = region
                article['language'] = 'en'
                articles.append(article)
    
    return articles


def collect_all_regions() -> dict[str, list[dict]]:
    """Collect from all configured regions."""
    results = {}
    for region in SOURCES:
        articles = collect_from_rss(region)
        results[region] = articles
        logger.info(f"[{region}] Collected {len(articles)} articles")
    return results
